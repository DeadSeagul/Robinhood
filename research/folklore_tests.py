"""Quick tests of popular day-trading 'rules' on SPY/QQQ 5-minute bars.

Usage: python3 -I research/folklore_tests.py <data_dir>
Each test reports what happened next on the underlying, in dollars per share.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import backtest  # noqa: E402
from backtest import load, sessions  # noqa: E402


def stats(x, label):
    x = pd.Series(x, dtype=float).dropna()
    if x.empty:
        print(f"  {label:58s} n=0")
        return
    t = x.mean() / (x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 1 and x.std() > 0 else float("nan")
    print(f"  {label:58s} n={len(x):3d}  avg ${x.mean():+.2f}  win {(x > 0).mean():.0%}  t={t:+.1f}")


def orb_pnl(g, hi, lo, horizon=18):
    """5-min ORB: entry at first close outside the first bar, stop at other side, exit after horizon bars."""
    rest = g.iloc[1:]
    brk = rest[(rest.close > hi) | (rest.close < lo)]
    if brk.empty or brk.index[0].strftime("%H:%M") > "11:30":
        return None, None
    t0 = brk.index[0]
    side = 1 if brk.iloc[0].close > hi else -1
    entry, stop = brk.iloc[0].close, (lo if side == 1 else hi)
    after = rest[rest.index > t0].iloc[:horizon]
    for _, b in after.iterrows():
        if (side == 1 and b.low <= stop) or (side == -1 and b.high >= stop):
            return side, (stop - entry) * side
    return side, (after.close.iloc[-1] - entry) * side if len(after) else 0.0


def main():
    backtest.DATA = Path(sys.argv[1])
    for sym in ("SPY", "QQQ"):
        bars = load(sym, "5m")
        days = sessions(bars)
        keys = sorted(days)
        rth = pd.concat([days[k] for k in keys])
        hourly = rth.close.resample("1h").last().dropna()
        ema100 = hourly.ewm(span=100, adjust=False).mean()
        print(f"\n===== {sym}: {len(keys)} sessions =====")

        # 1. ORB with / against the 1H 100-EMA trend
        with_t, against_t = [], []
        for d in keys[15:]:  # warm-up for the EMA
            g = days[d]
            prior = ema100[ema100.index < g.index[0]]
            prior_close = hourly[hourly.index < g.index[0]]
            if prior.empty:
                continue
            up = prior_close.iloc[-1] > prior.iloc[-1]
            side, pnl = orb_pnl(g, g.iloc[0].high, g.iloc[0].low)
            if side is None:
                continue
            (with_t if (side == 1) == up else against_t).append(pnl)
        print("1) 5-min ORB filtered by 1H 100-EMA trend")
        stats(with_t, "breakout WITH the 1H trend")
        stats(against_t, "breakout AGAINST the 1H trend")

        # 2. '9:45 reversal': does 10:00-10:30 reverse the 9:30-9:45 move?
        first, nxt = [], []
        for d in keys:
            g = days[d]
            m1 = g.between_time("09:30", "09:40")
            m2 = g.between_time("09:45", "10:25")
            if len(m1) < 3 or len(m2) < 2:
                continue
            first.append(m1.close.iloc[-1] - m1.open.iloc[0])
            nxt.append(m2.close.iloc[-1] - m2.open.iloc[0])
        first, nxt = np.array(first), np.array(nxt)
        print("2) '9:45 reversal' — trade AGAINST the 9:30-9:45 move, 9:45 -> 10:30")
        stats(-np.sign(first) * nxt, "fade the first 15 minutes")
        big = np.abs(first) > np.median(np.abs(first))
        stats((-np.sign(first) * nxt)[big], "fade, only when the first 15 min move is big")

        # 3. 'First hour trend lock': follow the 9:30-10:30 direction until 15:55
        follow = []
        for d in keys:
            g = days[d]
            h1 = g.between_time("09:30", "10:25")
            rest = g.between_time("10:30", "15:55")
            if len(h1) < 10 or len(rest) < 10:
                continue
            follow.append(np.sign(h1.close.iloc[-1] - h1.open.iloc[0]) * (rest.close.iloc[-1] - rest.open.iloc[0]))
        print("3) 'First hour trend lock' — follow the first hour, 10:30 -> close")
        stats(follow, "follow the first-hour direction")

        # 4. Stop-hunt reversal at prior-day high/low: pierce, then close back inside within 2 bars -> fade 1 hour
        fades = []
        for i, d in enumerate(keys[1:], 1):
            p = days[keys[i - 1]]
            ph, pl = p.high.max(), p.low.min()
            g = days[d].between_time("09:35", "15:00")
            for lvl, direction in ((ph, -1), (pl, 1)):
                pierced = g[(g.high > lvl + 0.05)] if direction == -1 else g[(g.low < lvl - 0.05)]
                if pierced.empty:
                    continue
                t0 = pierced.index[0]
                win = g[g.index >= t0].iloc[:3]
                back = win[(win.close < lvl)] if direction == -1 else win[(win.close > lvl)]
                if back.empty:
                    continue
                tb = back.index[0]
                fut = g[g.index > tb].iloc[:12]
                if len(fut) < 3:
                    continue
                fades.append(direction * (fut.close.iloc[-1] - back.loc[tb].close))
        print("4) Stop-hunt reversal at prior-day high/low — fade the failed break for 1 hour")
        stats(fades, "fade a pierce that closes back inside within 2 bars")

        # 5. 'Broken parabolic' (5-min version): after 4+ straight green bars, first red bar -> short 30 min
        shorts = []
        for d in keys:
            g = days[d]
            green = (g.close > g.open).values
            for j in range(4, len(g) - 6):
                if green[j - 4:j].all() and not green[j]:
                    shorts.append(-(g.close.iloc[j + 6] - g.close.iloc[j]))
        print("5) 'Broken parabolic' — short the first red bar after 4+ green 5-min bars, hold 30 min")
        stats(shorts, "short after the streak breaks")


if __name__ == "__main__":
    main()
