"""One trading day's decision loop, shared by the backtester and the paper trader.

Order of operations for every completed 5-minute bar:
  1. scheduled actions (end-of-day flatten, entry-window close, pending risk flatten)
  2. the broker evaluates working orders and stops against the new bar
  3. daily loss limit is checked on mark-to-market equity
  4. strategies see the completed bar and may place orders (which can only fill on later bars)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

import pandas as pd

from .config import AppConfig, StrategyConfig
from .journal import TradeProposal
from .risk import DayRisk, position_size
from .strategy import OrbStrategy

MARKET = ("SPY", "QQQ")


@dataclass
class DayLog:
    proposals: list[TradeProposal] = field(default_factory=list)
    skipped: list[dict] = field(default_factory=list)
    violations: list[str] = field(default_factory=list)
    risk_events: list[str] = field(default_factory=list)
    events: list = field(default_factory=list)


class DaySession:
    def __init__(self, day: date, cfg: AppConfig, strat_cfg: StrategyConfig, broker, strategies: dict[str, OrbStrategy],
                 start_equity: float, data_source: str):
        self.day, self.cfg, self.sc, self.broker = day, cfg, strat_cfg, broker
        self.strategies = strategies
        self.risk = DayRisk(start_equity, cfg.risk)
        self.start_equity = start_equity
        self.source = data_source
        self.last_px: dict[str, float] = {}
        self.flatten_next = False
        self.finished = False
        self.log = DayLog()

    def _skip(self, s, t, reason):
        self.log.skipped.append({"date": self.day, "symbol": s, "time": t, "reason": reason})

    def kill(self, ts: pd.Timestamp, reason: str) -> None:
        """Emergency stop: cancel everything, flatten at the last known prices, halt for the day."""
        self.risk.halt(reason)
        self.log.risk_events.append(f"{self.day}: {reason}")
        px = {s: self.last_px.get(s) for s in self.broker.positions}
        self.log.events += self.broker.flatten_all(ts, px, reason)
        for st in self.strategies.values():
            st.stop()
        self.finished = True

    def step(self, ts: pd.Timestamp, bars_now: dict[str, pd.Series], vwap_now: dict[str, float]) -> None:
        if self.finished:
            return
        sc, broker, risk = self.sc, self.broker, self.risk
        opens = {s: float(b.open) for s, b in bars_now.items()}

        if ts.time() >= sc.flatten_at or self.flatten_next:
            why = risk.halt_reason if self.flatten_next else "end-of-day flatten"
            px = {s: opens.get(s, self.last_px.get(s)) for s in broker.positions}
            self.log.events += broker.flatten_all(ts, px, why)
            for st in self.strategies.values():
                st.stop()
            self.flatten_next = False
            if ts.time() >= sc.flatten_at:
                self.finished = True
                return
        if ts.time() >= sc.entry_end and broker.working:
            for ev in broker.cancel_entries(ts, "entry window closed"):
                if ev.symbol in self.strategies:
                    self.strategies[ev.symbol].on_order_dead()

        for s in list(set(broker.working) | set(broker.positions)):
            if s not in bars_now:
                continue
            for ev in broker.on_bar(s, ts, bars_now[s]):
                self.log.events.append(ev)
                if ev.kind in ("filled", "partial"):
                    risk.entries += 1
                    self.strategies[s].on_order_filled()
                    if ts.time() >= sc.entry_end:
                        self.log.violations.append(f"{self.day} {s}: fill after entry window")
                elif ev.kind in ("expired", "rejected"):
                    self.strategies[s].on_order_dead()
                    self._skip(s, ts, ev.detail)
        for s, b in bars_now.items():
            self.last_px[s] = float(b.close)

        eq = broker.equity(self.last_px)
        if risk.check(eq):
            self.log.risk_events.append(f"{self.day}: {risk.halt_reason}")
            broker.cancel_entries(ts, risk.halt_reason)
            for st in self.strategies.values():
                st.stop()
            self.flatten_next = True
            return

        mk = all(m in bars_now and float(bars_now[m].close) > vwap_now[m] for m in MARKET)
        for s, st in self.strategies.items():
            if s not in bars_now:
                continue
            sig = st.on_bar(ts, bars_now[s], vwap_now[s], mk)
            if sig is None:
                continue
            qty, why = position_size(sig.trigger, sig.stop_loss, eq, broker.available_cash(), self.cfg.risk,
                                     self.cfg.costs)
            ok, block = risk.can_enter(eq, qty * sig.risk_per_share)
            if ok and risk.entries + len(broker.working) >= self.cfg.risk.max_entries_per_day:
                ok, block = False, "max entries per day (counting working orders)"
            prop = TradeProposal.from_signal(sig, qty, float(bars_now[s].close), self.source)
            self.log.proposals.append(prop)
            if qty < 1 or not ok:
                prop.status = "skipped: " + (why if qty < 1 else block)
                self._skip(s, sig.created_at, prop.status)
                st.on_order_dead()
                continue
            ev = broker.submit_entry(sig, qty, sig.created_at)
            if ev is not None and ev.kind == "rejected":
                prop.status = "rejected: " + ev.detail
                self._skip(s, sig.created_at, prop.status)
                st.on_order_dead()
            else:
                prop.status = "order working"

    def end(self, last_ts: pd.Timestamp) -> float:
        broker = self.broker
        if broker.positions or broker.working:
            self.log.violations.append(f"{self.day}: not flat at end of day")
            broker.flatten_all(last_ts, {s: self.last_px[s] for s in broker.positions}, "forced EOD")
        if self.risk.entries > self.cfg.risk.max_entries_per_day:
            self.log.violations.append(f"{self.day}: {self.risk.entries} entries")
        if broker.cash < -1e-6:
            self.log.violations.append(f"{self.day}: negative cash")
        loss = self.start_equity - broker.cash
        if loss > self.risk.loss_limit * 1.5:
            self.log.risk_events.append(
                f"{self.day}: day loss ${loss:.2f} overshot the ${self.risk.loss_limit:.2f} limit (gap/slippage)")
        for st in self.strategies.values():
            for rj in st.rejections:
                self._skip(rj.symbol, rj.at, rj.reason)
        return broker.cash
