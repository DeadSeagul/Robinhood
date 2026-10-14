"""Backtests of the most mechanical setups taught by famous traders, with rules fixed before the run.

Rules come from research_notes/Famous trader strategies compared/ (and reports/Famous trader strategies compared.md).
Every variant below was specified before any result was seen and is reported whether it wins or loses.

Intraday (5-minute bars, regular session only, last ~60 sessions, 63-symbol universe):
  ICT/TJR sweep model  First sweep of the prior-day high (low) between 9:35 and 11:00 ET, in a session that opened
                       inside yesterday's range. Within 6 bars a close below (above) the most recent swing low (high)
                       = market-structure shift. The first fair value gap (3-candle gap, >= 0.03% of price) formed
                       from the sweep bar onward = entry zone. Limit entry at the gap's near edge within 12 bars and
                       by 11:30. Stop just beyond the sweep extreme. Target A = 2R; target B = the opposite prior-day
                       level (at least 1R away). Exit at the 15:50 bar's close otherwise.
  ICT Silver Bullet    First fair value gap (>= 0.05% of price) completed between 10:00 and 10:55 ET; trade in its
                       direction with a limit at the gap's near edge until 11:00; stop beyond the gap's first candle;
                       target 2R; time exit at the 11:55 bar's close.
Daily (2 years, same universe):
  Turtle Soup (Raschke)  New 20-day low (high) whose previous 20-day low (high) is at least 4 sessions old and that
                         closes back above (below) it; enter at that close. Stop 0.1% beyond the day's extreme,
                         target 2R, exit at the 5th day's close.
  Turtle Soup, intraday fill (Raschke's actual order type, last ~60 sessions): same daily setup, but on 5-minute bars:
                         once price trades below the old 20-day low, a buy stop at the old low +0.1% (good for the day)
                         fills when price reclaims it; stop 0.1% under the day's low at fill time; target 2R; held up to
                         5 days (rest of the entry day on 5-minute bars, then daily bars). Shorts mirror.
                         (A first version entered at the old level on days that closed back above it. That used the
                         close to choose trades and was dropped as look-ahead biased; it showed an impossible +1.2R.)
  Holy Grail (Raschke)   ADX(14) > 30 the day before, +DI > -DI (long), first touch of the 20-day EMA; buy stop above
                         the touch day's high the next day; stop 0.1% under the touch day's low; target the prior
                         20-day high; 10-day time exit. Shorts mirror.
  Qullamaggie breakout   63-day return in the universe's top 20%, close >= 1.3x its 63-day low, 10-day range <= 15%,
                         close > SMA20, SMA10 > SMA20, ADR(20) >= 3%; buy stop 0.1% above the 10-day high next day;
                         stop 1 ADR below entry; sell half at the 3rd day's close if in profit (rest to breakeven
                         stop); remainder exits on the first close below SMA10 (max 60 days). Long only.
Fills are pessimistic: a bar (day) that touches both stop and target counts as a stop; on the entry bar (day) only the
stop is checked. Costs: 1 bp per side intraday, 2 bp per side daily.

Usage: python3 -I research/famous_setups.py data_cache/universe [out.csv]
"""
from __future__ import annotations

import json
import sys
from datetime import time
from pathlib import Path

import numpy as np
import pandas as pd

UNIVERSE_TODAY = pd.Timestamp("2026-10-14").date()  # drop the unfinished session


def _frame(path: Path) -> pd.DataFrame:
    raw = json.loads(path.read_text())["chart"]["result"][0]
    q = raw["indicators"]["quote"][0]
    idx = pd.to_datetime(raw["timestamp"], unit="s", utc=True).tz_convert("America/New_York")
    return pd.DataFrame({k: q[k] for k in ("open", "high", "low", "close", "volume")}, index=idx).dropna()


def load_intraday(data: Path, sym: str) -> dict:
    df = _frame(data / f"{sym}_5m.json").between_time("09:30", "15:55")
    return {d: g for d, g in df.groupby(df.index.date) if len(g) >= 70 and d < UNIVERSE_TODAY}


def load_daily(data: Path, sym: str) -> pd.DataFrame:
    df = _frame(data / f"{sym}_1d.json")
    df.index = pd.to_datetime(df.index.date)
    df = df[~df.index.duplicated(keep="last")]
    return df[df.index.date < UNIVERSE_TODAY]


# ---------- shared trade walker ----------

