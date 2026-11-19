"""Part 2: the live ORB rules on 2016-2026 QQQ 5-minute bars (questions fixed in PREREG2.md before running).

Signal and exits come from research/paper_orb.py, the same code that scores the paper trades. The option leg is a
Black-Scholes estimate (flat IV = prior-day VXN), not real option prices.

Usage: python3 -I research/history30/orb10.py <alpaca 5Min csv> <yahoo dir with QQQ_1d.json, ^VIX_1d.json, ^VXN_1d.json>
"""
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
from options_sim import bs, years_left  # noqa: E402

START, END = pd.Timestamp("2016-01-04"), pd.Timestamp("2026-11-18")
HALF = pd.Timestamp("2021-07-01")
CAP_FRAC = 0.0015   # price cap = 0.15% of QQQ at entry (about $1.00 at $660)
HALF_SPREAD = 0.01
BUDGET = 1000.0
FEE = 0.09          # per contract, round trip, as in the paper account
R_RATE = 0.04


# ---------- data ----------

def load_bars(path):
    df = pd.read_csv(path)
    idx = pd.to_datetime(df.t, utc=True).dt.tz_convert("America/New_York")
    out = pd.DataFrame({"open": df.o.values, "high": df.h.values, "low": df.l.values, "close": df.c.values},
                       index=pd.DatetimeIndex(idx)).sort_index()
    return out[~out.index.duplicated()].between_time("09:30", "15:55")


def sessions(bars):
    """{date: day frame}, keeping days with a 9:30 bar and at least 40 regular-hours bars."""
    keep, dropped = {}, []
    for d, g in bars.groupby(bars.index.date):
        if len(g) >= 40 and g.index[0].strftime("%H:%M") == "09:30":
            keep[pd.Timestamp(d)] = g
        else:
            dropped.append(pd.Timestamp(d))
    return keep, dropped


def prior_close_series(path):
    """Yahoo daily closes, shifted so each date carries the previous trading day's close."""
    s = study.load_yahoo(path).close.dropna()
    return s.shift(1)


# ---------- option model ----------

def pick_strike(s, ts, iv, call, cap):
    """Nearest-the-money $1 strike whose model ask (mid + half spread) is <= cap; None if none within 15%."""
    t = years_left(ts, 1)
    k = math.floor(s) if call else math.ceil(s)
    for _ in range(int(0.15 * s)):
        mid = bs_r(s, k, t, iv, call)
        if mid + HALF_SPREAD <= cap:
            return k, mid
        k = k + 1 if call else k - 1
    return None, None


def bs_r(s, k, t, iv, call):
    return bs(s, k, t, iv, call)


def option_bars(day, entry_ts, k, iv, call):
    """Model mid prices per QQQ 5-minute bar from entry on: open/high/low at the bar's start, close at its end."""
    rows = []
    for ts, b in day[day.index >= entry_ts].iterrows():
        t0, t1 = years_left(ts, 1), years_left(ts + paper_orb.BAR, 1)
        fav, adv = (b.high, b.low) if call else (b.low, b.high)
        rows.append((ts, bs(b.open, k, t0, iv, call), bs(fav, k, t0, iv, call), bs(adv, k, t0, iv, call),
                     bs(b.close, k, t1, iv, call)))
    return pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close"]).set_index("ts")


