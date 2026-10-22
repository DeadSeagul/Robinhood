"""Pre-market news reads, written down before the open and scored against what QQQ did afterwards.

On 2026-10-22 the user asked me to read the news each morning, since it shows how the market may act that day.
So before 9:30 ET each trading day I read the overnight and pre-market news (futures, scheduled data such as CPI or
jobs, Fed speakers, big-tech earnings, oil and rates) and record a call:

  bias  up / down / none   which way QQQ goes from the 9:30 open to 12:00, the window the ORB trades live in.
                           The overnight gap is already visible in futures, so it doesn't count.
  vol   normal / high      whether QQQ's 9:30-12:00 range beats 1.25x its median over the previous 20 sessions

The rules were fixed before the first entry:
  - An entry logged at or after 9:30 ET on its own date is marked late and left out of every score.
  - Only news published before the entry may be used. Search tools can mislabel dates, so check headline claims
    against prices.
  - The paper ORB rules don't change with the news. Instead, stats splits the ORB results into signals that agree
    with the news bias, signals against it, and days with no bias, so the news earns its place with a record.

Usage:
  python3 -I research/news_log.py add 2026-10-23 --bias down --vol high --events "CPI 8:30" \\
          --summary "..." --sources "https://... https://..."
  python3 -I research/news_log.py score 2026-10-23 [--bars FILE]
  python3 -I research/news_log.py stats
"""
from __future__ import annotations

import argparse
import math
import sys
from datetime import datetime, time, timezone
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from paper_orb import DEFAULT_BARS, LOG as ORB_LOG, load_bars  # noqa: E402

LOG = HERE / "news_log.csv"
FIELDS = ["date", "logged_at", "late", "bias", "vol", "events", "summary", "sources",
          "open", "px_1200", "move_pct", "range_pct", "base_range_pct", "bias_hit", "vol_hit",
          "orb_side", "orb_share_r", "orb_aligned"]
WINDOW = ("09:30", "11:55")  # bars starting 9:30 through 11:55, i.e. 9:30 to 12:00
HIGH_VOL = 1.25


def read_log() -> pd.DataFrame:
    if LOG.exists():
        return pd.read_csv(LOG, dtype={"date": str, "logged_at": str, "events": str, "summary": str, "sources": str,
                                       "orb_side": str, "orb_aligned": str})
    return pd.DataFrame(columns=FIELDS)


def write_log(log: pd.DataFrame) -> None:
    log.reindex(columns=FIELDS).sort_values("date").to_csv(LOG, index=False)


def is_late(date: str, logged_at: datetime) -> bool:
    """True when the entry was written at or after 9:30 ET on its own trading date (or on a later day)."""
    return pd.Timestamp(logged_at).tz_convert("America/New_York") >= pd.Timestamp(f"{date} 09:30",
                                                                                 tz="America/New_York")


def add(args, now: datetime | None = None) -> None:
    now = now or datetime.now(timezone.utc)
    log = read_log()
    if (log.date == args.date).any():
        sys.exit(f"{args.date} already has a news read; entries can't be rewritten.")
    late = is_late(args.date, now)
    row = dict(date=args.date, logged_at=now.strftime("%Y-%m-%d %H:%M:%S UTC"), late=late, bias=args.bias,
               vol=args.vol, events=args.events, summary=args.summary, sources=args.sources)
    write_log(pd.concat([log, pd.DataFrame([row])], ignore_index=True))
    print(f"News read for {args.date} logged at {row['logged_at']}" + (" - LATE (after 9:30 ET), won't be scored" if late else ""))


def window_stats(day: pd.DataFrame) -> tuple[float, float, float] | None:
    w = day.between_time(*WINDOW)
    if len(w) < 30 or w.index[0].time() != time(9, 30):
        return None
    o = w.open.iat[0]
    return o, w.close.iat[-1], (w.high.max() - w.low.min()) / o