def walk(bars: pd.DataFrame, side: int, entry: float, stop: float, target: float, cost_bps: float,
         last_exit: time | None = None, max_bars: int | None = None, entry_bar: bool = True) -> dict:
    """If entry_bar, bars[0] is the bar (or day) the entry filled on and only the stop is checked on it."""
    risk = abs(entry - stop)
    exit_px, reason, n = None, "time", 0
    for n, (ts, b) in enumerate(bars.iterrows()):
        hit_stop = b.low <= stop if side == 1 else b.high >= stop
        hit_tgt = (b.high >= target if side == 1 else b.low <= target) and (n > 0 or not entry_bar)
        if hit_stop:
            gap = (b.open < stop) if side == 1 else (b.open > stop)
            exit_px, reason = (b.open if gap and (n > 0 or not entry_bar) else stop), "stop"
        elif hit_tgt:
            gap = (b.open > target) if side == 1 else (b.open < target)
            exit_px, reason = (b.open if gap else target), "target"
        elif (last_exit is not None and ts.time() >= last_exit) or (max_bars is not None and n + 1 >= max_bars):
            exit_px = b.close
        if exit_px is not None:
            break
    if exit_px is None:
        exit_px = bars.close.iloc[-1]
    pnl = side * (exit_px - entry) - 2 * cost_bps / 1e4 * entry
    return dict(entry=entry, exit=exit_px, reason=reason, r=pnl / risk, r_gross=side * (exit_px - entry) / risk,
                bars=n + 1)


# ---------- intraday: ICT / TJR ----------

def swing_ref(g: pd.DataFrame, j: int, side: int) -> float:
    """Most recent 2-bar fractal swing low (side=-1 trade) / high (side=+1 trade) before bar j."""
    col = "low" if side == -1 else "high"
    v = g[col].to_numpy()
    for m in range(j - 3, 1, -1):
        window = v[m - 2:m + 3]
        if (side == -1 and v[m] == window.min()) or (side == 1 and v[m] == window.max()):
            return v[m]
    lo = max(0, j - 3)
    return v[lo:j].min() if side == -1 else v[lo:j].max()


def fvg(g: pd.DataFrame, i: int, side: int) -> tuple[float, float] | None:
    """(near edge, far edge) of the fair value gap whose third candle is i, in trade direction `side`."""
    if side == -1 and g.low.iat[i - 2] > g.high.iat[i]:
        return g.high.iat[i], g.low.iat[i - 2]
    if side == 1 and g.high.iat[i - 2] < g.low.iat[i]:
        return g.low.iat[i], g.high.iat[i - 2]
    return None


def ict_sweep(g: pd.DataFrame, prev: pd.DataFrame) -> list[dict]:
    pdh, pdl = prev.high.max(), prev.low.min()
    open0 = g.open.iat[0]
    if not pdl < open0 < pdh:
        return []
    t = g.index.time
    out = []
    for side, level, far in ((-1, pdh, pdl), (1, pdl, pdh)):
        swept = (g.high > level) if side == -1 else (g.low < level)
        cand = [j for j in range(1, len(g)) if swept.iat[j] and time(9, 35) <= t[j] <= time(11, 0)]
        if not cand:
            continue
        j = cand[0]
        if (swept.iloc[:j]).any():
            continue  # level already traded through earlier (e.g. in the first bar): not a fresh sweep
        ref = swing_ref(g, j, side)
        mss = next((c for c in range(j, min(j + 7, len(g)))
                    if (g.close.iat[c] < ref if side == -1 else g.close.iat[c] > ref)), None)
        if mss is None:
            continue
        gap = None
        for i in range(max(j + 2, 2), min(mss + 2, len(g))):
            z = fvg(g, i, side)
            if z and abs(z[1] - z[0]) >= 0.0003 * g.close.iat[i]:
                gap = (i, z)
                break
        if gap is None:
            continue
        i, (near, _) = gap
        extreme = g.high.iloc[j:i + 1].max() if side == -1 else g.low.iloc[j:i + 1].min()
        stop = extreme * (1 + 0.0002) if side == -1 else extreme * (1 - 0.0002)
        risk = abs(stop - near)
        tgt_a = near + side * 2 * risk
        tgt_b = far if abs(far - near) >= risk and (far - near) * side > 0 else near + side * risk
        fill = None
        for k in range(i + 1, min(i + 13, len(g))):
            if t[k] > time(11, 30):
                break
            b = g.iloc[k]
            if (b.low <= tgt_a if side == -1 else b.high >= tgt_a):
                break  # ran to target without us
            if (b.high >= near if side == -1 else b.low <= near):
                fill = k
                break
        if fill is None:
            continue
        rest = g.iloc[fill:]
        for name, tgt in (("ict_sweep_2R", tgt_a), ("ict_sweep_liq", tgt_b)):
            res = walk(rest, side, near, stop, tgt, 1.0, last_exit=time(15, 50))
            out.append(dict(setup=name, side=side, time=f"{g.index[fill]:%H:%M}", **res))
    return out


