"""Paper trading of the 5-minute QQQ opening-range breakout (ORB), scored after the fact with no discretion.

Live trading was paused on 2026-10-15 at the user's request ("just run paper trades"). Each trading day the playbook
signal is scored two ways and appended to research/paper_trades.csv:

  shares  QQQ itself: enter at the open of the bar after the signal bar; stop at the other side of the opening range;
          target 2R; exit at the close of the bar that ends 90 minutes after entry, or the 15:25 bar at the latest.
          A bar that touches both stop and target counts as a stop.
  option  the playbook contract (nearest-to-the-money next-day option priced <= $0.20 at entry). Its 5-minute bars,
          saved from Robinhood's get_option_historicals, get the playbook exits: stop -35%, target +100%,
          trail (arm at +50%, exit at +30%), 90-minute time stop. Entry = that bar's open + $0.01 (paying the ask);
          $0.09 of fees per round trip. Same stop-first rule.

Usage:
  python3 -I research/paper_orb.py score 2026-10-16 [--bars FILE] [--option-bars FILE --contract "10/19 735C"]
  python3 -I research/paper_orb.py score 2026-10-08 --contract "10/9 745P" --opt-entry 0.69 --opt-exit 0.45 \\
          --opt-reason stop --source live            # record an option result that is already known
  python3 -I research/paper_orb.py stats
--bars defaults to data_cache/yahoo/QQQ_5m.json (Yahoo chart JSON); Robinhood get_equity_historicals JSON also works.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
LOG = HERE / "paper_trades.csv"
DEFAULT_BARS = HERE.parent / "data_cache" / "yahoo" / "QQQ_5m.json"
FIELDS = ["date", "source", "signal_time", "side", "or_high", "or_low", "entry_time", "share_entry", "share_exit",
          "share_reason", "share_r", "contract", "opt_entry", "opt_exit", "opt_reason", "opt_ret", "opt_pnl", "note"]
BAR = pd.Timedelta(minutes=5)
FEES = 0.09


def load_bars(path: Path) -> pd.DataFrame:
    """5-minute OHLC bars (New York time) from Yahoo chart JSON or a Robinhood historicals response."""
    raw = json.loads(path.read_text())
    if "chart" in raw:
        r = raw["chart"]["result"][0]
        q = r["indicators"]["quote"][0]
        idx = pd.to_datetime(r["timestamp"], unit="s", utc=True)
        df = pd.DataFrame({k: q[k] for k in ("open", "high", "low", "close")}, index=idx)
    else:
        bars = raw["data"]["results"][0]["bars"]
        df = pd.DataFrame({"open": [float(b["open_price"]) for b in bars], "high": [float(b["high_price"]) for b in bars],
                           "low": [float(b["low_price"]) for b in bars], "close": [float(b["close_price"]) for b in bars]},
                          index=pd.to_datetime([b["begins_at"] for b in bars], utc=True))
    return df.dropna().tz_convert("America/New_York").sort_index()


def signal(day: pd.DataFrame) -> dict | None:
    """First 5-minute close beyond the 9:30 bar's range, on a bar that starts by 11:25."""
    day = day.between_time("09:30", "15:55")
    if day.empty or day.index[0].time() != time(9, 30):
        return None
    hi, lo = day.high.iat[0], day.low.iat[0]
    for k in range(1, len(day)):
        ts, b = day.index[k], day.iloc[k]
        if ts.time() > time(11, 25):
            break
        if b.close > hi or b.close < lo:
            return dict(k=k, signal_time=f"{ts + BAR:%H:%M}", side=1 if b.close > hi else -1, or_high=hi, or_low=lo)
    return dict(k=None, or_high=hi, or_low=lo)


def share_trade(day: pd.DataFrame, sig: dict) -> dict:
    day = day.between_time("09:30", "15:55")
    k, side = sig["k"] + 1, sig["side"]
    if k >= len(day):
        return {}
    entry, t0 = day.open.iat[k], day.index[k]
    stop = sig["or_low"] if side == 1 else sig["or_high"]
    risk = (entry - stop) * side
    if risk <= 0:
        return dict(entry_time=f"{t0:%H:%M}", share_entry=entry, share_exit=entry, share_reason="opened past stop",
                    share_r=0.0)
    target = entry + side * 2 * risk
    t_end = min(t0 + pd.Timedelta(minutes=90), t0.normalize() + pd.Timedelta(hours=15, minutes=30))
    exit_px, reason = None, "time"
    for ts, b in day.iloc[k:].iterrows():
        if (b.low <= stop) if side == 1 else (b.high >= stop):
            exit_px, reason = stop, "stop"
        elif (b.high >= target) if side == 1 else (b.low <= target):
            exit_px, reason = target, "target"
        elif ts + BAR >= t_end:
            exit_px = b.close
        if exit_px is not None:
            break
    if exit_px is None:
        return dict(entry_time=f"{t0:%H:%M}", share_entry=entry, share_reason="incomplete data")
    return dict(entry_time=f"{t0:%H:%M}", share_entry=round(entry, 2), share_exit=round(exit_px, 2), share_reason=reason,
                share_r=round(side * (exit_px - entry) / risk, 3))


