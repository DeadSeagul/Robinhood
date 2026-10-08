"""Paper-trading runner for one session. PAPER MODE ONLY.

Daily workflow:
  before 9:30   premarket watchlist (liquidity, gap from latest quote, news from the last 24h)
  9:30-9:45     record the opening range (5- and 15-minute), then run the opening scan
  9:45-11:00    feed each completed 5-minute bar to the shared DaySession; only qualifying paper trades
  after 11:00   no new entries; manage open positions; flatten at 15:55
  after close   write the daily report

Safety: a KILL_SWITCH file (or SIGINT) flattens everything and stops; so do repeated data/broker
errors or a stale data feed.
"""
from __future__ import annotations

import time as _time
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Callable

import pandas as pd

from .backtest import build_strategies
from .config import AppConfig, check_mode
from .engine import MARKET, DaySession
from .indicators import session_vwap
from .journal import NO_TRADE, trade_rows, write_csv
from .scanner import opening_scan, premarket_watchlist

NY = "America/New_York"


@dataclass
class PaperReport:
    day: date
    watchlist: list = field(default_factory=list)
    scan: list = field(default_factory=list)
    proposals: list = field(default_factory=list)
    trades: list = field(default_factory=list)
    skipped: list = field(default_factory=list)
    violations: list = field(default_factory=list)
    risk_events: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    start_equity: float = 0.0
    end_equity: float = 0.0

    def text(self) -> str:
        lines = [f"# Paper trading report {self.day}", "",
                 f"Start equity ${self.start_equity:,.2f} -> end equity ${self.end_equity:,.2f} "
                 f"(net {self.end_equity - self.start_equity:+,.2f})", ""]
        placed = [p for p in self.proposals if p.status == "order working"]
        lines += ["## Proposals", ""] + ([p.to_text() + "\n" for p in self.proposals] or [NO_TRADE, ""])
        if not placed:
            lines += ["Result: " + NO_TRADE, ""]
        lines += ["## Trades", ""]
        for t in self.trades:
            lines.append(f"- {t.symbol} {t.qty} sh: {t.entry_time:%H:%M} {t.entry_price:.2f} -> {t.exit_time:%H:%M} "
                         f"{t.exit_price:.2f} ({t.exit_reason}) net {t.net_pnl:+.2f}, costs {t.costs:.2f}, "
                         f"{t.r_multiple:+.2f}R")
        lines += ["", "## Missed or skipped setups", ""] + [f"- {s['time']} {s['symbol']}: {s['reason']}"
                                                           for s in self.skipped]
        lines += ["", "## Rule violations", ""] + ([f"- {v}" for v in self.violations] or ["none"])
        lines += ["", "## Risk events and errors", ""] + [f"- {e}" for e in self.risk_events + self.errors]
        return "\n".join(lines)


