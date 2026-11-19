"""30-year daily study (part 1): questions and rules fixed in PREREG.md before this was run.

Usage:
  python3 -I research/history30/study.py <yahoo_dir> [--news research/news_log.csv] [--bars data_cache/yahoo/QQQ_5m.json]
<yahoo_dir> holds ^NDX_1d.json, QQQ_1d.json and ^VIX_1d.json from the Yahoo chart API (interval=1d).
Prints every table as markdown. Nothing here trades or changes the paper rules.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
START, END = pd.Timestamp("1996-11-19"), pd.Timestamp("2026-11-18")
BLS_START = pd.Timestamp("2008-02-01")
HALF = pd.Timestamp("2017-07-01")
DECADES = [(START, pd.Timestamp("2006-11-18")), (pd.Timestamp("2006-11-19"), pd.Timestamp("2016-11-18")),
           (pd.Timestamp("2016-11-19"), END)]
BIG = 1.25
GAP_BUCKETS = [(0.0025, 0.005), (0.005, 0.01), (0.01, 0.02), (0.02, np.inf)]


# ---------- data ----------

def load_yahoo(path):
    """Daily OHLC indexed by exchange-local date (no time)."""
    res = json.load(open(path))["chart"]["result"][0]
    tz = res["meta"]["exchangeTimezoneName"]
    q = res["indicators"]["quote"][0]
    idx = pd.to_datetime(res["timestamp"], unit="s", utc=True).tz_convert(tz).tz_localize(None).normalize()
    df = pd.DataFrame({k: q[k] for k in ("open", "high", "low", "close")}, index=idx, dtype=float)
    return df[~df.index.duplicated(keep="last")].sort_index()


def clean(df):
    """Drop rows failing the PREREG checks; return (clean frame, number dropped)."""
    bad = df[["open", "high", "low", "close"]].isna().any(axis=1)
    bad |= df.high < df.low
    bad |= (df.open > df.high + 1e-9) | (df.open < df.low - 1e-9)
    bad |= (df.close > df.high + 1e-9) | (df.close < df.low - 1e-9)
    return df[~bad], int(bad.sum())


def features(df):
    """Per-day measures; every 'prior' input uses only earlier rows."""
    out = df.copy()
    prev = out.close.shift(1)
    out["ret"] = out.close / prev - 1
    out["range"] = (out.high - out.low) / prev
    out["gap"] = out.open / prev - 1
    out["intraday"] = out.close / out.open - 1
    out["base"] = out["range"].rolling(20).median().shift(1)  # median of the previous 20 days only
    out["big"] = (out["range"] > BIG * out["base"]).astype(float)
    out.loc[out.base.isna() | out["range"].isna(), "big"] = np.nan
    out["prior_big"] = out["big"].shift(1)
    out["open_eq_prev"] = (out.open.round(2) == prev.round(2))
    out["fill"] = np.where(out.gap > 0, out.low <= prev, out.high >= prev).astype(float)
    return out


def usable_open_years(f, limit=0.05):
    share = f.groupby(f.index.year)["open_eq_prev"].mean()
    return share, set(share[share < limit].index)


def add_vix(f, vix):
    v = vix.close.reindex(f.index).ffill()
    f = f.copy()
    f["vix_prev"] = v.shift(1)
    f["vix_ratio"] = f.vix_prev / v.shift(2).rolling(20).median()
    return f


def add_events(f, events):
    f = f.copy()
    for ev in ("fomc", "cpi", "jobs"):
        days = set(pd.to_datetime(events.loc[events.event == ev, "date"]))
        f[ev] = f.index.isin(days)
    f["any_event"] = f.fomc | f.cpi | f.jobs
    return f


# ---------- stats helpers ----------

def welch(a, b):
    a, b = pd.Series(a, dtype=float).dropna(), pd.Series(b, dtype=float).dropna()
    if len(a) < 2 or len(b) < 2:
        return float("nan")
    se = math.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    return (a.mean() - b.mean()) / se if se > 0 else float("nan")


def tstat(x):
    x = pd.Series(x, dtype=float).dropna()
    if len(x) < 2 or x.std(ddof=1) == 0:
        return float("nan")
    return x.mean() / (x.std(ddof=1) / math.sqrt(len(x)))


def pct(x, d=2):
    return "n/a" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{100 * x:.{d}f}%"


def md(rows, cols):
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    lines += ["| " + " | ".join(str(r[c]) for c in cols) + " |" for r in rows]
    return "\n".join(lines)


# ---------- questions ----------

def q1(f, open_years):
    rows, years_rows = [], []
    for ev, start in (("fomc", START), ("cpi", BLS_START), ("jobs", BLS_START)):
        s = f.loc[start:END].dropna(subset=["big"])
        evd, quiet = s[s[ev]], s[~s.any_event]
        g_ok = s.index.year.isin(open_years)
        for name, a, b in (("big-day rate", evd.big, quiet.big), ("mean range", evd["range"], quiet["range"]),
                           ("mean |gap|", evd.gap.abs()[g_ok[s[ev].values]], quiet.gap.abs()[g_ok[(~s.any_event).values]]),
                           ("mean return", evd.ret, quiet.ret)):
            rows.append({"event": ev, "period": f"{start:%Y-%m}→{END:%Y-%m}", "measure": name,
                         "event days": f"{pct(a.mean())} (n={a.notna().sum()})",
                         "quiet days": f"{pct(b.mean())} (n={b.notna().sum()})", "t": f"{welch(a, b):+.1f}"})
        yr = []
        for y, g in s.groupby(s.index.year):
            e, q = g.loc[g[ev], "range"], g.loc[~g.any_event, "range"]
            if len(e) and len(q):
                yr.append(e.mean() > q.mean())
        years_rows.append({"event": ev, "years with event-day range above quiet-day range": f"{sum(yr)} of {len(yr)}"})
    return rows, years_rows


def q2(f, open_years):
    s = f.loc[START:END]
    s = s[s.index.year.isin(open_years)].dropna(subset=["gap", "intraday"])

    def table(d):
        out = []
        for lo, hi in GAP_BUCKETS:
            for side, sign in (("up", 1), ("down", -1)):
                g = d[(d.gap * sign >= lo) & (d.gap * sign < hi)]
                signed = g.intraday * sign
                label = f"{lo * 100:g}–{hi * 100:g}%" if np.isfinite(hi) else f"≥{lo * 100:g}%"
                out.append({"gap": f"{side} {label}", "days": len(g),
                            "kept going (open→close)": pct((signed > 0).mean(), 0) if len(g) else "n/a",
                            "mean open→close, gap's way": pct(signed.mean()) if len(g) else "n/a",
                            "t": f"{tstat(signed):+.1f}" if len(g) > 1 else "n/a",
                            "touched prior close": pct(g.fill.astype(float).mean(), 0) if len(g) else "n/a"})
        return out

    whole = table(s)
    by_decade = {f"{a:%Y-%m}→{b:%Y-%m}": table(s.loc[a:b]) for a, b in DECADES}
    return whole, by_decade


def rate_row(label, mask, s):
    g = s.loc[mask.reindex(s.index, fill_value=False)]
    return {"condition": label, "days": len(g), "big-day rate": pct(g.big.mean(), 0) if len(g) else "n/a"}


def q3(f):
    s = f.loc[START:END].dropna(subset=["big"])
    rows = [rate_row("all days", pd.Series(True, index=s.index), s)]
    rows += [rate_row("prior day big", s.prior_big == 1, s), rate_row("prior day not big", s.prior_big == 0, s)]
    rows += [rate_row("VIX ratio < 0.9", s.vix_ratio < 0.9, s),
             rate_row("VIX ratio 0.9–1.1", (s.vix_ratio >= 0.9) & (s.vix_ratio <= 1.1), s),
             rate_row("VIX ratio > 1.1", s.vix_ratio > 1.1, s)]
    rows += [rate_row("VIX < 15", s.vix_prev < 15, s), rate_row("VIX 15–20", (s.vix_prev >= 15) & (s.vix_prev < 20), s),
             rate_row("VIX 20–30", (s.vix_prev >= 20) & (s.vix_prev < 30), s), rate_row("VIX ≥ 30", s.vix_prev >= 30, s)]
    b = s.loc[BLS_START:]
    rows += [rate_row("2008+: all days", pd.Series(True, index=b.index), b),
             rate_row("2008+: CPI, jobs or FOMC day", b.any_event, b),
             rate_row("2008+: no scheduled event", ~b.any_event, b)]
    rows += [rate_row("|gap| ≥ 1% (2001+, usable opens)", s.gap.abs() >= 0.01, s),
             rate_row("|gap| < 1% (2001+, usable opens)", s.gap.abs() < 0.01, s)]
    return rows


def rule(d):
    """The one pre-registered rule: HIGH if prior day big, |gap| >= 1%, or CPI/jobs/FOMC today."""
    return (d.prior_big == 1) | (d.gap.abs() >= 0.01) | d.any_event


def score_rule(d, call, truth):
    call, truth = call.astype(bool), truth.astype(bool)
    n = len(d)
    return {"days": n, "rule accuracy": pct((call == truth).mean(), 0),
            "'always normal' accuracy": pct((~truth).mean(), 0),
            "HIGH calls": int(call.sum()), "HIGH calls that were big": pct(truth[call].mean(), 0) if call.any() else "n/a",
            "big days caught": pct(call[truth].mean(), 0) if truth.any() else "n/a"}


def q3_rule(f):
    rows = []
    for a, b in ((BLS_START, HALF - pd.Timedelta(days=1)), (HALF, END)):
        d = f.loc[a:b].dropna(subset=["big", "prior_big", "gap"])
        r = score_rule(d, rule(d), d.big == 1)
        rows.append({"period": f"{a:%Y-%m}→{b:%Y-%m}", **r})
    return rows


def robustness(f):
    """PREREG 'what would change anything': a result counts only if it holds in every decade (or half) with |t| >= 2.
    Same measures as Q1/Q3, split by period. No new measures."""
    rows = []
    periods = {"fomc": [(a, b) for a, b in DECADES],
               "cpi": [(BLS_START, HALF - pd.Timedelta(days=1)), (HALF, END)],
               "jobs": [(BLS_START, HALF - pd.Timedelta(days=1)), (HALF, END)]}
    for ev, spans in periods.items():
        for a, b in spans:
            s = f.loc[a:b].dropna(subset=["big"])
            e, q = s[s[ev]], s[~s.any_event]
            for name, x, y in (("big-day rate", e.big, q.big), ("mean range", e["range"], q["range"]),
                               ("mean return", e.ret, q.ret)):
                rows.append({"test": f"{ev}: {name}", "period": f"{a:%Y-%m}→{b:%Y-%m}",
                             "event / condition": f"{pct(x.mean())} (n={len(x)})",
                             "quiet / rest": f"{pct(y.mean())} (n={len(y)})", "t": f"{welch(x, y):+.1f}"})
    for a, b in DECADES:
        s = f.loc[a:b].dropna(subset=["big"])
        for name, col, m in (("prior day big", "prior_big", s.prior_big == 1),
                             ("VIX ratio > 1.1", "vix_ratio", s.vix_ratio > 1.1),
                             ("VIX ratio < 0.9", "vix_ratio", s.vix_ratio < 0.9),
                             ("|gap| ≥ 1% (usable-open years)", "gap", s.gap.abs() >= 0.01)):
            known = s[col].notna()
            x, y = s.big[m & known], s.big[~m & known]
            rows.append({"test": f"big-day rate: {name}", "period": f"{a:%Y-%m}→{b:%Y-%m}",
                         "event / condition": f"{pct(x.mean(), 0)} (n={len(x)})",
                         "quiet / rest": f"{pct(y.mean(), 0)} (n={len(y)})", "t": f"{welch(x, y):+.1f}"})
    return rows


# ---------- Q3b: does it transfer to the morning call? ----------

def five_minute(path):
    res = json.load(open(path))["chart"]["result"][0]
    q = res["indicators"]["quote"][0]
    idx = pd.to_datetime(res["timestamp"], unit="s", utc=True).tz_convert("America/New_York")
    return pd.DataFrame({k: q[k] for k in ("open", "high", "low", "close")}, index=idx, dtype=float).dropna()


def morning_big(bars):
    """Same as news_log.py: 9:30-12:00 range / open vs 1.25x the median of the previous 20 sessions' ranges."""
    days = {}
    for d, g in bars.groupby(bars.index.date):
        w = g.between_time("09:30", "11:55")
        if len(w) >= 30 and w.index[0].strftime("%H:%M") == "09:30":
            days[pd.Timestamp(d)] = (w.high.max() - w.low.min()) / w.open.iat[0]
    s = pd.Series(days).sort_index()
    base = s.rolling(20).median().shift(1)
    return (s > BIG * base).where(base.notna()), s, base


