"""Performance statistics, benchmarks, walk-forward folds, regime breakdown and the go/no-go screen."""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .backtest import BacktestResult


def _dd(equity: pd.Series) -> tuple[float, float]:
    if equity.empty:
        return 0.0, 0.0
    peak = equity.cummax()
    dd = equity - peak
    return float(dd.min()), float((dd / peak).min())


def metrics(trades, daily_equity: pd.Series, start_equity: float) -> dict:
    r = np.array([t.r_multiple for t in trades], dtype=float)
    pnl = np.array([t.net_pnl for t in trades], dtype=float)
    wins, losses = pnl[pnl > 0], pnl[pnl <= 0]
    eq = pd.concat([pd.Series([start_equity]), daily_equity.reset_index(drop=True)])
    rets = eq.pct_change().dropna()
    dd_abs, dd_pct = _dd(eq.reset_index(drop=True))
    out = {
        "trades": int(len(pnl)),
        "win_rate": float((pnl > 0).mean()) if len(pnl) else 0.0,
        "avg_win": float(wins.mean()) if len(wins) else 0.0,
        "avg_loss": float(losses.mean()) if len(losses) else 0.0,
        "expectancy": float(pnl.mean()) if len(pnl) else 0.0,
        "expectancy_r": float(r.mean()) if len(r) else 0.0,
        "profit_factor": float(wins.sum() / -losses.sum()) if losses.sum() < 0 else (math.inf if len(wins) else 0.0),
        "net_profit": float(pnl.sum()),
        "total_costs": float(sum(t.costs for t in trades)),
        "gross_profit_before_costs": float(sum(t.gross_pnl for t in trades)),
        "return_pct": float(eq.iloc[-1] / start_equity - 1) if len(eq) else 0.0,
        "sharpe": float(rets.mean() / rets.std() * math.sqrt(252)) if len(rets) > 1 and rets.std() > 0 else 0.0,
        "max_drawdown": dd_abs,
        "max_drawdown_pct": dd_pct,
        "days": int(len(daily_equity)),
    }
    out["t_stat_r"], out["ci95_r"] = t_and_bootstrap(r)
    return out


def t_and_bootstrap(r: np.ndarray, n_boot: int = 5000, seed: int = 1) -> tuple[float, tuple[float, float]]:
    if len(r) < 2 or r.std(ddof=1) == 0:
        return 0.0, (float("nan"), float("nan"))
    t = float(r.mean() / (r.std(ddof=1) / math.sqrt(len(r))))
    rng = np.random.default_rng(seed)
    means = rng.choice(r, size=(n_boot, len(r)), replace=True).mean(axis=1)
    return t, (float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5)))


def buy_and_hold(spy_bars: pd.DataFrame, days: list, start_equity: float) -> dict:
    sel = spy_bars[pd.Series(spy_bars.index.date, index=spy_bars.index).isin(days).values]
    if sel.empty:
        return {"return_pct": 0.0, "max_drawdown_pct": 0.0}
    closes = sel.groupby(sel.index.date).close.last()
    first_open = float(sel.open.iloc[0])
    eq = start_equity * closes / first_open
    _, dd = _dd(pd.concat([pd.Series([start_equity]), eq.reset_index(drop=True)]))
    return {"return_pct": float(eq.iloc[-1] / start_equity - 1), "max_drawdown_pct": dd,
            "equity": eq}


def walk_forward(res: BacktestResult, folds: int = 3) -> list[dict]:
    """Chronological folds. Parameters are fixed in advance, so every fold is out-of-sample;
    the point is to see whether results hold up across periods rather than to pick parameters."""
    out = []
    chunks = np.array_split(np.array(res.days, dtype=object), folds)
    eq_prev = res.start_equity
    for i, chunk in enumerate(chunks, 1):
        if len(chunk) == 0:
            continue
        lo, hi = chunk[0], chunk[-1]
        tr = [t for t in res.trades if lo <= t.entry_time.date() <= hi]
        de = res.daily_equity[[d for d in res.daily_equity.index if lo <= d <= hi]]
        m = metrics(tr, de, eq_prev)
        m.update({"fold": i, "start": str(lo), "end": str(hi)})
        out.append(m)
        if len(de):
            eq_prev = float(de.iloc[-1])
    return out


def regimes(res: BacktestResult, spy_bars: pd.DataFrame) -> pd.DataFrame:
    by_day = spy_bars.groupby(spy_bars.index.date)
    info = pd.DataFrame({"spy_ret": by_day.close.last() / by_day.open.first() - 1,
                         "spy_range": (by_day.high.max() - by_day.low.min()) / by_day.open.first()})
    info = info.loc[[d for d in res.days if d in info.index]]
    med = info.spy_range.median()
    info["trend"] = np.where(info.spy_ret >= 0, "SPY up day", "SPY down day")
    info["vol"] = np.where(info.spy_range >= med, "high-range day", "low-range day")
    rows = []
    for t in res.trades:
        d = t.entry_time.date()
        if d in info.index:
            rows.append({"trend": info.loc[d, "trend"], "vol": info.loc[d, "vol"], "net_pnl": t.net_pnl,
                         "r": t.r_multiple, "symbol": t.symbol})
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    parts = []
    for col in ("trend", "vol", "symbol"):
        g = df.groupby(col).agg(trades=("r", "size"), net_pnl=("net_pnl", "sum"), avg_r=("r", "mean"))
        g.index = [f"{col}: {i}" for i in g.index]
        parts.append(g)
    return pd.concat(parts)


@dataclass(frozen=True)
class Screen:
    min_trades: int = 100
    min_profit_factor: float = 1.2
    max_drawdown_pct: float = 0.05
    min_t_stat: float = 2.0


def go_no_go(m: dict, screen: Screen = Screen()) -> tuple[bool, list[str]]:
    fails = []
    if m["trades"] < screen.min_trades:
        fails.append(f"only {m['trades']} trades (< {screen.min_trades})")
    if m["expectancy"] <= 0:
        fails.append(f"expectancy ${m['expectancy']:.2f} per trade is not positive after costs")
    if m["profit_factor"] < screen.min_profit_factor:
        fails.append(f"profit factor {m['profit_factor']:.2f} < {screen.min_profit_factor}")
    if m["max_drawdown_pct"] < -screen.max_drawdown_pct:
        fails.append(f"max drawdown {m['max_drawdown_pct']:.1%} worse than -{screen.max_drawdown_pct:.0%}")
    if m["t_stat_r"] < screen.min_t_stat:
        fails.append(f"t-stat of mean R {m['t_stat_r']:.2f} < {screen.min_t_stat} (not statistically credible)")
    return not fails, fails
