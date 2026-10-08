"""Broker-side records and the interface every broker adapter implements."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

import pandas as pd

from ..strategy import EntrySignal


@dataclass
class WorkingOrder:
    signal: EntrySignal
    qty: int
    placed_at: pd.Timestamp
    order_id: str = ""


@dataclass
class Position:
    symbol: str
    qty: int
    raw_entry: float          # trade price at the fill, before spread/slippage
    entry_price: float        # what we actually paid per share, including spread/slippage
    stop: float
    target: float | None
    entry_time: pd.Timestamp
    signal: EntrySignal
    entry_costs: float
    legs: dict = field(default_factory=dict)   # broker-side exit orders (Alpaca bracket legs)


@dataclass
class Trade:
    symbol: str
    qty: int
    entry_time: pd.Timestamp
    exit_time: pd.Timestamp
    raw_entry: float
    entry_price: float
    raw_exit: float
    exit_price: float
    stop: float
    target: float | None
    exit_reason: str
    gross_pnl: float          # on raw trade prices
    costs: float              # spread + slippage + commissions + fees
    net_pnl: float
    initial_risk: float       # qty * (raw_entry - stop)
    reasons: list[str] = field(default_factory=list)

    @property
    def r_multiple(self) -> float:
        return self.net_pnl / self.initial_risk if self.initial_risk > 0 else 0.0


@dataclass
class BrokerEvent:
    kind: str                 # "filled", "expired", "rejected", "partial", "exit"
    symbol: str
    at: pd.Timestamp
    detail: str = ""
    trade: Trade | None = None


class Broker(Protocol):
    def submit_entry(self, signal: EntrySignal, qty: int, at: pd.Timestamp) -> BrokerEvent | None: ...

    def cancel_entries(self, at: pd.Timestamp, reason: str) -> list[BrokerEvent]: ...

    def flatten_all(self, at: pd.Timestamp, prices: dict[str, float], reason: str) -> list[BrokerEvent]: ...

    def equity(self, prices: dict[str, float]) -> float: ...