def q3b(qqq_f, bars_path, news_path):
    out = {}
    if bars_path and Path(bars_path).exists():
        mb, _, _ = morning_big(five_minute(bars_path))
        both = pd.DataFrame({"morning": mb, "daily": qqq_f.big.reindex(mb.index)}).dropna()
        both = both.astype(bool)
        out["agreement"] = {"days": len(both), "same label": pct((both.morning == both.daily).mean(), 0),
                            "morning big": int(both.morning.sum()), "daily big": int(both.daily.sum()),
                            "both big": int((both.morning & both.daily).sum()),
                            "first": f"{both.index[0]:%Y-%m-%d}", "last": f"{both.index[-1]:%Y-%m-%d}"}
    if news_path and Path(news_path).exists():
        log = pd.read_csv(news_path)
        log = log[(log.late.astype(str) == "False") & log.range_pct.notna() & log.base_range_pct.notna()]
        log.index = pd.to_datetime(log.date)
        truth = log.range_pct > BIG * log.base_range_pct
        d = qqq_f.reindex(log.index)
        rule_call = rule(d)
        mine = log.vol == "high"
        out["news_days"] = [{"date": f"{t:%Y-%m-%d}", "morning big": "yes" if truth[t] else "no",
                             "my call": "high" if mine[t] else "normal",
                             "rule": "high" if rule_call[t] else "normal",
                             "rule inputs": ", ".join(x for x, on in (("prior day big", d.prior_big[t] == 1),
                                                                      (f"gap {100 * d.gap[t]:+.1f}%", abs(d.gap[t]) >= 0.01),
                                                                      ("CPI", d.cpi[t]), ("jobs", d.jobs[t]),
                                                                      ("FOMC", d.fomc[t])) if on) or "-"}
                            for t in log.index]
        out["news_score"] = {"days": len(log), "my calls right": int((mine == truth).sum()),
                             "rule right": int((rule_call == truth).sum()),
                             "'always normal' right": int((~truth).sum())}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("yahoo_dir")
    ap.add_argument("--news", default=str(HERE.parent / "news_log.csv"))
    ap.add_argument("--bars", default=str(HERE.parent.parent / "data_cache/yahoo/QQQ_5m.json"))
    a = ap.parse_args(argv)
    ydir = Path(a.yahoo_dir)
    events = pd.read_csv(HERE / "events.csv")

    print("## Data checks\n")
    raw = {}
    for sym in ("^NDX", "QQQ", "^VIX"):
        df = load_yahoo(ydir / f"{sym}_1d.json").loc[:END]
        if sym == "^VIX":
            df = df.dropna(subset=["close"])
            print(f"- {sym}: {len(df)} days with a close, {df.index[0]:%Y-%m-%d} → {df.index[-1]:%Y-%m-%d}")
        else:
            df, dropped = clean(df)
            print(f"- {sym}: {len(df)} days kept, {dropped} dropped by the checks, {df.index[0]:%Y-%m-%d} → {df.index[-1]:%Y-%m-%d}")
        raw[sym] = df
    ndx = add_events(add_vix(features(raw["^NDX"]), raw["^VIX"]), events)
    qqq = add_events(add_vix(features(raw["QQQ"]), raw["^VIX"]), events)
    share, ok_years = usable_open_years(ndx.loc[START:END])
    failed = sorted(set(share.index) - ok_years)
    # Years whose opens fail the check carry no gap or open-to-close values at all (PREREG data checks).
    ndx.loc[~ndx.index.year.isin(ok_years) & (ndx.index >= START), ["gap", "intraday"]] = np.nan
    print(f"- ^NDX opens equal to the prior close, by year: "
          + ", ".join(f"{y}: {100 * v:.0f}%" for y, v in share.items()))
    print(f"- Years whose opens fail the 5% check (left out of gap statistics): {failed or 'none'}")
    j = pd.DataFrame({"ndx": ndx.ret, "qqq": qqq.ret}).dropna()
    print(f"- ^NDX vs QQQ daily returns, {j.index[0]:%Y-%m-%d} → {j.index[-1]:%Y-%m-%d}: correlation {j.corr().iat[0, 1]:.4f} over {len(j)} days"
          f" (1999–2004: {j.loc[:'2004'].corr().iat[0, 1]:.4f}; 2005 on: {j.loc['2005':].corr().iat[0, 1]:.4f})")
    s = ndx.loc[START:END]
    print(f"- Sample: {len(s)} days, {s.index[0]:%Y-%m-%d} → {s.index[-1]:%Y-%m-%d}; big days {pct(s.big.mean(), 1)}")
    for ev in ("fomc", "cpi", "jobs"):
        ed = set(pd.to_datetime(events.loc[events.event == ev, "date"]))
        ed = {d for d in ed if START <= d <= END}
        missing = sorted(d for d in ed if d not in ndx.index)
        print(f"- {ev}: {len(ed)} dates in range, {len(ed) - len(missing)} on trading days"
              + (f"; not trading days: {[f'{d:%Y-%m-%d}' for d in missing]}" if missing else ""))

    rows, years = q1(ndx, ok_years)
    print("\n## Q1. Scheduled news days vs quiet days (^NDX)\n")
    print(md(rows, ["event", "period", "measure", "event days", "quiet days", "t"]))
    print()
    print(md(years, ["event", "years with event-day range above quiet-day range"]))

    whole, by_dec = q2(ndx, ok_years)
    cols = ["gap", "days", "kept going (open→close)", "mean open→close, gap's way", "t", "touched prior close"]
    print("\n## Q2. Opening gaps (^NDX, years with usable opens)\n")
    print(md(whole, cols))
    for k, t in by_dec.items():
        print(f"\n### {k}\n")
        print(md(t, cols))

    print("\n## Q3. Big-day rate by what's known before the open (^NDX)\n")
    print(md(q3(ndx), ["condition", "days", "big-day rate"]))
    print("\n### The pre-registered rule: HIGH if prior day big, |gap| ≥ 1%, or CPI/jobs/FOMC today\n")
    print(md(q3_rule(ndx), ["period", "days", "rule accuracy", "'always normal' accuracy", "HIGH calls",
                            "HIGH calls that were big", "big days caught"]))

    print("\n## Robustness: does each result hold in every decade or half? (^NDX)\n")
    print(md(robustness(ndx), ["test", "period", "event / condition", "quiet / rest", "t"]))

    print("\n## Q3b. Does it carry over to the morning call? (QQQ)\n")
    r = q3b(qqq, a.bars, a.news)
    if "agreement" in r:
        g = r["agreement"]
        print(f"- 5-minute bars {g['first']} → {g['last']}, {g['days']} sessions: the daily 'big' label matched the "
              f"morning one on {g['same label']} ({g['morning big']} big mornings, {g['daily big']} big days, {g['both big']} both).")
    if "news_days" in r:
        print()
        print(md(r["news_days"], ["date", "morning big", "my call", "rule", "rule inputs"]))
        n = r["news_score"]
        print(f"\nOn {n['days']} scored news days: my calls right {n['my calls right']}, the rule right {n['rule right']}, "
              f"'always normal' right {n["'always normal' right"]}.")


if __name__ == "__main__":
    main(sys.argv[1:])
