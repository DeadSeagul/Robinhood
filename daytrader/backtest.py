"""Historical backtester: replays sessions bar by bar through the same DaySession the paper trader uses."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

import pandas as pd

from .broker.sim import SimBroker
from .config import AppConfig, StrategyConfig
from .engine import MARKET, DaySession
from .indicators import opening_range, session_vwap
from .journal import TradeProposal
from .scanner import ScanResult, opening_scan
from .strategy import DayContext, OrbStrategy


@dataclass
class BacktestResult:
    variant: str
    trades: list
    daily_equity: pd.Series
    scans: list[tuple[date, ScanResult]]
    proposals: list[TradeProposal]
    skipped: list[dict]
    violations: list[str]
    risk_events: list[str]
    days: list[date]
    start_equity: float
    excluded_symbols: dict[str, str] = field(default_factory=dict)


def split_sessions(bars: pd.DataFrame) -> dict[date, pd.DataFrame]:
    return {d: g for d, g in bars.groupby(bars.index.date)} if not bars.empty else {}


def build_strategies(candidates, today, dbefore, strat_cfg) -> dict[str, OrbStrategy]:
    out = {}
    for s in candidates:
        o = opening_range(today[s], strat_cfg.opening_range_minutes)
        db = dbefore.get(s)
        has = db is not None and len(db) > 0
        ctx = DayContext(s, float(db.high.iloc[-1]) if has else None, float(db.close.iloc[-1]) if has else None,
                         float(today[s].open.iloc[0]))
        out[s] = OrbStrategy(strat_cfg, ctx, o)
    return out


def run_backtest(intraday: dict[str, pd.DataFrame], daily: dict[str, pd.DataFrame], cfg: AppConfig,
                 strat_cfg: StrategyConfig, variant: str = "", data_source: str = "",
                 excluded: dict[str, str] | None = None) -> BacktestResult:
    for m in MARKET:
        if m not in intraday:
            raise ValueError(f"{m} bars are required for the market filter")
    excluded = excluded or {}
    sessions = {s: split_sessions(b) for s, b in intraday.items()}
    days = sorted(d for d, g in sessions["SPY"].items() if len(g) >= 70)  # full sessions only
    lookback = cfg.scanner.lookback_days
    test_days = days[lookback:]
    broker = SimBroker(cfg.risk.starting_equity, cfg.costs, strat_cfg.tick)
    tradeable = [s for s in intraday if s not in excluded]
    equity_by_day, scans, proposals, skipped, violations, risk_events = {}, [], [], [], [], []

    for d in test_days:
        prior_days = [x for x in days if x < d]
        today = {s: sessions[s][d] for s in tradeable if d in sessions[s]}
        or_end = pd.Timestamp(d).tz_localize("America/New_York") + pd.Timedelta(
            hours=9, minutes=30 + strat_cfg.opening_range_minutes)
        so_far = {s: b[b.index < or_end] for s, b in today.items()}
        hist = {s: [sessions[s][x] for x in prior_days[-lookback:] if x in sessions[s]] for s in today}
        dbefore = {s: daily[s][daily[s].index.date < d] for s in today if s in daily}
        results = opening_scan(so_far, hist, dbefore, cfg.scanner, strat_cfg.opening_range_minutes)
        scans += [(d, r) for r in results]
        strategies = build_strategies([r.symbol for r in results if r.passed], today, dbefore, strat_cfg)

        mkt = {m: sessions[m][d] for m in MARKET}
        vw = {s: session_vwap(today[s]) for s in strategies}
        vw.update({m: session_vwap(mkt[m]) for m in MARKET})
        session = DaySession(d, cfg, strat_cfg, broker, strategies, broker.cash, data_source)
        timeline = mkt["SPY"].index
        for ts in timeline:
            bars_now = {s: today[s].loc[ts] for s in strategies if ts in today[s].index}
            bars_now.update({m: mkt[m].loc[ts] for m in MARKET if ts in mkt[m].index})
            vnow = {s: float(vw[s].loc[ts]) for s in bars_now}
            session.step(ts, bars_now, vnow)
            if session.finished:
                break
        equity_by_day[d] = session.end(timeline[-1])
        proposals += session.log.proposals
        skipped += session.log.skipped
        violations += session.log.violations
        risk_events += session.log.risk_events

    return BacktestResult(variant, broker.trades, pd.Series(equity_by_day, dtype=float), scans, proposals,
                          skipped, violations, risk_events, test_days, cfg.risk.starting_equity, excluded)