class PaperTrader:
    def __init__(self, cfg: AppConfig, provider, broker, universe: list[str], news_provider=None,
                 clock: Callable[[], datetime] | None = None, sleep: Callable[[float], None] = _time.sleep,
                 max_errors: int = 5, stale_after: timedelta = timedelta(minutes=12)):
        check_mode(cfg.mode)
        if cfg.mode != "paper":
            raise ValueError("PaperTrader requires mode='paper'")
        self.cfg, self.provider, self.broker = cfg, provider, broker
        self.universe, self.news = universe, news_provider
        self.clock = clock or (lambda: pd.Timestamp.now(tz=NY).to_pydatetime())
        self.sleep, self.max_errors, self.stale_after = sleep, max_errors, stale_after

    def _now(self) -> pd.Timestamp:
        return pd.Timestamp(self.clock()).tz_convert(NY)

    def _wait_until(self, t: pd.Timestamp) -> None:
        while self._now() < t:
            if self.kill_requested():
                return
            self.sleep(min(30.0, max(1.0, (t - self._now()).total_seconds())))

    def kill_requested(self) -> bool:
        return Path(self.cfg.kill_switch_path).exists()

    def run_day(self, journal_dir: str | Path | None = None) -> PaperReport:
        sc = self.cfg.strategy
        now = self._now()
        d = now.date()
        base = pd.Timestamp(d).tz_localize(NY)
        report = PaperReport(d)
        lookback_start = d - timedelta(days=45)

        daily = {s: self.provider.daily_bars(s, lookback_start, d - timedelta(days=1)) for s in self.universe}
        quotes = self.provider if hasattr(self.provider, "latest_quote") else None
        report.watchlist = premarket_watchlist(self.universe, daily, self.cfg.scanner, quotes, self.news, now)
        watch = [r.symbol for r in report.watchlist if r.passed] or list(self.universe)

        or_end = base + pd.Timedelta(hours=9, minutes=30 + sc.opening_range_minutes)
        self._wait_until(or_end + pd.Timedelta(seconds=20))
        if self.kill_requested():
            report.errors.append("kill switch present before the open; no trading")
            return report

        hist_start = d - timedelta(days=40)
        intraday = {s: self.provider.intraday_bars(s, hist_start, d, sc.bar_minutes) for s in set(watch) | set(MARKET)}
        sessions = {s: {x: g for x, g in b.groupby(b.index.date)} for s, b in intraday.items()}
        today = {s: sessions[s].get(d, pd.DataFrame()) for s in watch}
        today = {s: b[b.index < or_end] for s, b in today.items() if len(b)}
        hist = {s: [g for x, g in sorted(sessions[s].items()) if x < d][-self.cfg.scanner.lookback_days:] for s in today}
        report.scan = opening_scan(today, hist, daily, self.cfg.scanner, sc.opening_range_minutes)
        candidates = [r.symbol for r in report.scan if r.passed]
        strategies = build_strategies(candidates, today, daily, sc)
        start_eq = self.broker.equity({})
        report.start_equity = start_eq
        session = DaySession(d, self.cfg, sc, self.broker, strategies, start_eq, getattr(self.provider, "name", ""))
        done: set[pd.Timestamp] = set()
        errors = 0
        bar = pd.Timedelta(minutes=sc.bar_minutes)
        close_t = base + pd.Timedelta(hours=16)

        while not session.finished and self._now() < close_t:
            if self.kill_requested():
                session.kill(self._now(), "kill switch activated")
                break
            try:
                bars = {s: self.provider.intraday_bars(s, d, d, sc.bar_minutes) for s in set(strategies) | set(MARKET)}
                newest = max((b.index[-1] for b in bars.values() if len(b)), default=None)
                if newest is None or self._now() - (newest + bar) > self.stale_after:
                    raise RuntimeError(f"stale data feed (latest bar {newest})")
                ready = sorted({ts for b in bars.values() for ts in b.index if ts + bar <= self._now() and ts not in done})
                for ts in ready:
                    now_bars = {s: b.loc[ts] for s, b in bars.items() if ts in b.index}
                    vnow = {s: float(session_vwap(b[b.index <= ts]).iloc[-1]) for s, b in bars.items() if ts in b.index}
                    session.step(ts, now_bars, vnow)
                    done.add(ts)
                    if session.finished:
                        break
                errors = 0
            except Exception as exc:  # reconnect: retry next cycle; give up after max_errors in a row
                errors += 1
                report.errors.append(f"{self._now():%H:%M:%S} error {errors}/{self.max_errors}: {exc}")
                if errors >= self.max_errors:
                    session.kill(self._now(), f"critical system error: {exc}")
                    break
            if not session.finished:
                self.sleep(60.0)

        report.end_equity = session.end(self._now())
        report.proposals, report.skipped = session.log.proposals, session.log.skipped
        report.violations, report.risk_events = session.log.violations, session.log.risk_events
        report.trades = [t for t in getattr(self.broker, "trades", []) if t.entry_time.date() == d]
        if journal_dir:
            jd = Path(journal_dir)
            jd.mkdir(parents=True, exist_ok=True)
            (jd / f"{d}_report.md").write_text(report.text())
            write_csv(jd / f"{d}_trades.csv", trade_rows(report.trades))
        return report
