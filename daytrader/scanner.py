"""Premarket watchlist and opening-range scanner. Uses only data available at decision time."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

import pandas as pd

from .config import ScannerConfig
from .data.base import NewsProvider, QuoteProvider
from .indicators import opening_range, relative_opening_volume


@dataclass
class ScanResult:
    symbol: str
    price: float | None
    avg_daily_volume: float | None
    rel_open_volume: float | None
    gap_pct: float | None
    passed: bool
    failed: list[str] = field(default_factory=list)
    news: list[str] = field(default_factory=list)


def avg_daily_volume(daily_before: pd.DataFrame, lookback: int) -> float | None:
    tail = daily_before.tail(lookback)
    return float(tail.volume.mean()) if len(tail) >= max(5, lookback // 2) else None


def opening_scan(today: dict[str, pd.DataFrame], prior_sessions: dict[str, list[pd.DataFrame]],
                 daily_before: dict[str, pd.DataFrame], cfg: ScannerConfig, or_minutes: int,
                 news: dict[str, list[str]] | None = None) -> list[ScanResult]:
    """Run once the opening range is complete. `today` holds only today's bars up to that point."""
    out = []
    for sym, bars in today.items():
        fails = []
        orange = opening_range(bars, or_minutes)
        price = float(bars.close.iloc[-1]) if len(bars) else None
        d = daily_before.get(sym, pd.DataFrame())
        adv = avg_daily_volume(d, cfg.lookback_days) if not d.empty else None
        prior = prior_sessions.get(sym, [])[-cfg.lookback_days:]
        rvol = relative_opening_volume(bars, prior, or_minutes) if len(prior) >= cfg.lookback_days // 2 else None
        gap = (float(bars.open.iloc[0]) / float(d.close.iloc[-1]) - 1) if len(d) and len(bars) else None
        if orange is None:
            fails.append("opening range incomplete")
        if price is None or price < cfg.min_price:
            fails.append(f"price below ${cfg.min_price:.0f}")
        if adv is None or adv < cfg.min_avg_daily_volume:
            fails.append("average daily volume below 1M (or not enough history)")
        if rvol is None or rvol < cfg.min_relative_opening_volume:
            fails.append(f"relative opening volume below {cfg.min_relative_opening_volume}")
        headlines = (news or {}).get(sym, [])
        if cfg.require_verified_news and not headlines:
            fails.append("no verified news catalyst")
        out.append(ScanResult(sym, price, adv, rvol, gap, not fails, fails, headlines))
    passed = sorted([r for r in out if r.passed], key=lambda r: -(r.rel_open_volume or 0))
    for r in passed[cfg.max_candidates:]:
        r.passed, r.failed = False, ["ranked below the top candidates"]
    return sorted(out, key=lambda r: (not r.passed, -(r.rel_open_volume or 0)))


def premarket_watchlist(universe: list[str], daily_before: dict[str, pd.DataFrame], cfg: ScannerConfig,
                        quotes: QuoteProvider | None = None, news_provider: NewsProvider | None = None,
                        now: datetime | None = None) -> list[ScanResult]:
    """Before the open: liquidity filter, gap from the latest quote, and news from the last 24 hours."""
    headlines: dict[str, list[str]] = {}
    if news_provider is not None and now is not None:
        for item in news_provider.news(universe, now - timedelta(hours=24), now):
            headlines.setdefault(item.symbol, []).append(f"{item.created_at:%H:%M} {item.headline} ({item.source})")
    out = []
    for sym in universe:
        d = daily_before.get(sym, pd.DataFrame())
        fails, gap, price = [], None, None
        adv = avg_daily_volume(d, cfg.lookback_days) if not d.empty else None
        if adv is None or adv < cfg.min_avg_daily_volume:
            fails.append("average daily volume below 1M")
        if quotes is not None and len(d):
            try:
                q = quotes.latest_quote(sym)
                price = (q.bid + q.ask) / 2
                gap = price / float(d.close.iloc[-1]) - 1
                if q.spread_pct > cfg.max_spread_pct:
                    fails.append(f"spread {q.spread_pct:.2%} too wide")
            except Exception as exc:  # a missing quote should not stop the scan
                fails.append(f"no quote: {exc}")
        if price is not None and price < cfg.min_price:
            fails.append(f"price below ${cfg.min_price:.0f}")
        if cfg.require_verified_news and not headlines.get(sym):
            fails.append("no verified news catalyst")
        out.append(ScanResult(sym, price, adv, None, gap, not fails, fails, headlines.get(sym, [])))
    return sorted(out, key=lambda r: (not r.passed, -(abs(r.gap_pct) if r.gap_pct is not None else 0),
                                      -len(r.news)))