def score_day(bars: pd.DataFrame, date: str, bias: str, vol: str) -> dict:
    days = {d: g for d, g in bars.groupby(bars.index.date)}
    d = pd.Timestamp(date).date()
    if d not in days or window_stats(days[d]) is None:
        return {}
    o, px, rng = window_stats(days[d])
    prior = [window_stats(days[k]) for k in sorted(days) if k < d][-20:]
    prior = [p[2] for p in prior if p is not None]
    base = float(pd.Series(prior).median()) if prior else float("nan")
    move = px / o - 1
    hit = {"up": float(move > 0), "down": float(move < 0)}.get(bias, float("nan"))
    vol_hit = float((rng > HIGH_VOL * base) == (vol == "high")) if prior else float("nan")
    return dict(open=round(o, 2), px_1200=round(px, 2), move_pct=round(100 * move, 3), range_pct=round(100 * rng, 3),
                base_range_pct=round(100 * base, 3), bias_hit=hit, vol_hit=vol_hit)


def orb_alignment(date: str, bias: str) -> dict:
    if not ORB_LOG.exists():
        return {}
    orb = pd.read_csv(ORB_LOG, dtype={"date": str})
    row = orb[orb.date == date]
    if row.empty or row.side.iat[0] not in ("long", "short"):
        return dict(orb_side="none", orb_aligned="no signal")
    side = row.side.iat[0]
    if bias not in ("up", "down"):
        aligned = "no bias"
    else:
        aligned = "with" if (side == "long") == (bias == "up") else "against"
    return dict(orb_side=side, orb_share_r=row.share_r.iat[0], orb_aligned=aligned)


def score(args) -> None:
    log = read_log()
    hit = log.index[log.date == args.date]
    if not len(hit):
        sys.exit(f"No news read logged for {args.date}.")
    i = hit[0]
    res = score_day(load_bars(Path(args.bars)), args.date, log.at[i, "bias"], log.at[i, "vol"])
    if not res:
        sys.exit(f"No full 9:30-12:00 window for {args.date} in {args.bars} yet.")
    res.update(orb_alignment(args.date, log.at[i, "bias"]))
    for k, v in res.items():
        log.at[i, k] = v
    write_log(log)
    print(", ".join(f"{k}={log.at[i, k]}" for k in ["date", "late", "bias", "vol", "move_pct", "range_pct",
                                                      "base_range_pct", "bias_hit", "vol_hit", "orb_side",
                                                      "orb_share_r", "orb_aligned"]))


def binom_p(k: int, n: int) -> float:
    """Two-sided exact binomial p-value against a coin flip."""
    if n == 0:
        return float("nan")
    tail = sum(math.comb(n, j) for j in range(min(k, n - k) + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def stats(args) -> None:
    log = read_log()
    if log.empty:
        sys.exit("No news reads yet.")
    log["late"] = log.late.astype(str).str.lower() == "true"
    s = log[~log.late & log.move_pct.notna()]
    print(f"News reads: {len(log)} logged, {int(log.late.sum())} late, {len(s)} scored")
    calls = s[s.bias.isin(["up", "down"])]
    if len(calls):
        k = int(calls.bias_hit.sum())
        print(f"Direction (open to 12:00): {k}/{len(calls)} right ({k / len(calls):.0%}); "
              f"coin-flip p = {binom_p(k, len(calls)):.2f}; {int((s.bias == 'none').sum())} days with no bias")
    v = s.vol_hit.dropna()
    if len(v):
        print(f"Volatility calls: {int(v.sum())}/{len(v)} right ({v.mean():.0%})")
    orb = s[s.orb_aligned.isin(["with", "against", "no bias"])].copy()
    if len(orb):
        orb["orb_share_r"] = pd.to_numeric(orb.orb_share_r)
        tab = orb.groupby("orb_aligned").orb_share_r.agg(["count", "mean", "sum"]).round(2)
        print("ORB share results by agreement with the news bias:\n" + tab.to_string())


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add")
    a.add_argument("date")
    a.add_argument("--bias", required=True, choices=["up", "down", "none"])
    a.add_argument("--vol", required=True, choices=["normal", "high"])
    a.add_argument("--events", default="")
    a.add_argument("--summary", required=True)
    a.add_argument("--sources", required=True)
    s = sub.add_parser("score")
    s.add_argument("date")
    s.add_argument("--bars", default=str(DEFAULT_BARS))
    sub.add_parser("stats")
    args = p.parse_args(argv)
    {"add": add, "score": score, "stats": stats}[args.cmd](args)


if __name__ == "__main__":
    main()
