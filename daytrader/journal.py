"""Trade proposals in the required reporting format, and CSV journals."""
from __future__ import annotations

import csv
from dataclasses import asdict, dataclass, field
from pathlib import Path

import pandas as pd

from .strategy import EntrySignal


@dataclass
class TradeProposal:
    ticker: str
    timestamp: pd.Timestamp
    market_price: float
    data_source: str
    entry_trigger: str
    stop_loss: float
    profit_target: float | None
    position_size: int
    dollars_at_risk: float
    reward_risk: float | None
    reasons: list[str] = field(default_factory=list)
    invalidation: list[str] = field(default_factory=list)
    status: str = "proposed"

    @classmethod
    def from_signal(cls, sig: EntrySignal, qty: int, last_price: float, source: str) -> "TradeProposal":
        target = sig.target(sig.trigger)
        trig = (f"buy-stop at {sig.trigger:.2f} (valid until {sig.expires_at:%H:%M} ET)" if sig.order_type == "stop"
                else f"market buy at next bar open (ref {sig.trigger:.2f})")
        return cls(sig.symbol, sig.created_at, last_price, source, trig, sig.stop_loss, target, qty,
                   round(qty * sig.risk_per_share, 2), sig.target_r, sig.reasons, sig.invalidation)

    def to_text(self) -> str:
        tgt = f"{self.profit_target:.2f}" if self.profit_target is not None else "none (stop or end of day)"
        rr = f"{self.reward_risk:.1f} : 1" if self.reward_risk is not None else "open-ended"
        lines = [f"Ticker:            {self.ticker}",
                 f"Date / time:       {self.timestamp:%Y-%m-%d %H:%M %Z}",
                 f"Market price:      {self.market_price:.2f} (source: {self.data_source})",
                 f"Entry trigger:     {self.entry_trigger}",
                 f"Stop-loss:         {self.stop_loss:.2f}",
                 f"Profit target:     {tgt}",
                 f"Position size:     {self.position_size} shares",
                 f"Dollars at risk:   ${self.dollars_at_risk:.2f} (before costs)",
                 f"Reward : risk:     {rr}",
                 "Why it qualifies:  " + "; ".join(self.reasons),
                 "Invalidated if:    " + "; ".join(self.invalidation),
                 f"Status:            {self.status}"]
        return "\n".join(lines)


NO_TRADE = "NO TRADE"


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("")
        return
    keys = list(rows[0].keys())
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow({k: (";".join(v) if isinstance(v, list) else v) for k, v in r.items()})


def trade_rows(trades) -> list[dict]:
    rows = []
    for t in trades:
        d = asdict(t)
        d["r_multiple"] = round(t.r_multiple, 3)
        rows.append(d)
    return rows