def option_trade(opt: pd.DataFrame, entry_time: pd.Timestamp) -> dict:
    """Playbook exits on the option's 5-minute bars, starting at the bar that opens at entry_time."""
    bars = opt[opt.index >= entry_time]
    if bars.empty:
        return {}
    entry = round(bars.open.iat[0] + 0.01, 2)
    stop, target, arm, trail = entry * 0.65, entry * 2.0, entry * 1.5, entry * 1.3
    t_end = entry_time + pd.Timedelta(minutes=90)
    best, exit_px, reason = entry, None, "time"
    for n, (ts, b) in enumerate(bars.iterrows()):
        if b.low <= stop:
            exit_px, reason = (min(b.open, stop) if n else stop), "stop"
        elif b.high >= target and n:
            exit_px, reason = target, "target"
        elif best >= arm and b.low <= trail:
            exit_px, reason = trail, "trail"
        elif ts + BAR >= t_end:
            exit_px = b.close
        best = max(best, b.high)
        if exit_px is not None:
            break
    if exit_px is None:
        return dict(opt_entry=entry, opt_reason="incomplete data")
    return dict(opt_entry=entry, opt_exit=round(exit_px, 3), opt_reason=reason)


def read_log() -> pd.DataFrame:
    return pd.read_csv(LOG, dtype={"date": str, "contract": str, "note": str}) if LOG.exists() else pd.DataFrame(columns=FIELDS)


def score(args) -> None:
    bars = load_bars(Path(args.bars))
    day = bars[bars.index.date == pd.Timestamp(args.date).date()]
    row = dict(date=args.date, source=args.source, note=args.note)
    sig = signal(day)
    if sig is None:
        sys.exit(f"No regular-session bars for {args.date} in {args.bars}.")
    row.update(or_high=round(sig["or_high"], 2), or_low=round(sig["or_low"], 2))
    if sig["k"] is None:
        row.update(side="none")
    else:
        row.update(signal_time=sig["signal_time"], side="long" if sig["side"] == 1 else "short")
        row.update(share_trade(day, sig))
        if args.contract:
            row["contract"] = args.contract
        if args.option_bars:
            opt = load_bars(Path(args.option_bars))
            t0 = pd.Timestamp(f"{args.date} {row['entry_time']}", tz="America/New_York")
            row.update(option_trade(opt, t0))
        elif args.opt_entry is not None:
            row.update(opt_entry=args.opt_entry, opt_exit=args.opt_exit, opt_reason=args.opt_reason)
        if pd.notna(row.get("opt_exit", np.nan)):
            row["opt_ret"] = round(row["opt_exit"] / row["opt_entry"] - 1, 3)
            row["opt_pnl"] = round((row["opt_exit"] - row["opt_entry"]) * 100 - FEES, 2)
    log = read_log()
    prev = log[log.date == args.date]
    if len(prev):  # re-scoring a day keeps what is already known (live/shadow source, option result, note)
        old = prev.iloc[0].to_dict()
        for k in ("source", "contract", "opt_entry", "opt_exit", "opt_reason", "opt_ret", "opt_pnl", "note"):
            if (pd.isna(row.get(k)) or row.get(k) in (None, "", "paper")) and pd.notna(old.get(k)):
                row[k] = old[k]
    log = pd.concat([log[log.date != args.date], pd.DataFrame([row])], ignore_index=True).sort_values("date")
    log.reindex(columns=FIELDS).to_csv(LOG, index=False)
    print(", ".join(f"{k}={v}" for k, v in row.items() if pd.notna(v) and v != ""))


def stats(args) -> None:
    log = read_log()
    sig = log[log.side.isin(["long", "short"])]
    print(f"Days logged: {len(log)}; signals: {len(sig)} ({(log.side == 'none').sum()} days without one)")
    if len(sig):
        r = pd.to_numeric(sig.share_r, errors="coerce").dropna()
        print(f"QQQ shares: {len(r)} trades, win rate {(r > 0).mean():.0%}, avg {r.mean():+.2f}R, total {r.sum():+.2f}R")
        o = sig.dropna(subset=["opt_ret"])
        if len(o):
            print(f"Options: {len(o)} trades, win rate {(o.opt_ret > 0).mean():.0%}, avg {o.opt_ret.mean():+.0%}, "
                  f"total ${o.opt_pnl.sum():+.2f} per 1 contract")
        for src, g in sig.groupby("source"):
            print(f"  {src}: {len(g)} signals")


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("score")
    s.add_argument("date")
    s.add_argument("--bars", default=str(DEFAULT_BARS))
    s.add_argument("--option-bars")
    s.add_argument("--contract")
    s.add_argument("--opt-entry", type=float)
    s.add_argument("--opt-exit", type=float)
    s.add_argument("--opt-reason")
    s.add_argument("--source", default="paper", choices=["paper", "shadow", "live"])
    s.add_argument("--note")
    sub.add_parser("stats")
    args = p.parse_args(argv)
    {"score": score, "stats": stats}[args.cmd](args)


if __name__ == "__main__":
    main()