def option_leg(day, sig, share, iv):
    entry_ts = day.index[sig["k"] + 1]
    s0 = day.open.iat[sig["k"] + 1]
    call = sig["side"] == 1
    cap = CAP_FRAC * s0
    k, mid = pick_strike(s0, entry_ts, iv, call, cap)
    if k is None:
        return {"opt_reason": "no strike under cap"}
    opt = option_bars(day, entry_ts, k, iv, call)
    stop = sig["or_low"] if call else sig["or_high"]
    r = paper_orb.option_trade(opt, entry_ts, und=day, side=sig["side"], und_stop=stop, breakeven=True)
    if "opt_exit" not in r:
        return {"opt_reason": r.get("opt_reason", "no result")}
    entry = r["opt_entry"]  # model mid at the entry bar's open + $0.01 = the model ask
    exit_px = r["opt_exit"] if r["opt_reason"] == "target" else max(0.0, r["opt_exit"] - HALF_SPREAD)  # sell at the bid
    n = math.floor(BUDGET / (entry * 100))
    if n < 1:
        return {"opt_reason": "budget too small"}
    pnl = n * 100 * (exit_px - entry) - n * FEE
    return {"strike": k, "opt_entry": round(entry, 3), "opt_exit": round(exit_px, 3), "opt_reason": r["opt_reason"],
            "contracts": n, "opt_pnl": round(pnl, 2), "cap": round(cap, 3)}


# ---------- run ----------

def run(bars_path, ydir):
    bars = load_bars(bars_path)
    days, dropped = sessions(bars)
    ydir = Path(ydir)
    vxn_prev = prior_close_series(ydir / "^VXN_1d.json")
    qqq_daily = study.load_yahoo(ydir / "QQQ_1d.json")
    qf = study.add_vix(study.features(qqq_daily), study.load_yahoo(ydir / "^VIX_1d.json"))
    events = pd.read_csv(HERE / "events.csv")
    ev = {e: set(pd.to_datetime(events.loc[events.event == e, "date"])) for e in ("fomc", "cpi", "jobs")}
    rows = []
    for d, day in sorted(days.items()):
        if not START <= d <= END:
            continue
        sig = paper_orb.signal(day)
        if not sig or sig.get("k") is None:
            rows.append({"date": d, "signal": False})
            continue
        share = paper_orb.share_trade(day, sig)
        row = {"date": d, "signal": True, "side": sig["side"], "signal_time": sig["signal_time"], **share}
        iv = vxn_prev.get(d, np.nan)
        if share.get("share_reason") in ("stop", "target", "time") and not np.isnan(iv):
            row.update(option_leg(day, sig, share, iv / 100))
        elif np.isnan(iv):
            row["opt_reason"] = "no VXN"
        row.update({e: d in ev[e] for e in ev})
        row["vix_ratio"] = qf.vix_ratio.get(d, np.nan)
        rows.append(row)
    return pd.DataFrame(rows), dropped, days, qqq_daily


# ---------- report ----------

def summ(df, col, unit):
    x = df[col].dropna()
    if x.empty:
        return {"trades": 0, "win rate": "n/a", f"mean {unit}": "n/a", "t": "n/a", f"total {unit}": "n/a"}
    fmt = (lambda v: f"{v:+.3f}") if unit == "R" else (lambda v: f"${v:+,.2f}")
    return {"trades": len(x), "win rate": f"{(x > 0).mean():.0%}", f"mean {unit}": fmt(x.mean()),
            "t": f"{study.tstat(x):+.1f}", f"total {unit}": fmt(x.sum())}


def table(groups, col, unit, label="group"):
    rows = [{label: name, **summ(g, col, unit)} for name, g in groups]
    return study.md(rows, [label, "trades", "win rate", f"mean {unit}", "t", f"total {unit}"])