def silver_bullet(g: pd.DataFrame) -> list[dict]:
    t = g.index.time
    for i in range(2, len(g)):
        if not time(10, 0) <= t[i] <= time(10, 55):
            continue
        for side in (1, -1):
            z = fvg(g, i, side)
            if not z or abs(z[1] - z[0]) < 0.0005 * g.close.iat[i]:
                continue
            near = z[0]
            stop = g.low.iat[i - 2] * (1 - 0.0002) if side == 1 else g.high.iat[i - 2] * (1 + 0.0002)
            risk = abs(near - stop)
            target = near + side * 2 * risk
            for k in range(i + 1, len(g)):
                if t[k] >= time(11, 0):
                    return []
                b = g.iloc[k]
                if (b.high >= target if side == 1 else b.low <= target):
                    return []
                if (b.low <= near if side == 1 else b.high >= near):
                    res = walk(g.iloc[k:], side, near, stop, target, 1.0, last_exit=time(11, 55))
                    return [dict(setup="silver_bullet_2R", side=side, time=f"{g.index[k]:%H:%M}", **res)]
            return []
    return []


# ---------- daily: Raschke, Qullamaggie ----------

def adx(df: pd.DataFrame, n: int = 14) -> pd.DataFrame:
    up, dn = df.high.diff(), -df.low.diff()
    plus = np.where((up > dn) & (up > 0), up, 0.0)
    minus = np.where((dn > up) & (dn > 0), dn, 0.0)
    tr = pd.concat([df.high - df.low, (df.high - df.close.shift()).abs(), (df.low - df.close.shift()).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / n, adjust=False).mean()
    pdi = 100 * pd.Series(plus, index=df.index).ewm(alpha=1 / n, adjust=False).mean() / atr
    mdi = 100 * pd.Series(minus, index=df.index).ewm(alpha=1 / n, adjust=False).mean() / atr
    dx = 100 * (pdi - mdi).abs() / (pdi + mdi)
    return pd.DataFrame({"adx": dx.ewm(alpha=1 / n, adjust=False).mean(), "pdi": pdi, "mdi": mdi})


def turtle_soup(df: pd.DataFrame) -> list[dict]:
    out, busy_until = [], -1
    for t in range(21, len(df) - 1):
        if t <= busy_until:
            continue
        for side in (1, -1):
            col = "low" if side == 1 else "high"
            win = df[col].iloc[t - 20:t]
            prior = win.min() if side == 1 else win.max()
            age = t - (t - 20 + int(np.argmin(win.to_numpy()) if side == 1 else np.argmax(win.to_numpy())))
            today = df.iloc[t]
            new_ext = today.low < prior if side == 1 else today.high > prior
            reclaim = today.close > prior if side == 1 else today.close < prior
            if not (new_ext and reclaim and age >= 4):
                continue
            stop = today.low * 0.999 if side == 1 else today.high * 1.001
            for variant, entry in (("turtle_soup_close", today.close),):
                if (entry - stop) * side <= 0:
                    continue
                target = entry + side * 2 * abs(entry - stop)
                # The signal day's extreme came before the reclaim, so the walk starts the next day.
                res = walk(df.iloc[t + 1:t + 6], side, entry, stop, target, 2.0, max_bars=5, entry_bar=False)
                out.append(dict(setup=variant, side=side, date=str(df.index[t].date()), **res))
            busy_until = t + 5
            break
    return out


def turtle_soup_intraday(days: dict, daily: pd.DataFrame) -> list[dict]:
    out, busy_until = [], None
    dates = list(daily.index)
    for d, g in sorted(days.items()):
        ts = pd.Timestamp(d)
        if ts not in daily.index or (busy_until is not None and ts <= busy_until):
            continue
        t = dates.index(ts)
        if t < 21:
            continue
        for side in (1, -1):
            col = "low" if side == 1 else "high"
            win = daily[col].iloc[t - 20:t].to_numpy()
            prior = win.min() if side == 1 else win.max()
            age = 20 - int(np.argmin(win) if side == 1 else np.argmax(win))
            if age < 4:
                continue
            level = prior * (1 + side * 0.001)
            broke, fill = False, None
            for k in range(len(g)):
                b = g.iloc[k]
                if not broke:
                    broke = b.low < prior if side == 1 else b.high > prior
                    if broke and (b.close > level if side == 1 else b.close < level):
                        # broke and reclaimed inside one bar: order unknown, so wait for the next bar
                        pass
                    continue
                if (b.high >= level if side == 1 else b.low <= level):
                    fill = k
                    break
            if fill is None:
                continue
            day_ext = g.low.iloc[:fill + 1].min() if side == 1 else g.high.iloc[:fill + 1].max()
            entry = max(g.open.iat[fill], level) if side == 1 else min(g.open.iat[fill], level)
            stop = day_ext * (1 - side * 0.001)
            if (entry - stop) * side <= 0:
                continue
            target = entry + side * 2 * abs(entry - stop)
            # rest of the entry day on 5-minute bars (stop checked on the fill bar, target from the next bar)
            res = walk(g.iloc[fill:], side, entry, stop, target, 0.0)
            if res["reason"] == "time":
                nxt = daily.iloc[t + 1:t + 5]
                if len(nxt):
                    res = walk(nxt, side, entry, stop, target, 0.0, max_bars=4, entry_bar=False)
            res["r"] -= 2 * 2.0 / 1e4 * entry / abs(entry - stop)
            out.append(dict(setup="turtle_soup_intraday", side=side, date=str(d), **res))
            busy_until = dates[min(t + 5, len(dates) - 1)]
            break
    return out


def holy_grail(df: pd.DataFrame) -> list[dict]:
    d = df.join(adx(df))
    d["ema"] = d.close.ewm(span=20, adjust=False).mean()
    out, busy_until = [], -1
    for t in range(40, len(d) - 1):
        if t <= busy_until:
            continue
        prev, cur, nxt = d.iloc[t - 1], d.iloc[t], d.iloc[t + 1]
        if prev.adx <= 30:
            continue
        side = 1 if prev.pdi > prev.mdi else -1
        first_touch = (cur.low <= cur.ema and prev.close > prev.ema) if side == 1 else (cur.high >= cur.ema and prev.close < prev.ema)
        if not first_touch:
            continue
        trigger = cur.high if side == 1 else cur.low
        if not (nxt.high > trigger if side == 1 else nxt.low < trigger):
            continue
        entry = max(nxt.open, trigger) if side == 1 else min(nxt.open, trigger)
        stop = cur.low * 0.999 if side == 1 else cur.high * 1.001
        target = d.high.iloc[t - 20:t].max() if side == 1 else d.low.iloc[t - 20:t].min()
        if (target - entry) * side <= 0 or (entry - stop) * side <= 0:
            continue
        res = walk(d.iloc[t + 1:t + 11], side, entry, stop, target, 2.0, max_bars=10)
        out.append(dict(setup="holy_grail", side=side, date=str(d.index[t].date()), **res))
        busy_until = t + res["bars"]
    return out


def qullamaggie(panel: dict[str, pd.DataFrame]) -> list[dict]:
    closes = pd.DataFrame({s: df.close for s, df in panel.items()})
    rank = (closes / closes.shift(63) - 1).rank(axis=1, pct=True)
    out = []
    for s, df in panel.items():
        d = df.copy()
        d["sma10"], d["sma20"] = d.close.rolling(10).mean(), d.close.rolling(20).mean()
        d["adr"] = (d.high / d.low - 1).rolling(20).mean()
        d["low63"] = d.close.rolling(63).min()
        d["hi10"], d["lo10"] = d.high.rolling(10).max(), d.low.rolling(10).min()
        d["rank"] = rank[s]
        t, n = 70, len(d)
        while t < n - 1:
            c = d.iloc[t]
            ok = (c["rank"] >= 0.8 and c.close >= 1.3 * c.low63 and (c.hi10 - c.lo10) / c.close <= 0.15
                  and c.close > c.sma20 and c.sma10 > c.sma20 and c.adr >= 0.03)
            nxt = d.iloc[t + 1]
            level = c.hi10 * 1.001
            if not (ok and nxt.high >= level):
                t += 1
                continue
            entry = max(nxt.open, level)
            risk = c.adr * entry
            stop = entry - risk
            cost = 2 * 2.0 / 1e4 * entry
            if nxt.low <= stop:  # stopped on the entry day (pessimistic)
                out.append(dict(setup="qullamaggie_breakout", side=1, date=str(d.index[t + 1].date()),
                                entry=entry, exit=stop, reason="stop", r=(stop - entry - cost) / risk, r_gross=-1.0,
                                bars=1))
                t += 2
                continue
            half, k, r_total, reason = None, t + 2, 0.0, "time"
            while k < min(n, t + 61):
                b = d.iloc[k]
                cur_stop = entry if half is not None else stop
                if b.low <= cur_stop:
                    px = min(b.open, cur_stop)
                    r_part = (px - entry) / risk
                    r_total = (0.5 * half + 0.5 * r_part) if half is not None else r_part
                    reason = "stop"
                    break
                if half is None and k == t + 3 and b.close > entry:
                    half = (b.close - entry) / risk
                if b.close < b.sma10 and k > t + 3:
                    r_part = (b.close - entry) / risk
                    r_total = (0.5 * half + 0.5 * r_part) if half is not None else r_part
                    reason = "sma10"
                    break
                k += 1
            else:
                b = d.iloc[min(k, n - 1)]
                r_part = (b.close - entry) / risk
                r_total = (0.5 * half + 0.5 * r_part) if half is not None else r_part
            out.append(dict(setup="qullamaggie_breakout", side=1, date=str(d.index[t + 1].date()), entry=entry,
                            exit=np.nan, reason=reason, r=r_total - cost / risk, r_gross=r_total, bars=k - t))
            t = k + 1
    return out


def summarize(trades: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for name, g in trades.groupby("setup"):
        r = g.r
        wins, losses = r[r > 0].sum(), -r[r < 0].sum()
        half = len(g) // 2
        rows.append(dict(setup=name, trades=len(g), win_rate=(r > 0).mean(), avg_r=r.mean(),
                         avg_r_before_costs=g.r_gross.mean(), total_r=r.sum(),
                         profit_factor=wins / losses if losses else np.inf,
                         t_stat=r.mean() / (r.std(ddof=1) / np.sqrt(len(r))) if len(r) > 2 else np.nan,
                         first_half_avg_r=g.r.iloc[:half].mean(), second_half_avg_r=g.r.iloc[half:].mean(),
                         longs=(g.side == 1).sum(), shorts=(g.side == -1).sum()))
    return pd.DataFrame(rows).set_index("setup")


def main() -> None:
    data = Path(sys.argv[1])
    syms = sorted(p.name.split("_")[0] for p in data.glob("*_5m.json"))
    trades = []
    for s in syms:
        days = load_intraday(data, s)
        keys = sorted(days)
        for a, b in zip(keys, keys[1:]):
            for tr in ict_sweep(days[b], days[a]) + silver_bullet(days[b]):
                trades.append(dict(symbol=s, date=str(b), **tr))
        for tr in turtle_soup_intraday(days, load_daily(data, s)):
            trades.append(dict(symbol=s, **tr))
    panel = {s: load_daily(data, s) for s in syms}
    for s, df in panel.items():
        for tr in turtle_soup(df) + holy_grail(df):
            trades.append(dict(symbol=s, **tr))
    trades += qullamaggie(panel)
    tdf = pd.DataFrame(trades).sort_values(["setup", "date"]).reset_index(drop=True)
    if len(sys.argv) > 2:
        tdf.to_csv(sys.argv[2], index=False)
    pd.set_option("display.width", 200)
    print(f"{len(syms)} symbols; intraday sessions {min(map(str, keys))}..{max(map(str, keys))}; "
          f"daily {panel[syms[0]].index[0].date()}..{panel[syms[0]].index[-1].date()}")
    print(summarize(tdf).round(3).to_string())
    for name in ("ict_sweep_2R", "silver_bullet_2R"):
        g = tdf[(tdf.setup == name) & tdf.symbol.isin(["QQQ", "SPY"])]
        if len(g):
            print(f"{name} on QQQ/SPY only: {len(g)} trades, avg {g.r.mean():+.2f}R, total {g.r.sum():+.1f}R")


if __name__ == "__main__":
    main()
