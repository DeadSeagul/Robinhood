"""Configuration. Every strategy and risk parameter is fixed here, before any backtest is run.

Secrets are read from environment variables only and are never written to disk by this package.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field, replace
from datetime import time


class LiveTradingDisabled(RuntimeError):
    """Raised when anything other than paper or backtest mode is requested."""


@dataclass(frozen=True)
class StrategyConfig:
    name: str = "orb15_vwap_retest"
    opening_range_minutes: int = 15          # 15-min OR for the initial strategy (5-min OR is also recorded)
    bar_minutes: int = 5
    entry_start: time = time(9, 45)          # first bar that can confirm a breakout starts at 9:45
    entry_end: time = time(11, 0)            # no new entries (or working entry orders) after 11:00
    flatten_at: time = time(15, 55)          # every position is closed at the open of the 15:55 bar
    require_retest: bool = True              # wait for a pullback that holds the breakout level
    retest_tolerance: float = 0.15           # a retest bar's low must come within 0.15 x OR width of OR high
    confirm_bars: int = 2                    # the buy-stop above the retest bar stays live for 2 bars
    max_extension: float = 0.5               # skip if entry is more than 0.5 x OR width above OR high
    min_stop_fraction: float = 0.10          # stop distance must be at least 0.10 x OR width
    target_r: float | None = 2.0             # profit target in R; None = no target (stop or end of day only)
    min_reward_risk: float = 2.0             # reject if overhead resistance (prior-day high) caps reward below this
    require_market_above_vwap: bool = True   # SPY and QQQ must both trade above their session VWAP
    require_above_open: bool = True          # "bullish structure": price above the day's opening price
    tick: float = 0.01


@dataclass(frozen=True)
class ScannerConfig:
    min_price: float = 5.0
    min_avg_daily_volume: float = 1_000_000
    min_relative_opening_volume: float = 2.0  # 9:30-9:45 volume vs the same window's 20-day average
    lookback_days: int = 20
    max_candidates: int = 10
    max_spread_pct: float = 0.002             # live only: skip if quoted spread > 0.20% of price
    require_verified_news: bool = False       # backtests have no point-in-time news archive; see docs


@dataclass(frozen=True)
class RiskConfig:
    starting_equity: float = 25_000.0
    risk_per_trade: float = 0.0025            # 0.25% of equity at risk per trade
    max_daily_loss: float = 0.01              # 1% of the day's starting equity, realized + unrealized
    max_entries_per_day: int = 2
    max_position_fraction: float = 1.0        # no leverage: position value <= available cash
    allow_short: bool = False
    allow_options: bool = False


@dataclass(frozen=True)
class CostConfig:
    commission_per_share: float = 0.0         # Alpaca and most US retail brokers: $0 stock commissions
    min_half_spread: float = 0.005            # assumed half-spread floor in dollars
    half_spread_bps: float = 1.5              # assumed half-spread in basis points of price
    slippage_bps: float = 1.0                 # extra adverse slippage on market and stop fills
    # Regulatory fees on sales. Approximate; the SEC and FINRA reset these rates periodically.
    sec_fee_per_dollar: float = 0.0000278
    taf_per_share: float = 0.000166
    taf_max: float = 8.30
    reject_probability: float = 0.02          # share of entry orders randomly rejected
    max_fill_volume_fraction: float = 0.02    # never fill more than 2% of a bar's volume
    seed: int = 7


@dataclass(frozen=True)
class AppConfig:
    mode: str = "paper"                       # "backtest" or "paper"; nothing else is accepted
    strategy: StrategyConfig = field(default_factory=StrategyConfig)
    scanner: ScannerConfig = field(default_factory=ScannerConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)
    costs: CostConfig = field(default_factory=CostConfig)
    kill_switch_path: str = "KILL_SWITCH"
    journal_dir: str = "journal"

    def __post_init__(self) -> None:
        check_mode(self.mode)
        if self.risk.allow_short or self.risk.allow_options:
            raise ValueError("Short selling and options are disabled during initial testing.")


def check_mode(mode: str) -> str:
    if mode not in ("backtest", "paper"):
        raise LiveTradingDisabled(
            f"Mode {mode!r} is not allowed. This system only runs in 'backtest' or 'paper' mode; "
            "live order routing is not implemented and needs explicit authorization first."
        )
    return mode


def env_mode() -> str:
    return check_mode(os.environ.get("TRADING_MODE", "paper"))


def variant(base: StrategyConfig, **changes) -> StrategyConfig:
    return replace(base, **changes)


# Pre-registered strategy variants. Each is tested on its own; they are never combined or tuned.
VARIANTS: dict[str, StrategyConfig] = {
    "V1_orb15_retest_2R": StrategyConfig(),
    "V2_orb15_retest_no_target": StrategyConfig(name="orb15_vwap_retest_eod", target_r=None),
    "V3_orb15_breakout_close_2R": StrategyConfig(name="orb15_vwap_breakout", require_retest=False),
    "V4_orb5_retest_2R": StrategyConfig(name="orb5_vwap_retest", opening_range_minutes=5,
                                        entry_start=time(9, 35)),
}
