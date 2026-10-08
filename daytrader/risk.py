"""Position sizing and account-level risk limits."""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from .config import CostConfig, RiskConfig


def est_cost_per_share(price: float, costs: CostConfig) -> float:
    """Round-trip estimate: spread + slippage on both sides, commissions and sale fees."""
    half = max(costs.min_half_spread, price * costs.half_spread_bps / 1e4)
    slip = price * costs.slippage_bps / 1e4
    fees = price * costs.sec_fee_per_dollar + costs.taf_per_share
    return 2 * (half + slip) + 2 * costs.commission_per_share + fees


def position_size(entry: float, stop: float, equity: float, cash: float, risk: RiskConfig,
                  costs: CostConfig) -> tuple[int, str]:
    """Whole shares so that (entry - stop + costs) * qty <= risk budget and qty * entry <= cash."""
    per_share_risk = entry - stop
    if per_share_risk <= 0:
        return 0, "stop is not below entry"
    budget = equity * risk.risk_per_trade
    by_risk = budget / (per_share_risk + est_cost_per_share(entry, costs))
    by_cash = cash * risk.max_position_fraction / (entry * 1.001)
    qty = math.floor(min(by_risk, by_cash))
    if qty < 1:
        return 0, f"size rounds to 0 shares (risk budget ${budget:.2f}, risk/share ${per_share_risk:.2f})"
    return qty, "risk-limited" if by_risk <= by_cash else "cash-limited"


@dataclass
class DayRisk:
    start_equity: float
    cfg: RiskConfig
    entries: int = 0
    halted: bool = False
    halt_reason: str = ""
    events: list[str] = field(default_factory=list)

    @property
    def loss_limit(self) -> float:
        return self.start_equity * self.cfg.max_daily_loss

    def can_enter(self, equity_now: float, new_trade_risk: float) -> tuple[bool, str]:
        if self.halted:
            return False, f"trading halted: {self.halt_reason}"
        if self.entries >= self.cfg.max_entries_per_day:
            return False, f"max {self.cfg.max_entries_per_day} entries per day reached"
        day_loss = max(0.0, self.start_equity - equity_now)
        if day_loss + new_trade_risk > self.loss_limit:
            return False, (f"would exceed daily loss limit (${day_loss:.2f} lost + ${new_trade_risk:.2f} "
                           f"at risk > ${self.loss_limit:.2f})")
        return True, ""

    def check(self, equity_now: float) -> bool:
        """Returns True if the daily loss limit has just been breached (caller must flatten)."""
        if not self.halted and self.start_equity - equity_now >= self.loss_limit:
            self.halt(f"daily loss limit hit (equity {equity_now:.2f} vs start {self.start_equity:.2f})")
            return True
        return False

    def halt(self, reason: str) -> None:
        self.halted, self.halt_reason = True, reason
        self.events.append(reason)
