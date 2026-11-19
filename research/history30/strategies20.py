"""Part 3: 14 pre-registered QQQ strategies (PREREG3.md), run once with textbook settings and costs.

Usage: python3 -I research/history30/strategies20.py <yahoo QQQ_1d_div.json> <alpaca QQQ_5Min.csv>
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import paper_orb  # noqa: E402
import study  # noqa: E402

COST = 0.0002  # 2 bp per side
D_START, D_END, D_HALF = pd.Timestamp("2006-11-20"), pd.Timestamp("2026-11-18"), pd.Timestamp("2016-11-19")
I_START, I_END, I_HALF = pd.Timestamp("2016-01-04"), pd.Timestamp("2026-11-18"), pd.Timestamp("2021-07-01")
T_BAR = 3.0


# ---------- daily data ----------

def load_daily(path):
    res = json.load(open(path))["chart"]["result"][0]
    q = res["indicators"]["quote"][0]
    idx = pd.to_datetime(res["timestamp"], unit="s", utc=True).tz_convert("America/New_York").tz_localize(None).normalize()
    df = pd.DataFrame({k: q[k] for k in ("open", "high", "low", "close")}, index=idx, dtype=float)
    df = df[~df.index.duplicated(keep="last")].dropna().sort_index()
    div = pd.Series(0.0, index=df.index)
    for v in (res.get("events", {}).get("dividends") or {}).values():
        d = pd.Timestamp(v["date"], unit="s", tz="UTC").tz_convert("America/New_York").tz_localize(None).normalize()
        if d in div.index:
            div[d] += float(v["amount"])
    df["div"] = div
    return df.loc[:D_END]


def rsi(close, n=2):
    d = close.diff()
    up, dn = d.clip(lower=0), (-d).clip(lower=0)
    au = up.ewm(alpha=1 / n, adjust=False).mean()
    ad = dn.ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + au / ad.replace(0, np.nan))


def stateful(enter, exit_):
    """Position after each close: 1 from an entry signal until an exit signal (exit checked first when in)."""
    pos, out = 0, []
    for e, x in zip(enter.values, exit_.values):
        if pos and x:
            pos = 0
        elif not pos and e:
            pos = 1
        out.append(pos)
    return pd.Series(out, index=enter.index)


def daily_signals(df):
    c = df.close
    sma5, sma20, sma50, sma200 = (c.rolling(n).mean() for n in (5, 20, 50, 200))
    sd20 = c.rolling(20).std()
    ibs = ((c - df.low) / (df.high - df.low)).where(df.high > df.low)
    sig = {
        "D1": (c > sma200).astype(int),
        "D2": (sma50 > sma200).astype(int),
        "D3": stateful(c > c.shift(1).rolling(20).max(), c < c.shift(1).rolling(10).min()),
        "D4": stateful((rsi(c) < 10) & (c > sma200), c > sma5),
        "D5": stateful(c < sma20 - 2 * sd20, c > sma20),
        "D6": (ibs < 0.2).astype(int),
    }
    return sig


def exposures(df):
    """{name: (on, dp)}: on[t] = exposure overnight into day t, dp[t] = exposure during day t."""
    n = len(df)
    ones, zeros = pd.Series(1.0, index=df.index), pd.Series(0.0, index=df.index)
    out = {"D0": (ones, ones)}
    for k, s in daily_signals(df).items():
        dp = s.shift(1).fillna(0)          # signal at close t-1 -> held during day t (bought at the open)
        on = dp.shift(1).fillna(0)         # held overnight into t if held during t-1 (sold at the open of t if off)
        out[k] = (on, dp)
    # D7 turn of month: last trading day of a month through the 3rd trading day of the next
    ym = pd.Series(df.index.to_period("M"), index=df.index)
    rank_fwd = ym.groupby(ym).cumcount() + 1
    rank_back = ym.groupby(ym).cumcount(ascending=False)
    dp7 = ((rank_back == 0) | (rank_fwd <= 3)).astype(float)
    on7 = (dp7.astype(bool) & (rank_back != 0)).astype(float)  # nights inside the window: into TD1..TD3
    # the night into the month's last day isn't held; the night after TD3 isn't held
    on7[(rank_fwd == 1)] = 1.0
    out["D7"] = (on7, dp7)
    out["D8"] = (ones, zeros)
    out["D9"] = (zeros, ones)
    return out


def daily_returns(df, on, dp, cost=COST):
    prev_c = df.close.shift(1)
    overnight = (df.open + df["div"]) / prev_c - 1
    day = df.close / df.open - 1
    r = (1 + on * overnight) * (1 + dp * day) - 1
    turns = (dp - on).abs() + (on.shift(-1).fillna(0) - dp).abs()
    return r.fillna(0), (r - cost * turns).fillna(0), turns


def entries(on, dp):
    held = pd.concat([on.rename("on"), dp.rename("dp")], axis=1).stack().values
    return int(((held[1:] > 0) & (held[:-1] == 0)).sum())


def ols_alpha(y, x):
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    X = np.column_stack([np.ones_like(x), x])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    s2 = resid @ resid / (len(y) - 2)
    cov = s2 * np.linalg.inv(X.T @ X)
    return beta[0], beta[0] / math.sqrt(cov[0, 0]), beta[1]


def perf(r):
    eq = (1 + r).cumprod()
    yrs = len(r) / 252
    cagr = eq.iloc[-1] ** (1 / yrs) - 1
    dd = (eq / eq.cummax() - 1).min()
    sharpe = r.mean() / r.std() * math.sqrt(252) if r.std() > 0 else float("nan")
    return cagr, dd, sharpe


def run_daily(df):
    ex = exposures(df)
    rows, series = [], {}
    bh_gross, bh_net, _ = daily_returns(df, *ex["D0"])
    for k, (on, dp) in ex.items():
        g, n, turns = daily_returns(df, on, dp)
        series[k] = n
        row = {"id": k}
        for label, a, b in (("all", D_START, D_END), ("h1", D_START, D_HALF - pd.Timedelta(days=1)), ("h2", D_HALF, D_END)):
            nn, gg, bb = n.loc[a:b], g.loc[a:b], bh_gross.loc[a:b]
            cagr, dd, sh = perf(nn)
            row[f"{label}_cagr_gross"] = perf(gg)[0]
            al, at, beta = ols_alpha(nn, bb)
            alg, atg, _ = ols_alpha(gg, bb)
            row.update({f"{label}_cagr": cagr, f"{label}_dd": dd, f"{label}_sharpe": sh, f"{label}_alpha": al * 252,
                        f"{label}_t": at, f"{label}_beta": beta, f"{label}_alpha_gross": alg * 252, f"{label}_t_gross": atg})
        w = slice(D_START, D_END)
        row["exposure"] = float(((on.loc[w] > 0) | (dp.loc[w] > 0)).mean())
        row["trades"] = entries(on.loc[w], dp.loc[w])
        rows.append(row)
    return pd.DataFrame(rows).set_index("id"), series


# ---------- intraday ----------

def load_5min(path):
    df = pd.read_csv(path)
    idx = pd.to_datetime(df.t, utc=True).dt.tz_convert("America/New_York")
    b = pd.DataFrame({"open": df.o.values, "high": df.h.values, "low": df.l.values, "close": df.c.values},
                     index=pd.DatetimeIndex(idx)).sort_index()
    b = b[~b.index.duplicated()].between_time("09:30", "15:55")
    days = {}
    for d, g in b.groupby(b.index.date):
        if len(g) >= 40 and g.index[0].strftime("%H:%M") == "09:30":
            days[pd.Timestamp(d)] = g
    return dict(sorted(days.items()))


def bar_at(g, hhmm):
    m = g.index.strftime("%H:%M") == hhmm
    return g[m].iloc[0] if m.any() else None


def walk(g, start_i, side, entry, stop, target, t_end):
    """Exit from bar start_i on: stop first, then target, else close of the last bar starting before t_end."""
    last = None
    for ts, b in g.iloc[start_i:].iterrows():
        if ts.strftime("%H:%M") >= t_end:
            break
        if stop is not None and ((b.low <= stop) if side == 1 else (b.high >= stop)):
            return stop, "stop"
        if target is not None and ((b.high >= target) if side == 1 else (b.low <= target)):
            return target, "target"
        last = b
    if last is None:
        return None, None
    return last.close, "time"


def i2_first_candle(g, prev):
    f = g.iloc[0]
    if f.close == f.open or len(g) < 2:
        return None
    side = 1 if f.close > f.open else -1
    entry = g.open.iat[1]
    stop = f.low if side == 1 else f.high
    risk = (entry - stop) * side
    if risk <= 0:
        return None
    px, why = walk(g, 1, side, entry, stop, entry + side * 10 * risk, "16:00")
    return side, entry, px, why


def i3_momentum(g, prev):
    b955, b1530 = bar_at(g, "09:55"), bar_at(g, "15:30")
    if b955 is None or b1530 is None or prev is None:
        return None
    r1 = b955.close / prev["close"] - 1
    if r1 == 0:
        return None
    side = 1 if r1 > 0 else -1
    i = list(g.index.strftime("%H:%M")).index("15:30")
    px, why = walk(g, i, side, b1530.open, None, None, "16:00")
    return side, b1530.open, px, why


def i4_gap_fade(g, prev):
    if prev is None:
        return None
    o = g.open.iat[0]
    gap = o / prev["close"] - 1
    if abs(gap) < 0.005:
        return None
    side = -1 if gap > 0 else 1
    px, why = walk(g, 0, side, o, None, prev["close"], "16:00")
    return side, o, px, why


def i5_sweep(g, prev):
    if prev is None:
        return None
    pdh, pdl = prev["high"], prev["low"]
    times = list(g.index.strftime("%H:%M"))
    for i in range(1, len(g) - 1):
        t = times[i]
        if t > "10:55":
            break
        b = g.iloc[i]
        side = None
        if b.high > pdh and b.close < pdh:
            side, stop = -1, b.high
        elif b.low < pdl and b.close > pdl:
            side, stop = 1, b.low
        if side is None:
            continue
        entry = g.open.iat[i + 1]
        risk = (entry - stop) * side
        if risk <= 0:
            return None
        px, why = walk(g, i + 1, side, entry, stop, entry + side * 2 * risk, "12:00")
        return side, entry, px, why
    return None


def i1_orb(g, prev):
    sig = paper_orb.signal(g)
    if not sig or sig.get("k") is None:
        return None
    t = paper_orb.share_trade(g, sig)
    if t.get("share_reason") not in ("stop", "target", "time"):
        return None
    return sig["side"], t["share_entry"], t["share_exit"], t["share_reason"]


INTRADAY = {"I1": i1_orb, "I2": i2_first_candle, "I3": i3_momentum, "I4": i4_gap_fade, "I5": i5_sweep}


def run_intraday(days):
    trades = []
    prev = None
    for d, g in days.items():
        if I_START <= d <= I_END:
            for k, fn in INTRADAY.items():
                r = fn(g, prev)
                if r is None or r[2] is None:
                    continue
                side, entry, px, why = r
                gross = side * (px - entry) / entry
                trades.append({"id": k, "date": d, "side": side, "entry": entry, "exit": px, "reason": why,
                               "gross": gross, "net": gross - 2 * COST})
        prev = {"close": g.close.iat[-1], "high": g.high.max(), "low": g.low.min()}
    return pd.DataFrame(trades)


def summarize_intraday(tr):
    rows = []
    for k in INTRADAY:
        t = tr[tr.id == k]
        row = {"id": k}
        for label, a, b in (("all", I_START, I_END), ("h1", I_START, I_HALF - pd.Timedelta(days=1)), ("h2", I_HALF, I_END)):
            x = t[(t.date >= a) & (t.date <= b)]
            yrs = (b - a).days / 365.25
            growth = (1 + x.net).prod() ** (1 / yrs) - 1 if len(x) else float("nan")
            row.update({f"{label}_n": len(x), f"{label}_win": (x.net > 0).mean(), f"{label}_mean": x.net.mean(),
                        f"{label}_t": study.tstat(x.net), f"{label}_mean_gross": x.gross.mean(),
                        f"{label}_t_gross": study.tstat(x.gross), f"{label}_sum": x.net.sum(), f"{label}_growth": growth})
        row["reasons"] = ", ".join(f"{r} {c}" for r, c in t.reason.value_counts().items())
        rows.append(row)
    return pd.DataFrame(rows).set_index("id")


# ---------- report ----------

NAMES = {"D0": "Buy and hold (benchmark)", "D1": "200-day trend filter", "D2": "Golden cross (50 > 200)",
         "D3": "20-day breakout", "D4": "RSI(2) pullback", "D5": "Bollinger reversion", "D6": "IBS < 0.2, hold 1 day",
         "D7": "Turn of the month", "D8": "Overnight only", "D9": "Daytime only",
         "I1": "Our 5-min ORB (2R, 90 min)", "I2": "First-candle ORB to the close (10R)", "I3": "Intraday momentum (last 30 min)",
         "I4": "Gap fade (≥ 0.5%)", "I5": "Prior-day high/low sweep reversal"}


def pct(x, d=1):
    return "n/a" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{100 * x:+.{d}f}%"


def main(argv):
    df = load_daily(argv[0])
    dres, dseries = run_daily(df)
    days = load_5min(argv[1])
    tr = run_intraday(days)
    ires = summarize_intraday(tr)

    print("## Data\n")
    w = df.loc[D_START:D_END]
    print(f"- Daily: {len(w)} trading days {w.index[0]:%Y-%m-%d} → {w.index[-1]:%Y-%m-%d}; dividends on {int((w['div'] > 0).sum())} days")
    print(f"- Intraday: {sum(1 for d in days if I_START <= d <= I_END)} sessions {I_START:%Y-%m-%d} → {I_END:%Y-%m-%d}")
    print(f"- Costs: {COST * 1e4:.0f} bp per side. Bar for a real edge: t ≥ {T_BAR} after costs and positive in both halves.\n")

    print("## Daily strategies, 2006-11-20 → 2026-11-18 (QQQ, entries at the next open)\n")
    cols = ["Strategy", "Growth/yr", "Growth/yr before costs", "Worst drawdown", "Sharpe", "Time in market", "Trades", "Alpha/yr", "t", "Alpha/yr before costs (t)", "1st half alpha (t)", "2nd half alpha (t)"]
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for k, r in dres.iterrows():
        lines.append("| " + " | ".join([
            f"{k} {NAMES[k]}", pct(r.all_cagr), pct(r.all_cagr_gross), pct(r.all_dd, 0), f"{r.all_sharpe:.2f}", f"{100 * r.exposure:.0f}%", str(int(r.trades)),
            "—" if k == "D0" else pct(r.all_alpha), "—" if k == "D0" else f"{r.all_t:+.1f}",
            "—" if k == "D0" else f"{pct(r.all_alpha_gross)} ({r.all_t_gross:+.1f})",
            "—" if k == "D0" else f"{pct(r.h1_alpha)} ({r.h1_t:+.1f})", "—" if k == "D0" else f"{pct(r.h2_alpha)} ({r.h2_t:+.1f})"]) + " |")
    print("\n".join(lines))

    print("\n## Intraday strategies, 2016-01-04 → 2026-11-18 (QQQ shares, 1x, all weekdays)\n")
    cols = ["Strategy", "Trades", "Win rate", "Mean per trade", "t", "Mean before costs (t)", "Growth/yr (1x)", "1st half mean (t)", "2nd half mean (t)", "Exits"]
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for k, r in ires.iterrows():
        lines.append("| " + " | ".join([
            f"{k} {NAMES[k]}", str(r.all_n), f"{100 * r.all_win:.0f}%", pct(r.all_mean, 3), f"{r.all_t:+.1f}",
            f"{pct(r.all_mean_gross, 3)} ({r.all_t_gross:+.1f})", pct(r.all_growth), f"{pct(r.h1_mean, 3)} ({r.h1_t:+.1f})", f"{pct(r.h2_mean, 3)} ({r.h2_t:+.1f})",
            r.reasons]) + " |")
    print("\n".join(lines))

    print("\n## Ranking by t after costs (the pre-registered measure)\n")
    rank = [(k, dres.loc[k, "all_t"], dres.loc[k, "h1_t"], dres.loc[k, "h2_t"]) for k in dres.index if k != "D0"]
    rank += [(k, ires.loc[k, "all_t"], ires.loc[k, "h1_t"], ires.loc[k, "h2_t"]) for k in ires.index]
    rank.sort(key=lambda x: -x[1])
    lines = ["| Rank | Strategy | t | Both halves positive | Passes the bar (t ≥ 3, both halves) |", "|---|---|---|---|---|"]
    for i, (k, t, t1, t2) in enumerate(rank, 1):
        both = t1 > 0 and t2 > 0
        lines.append(f"| {i} | {k} {NAMES[k]} | {t:+.1f} | {'yes' if both else 'no'} | {'YES' if (t >= T_BAR and both) else 'no'} |")
    print("\n".join(lines))
    tr.to_csv(HERE / "strategies20_intraday_trades.csv", index=False)
    pd.DataFrame(dseries).loc[D_START:D_END].round(6).to_csv(HERE / "strategies20_daily_returns.csv")


if __name__ == "__main__":
    main(sys.argv[1:])
