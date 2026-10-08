"""Runs every pre-registered variant once, writes the reports and the dashboard. No parameter search."""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from .analytics import buy_and_hold, go_no_go, metrics, regimes, walk_forward
from .backtest import run_backtest
from .config import VARIANTS, AppConfig
from .dashboard import write_dashboard
from .data.base import DataError
from .journal import trade_rows, write_csv


def load_universe(provider, universe: list[str], start: date | None = None, end: date | None = None):
    intraday, daily, excluded = {}, {}, {}
    for s in universe:
        try:
            bars = provider.intraday_bars(s, start, end)
            dbars = provider.daily_bars(s, start - timedelta(days=60) if start else None, end)
        except (DataError, Exception) as exc:  # one bad symbol must not stop the run
            excluded[s] = f"data error: {exc}"
            continue
        if bars.empty or dbars.empty:
            excluded[s] = "no data"
            continue
        splits = [x for x in getattr(provider, "splits", {}).get(s, []) if bars.index[0] <= x <= bars.index[-1]]
        if splits:
            excluded[s] = f"split inside the test window ({splits[0].date()}); intraday bars are unadjusted"
            continue
        intraday[s], daily[s] = bars, dbars
    return intraday, daily, excluded


def _fmt(m: dict) -> str:
    pf = "inf" if m["profit_factor"] == float("inf") else f"{m['profit_factor']:.2f}"
    lo, hi = m["ci95_r"]
    ci = "n/a" if np.isnan(lo) else f"[{lo:+.2f}, {hi:+.2f}]"
    return (f"| {m['trades']} | {m['win_rate']:.0%} | ${m['avg_win']:,.2f} | ${m['avg_loss']:,.2f} | "
            f"${m['expectancy']:,.2f} ({m['expectancy_r']:+.2f}R) | {pf} | {m['sharpe']:.2f} | "
            f"{m['max_drawdown_pct']:.2%} | ${m['net_profit']:,.2f} | ${m['total_costs']:,.2f} | "
            f"{m['t_stat_r']:+.2f} | {ci} |")


HEAD = ("| Trades | Win rate | Avg win | Avg loss | Expectancy | Profit factor | Sharpe | Max DD | Net profit | "
        "Costs | t (mean R) | 95% CI mean R |\n|---|---|---|---|---|---|---|---|---|---|---|---|")


