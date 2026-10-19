"""Blind chart-replay drills: practise reading intraday charts without risking money.

  deal    pick a random moment on a day not used before and print the chart up to that moment only
  decide  record a call (long / short / pass, stop, target) before anything after that moment is shown
  reveal  play the following bars forward and score the call
  stats   how the calls have done, against the same bracket with the direction flipped (a coin flip)

Usage:
  python3 -I research/replay.py deal [--symbol QQQ]
  python3 -I research/replay.py decide 7 short --stop 746.20 --target 744.00 --tag orb-break --note "..."
  python3 -I research/replay.py reveal 7
  python3 -I research/replay.py stats

Data: Yahoo chart JSON in data_cache/yahoo (refresh with research/fetch_data.sh data_cache/yahoo QQQ SPY ...).
Only the last ~60 sessions are available, and each date is used for one drill so that a reveal on one
symbol cannot leak the market's direction into a later drill. Never open the data files while a drill
is open: the point is to decide without seeing the future.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

JOURNAL = HERE / "replay_journal.csv"
DATA = HERE.parent / "data_cache" / "yahoo"
FIELDS = ["id", "symbol", "date", "time", "last", "side", "stop", "target", "minutes", "tag", "note",
          "entry", "exit", "exit_time", "reason", "r", "r_flip", "r_long_def", "r_short_def",
          "mfe_r", "mae_r", "opt_ret", "dealt_at", "decided_at", "revealed_at"]
SLIP_BPS = 1.0  # per side
DEFAULT_STOP, DEFAULT_TARGET, DEFAULT_MINUTES = 0.0025, 0.005, 60  # brackets used to score passes
INDEX_ETFS = {"QQQ", "SPY"}
# Sessions I watched or traded live: I already know how they went, so they can't be drills.
SEEN_LIVE = {"2026-10-07", "2026-10-08", "2026-10-09", "2026-10-12", "2026-10-13", "2026-10-14", "2026-10-15", "2026-10-16", "2026-10-19"}
BAR = pd.Timedelta(minutes=5)


def load_sessions(sym: str, data: Path = DATA) -> dict:
    raw = json.loads((data / f"{sym}_5m.json").read_text())["chart"]["result"][0]
    q = raw["indicators"]["quote"][0]
    df = pd.DataFrame({k: q[k] for k in ("open", "high", "low", "close", "volume")},
                      index=pd.to_datetime(raw["timestamp"], unit="s", utc=True).tz_convert("America/New_York"))
    df = df.dropna().between_time("09:30", "15:55")
    return {d: g for d, g in df.groupby(df.index.date) if len(g) >= 70}


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def read_journal() -> pd.DataFrame:
    if JOURNAL.exists():
        text = ("date", "time", "side", "tag", "note", "exit_time", "reason", "dealt_at", "decided_at", "revealed_at")
        return pd.read_csv(JOURNAL, dtype={c: object for c in text})
    return pd.DataFrame(columns=FIELDS)


def write_journal(j: pd.DataFrame) -> None:
    j[FIELDS].to_csv(JOURNAL, index=False)


def vwap(g: pd.DataFrame) -> pd.Series:
    tp = (g.high + g.low + g.close) / 3
    return (tp * g.volume).cumsum() / g.volume.cumsum()


def ascii_chart(bars: pd.DataFrame, levels: dict, height: int = 14, marks: dict | None = None) -> str:
    """Text chart: '|' is a bar's high-low range, '*' its close, '-' a level line. marks: {timestamp: char}."""
    if len(bars) > 60:
        bars = bars.resample("10min", label="left", closed="left").agg(
            {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}).dropna()
    hi, lo = bars.high.max(), bars.low.min()
    span = max(hi - lo, 1e-6)
    shown = {k: v for k, v in levels.items() if lo - span * 0.3 <= v <= hi + span * 0.3}
    top = max([hi, *shown.values()]) + span * 0.04
    bottom = min([lo, *shown.values()]) - span * 0.04
    step = (top - bottom) / height
    rows = []
    for i in range(height):
        r_hi = top - i * step
        r_lo = r_hi - step
        cells = []
        for _, b in bars.iterrows():
            if r_lo <= b.close < r_hi:
                cells.append("*")
            elif b.low < r_hi and b.high >= r_lo:
                cells.append("|")
            else:
                cells.append(" ")
        labels = [k for k, v in shown.items() if r_lo <= v < r_hi]
        if labels:
            cells = [c if c != " " else "-" for c in cells]
        rows.append(f"{r_hi:10.2f} {''.join(cells)}  {' '.join(labels)}")
    if marks:
        line = [" "] * len(bars)
        for ts, ch in marks.items():
            pos = bars.index.searchsorted(ts, side="right") - 1
            if 0 <= pos < len(line):
                line[pos] = ch if line[pos] == " " else "!"  # ! = decision and exit in the same column
        rows.append(" " * 11 + "".join(line))
    n = len(bars)
    axis = [" "] * n
    free_from = 0
    for pos in sorted({0, n // 2, max(n - 5, 0)}):
        if pos < free_from:
            continue
        for k, ch in enumerate(f"{bars.index[pos]:%H:%M}"):
            if pos + k < n:
                axis[pos + k] = ch
        free_from = pos + 6
    rows.append(" " * 11 + "".join(axis))
    return "\n".join(rows)


def render(sym: str, days: dict, d, t: pd.Timestamp) -> str:
    """Everything a trader could know at the close of the bar labelled t, and nothing after it."""
    keys = sorted(days)
    g = days[d]
    vis = g[g.index <= t]
    prior = [days[k] for k in keys[:keys.index(d)]]
    prev = prior[-1]
    ph, pl, pc = prev.high.max(), prev.low.min(), prev.close.iloc[-1]
    p = (ph + pl + pc) / 3
    closes = [x.close.iloc[-1] for x in prior[-6:]]
    trend = " ".join(f"{c:.2f}({(c / b - 1):+.1%})" for b, c in zip(closes, closes[1:]))
    cum = [x[x.index.time <= t.time()].volume.sum() for x in prior[-20:]]
    rvol = vis.volume.sum() / np.mean(cum)
    last = vis.close.iloc[-1]
    vw = vwap(vis).iloc[-1]
    orh, orl = g.iloc[0].high, g.iloc[0].low
    out = [f"{sym}  {d:%a}  as of {t + BAR:%H:%M} ET  (date hidden until reveal)",
           f"Prior day  H {ph:.2f}  L {pl:.2f}  C {pc:.2f}   pivot {p:.2f}  R1 {2 * p - pl:.2f}  S1 {2 * p - ph:.2f}",
           f"Last 5 daily closes  {trend}",
           f"Today  open {vis.open.iloc[0]:.2f} (gap {vis.open.iloc[0] / pc - 1:+.2%})  high {vis.high.max():.2f}  "
           f"low {vis.low.min():.2f}  OR5 {orl:.2f}-{orh:.2f}  VWAP {vw:.2f}",
           f"Last {last:.2f} ({last / pc - 1:+.2%} on the day)   volume so far {rvol:.1f}x the 20-day average to this time",
           "",
           ascii_chart(vis, {"PDH": ph, "PDL": pl, "PDC": pc, "ORH": orh, "ORL": orl, "VWAP": vw}),
           "",
           " time     open     high      low    close   vol(k)"]
    for ts, b in vis.tail(12).iterrows():
        out.append(f"{ts:%H:%M} {b.open:8.2f} {b.high:8.2f} {b.low:8.2f} {b.close:8.2f} {b.volume / 1000:8.0f}")
    return "\n".join(out)


def simulate(future: pd.DataFrame, side: int, stop: float, target: float, minutes: int) -> dict:
    """Enter at the next bar's open; stop first if a bar touches both; time stop after `minutes` or 15:55."""
    entry, t0 = future.open.iloc[0], future.index[0]
    nan = float("nan")
    if (side == 1 and not stop < entry < target) or (side == -1 and not target < entry < stop):
        return dict(entry=entry, exit=entry, exit_time=t0, reason="skipped: opened past stop or target",
                    r=0.0, mfe_r=nan, mae_r=nan)
    risk = abs(entry - stop)
    mfe = mae = 0.0
    for ts, b in future.iterrows():
        fav = (b.high - entry) if side == 1 else (entry - b.low)
        adv = (entry - b.low) if side == 1 else (b.high - entry)
        mfe, mae = max(mfe, fav), max(mae, adv)
        hit_stop = b.low <= stop if side == 1 else b.high >= stop
        hit_target = b.high >= target if side == 1 else b.low <= target
        if hit_stop:
            px, why, when = stop, "stop", ts
        elif hit_target:
            px, why, when = target, "target", ts
        elif ts + BAR >= t0 + pd.Timedelta(minutes=minutes) or ts.time() >= pd.Timestamp("15:50").time():
            px, why, when = b.close, "time", ts + BAR
        else:
            continue
        pnl = side * (px - entry) - 2 * SLIP_BPS / 1e4 * entry
        return dict(entry=entry, exit=px, exit_time=when, reason=why, r=pnl / risk, mfe_r=mfe / risk, mae_r=mae / risk)
    b = future.iloc[-1]
    pnl = side * (b.close - entry) - 2 * SLIP_BPS / 1e4 * entry
    return dict(entry=entry, exit=b.close, exit_time=future.index[-1] + BAR, reason="time", r=pnl / risk,
                mfe_r=mfe / risk, mae_r=mae / risk)


def default_r(future: pd.DataFrame, side: int) -> float:
    e = future.open.iloc[0]
    return simulate(future, side, e * (1 - side * DEFAULT_STOP), e * (1 + side * DEFAULT_TARGET), DEFAULT_MINUTES)["r"]


def option_estimate(sym: str, side: int, res: dict) -> float:
    """Rough % return of a <= $0.20 next-day option over the same entry/exit (flat-IV Black-Scholes)."""
    if sym not in INDEX_ETFS or res["reason"].startswith("skipped"):
        return float("nan")
    import options_sim as o
    call = side == 1
    t0 = res["entry_time"]
    k, px = o.pick_strike(res["entry"], t0, 1, o.IV[sym], call)
    if k is None:
        return float("nan")
    v = o.bs(res["exit"], k, o.years_left(res["exit_time"], 1), o.IV[sym], call)
    return (v - 0.005) / (px + 0.005) - 1


def deal(args) -> None:
    j = read_journal()
    open_rows = j[j.revealed_at.isna()]
    if len(open_rows):
        sys.exit(f"Drill #{int(open_rows.id.iloc[0])} is still open: decide and reveal it first.")
    rng = random.Random(args.seed)
    syms = [args.symbol] if args.symbol else sorted(p.name.split("_")[0] for p in DATA.glob("*_5m.json"))
    if not syms:
        sys.exit(f"No data in {DATA}. Run: research/fetch_data.sh {DATA} QQQ SPY NVDA ...")
    used = set(j.date.astype(str)) | SEEN_LIVE
    cache = {s: load_sessions(s) for s in syms}
    free = [(s, d) for s in syms for d in sorted(cache[s])[6:] if str(d) not in used]
    if not free:
        sys.exit("Every available date has been used. Refresh the data to get new days.")
    sym, d = rng.choice(free)
    u = rng.random()
    lo, hi = ("09:40", "11:25") if u < 0.6 else ("11:30", "14:25") if u < 0.9 else ("14:30", "15:05")
    g = cache[sym][d]
    t = rng.choice(list(g.between_time(lo, hi).index))
    row = dict(id=int(j.id.max()) + 1 if len(j) else 1, symbol=sym, date=str(d), time=f"{t:%H:%M}",
               last=round(float(g.loc[t].close), 4), dealt_at=now())
    j = pd.concat([j, pd.DataFrame([row])], ignore_index=True)
    write_journal(j)
    print(f"Drill #{row['id']}\n")
    print(render(sym, cache[sym], d, t))
    print(f"\nDecide: python3 -I research/replay.py decide {row['id']} long|short|pass --stop P --target P "
          "[--minutes 60] [--tag T] [--note N]")


def locate(j: pd.DataFrame, drill_id: int):
    hit = j.index[j.id.astype(int) == drill_id]
    if not len(hit):
        sys.exit(f"No drill #{drill_id}.")
    return hit[0]


def decide(args) -> None:
    j = read_journal()
    i = locate(j, args.id)
    if pd.notna(j.at[i, "decided_at"]):
        sys.exit(f"Drill #{args.id} already has a decision; it can't be changed.")
    last = float(j.at[i, "last"])
    if args.side != "pass":
        if args.stop is None or args.target is None:
            sys.exit("long/short needs --stop and --target.")
        ok = args.stop < last < args.target if args.side == "long" else args.target < last < args.stop
        if not ok:
            sys.exit(f"Stop/target are on the wrong side of the last price {last:.2f}.")
    for k, v in dict(side=args.side, stop=args.stop, target=args.target, minutes=args.minutes,
                     tag=args.tag, note=args.note, decided_at=now()).items():
        j.at[i, k] = v
    write_journal(j)
    if args.side == "pass":
        print(f"Drill #{args.id}: PASS recorded.")
    else:
        rr = abs(args.target - last) / abs(last - args.stop)
        print(f"Drill #{args.id}: {args.side.upper()} from ~{last:.2f}, stop {args.stop:.2f}, target {args.target:.2f} "
              f"(planned {rr:.1f}:1), time stop {args.minutes} min. Recorded.")


def reveal(args) -> None:
    j = read_journal()
    i = locate(j, args.id)
    row = j.loc[i]
    if pd.isna(row.decided_at):
        sys.exit(f"Decide drill #{args.id} first.")
    if pd.notna(row.revealed_at):
        sys.exit(f"Drill #{args.id} was already revealed.")
    sym = row.symbol
    days = load_sessions(sym)
    d = pd.Timestamp(row.date).date()
    g = days[d]
    t = pd.Timestamp(f"{row.date} {row.time}", tz="America/New_York")
    future = g[g.index > t]
    upd = dict(r_long_def=default_r(future, 1), r_short_def=default_r(future, -1), revealed_at=now())
    marks = {t: "^"}
    print(f"Drill #{args.id}: {sym} on {d:%a %Y-%m-%d}, decision at {t + BAR:%H:%M} ET\n")
    if row.side == "pass":
        upd.update(r=0.0)
        print("You passed.")
    else:
        side = 1 if row.side == "long" else -1
        res = simulate(future, side, float(row.stop), float(row.target), int(row.minutes))
        res["entry_time"] = future.index[0]
        e = res["entry"]
        flip = simulate(future, -side, e + (e - float(row.stop)), e - (float(row.target) - e), int(row.minutes))
        upd.update(entry=round(e, 4), exit=round(res["exit"], 4), exit_time=f"{res['exit_time']:%H:%M}",
                   reason=res["reason"], r=res["r"], r_flip=flip["r"], mfe_r=res["mfe_r"], mae_r=res["mae_r"],
                   opt_ret=option_estimate(sym, side, res))
        marks[res["exit_time"] - BAR if res["reason"] == "time" else res["exit_time"]] = "x"
        if res["reason"].startswith("skipped"):
            print(f"{row.side.upper()} {res['reason']} (next open {e:.2f}); scored 0R.")
        else:
            print(f"{row.side.upper()} entered {e:.2f} at {future.index[0]:%H:%M}, exited {res['exit']:.2f} at "
                  f"{res['exit_time']:%H:%M} ({res['reason']}).  Result {res['r']:+.2f}R "
                  f"(${side * (res['exit'] - e):+.2f}/share before costs).")
            print(f"Best it got: {res['mfe_r']:+.2f}R in your favour; worst: {res['mae_r']:.2f}R against.")
        print(f"Same bracket, opposite direction: {flip['r']:+.2f}R.")
        if not np.isnan(upd["opt_ret"]):
            print(f"Rough <= $0.20 next-day option over the same window: {upd['opt_ret']:+.0%}.")
    print(f"Default bracket ({DEFAULT_STOP:.2%} stop / {DEFAULT_TARGET:.2%} target / {DEFAULT_MINUTES} min): "
          f"long {upd['r_long_def']:+.2f}R, short {upd['r_short_def']:+.2f}R.")
    print(f"Rest of day: {future.open.iloc[0]:.2f} -> high {future.high.max():.2f}, low {future.low.min():.2f}, "
          f"close {g.close.iloc[-1]:.2f}.\n")
    prev = days[sorted(days)[sorted(days).index(d) - 1]]
    print(ascii_chart(g, {"PDH": prev.high.max(), "PDL": prev.low.min(), "ORH": g.iloc[0].high,
                          "ORL": g.iloc[0].low}, height=16, marks=marks))
    print("   ^ = decision, x = exit, ! = both in one column")
    for k, v in upd.items():
        j.at[i, k] = v
    write_journal(j)


def stats(args) -> None:
    j = read_journal()
    r = j[j.revealed_at.notna()].copy()
    if r.empty:
        sys.exit("No revealed drills yet.")
    for c in ("r", "r_flip", "r_long_def", "r_short_def", "opt_ret"):
        r[c] = pd.to_numeric(r[c])
    calls = r[r.side.isin(["long", "short"]) & ~r.reason.astype(str).str.startswith("skipped")]
    passes = r[r.side == "pass"]
    print(f"Revealed drills: {len(r)}  (calls {len(calls)}, passes {len(passes)})")
    if len(calls):
        edge = (calls.r - calls.r_flip) / 2
        t = edge.mean() / (edge.std(ddof=1) / np.sqrt(len(edge))) if len(edge) > 2 and edge.std() > 0 else float("nan")
        print(f"Calls: win rate {(calls.r > 0).mean():.0%}, average {calls.r.mean():+.2f}R, total {calls.r.sum():+.1f}R")
        print(f"Same brackets with the direction flipped: average {calls.r_flip.mean():+.2f}R")
        print(f"Direction skill vs a coin flip: {edge.mean():+.2f}R per call (t = {t:.2f}; |t| < 2 is noise)")
        opt = calls.opt_ret.dropna()
        if len(opt):
            print(f"QQQ/SPY calls as <= $0.20 next-day options (rough): average {opt.mean():+.0%} over {len(opt)}")
        bucket = pd.cut(pd.to_datetime(calls.time, format="%H:%M").dt.hour * 60
                        + pd.to_datetime(calls.time, format="%H:%M").dt.minute,
                        [0, 690, 870, 1000], labels=["open-11:30", "11:30-14:30", "after 14:30"])
        for name, grp in [("tag", calls.tag.fillna("-")), ("time", bucket)]:
            tab = calls.groupby(grp, observed=True).r.agg(["count", "mean", "sum"])
            print(f"\nBy {name}:\n" + tab.round(2).to_string())
    if len(passes):
        best = passes[["r_long_def", "r_short_def"]].max(axis=1)
        print(f"\nPasses: default long {passes.r_long_def.mean():+.2f}R, default short {passes.r_short_def.mean():+.2f}R "
              f"on average; the better side made {best.mean():+.2f}R (hindsight).")


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("deal")
    s.add_argument("--symbol")
    s.add_argument("--seed", type=int)
    s = sub.add_parser("decide")
    s.add_argument("id", type=int)
    s.add_argument("side", choices=["long", "short", "pass"])
    s.add_argument("--stop", type=float)
    s.add_argument("--target", type=float)
    s.add_argument("--minutes", type=int, default=DEFAULT_MINUTES)
    s.add_argument("--tag")
    s.add_argument("--note")
    s = sub.add_parser("reveal")
    s.add_argument("id", type=int)
    sub.add_parser("stats")
    args = p.parse_args(argv)
    {"deal": deal, "decide": decide, "reveal": reveal, "stats": stats}[args.cmd](args)


if __name__ == "__main__":
    main()