def main(argv):
    res, dropped, days, qqq_daily = run(argv[0], argv[1])
    print("## Data checks\n")
    print(f"- Sessions kept: {len(days)}; dropped (no 9:30 bar or < 40 bars): {len(dropped)}"
          + (f" — {', '.join(f'{d:%Y-%m-%d}' for d in dropped[:15])}{' …' if len(dropped) > 15 else ''}" if dropped else ""))
    last = pd.Series({d: g.close.iat[-1] for d, g in days.items()})
    yc = qqq_daily.close.reindex(last.index)
    diff = (last / yc - 1).abs().dropna()
    print(f"- Last 5-minute close vs Yahoo daily close: {len(diff)} days, {(diff <= 0.001).mean():.1%} within 0.1%; "
          f"worst: " + ", ".join(f"{d:%Y-%m-%d} {100 * v:.2f}%" for d, v in diff.sort_values(ascending=False).head(5).items()))
    sig = res[res.signal]
    print(f"- {len(res)} sessions {res.date.min():%Y-%m-%d} → {res.date.max():%Y-%m-%d}; {len(sig)} signals "
          f"({len(res) - len(sig)} days without one)")
    print(f"- Option leg not priced: " + ", ".join(f"{k}: {v}" for k, v in
                                                   sig.opt_reason[sig.opt_pnl.isna()].value_counts().items()))
    wk = sig[sig.date.dt.weekday < 4]
    fri = sig[sig.date.dt.weekday == 4]
    halves = [("2016-01 → 2021-06", wk[wk.date < HALF]), ("2021-07 → 2026-11", wk[wk.date >= HALF])]

    print("\n## 1. Shares (no model), Monday–Thursday\n")
    print(table([("all", wk)] + halves, "share_r", "R", "period"))
    print("\nExit reasons: " + ", ".join(f"{k} {v}" for k, v in wk.share_reason.value_counts().items()))
    print("\n" + table([(str(y), g) for y, g in wk.groupby(wk.date.dt.year)], "share_r", "R", "year"))

    print("\n## 2. Options (Black-Scholes estimate), Monday–Thursday, $1,000 a trade\n")
    print(table([("all", wk)] + halves, "opt_pnl", "$", "period"))
    print("\nExit reasons: " + ", ".join(f"{k} {v}" for k, v in wk.opt_reason[wk.opt_pnl.notna()].value_counts().items()))
    print("\n" + table([(str(y), g) for y, g in wk.groupby(wk.date.dt.year)], "opt_pnl", "$", "year"))

    print("\n## 3. News days (Monday–Thursday)\n")
    any_ev = wk.fomc | wk.cpi | wk.jobs
    groups = [("jobs day", wk[wk.jobs]), ("CPI day", wk[wk.cpi]), ("FOMC day", wk[wk.fomc]),
              ("no scheduled event", wk[~any_ev]), ("(a) skip event days", wk[~any_ev]), ("(b) only event days", wk[any_ev]),
              ("every signal", wk)]
    for col, unit in (("share_r", "R"), ("opt_pnl", "$")):
        print(table(groups, col, unit))
        x, y = wk.loc[any_ev, col].dropna(), wk.loc[~any_ev, col].dropna()
        print(f"\nEvent days vs the rest ({unit}): Welch t = {study.welch(x, y):+.1f}; by half: "
              + "; ".join(f"{n} t = {study.welch(g.loc[g.fomc | g.cpi | g.jobs, col], g.loc[~(g.fomc | g.cpi | g.jobs), col]):+.1f}"
                          for n, g in halves) + "\n")

    print("## 4. Prior-day VIX ratio (Monday–Thursday)\n")
    vg = [("VIX ratio < 0.9", wk[wk.vix_ratio < 0.9]), ("0.9–1.1", wk[(wk.vix_ratio >= 0.9) & (wk.vix_ratio <= 1.1)]),
          ("> 1.1", wk[wk.vix_ratio > 1.1])]
    for col, unit in (("share_r", "R"), ("opt_pnl", "$")):
        print(table(vg, col, unit))
        hi, rest = wk[wk.vix_ratio > 1.1], wk[wk.vix_ratio <= 1.1]
        print(f"\n> 1.1 vs the rest ({unit}): Welch t = {study.welch(hi[col], rest[col]):+.1f}; by half: "
              + "; ".join(f"{n} t = {study.welch(g.loc[g.vix_ratio > 1.1, col], g.loc[g.vix_ratio <= 1.1, col]):+.1f}"
                          for n, g in halves) + "\n")

    print("## 5. Friday signals (skipped live)\n")
    print(table([("Fridays", fri)], "share_r", "R"))
    print()
    print(table([("Fridays", fri)], "opt_pnl", "$"))
    return res


if __name__ == "__main__":
    out = main(sys.argv[1:])
    out.to_csv(HERE / "orb10_trades.csv", index=False)