def run_all(provider, universe: list[str], out_dir: str | Path, cfg: AppConfig | None = None,
            start: date | None = None, end: date | None = None) -> str:
    cfg = cfg or AppConfig(mode="backtest")
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    intraday, daily, excluded = load_universe(provider, universe, start, end)
    if "SPY" not in intraday or "QQQ" not in intraday:
        raise DataError("SPY and QQQ data are required")
    lines = ["# Backtest report", "",
             f"Data source: {provider.name}. Universe: {len(universe)} symbols fixed in advance "
             f"({len(intraday)} usable). Start equity ${cfg.risk.starting_equity:,.0f}. "
             "Every variant was run exactly once with parameters fixed before the run.", ""]
    if excluded:
        lines += ["Excluded symbols:", ""] + [f"- {s}: {why}" for s, why in excluded.items()] + [""]
    payload = {"variants": {}, "source": provider.name, "universe_size": len(intraday),
               "start_equity": cfg.risk.starting_equity}
    summary = ["## Summary (all costs included)", "", "| Variant | " + HEAD.split("\n")[0][2:],
               "|---" + HEAD.split("\n")[1][0:]]
    for name, sc in VARIANTS.items():
        res = run_backtest(intraday, daily, cfg, sc, name, provider.name, excluded)
        m = metrics(res.trades, res.daily_equity, res.start_equity)
        bh = buy_and_hold(intraday["SPY"], res.days, res.start_equity)
        ok, fails = go_no_go(m)
        summary.append(f"| {name} " + _fmt(m))
        lines += [f"## {name}", "", f"Period {res.days[0]} to {res.days[-1]} ({len(res.days)} trading days after a "
                  f"{cfg.scanner.lookback_days}-day warm-up).", "", HEAD, _fmt(m), "",
                  f"Benchmarks: SPY buy-and-hold {bh['return_pct']:+.2%} (max DD {bh['max_drawdown_pct']:.2%}); "
                  f"no-trade 0.00%. Strategy {m['return_pct']:+.2%}.", "",
                  f"Screen: **{'PASS' if ok else 'FAIL'}**" + ("" if ok else " — " + "; ".join(fails)), ""]
        wf = walk_forward(res)
        lines += ["Chronological folds (fixed parameters, each fold out-of-sample):", "",
                  "| Fold | Dates | Trades | Net profit | Expectancy R | Profit factor |", "|---|---|---|---|---|---|"]
        for f in wf:
            pf = "inf" if f["profit_factor"] == float("inf") else f"{f['profit_factor']:.2f}"
            lines.append(f"| {f['fold']} | {f['start']} to {f['end']} | {f['trades']} | ${f['net_profit']:,.2f} | "
                         f"{f['expectancy_r']:+.2f} | {pf} |")
        rg = regimes(res, intraday["SPY"])
        if not rg.empty:
            lines += ["", "Where it made and lost money:", "", "| Bucket | Trades | Net P/L | Avg R |", "|---|---|---|---|"]
            lines += [f"| {i} | {int(r.trades)} | ${r.net_pnl:,.2f} | {r.avg_r:+.2f} |" for i, r in rg.iterrows()]
        reasons = pd.Series([s["reason"].split(":")[0] for s in res.skipped]).value_counts()
        scans = [r for _, r in res.scans]
        lines += ["", f"Scanner: {sum(r.passed for r in scans)} candidate-days out of {len(scans)} symbol-days. "
                  f"Signals proposed: {len(res.proposals)}. Rule violations: {len(res.violations)}"
                  + (f" ({'; '.join(res.violations[:5])})" if res.violations else "") + ".",
                  "", "Skipped/rejected setups by reason:", ""]
        lines += [f"- {k}: {v}" for k, v in reasons.items()] + [""]
        if res.risk_events:
            lines += ["Risk events:", ""] + [f"- {e}" for e in res.risk_events] + [""]
        write_csv(out / f"{name}_trades.csv", trade_rows(res.trades))
        write_csv(out / f"{name}_skipped.csv", res.skipped)
        write_csv(out / f"{name}_scan.csv", [{"date": d, **{k: v for k, v in r.__dict__.items()}} for d, r in res.scans])
        eq = res.daily_equity
        peak = eq.cummax()
        bh_eq = bh.get("equity", pd.Series(dtype=float))
        payload["variants"][name] = {
            "metrics": {k: v for k, v in m.items() if k != "ci95_r"}, "pass": ok, "fails": fails,
            "dates": [str(d) for d in eq.index], "equity": [round(float(v), 2) for v in eq],
            "spy": [round(float(bh_eq.get(d, np.nan)), 2) for d in eq.index],
            "drawdown": [round(float(v), 5) for v in (eq / peak - 1)],
            "trades": [{"date": str(t.entry_time.date()), "symbol": t.symbol,
                        "entry": f"{t.entry_time:%H:%M} {t.entry_price:.2f}", "exit": f"{t.exit_time:%H:%M} {t.exit_price:.2f}",
                        "qty": t.qty, "reason": t.exit_reason, "pnl": round(t.net_pnl, 2), "r": round(t.r_multiple, 3),
                        "costs": round(t.costs, 2)} for t in res.trades],
        }
        payload["period"] = f"{res.days[0]} to {res.days[-1]}"
        payload["spy_return"] = bh["return_pct"]
    report = "\n".join(lines[:4] + summary + [""] + lines[4:])
    (out / "backtest_report.md").write_text(report)
    write_dashboard(out / "dashboard.html", payload)
    return report
