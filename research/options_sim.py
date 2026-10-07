"""Approximate how a <= $0.20 SPY/QQQ option would have performed on 5-minute ORB breaks.

Black-Scholes with a flat IV (no smile, no IV crush/expansion), priced on 5-minute closes,
fills at mid +/- half a 1-cent spread. It is a rough guide to sizing exits, not a forecast.

Usage: python3 -I research/options_sim.py <data_dir>
"""
import sys
from math import erf, exp, log, sqrt
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from backtest import load, sessions  # noqa: E402

IV = {"SPY": 0.14, "QQQ": 0.18}
R = 0.04
MAX_PREMIUM = 0.20
YEAR_MIN = 252 * 390


def ncdf(x):
    return 0.5 * (1 + erf(x / sqrt(2)))


def bs(s, k, t, iv, call):
    if t <= 0:
        return max(0.0, s - k) if call else max(0.0, k - s)
    d1 = (log(s / k) + (R + iv * iv / 2) * t) / (iv * sqrt(t))
    d2 = d1 - iv * sqrt(t)
    if call:
        return s * ncdf(d1) - k * exp(-R * t) * ncdf(d2)
    return k * exp(-R * t) * ncdf(-d2) - s * ncdf(-d1)


def years_left(ts, dte):
    close = ts.normalize() + pd.Timedelta(hours=16)
    return ((close - ts).total_seconds() / 60 + dte * 390) / YEAR_MIN


def pick_strike(s, ts, dte, iv, call):
    """Nearest-to-the-money whole-dollar strike whose price is <= MAX_PREMIUM."""
    base = round(s)
    for off in range(0, 40):
        k = base + off if call else base - off
        px = bs(s, k, years_left(ts, dte), iv, call)
        if px <= MAX_PREMIUM:
            return k, px
    return None, None


def run(sym, dte, tp=1.0, sl=0.5, trail_arm=0.5, trail_to=0.3, last_exit="15:30", max_hold=90, filt=None):
    """filt: None, "with_prior_close" (calls only above yesterday's close, puts only below),
    or "narrow" (first 5-min range below its 14-day median)."""
    days = sessions(load(sym, "5m"))
    iv = IV[sym]
    keys = sorted(days)
    first_ranges = {d: days[d].iloc[0].high - days[d].iloc[0].low for d in keys}
    out = []
    for i, d in enumerate(keys):
        g = days[d]
        hi, lo = g.iloc[0].high, g.iloc[0].low
        rest = g.iloc[1:]
        brk = rest[(rest.close > hi) | (rest.close < lo)]
        if brk.empty or brk.index[0].strftime("%H:%M") > "11:30":
            continue
        t0, b0 = brk.index[0], brk.iloc[0]
        call = b0.close > hi
        if filt and i < 14:
            continue
        if filt == "with_prior_close":
            prev_close = days[keys[i - 1]].close.iloc[-1]
            if call != (b0.close > prev_close):
                continue
        if filt == "narrow":
            med = pd.Series([first_ranges[k] for k in keys[i - 14:i]]).median()
            if hi - lo >= med:
                continue
        k, px = pick_strike(b0.close, t0, dte, iv, call)
        if k is None:
            continue
        entry = round(px, 2) + 0.005
        best, exit_px, reason = entry, None, "time"
        for ts, b in rest[rest.index > t0].iterrows():
            v = bs(b.close, k, years_left(ts, dte), iv, call) - 0.005
            best = max(best, v)
            gain = v / entry - 1
            held = (ts - t0).total_seconds() / 60
            if gain >= tp:
                exit_px, reason = v, "target"
            elif gain <= -sl:
                exit_px, reason = v, "stop"
            elif best / entry - 1 >= trail_arm and v / entry - 1 <= trail_to:
                exit_px, reason = v, "trail"
            elif held >= max_hold or ts.strftime("%H:%M") >= last_exit:
                exit_px, reason = v, "time"
            if exit_px is not None:
                break
        if exit_px is None:
            exit_px = v
        out.append(dict(day=d, call=call, strike=k, entry=entry, exit=max(exit_px, 0.0), reason=reason))
    df = pd.DataFrame(out)
    df["ret"] = df.exit / df.entry - 1
    df["pnl_contract"] = (df.exit - df.entry) * 100 - 0.08  # ~4c fees each side
    return df


def main():
    data = Path(sys.argv[1])
    import backtest
    backtest.DATA = data
    for sym in ("SPY", "QQQ"):
        for dte in (0, 1):
            for label, kw in [("TP+100/SL-50", {}), ("TP+50/SL-50", {"tp": 0.5}), ("TP+100/SL-35", {"sl": 0.35}),
                              ("+prior-close", {"filt": "with_prior_close"}), ("+narrow-OR", {"filt": "narrow"})]:
                df = run(sym, dte, **kw)
                print(f"{sym} {dte}DTE {label:13s} trades {len(df):2d}  win {(df.ret > 0).mean():.0%}  "
                      f"avg return {df.ret.mean():+.0%}  avg $/contract {df.pnl_contract.mean():+.2f}  "
                      f"total ${df.pnl_contract.sum():+.0f}  exits {df.reason.value_counts().to_dict()}")


if __name__ == "__main__":
    main()
