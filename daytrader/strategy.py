"""Rule-based signal engine: 15-minute opening-range breakout, long only, with VWAP filter and a
pullback-retest confirmation. One state machine per symbol per day, fed one COMPLETED bar at a time,
so it cannot see the future in a backtest or in paper trading.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import pandas as pd

from .config import StrategyConfig
from .indicators import OpeningRange


class State(Enum):
    FORMING_RANGE = "forming_range"
    WAIT_BREAKOUT = "wait_breakout"
    BROKEN_OUT = "broken_out"
    ORDER_PENDING = "order_pending"
    IN_TRADE = "in_trade"
    DONE = "done"


@dataclass
class EntrySignal:
    symbol: str
    created_at: pd.Timestamp        # time the signal bar completed
    order_type: str                 # "stop" (buy-stop above the confirmation bar) or "market" (next open)
    trigger: float                  # buy-stop price, or the reference price for a market order
    stop_loss: float
    target_r: float | None
    expires_at: pd.Timestamp
    reasons: list[str] = field(default_factory=list)
    invalidation: list[str] = field(default_factory=list)

    @property
    def risk_per_share(self) -> float:
        return self.trigger - self.stop_loss

    def target(self, entry: float) -> float | None:
        return None if self.target_r is None else entry + self.target_r * (entry - self.stop_loss)


@dataclass
class Rejection:
    symbol: str
    at: pd.Timestamp
    reason: str


@dataclass(frozen=True)
class DayContext:
    symbol: str
    prior_high: float | None
    prior_close: float | None
    day_open: float


class OrbStrategy:
    def __init__(self, cfg: StrategyConfig, ctx: DayContext, orange: OpeningRange):
        self.cfg, self.ctx, self.orange = cfg, ctx, orange
        self.state = State.WAIT_BREAKOUT
        self.rejections: list[Rejection] = []
        self._bar = pd.Timedelta(minutes=cfg.bar_minutes)

    # --- engine callbacks -------------------------------------------------------------------
    def on_order_filled(self) -> None:
        self.state = State.IN_TRADE

    def on_order_dead(self) -> None:
        """Entry order expired, was rejected, or could not be sized: look for another retest."""
        if self.state == State.ORDER_PENDING:
            self.state = State.BROKEN_OUT if self.cfg.require_retest else State.WAIT_BREAKOUT

    def stop(self) -> None:
        if self.state not in (State.IN_TRADE,):
            self.state = State.DONE

    # --- main step ----------------------------------------------------------------------------
    def on_bar(self, ts: pd.Timestamp, bar: pd.Series, vwap: float, market_ok: bool) -> EntrySignal | None:
        """`ts` is the bar's start; the bar is complete at ts + bar length."""
        done_at = ts + self._bar
        cfg, o = self.cfg, self.orange
        if self.state in (State.IN_TRADE, State.DONE, State.ORDER_PENDING):
            return None
        if ts.time() < cfg.entry_start:
            return None
        if done_at.time() > cfg.entry_end:
            self.state = State.DONE
            return None

        close = float(bar.close)
        if self.state == State.WAIT_BREAKOUT:
            if close <= o.high:
                return None
            why = self._filters(close, vwap, market_ok)
            if why:
                self._reject(done_at, "breakout ignored: " + why)
                return None
            if cfg.require_retest:
                self.state = State.BROKEN_OUT
                return None
            stop = min(float(bar.low), o.high) - cfg.tick
            return self._signal(done_at, "market", close, stop, ["5-min close above opening-range high"])

        # BROKEN_OUT: waiting for a pullback that holds the breakout level
        if close < o.high:
            self.state = State.WAIT_BREAKOUT
            self._reject(done_at, "breakout failed: closed back inside the opening range")
            return None
        tested = float(bar.low) <= o.high + cfg.retest_tolerance * o.width
        if not tested:
            return None
        why = self._filters(close, vwap, market_ok)
        if why:
            self._reject(done_at, "retest ignored: " + why)
            return None
        trigger = float(bar.high) + cfg.tick
        stop = float(bar.low) - cfg.tick
        return self._signal(done_at, "stop", trigger, stop,
                            ["5-min close above opening-range high",
                             "pullback tested the breakout level and closed above it"])

    # --- helpers --------------------------------------------------------------------------------
    def _filters(self, close: float, vwap: float, market_ok: bool) -> str:
        if close <= vwap:
            return "price not above session VWAP"
        if self.cfg.require_above_open and close <= self.ctx.day_open:
            return "price not above the day's open"
        if self.cfg.require_market_above_vwap and not market_ok:
            return "SPY/QQQ not both above their VWAP"
        return ""

    def _signal(self, done_at, order_type, trigger, stop, reasons) -> EntrySignal | None:
        cfg, o = self.cfg, self.orange
        min_stop = cfg.min_stop_fraction * o.width
        if trigger - stop < min_stop:
            stop = trigger - min_stop
        if trigger - o.high > cfg.max_extension * o.width:
            self._reject(done_at, f"extended: entry {trigger:.2f} is more than {cfg.max_extension} x range above OR high")
            return None
        risk = trigger - stop
        if risk <= 0:
            self._reject(done_at, "non-positive risk")
            return None
        ph = self.ctx.prior_high
        if ph is not None and trigger < ph < trigger + cfg.min_reward_risk * risk:
            self._reject(done_at, f"reward/risk to prior-day high {ph:.2f} is {(ph - trigger) / risk:.2f} < {cfg.min_reward_risk}")
            return None
        expires = done_at + self._bar * (cfg.confirm_bars if order_type == "stop" else 1)
        self.state = State.ORDER_PENDING
        return EntrySignal(
            symbol=self.ctx.symbol, created_at=done_at, order_type=order_type, trigger=round(trigger, 2),
            stop_loss=round(stop, 2), target_r=cfg.target_r, expires_at=expires,
            reasons=reasons + ["closed above session VWAP and the day's open",
                               "SPY and QQQ above their VWAP" if cfg.require_market_above_vwap
                               else "market filter off",
                               f"reward/risk to prior-day high >= {cfg.min_reward_risk} (or no overhead high)"],
            invalidation=[f"price trades at or below stop {stop:.2f}",
                          f"a 5-min close back below the opening-range high {o.high:.2f} before entry",
                          f"entry not triggered by {expires.strftime('%H:%M')} ET",
                          "SPY or QQQ falls below its VWAP before entry"],
        )

    def _reject(self, at, reason: str) -> None:
        self.rejections.append(Rejection(self.ctx.symbol, at, reason))
