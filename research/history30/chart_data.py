"""Build the CSV files behind the Nasdaq-100 chart study page (the user, 2026-11-19: "I just wanted to study the
chart ... look at the trends and how the chart moves").

Usage: python3 -I research/history30/chart_data.py <yahoo dir> <alpaca QQQ_5Min.csv> <out dir>
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import study  # noqa: E402

START, END = "1996-11-19", "2026-11-18"
# Big declines, grouped by episode: (name, window to find the peak, window to find the trough). The peak is the
# highest close in the first window and the trough the lowest close in the second; the numbers come from the data.
EPISODES = [
    ("1998 Russia / LTCM crisis", ("1998-06-01", "1998-08-01"), ("1998-08-01", "1998-10-31")),
    ("Dot-com bust", ("2000-01-01", "2000-06-30"), ("2000-07-01", "2002-12-31")),
    ("2008 financial crisis", ("2007-07-01", "2007-12-31"), ("2008-01-01", "2009-06-30")),
    ("2018 fourth-quarter selloff", ("2018-07-01", "2018-10-31"), ("2018-10-01", "2018-12-31")),
    ("COVID crash", ("2020-01-01", "2020-02-29"), ("2020-02-20", "2020-04-30")),
    ("2022 rate-hike bear market", ("2021-10-01", "2021-12-31"), ("2022-01-01", "2022-12-31")),
    ("2025 tariff selloff", ("2025-01-01", "2025-03-01"), ("2025-03-01", "2025-05-31")),
]


def ndx_files(ydir, out):
    full = study.load_yahoo(Path(ydir) / "^NDX_1d.json").loc[:END].close.dropna()
    ma200 = full.rolling(200).mean()
    s = full.loc[START:]
    dd = s / s.cummax() - 1
    above = (s > ma200.loc[START:])
    # weekly: last trading day of each week
    wk = pd.DataFrame({"close": s, "ma200": ma200.loc[START:], "drawdown_pct": 100 * dd})
    wk = wk.groupby(wk.index.to_period("W")).tail(1)
    wk.index.name = "date"
    wk.round(2).to_csv(out / "ndx_weekly.csv", date_format="%Y-%m-%d")

    rows = []
    for name, (p0, p1), (t0, t1) in EPISODES:
        pk_d = full.loc[p0:p1].idxmax()
        pk = full.loc[pk_d]
        tr_d = full.loc[t0:t1].idxmin()
        tr = full.loc[tr_d]
        after = full.loc[tr_d:]
        rec = after[after >= pk]
        rec_d = rec.index[0] if len(rec) else pd.NaT
        rows.append({"episode": name, "peak_date": pk_d.date(), "peak": round(pk, 2), "trough_date": tr_d.date(),
                     "trough": round(tr, 2), "decline_pct": round(100 * (tr / pk - 1), 1),
                     "months_falling": round((tr_d - pk_d).days / 30.44, 1),
                     "recovered_date": rec_d.date() if pd.notna(rec_d) else "",
                     "months_to_recover": round((rec_d - tr_d).days / 30.44, 1) if pd.notna(rec_d) else ""})
    pd.DataFrame(rows).to_csv(out / "ndx_declines.csv", index=False)

    ye = full.groupby(full.index.year).last()
    yrs = []
    for y in range(1997, 2027):
        r = ye[y] / ye[y - 1] - 1
        yrs.append({"year": str(y), "return_pct": round(100 * r, 1), "partial": "yes" if y == 2026 else "no"})
    pd.DataFrame(yrs).to_csv(out / "ndx_years.csv", index=False)

    full_years = [r for r in yrs if r["partial"] == "no"]
    summary = [
        ("start_date", START), ("end_date", END),
        ("start_close", round(s.iloc[0], 2)), ("end_close", round(s.iloc[-1], 2)),
        ("growth_multiple", round(s.iloc[-1] / s.iloc[0], 1)),
        ("annual_growth_pct", round(100 * ((s.iloc[-1] / s.iloc[0]) ** (365.25 / (s.index[-1] - s.index[0]).days) - 1), 1)),
        ("pct_days_above_200d", round(100 * above.mean(), 0)),
        ("up_years", sum(r["return_pct"] > 0 for r in full_years)),
        ("down_years", sum(r["return_pct"] <= 0 for r in full_years)),
        ("full_years", len(full_years)),
        ("worst_drawdown_pct", round(100 * dd.min(), 1)), ("worst_drawdown_date", dd.idxmin().date()),
        ("pct_days_within_10pct_of_high", round(100 * (dd > -0.10).mean(), 0)),
        ("ytd_2026_pct", next(r["return_pct"] for r in yrs if r["year"] == "2026")),
        ("end_vs_200d_pct", round(100 * (s.iloc[-1] / ma200.iloc[-1] - 1), 1)),
        ("end_drawdown_pct", round(100 * dd.iloc[-1], 1)),
    ]
    pd.DataFrame(summary, columns=["metric", "value"]).to_csv(out / "ndx_summary.csv", index=False)


def intraday_files(bars_path, out):
    df = pd.read_csv(bars_path)
    idx = pd.to_datetime(df.t, utc=True).dt.tz_convert("America/New_York")
    b = pd.DataFrame({"open": df.o.values, "high": df.h.values, "low": df.l.values, "close": df.c.values},
                     index=pd.DatetimeIndex(idx)).between_time("09:30", "15:55")
    b = b.loc["2016-01-04":END]
    days = [g for _, g in b.groupby(b.index.date) if len(g) >= 75 and g.index[0].strftime("%H:%M") == "09:30"]
    blocks = [f"{h:02d}:{m:02d}" for h in range(9, 16) for m in (0, 30)][1:]  # 09:30 ... 15:30
    rng = {k: [] for k in blocks}
    hi_cnt = dict.fromkeys(blocks, 0)
    lo_cnt = dict.fromkeys(blocks, 0)
    first30_share, close_pos = [], []
    for g in days:
        blk = g.index.strftime("%H:") + np.where(g.index.minute < 30, "00", "30")
        o = g.open.iat[0]
        for k, part in g.groupby(blk):
            rng[k].append((part.high.max() - part.low.min()) / o)
        hi_cnt[blk[np.argmax(g.high.values)]] += 1
        lo_cnt[blk[np.argmin(g.low.values)]] += 1
        day_range = g.high.max() - g.low.min()
        if day_range > 0:
            f = g.iloc[:6]
            first30_share.append((f.high.max() - f.low.min()) / day_range)
            close_pos.append((g.close.iat[-1] - g.low.min()) / day_range)
    n = len(days)
    prof = pd.DataFrame({"time": [k for k in blocks],
                         "avg_range_pct": [round(100 * np.mean(rng[k]), 3) for k in blocks],
                         "day_high_pct": [round(100 * hi_cnt[k] / n, 1) for k in blocks],
                         "day_low_pct": [round(100 * lo_cnt[k] / n, 1) for k in blocks]})
    prof.to_csv(out / "qqq_intraday_profile.csv", index=False)
    cp = np.array(close_pos)
    kinds = pd.DataFrame({"day_type": ["Closed in the top 20% of its range", "Closed in the middle 60%",
                                       "Closed in the bottom 20% of its range"],
                          "pct_of_days": [round(100 * (cp >= 0.8).mean(), 1), round(100 * ((cp > 0.2) & (cp < 0.8)).mean(), 1),
                                          round(100 * (cp <= 0.2).mean(), 1)]})
    kinds.to_csv(out / "qqq_day_types.csv", index=False)
    extremes_first_hour = np.mean([(np.argmax(g.high.values) < 12) or (np.argmin(g.low.values) < 12) for g in days])
    pd.DataFrame([("sessions", n), ("first_date", f"{pd.Timestamp(days[0].index[0]):%Y-%m-%d}"),
                  ("last_date", f"{pd.Timestamp(days[-1].index[0]):%Y-%m-%d}"),
                  ("median_first30_share_pct", round(100 * float(np.median(first30_share)), 0)),
                  ("pct_days_high_or_low_in_first_hour", round(100 * extremes_first_hour, 0))],
                 columns=["metric", "value"]).to_csv(out / "qqq_intraday_summary.csv", index=False)


def recent_file(ydir, out):
    q = study.load_yahoo(Path(ydir) / "QQQ_1d.json").loc[:END]
    q["ma20"] = q.close.rolling(20).mean()
    q["ma50"] = q.close.rolling(50).mean()
    r = q.iloc[-128:][["open", "high", "low", "close", "ma20", "ma50"]].round(2)
    r.index.name = "date"
    r.to_csv(out / "qqq_recent.csv", date_format="%Y-%m-%d")


if __name__ == "__main__":
    ydir, bars, out = sys.argv[1], sys.argv[2], Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    ndx_files(ydir, out)
    intraday_files(bars, out)
    recent_file(ydir, out)
    for f in sorted(out.glob("*.csv")):
        print(f.name, sum(1 for _ in open(f)) - 1, "rows", f.stat().st_size, "bytes")
