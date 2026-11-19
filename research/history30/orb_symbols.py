"""Part 4: our ORB (R1) and the first-candle ORB (R2) on 10 other symbols, plus a one-a-day "stock in play" pick
(R3a/R3b). Rules and the bar fixed in PREREG4.md before the data was downloaded.

Usage: python3 -I research/history30/orb_symbols.py <dir with SYMBOL_5Min.csv (raw)> <QQQ_5Min.csv>
"""
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import study  # noqa: E402
import strategies20 as s20  # noqa: E402

SYMBOLS = ["SPY", "IWM", "NVDA", "MSFT", "AAPL", "AMZN", "META", "GOOGL", "AVGO", "TSLA"]
STOCKS = ["NVDA", "MSFT", "AAPL", "AMZN", "META", "GOOGL", "AVGO", "TSLA"]
TICK = 0.01
START, END, HALF = pd.Timestamp("2016-01-04"), pd.Timestamp("2026-11-18"), pd.Timestamp("2021-07-01")
N_TESTS = 22
T_BAR = 3.1


def load(path):
    df = pd.read_csv(path)
    idx = pd.to_datetime(df.t, utc=True).dt.tz_convert("America/New_York")
    b = pd.DataFrame({"open": df.o.values, "high": df.h.values, "low": df.l.values, "close": df.c.values,
                      "volume": df.v.values}, index=pd.DatetimeIndex(idx)).sort_index()
    b = b[~b.index.duplicated()].between_time("09:30", "15:55")
    days, dropped = {}, 0
    for d, g in b.groupby(b.index.date):
        if len(g) >= 40 and g.index[0].strftime("%H:%M") == "09:30":
            days[pd.Timestamp(d)] = g
        else:
            dropped += 1
    return dict(sorted(days.items())), dropped


RULES = {"R1": s20.i1_orb, "R2": s20.i2_first_candle}


def trades_for(sym, days):
    out = []
    for d, g in days.items():
        if not START <= d <= END:
            continue
        for k, fn in RULES.items():
            r = fn(g, None)
            if r is None or r[2] is None:
                continue
            side, entry, px, why = r
            gross = side * (px - entry) / entry
            out.append({"symbol": sym, "rule": k, "date": d, "side": side, "entry": entry, "exit": px, "reason": why,
                        "gross": gross, "net": gross - 2 * TICK / entry})
    return out


def in_play(all_days):
    """Each date: the stock whose 9:30-bar volume / its prior-14-session average 9:30-bar volume is highest."""
    rv = {}
    for s in STOCKS:
        v = pd.Series({d: g.volume.iat[0] for d, g in all_days[s].items()}).sort_index()
        rv[s] = v / v.shift(1).rolling(14).mean()
    frame = pd.DataFrame(rv).dropna(how="all")
    return frame.idxmax(axis=1), frame


def summarize(t, label):
    row = {"test": label}
    for part, a, b in (("all", START, END), ("h1", START, HALF - pd.Timedelta(days=1)), ("h2", HALF, END)):
        x = t[(t.date >= a) & (t.date <= b)]
        row.update({f"{part}_n": len(x), f"{part}_win": (x.net > 0).mean() if len(x) else float("nan"),
                    f"{part}_mean": x.net.mean() if len(x) else float("nan"), f"{part}_t": study.tstat(x.net),
                    f"{part}_gmean": x.gross.mean() if len(x) else float("nan"), f"{part}_gt": study.tstat(x.gross)})
    row["first"] = f"{t.date.min():%Y-%m-%d}" if len(t) else ""
    return row


def bp(x):
    return "n/a" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{1e4 * x:+.2f}"


def main(argv):
    raw_dir, qqq_path = Path(argv[0]), argv[1]
    all_days, info, trades = {}, [], []
    for s in SYMBOLS:
        days, dropped = load(raw_dir / f"{s}_5Min.csv")
        all_days[s] = days
        inrange = [d for d in days if START <= d <= END]
        info.append(f"- {s}: {len(inrange)} sessions {inrange[0]:%Y-%m-%d} → {inrange[-1]:%Y-%m-%d}, {dropped} dropped")
        trades += trades_for(s, days)
    qdays, _ = load(qqq_path)
    qtr = pd.DataFrame(trades_for("QQQ", qdays))
    tr = pd.DataFrame(trades)

    pick, rvframe = in_play(all_days)
    r3 = []
    for d, s in pick.items():
        if not START <= d <= END or d not in all_days[s]:
            continue
        g = all_days[s][d]
        for k, lab in (("R1", "R3a"), ("R2", "R3b")):
            r = RULES[k](g, None)
            if r is None or r[2] is None:
                continue
            side, entry, px, why = r
            gross = side * (px - entry) / entry
            r3.append({"symbol": s, "rule": lab, "date": d, "side": side, "entry": entry, "exit": px, "reason": why,
                       "gross": gross, "net": gross - 2 * TICK / entry})
    r3 = pd.DataFrame(r3)

    print("## Data\n")
    print("\n".join(info))
    print(f"- Costs: ${TICK:.2f} a share on each side at the real price. Bar: t ≥ {T_BAR} after costs ({N_TESTS} tests) and positive in both halves.")
    print(f"- Stock-in-play pick, days per stock: " + ", ".join(f"{k} {v}" for k, v in pick.loc[START:END].value_counts().items()))

    rows = []
    for s in SYMBOLS:
        for k in RULES:
            rows.append(summarize(tr[(tr.symbol == s) & (tr.rule == k)], f"{s} {k}"))
    for lab in ("R3a", "R3b"):
        rows.append(summarize(r3[r3.rule == lab], f"In play {lab}"))
    res = pd.DataFrame(rows).set_index("test")
    comp = pd.DataFrame([summarize(qtr[qtr.rule == k], f"QQQ {k} (comparison)") for k in RULES]).set_index("test")

    cols = ["Symbol / rule", "Trades", "Win rate", "Mean per trade after costs (bp)", "t", "Before costs (bp, t)",
            "1st half (bp, t)", "2nd half (bp, t)"]
    print("\n## Results (1 bp = 0.01% of the price)\n")
    print("R1 = our 5-min ORB (2R, 90 min). R2 = first-candle ORB (10R or the close). R3 = the day's stock in play (a = R1, b = R2).\n")
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for k, r in pd.concat([res, comp]).iterrows():
        lines.append("| " + " | ".join([k, str(r.all_n), f"{100 * r.all_win:.0f}%", bp(r.all_mean), f"{r.all_t:+.1f}",
                                         f"{bp(r.all_gmean)} ({r.all_gt:+.1f})", f"{bp(r.h1_mean)} ({r.h1_t:+.1f})",
                                         f"{bp(r.h2_mean)} ({r.h2_t:+.1f})"]) + " |")
    print("\n".join(lines))

    print("\n## Ranking by t after costs (the pre-registered measure; QQQ not included)\n")
    rk = res.sort_values("all_t", ascending=False)
    lines = ["| Rank | Symbol / rule | t | Both halves positive | Passes the bar |", "|---|---|---|---|---|"]
    for i, (k, r) in enumerate(rk.iterrows(), 1):
        both = r.h1_mean > 0 and r.h2_mean > 0
        lines.append(f"| {i} | {k} | {r.all_t:+.1f} | {'yes' if both else 'no'} | {'YES' if (r.all_t >= T_BAR and both) else 'no'} |")
    print("\n".join(lines))
    pd.concat([tr, r3, qtr]).to_csv(HERE / "orb_symbols_trades.csv", index=False)


if __name__ == "__main__":
    main(sys.argv[1:])
