"""Simulated broker for backtests and local paper trading.

Fill model (pessimistic on purpose):
- Orders are only evaluated against bars that START after the order was placed.
- Buy-stop fills at max(trigger, bar open) plus half-spread and slippage; market orders at the open.
- If a bar touches both the stop and the target, the stop is assumed to fill first.
- On the entry bar, the stop can be hit but the target is not taken.
- Stops gap: if a bar opens below the stop, the fill is at the open.
- A target limit only fills if the bar trades at least one tick through it (or opens above it).
- Fill size is capped at a fraction of the bar's volume; a random share of entries is rejected.
"""
from __future__ import annotations

import math
import random

import pandas as pd

from ..config import CostConfig
from ..strategy import EntrySignal
from .base import BrokerEvent, Position, Trade, WorkingOrder


class SimBroker:
    def __init__(self, cash: float, costs: CostConfig, tick: float = 0.01):
        self.cash = cash
        self.costs = costs
        self.tick = tick
        self.rng = random.Random(costs.seed)
        self.working: dict[str, WorkingOrder] = {}
        self.positions: dict[str, Position] = {}
        self.trades: list[Trade] = []
        self.log: list[BrokerEvent] = []

    # --- cost model ---------------------------------------------------------------------------
    def half_spread(self, price: float) -> float:
        return max(self.costs.min_half_spread, price * self.costs.half_spread_bps / 1e4)

    def _slip(self, price: float) -> float:
        return price * self.costs.slippage_bps / 1e4

    def _sell_fees(self, price: float, qty: int) -> float:
        return price * qty * self.costs.sec_fee_per_dollar + min(self.costs.taf_per_share * qty, self.costs.taf_max)

    # --- interface ----------------------------------------------------------------------------
    def reserved_cash(self) -> float:
        return sum(w.qty * w.signal.trigger * 1.001 for w in self.working.values())

    def available_cash(self) -> float:
        return self.cash - self.reserved_cash()

    def equity(self, prices: dict[str, float]) -> float:
        return self.cash + sum(p.qty * prices.get(s, p.raw_entry) for s, p in self.positions.items())

    def submit_entry(self, signal: EntrySignal, qty: int, at: pd.Timestamp) -> BrokerEvent | None:
        if signal.symbol in self.working or signal.symbol in self.positions:
            return self._event("rejected", signal.symbol, at, "already have an order or position")
        if self.rng.random() < self.costs.reject_probability:
            return self._event("rejected", signal.symbol, at, "simulated broker rejection")
        self.working[signal.symbol] = WorkingOrder(signal, qty, at)
        return None

    def cancel_entries(self, at: pd.Timestamp, reason: str) -> list[BrokerEvent]:
        out = [self._event("expired", s, at, reason) for s in list(self.working)]
        self.working.clear()
        return out

    def flatten_all(self, at: pd.Timestamp, prices: dict[str, float], reason: str) -> list[BrokerEvent]:
        out = self.cancel_entries(at, reason)
        for sym in list(self.positions):
            out.append(self._exit(sym, at, prices[sym], "market", reason))
        return out

    def on_bar(self, symbol: str, ts: pd.Timestamp, bar: pd.Series) -> list[BrokerEvent]:
        out: list[BrokerEvent] = []
        o, h, low = float(bar.open), float(bar.high), float(bar.low)
        w = self.working.get(symbol)
        if w is not None:
            sig = w.signal
            if ts >= sig.expires_at:
                del self.working[symbol]
                out.append(self._event("expired", symbol, ts, "entry not triggered in time"))
            elif sig.order_type == "market" or h >= sig.trigger:
                raw = o if sig.order_type == "market" else max(sig.trigger, o)
                out += self._enter(w, ts, raw, int(bar.volume))
                if symbol in self.positions and low <= self.positions[symbol].stop:
                    out.append(self._exit(symbol, ts, min(self.positions[symbol].stop, raw), "stop",
                                          "stopped on the entry bar"))
                return out
        p = self.positions.get(symbol)
        if p is None or p.entry_time == ts:
            return out
        if o <= p.stop:
            out.append(self._exit(symbol, ts, o, "stop", "gapped through stop"))
        elif low <= p.stop:
            out.append(self._exit(symbol, ts, p.stop, "stop", "stop hit"))
        elif p.target is not None and o >= p.target:
            out.append(self._exit(symbol, ts, o, "limit", "opened above target"))
        elif p.target is not None and h >= p.target + self.tick:
            out.append(self._exit(symbol, ts, p.target, "limit", "target hit"))
        return out

    # --- internals ----------------------------------------------------------------------------
    def _enter(self, w: WorkingOrder, ts: pd.Timestamp, raw: float, bar_volume: int) -> list[BrokerEvent]:
        sig = w.signal
        del self.working[sig.symbol]
        cap = math.floor(bar_volume * self.costs.max_fill_volume_fraction)
        qty = min(w.qty, cap)
        if qty < 1:
            return [self._event("rejected", sig.symbol, ts, "no liquidity in the fill bar")]
        price = raw + self.half_spread(raw) + self._slip(raw)
        cost = qty * price + qty * self.costs.commission_per_share
        if cost > self.cash:
            qty = math.floor(self.cash / (price + self.costs.commission_per_share))
            if qty < 1:
                return [self._event("rejected", sig.symbol, ts, "insufficient cash at fill")]
            cost = qty * price + qty * self.costs.commission_per_share
        self.cash -= cost
        entry_costs = qty * (price - raw) + qty * self.costs.commission_per_share
        self.positions[sig.symbol] = Position(sig.symbol, qty, raw, price, sig.stop_loss, sig.target(raw), ts, sig,
                                              entry_costs)
        kind = "partial" if qty < w.qty else "filled"
        return [self._event(kind, sig.symbol, ts, f"bought {qty} @ {price:.4f} (trade {raw:.2f})")]

    def _exit(self, symbol: str, ts: pd.Timestamp, raw: float, order_type: str, reason: str) -> BrokerEvent:
        p = self.positions.pop(symbol)
        price = raw if order_type == "limit" else raw - self.half_spread(raw) - self._slip(raw)
        fees = self._sell_fees(price, p.qty) + p.qty * self.costs.commission_per_share
        self.cash += p.qty * price - fees
        gross = p.qty * (raw - p.raw_entry)
        net = p.qty * (price - p.entry_price) - fees - p.qty * self.costs.commission_per_share
        trade = Trade(symbol, p.qty, p.entry_time, ts, p.raw_entry, p.entry_price, raw, price, p.stop, p.target,
                      reason, gross, gross - net, net, p.qty * (p.raw_entry - p.stop), list(p.signal.reasons))
        self.trades.append(trade)
        return self._event("exit", symbol, ts, f"{reason}: sold {p.qty} @ {price:.4f}", trade)

    def _event(self, kind, symbol, at, detail="", trade=None) -> BrokerEvent:
        ev = BrokerEvent(kind, symbol, at, detail, trade)
        self.log.append(ev)
        return ev
