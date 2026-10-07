"""Intraday strategy research on SPY/QQQ 5-minute bars.

Usage: python3 -I research/backtest.py <data_dir>
<data_dir> holds Yahoo chart JSON: {SYM}_5m.json (range=60d) and {SYM}_1d.json.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(sys.argv[1])
SYMBOLS = ["SPY", "QQQ"]


def load(sym, interval):
    raw = json.loads((DATA / f"{sym}_{interval}.json").read_text())["chart"]["result"][0]
    q = raw["indicators"]["quote"][0]
    df = pd.DataFrame(
        {k: q[k] for k in ["open", "high", "low", "close", "volume"]},
        index=pd.to_datetime(raw["timestamp"], unit="s", utc=True).tz_convert("America/New_York"),
    ).dropna()
    return df


def sessions(df):
    df = df.between_time("09:30", "15:55")
    return {d: g for d, g in df.groupby(df.index.date) if len(g) >= 70}


def orb(days, minutes, horizon_min=90):
    """Opening-range breakout: first close outside the range after it forms.
    Stop = other side of the range. Record max favorable move before the stop
    or the horizon, and whether price reached 1R / 2R."""
    n = minutes // 5
    rows = []
    for d, g in days.items():
        rng = g.iloc[:n]
        hi, lo = rng.high.max(), rng.low.min()
        rest = g.iloc[n:]
        brk = rest[(rest.close > hi) | (rest.close < lo)]
        if brk.empty or brk.index[0].time() > pd.Timestamp("11:30").time():
            rows.append(dict(day=d, side=None))
            continue
        t0 = brk.index[0]
        side = 1 if brk.iloc[0].close > hi else -1
        entry = brk.iloc[0].close
        stop = lo if side == 1 else hi
        risk = abs(entry - stop)
        after = rest[rest.index > t0].iloc[: horizon_min // 5]
        mfe, stopped, exit_px = 0.0, False, after.close.iloc[-1] if len(after) else entry
        for _, b in after.iterrows():
            fav = (b.high - entry) if side == 1 else (entry - b.low)
            adv = (stop - b.low) if side == 1 else (b.high - stop)
            if adv >= 0:  # stop touched
                stopped, exit_px = True, stop
                break
            mfe = max(mfe, fav)
        rows.append(dict(day=d, side=side, time=t0.strftime("%H:%M"), risk=risk, mfe=mfe,
                         hit_050=mfe >= 0.50, hit_100=mfe >= 1.00, hit_1R=mfe >= risk, hit_2R=mfe >= 2 * risk,
                         stopped=stopped, pnl=(exit_px - entry) * side))
    return pd.DataFrame(rows)


def noise_momentum(days, lookback=14):
    """Zarattini/Aziz/Barbon 'noise area': at each 30-min mark, go long if price is
    above open*(1+sigma_t), short if below open*(1-sigma_t); sigma_t = mean |move from open|
    at that time of day over the prior `lookback` days. Exit on VWAP cross or at 15:55."""
    keys = sorted(days)
    moves = {}
    for d in keys:
        g = days[d]
        moves[d] = (g.close / g.open.iloc[0] - 1).abs().groupby(g.index.strftime("%H:%M")).first()
    trades = []
    for i, d in enumerate(keys):
        if i < lookback:
            continue
        sigma = pd.concat([moves[k] for k in keys[i - lookback:i]], axis=1).mean(axis=1)
        g = days[d].copy()
        o = g.open.iloc[0]
        tp = (g.high + g.low + g.close) / 3
        g["vwap"] = (tp * g.volume).cumsum() / g.volume.cumsum()
        pos, entry = 0, None
        for ts, b in g.iterrows():
            hm = ts.strftime("%H:%M")
            s = sigma.get(hm, np.nan)
            if pos != 0 and ((pos == 1 and b.close < b.vwap) or (pos == -1 and b.close > b.vwap) or hm == "15:55"):
                trades.append(dict(day=d, side=pos, pnl=(b.close - entry) * pos, exit=hm))
                pos = 0
                continue
            if pos == 0 and ts.minute in (0, 30) and hm >= "10:00" and hm <= "15:00" and not np.isnan(s):
                if b.close > o * (1 + s) and b.close > b.vwap:
                    pos, entry = 1, b.close
                elif b.close < o * (1 - s) and b.close < b.vwap:
                    pos, entry = -1, b.close
    return pd.DataFrame(trades)


def level_reactions(days, daily):
    """How price behaves at prior-day high/low/close: touch rate and whether the first
    touch holds (bounces 0.30 away within 30 min) or breaks (closes 0.30 through)."""
    rows = []
    keys = sorted(days)
    for d in keys:
        prev = daily[daily.index.date < d]
        if prev.empty:
            continue
        p = prev.iloc[-1]
        g = days[d]
        for name, lvl in [("prior_high", p.high), ("prior_low", p.low), ("prior_close", p.close)]:
            o = g.open.iloc[0]
            if abs(o - lvl) < 0.10:
                continue
            from_below = o < lvl
            touch = g[(g.high >= lvl) if from_below else (g.low <= lvl)]
            if touch.empty:
                rows.append(dict(level=name, touched=False))
                continue
            t0 = touch.index[0]
            nxt = g[g.index > t0].iloc[:6]
            if from_below:
                rejected = (nxt.low <= lvl - 0.30).any() and not (nxt.close >= lvl + 0.30).any()
                broke = (nxt.close >= lvl + 0.30).any()
            else:
                rejected = (nxt.high >= lvl + 0.30).any() and not (nxt.close <= lvl - 0.30).any()
                broke = (nxt.close <= lvl - 0.30).any()
            rows.append(dict(level=name, touched=True, rejected=rejected, broke=broke))
    return pd.DataFrame(rows)


def time_of_day(days):
    """Average absolute 30-minute move by time of day."""
    rows = []
    for d, g in days.items():
        c = g.close.resample("30min").last().dropna()
        o = g.open.resample("30min").first().dropna()
        mv = (c - o).abs()
        for ts, v in mv.items():
            rows.append(dict(slot=ts.strftime("%H:%M"), move=v))
    return pd.DataFrame(rows).groupby("slot").move.mean()


def main():
    for sym in SYMBOLS:
        bars = load(sym, "5m")
        daily = load(sym, "1d")
        days = sessions(bars)
        print(f"\n===== {sym}: {len(days)} sessions, {min(days)} to {max(days)} =====")

        print("\n-- Avg absolute 30-min move by time of day ($) --")
        print(time_of_day(days).round(2).to_string())

        for m in (5, 15, 30):
            r = orb(days, m)
            t = r.dropna(subset=["side"]).astype(
                {"risk": float, "mfe": float, "pnl": float, "hit_050": bool, "hit_100": bool,
                 "hit_1R": bool, "hit_2R": bool, "stopped": bool})
            print(f"\n-- ORB {m}-min (break by 11:30, stop = other side, 90-min window) --")
            print(f"days with a break: {len(t)}/{len(r)}  longs {int((t.side == 1).sum())} shorts {int((t.side == -1).sum())}")
            print(f"median range/risk ${t.risk.median():.2f}  median max favorable move ${t.mfe.median():.2f}")
            print(f"reached +$0.50: {t.hit_050.mean():.0%}  +$1.00: {t.hit_100.mean():.0%}  1R: {t.hit_1R.mean():.0%}  2R: {t.hit_2R.mean():.0%}  stopped: {t.stopped.mean():.0%}")
            print(f"avg P/L per share if held to stop/90min: ${t.pnl.mean():.2f}  win rate {(t.pnl > 0).mean():.0%}")

        nm = noise_momentum(days)
        if len(nm):
            print("\n-- Noise-area momentum (14d sigma, VWAP exit) --")
            print(f"trades {len(nm)}  win rate {(nm.pnl > 0).mean():.0%}  avg ${nm.pnl.mean():.2f}  "
                  f"avg win ${nm[nm.pnl > 0].pnl.mean():.2f}  avg loss ${nm[nm.pnl <= 0].pnl.mean():.2f}  total ${nm.pnl.sum():.2f}")

        lv = level_reactions(days, daily)
        print("\n-- Prior-day level reactions (first touch, 30-min window, 0.30 threshold) --")
        for name, g in lv.groupby("level"):
            t = g[g.touched == True].astype({"rejected": bool, "broke": bool})
            print(f"{name:12s} touched {len(t)}/{len(g)} ({len(t)/len(g):.0%})  rejected {t.rejected.mean():.0%}  broke {t.broke.mean():.0%}")


if __name__ == "__main__":
    main()
