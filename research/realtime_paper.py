"""Real-time paper trading: the ORB options trade decided as it happens, with fills at the live ask and bid.

On 2026-11-09 the user agreed to switch from after-the-fact scoring to real-time paper trading before any move to
real money (see REALTIME.md for the procedure and the go-live bar). The rules are the $10,000 options account's
(paper_account.py); only the fills change. paper_orb.py still scores every day after the fact, so the two logs
side by side show how much the bar-open fills flattered the results.

The QQQ side runs here, from Yahoo's 1- and 5-minute bars, so the waiting costs nothing. Option quotes come from
Robinhood through my tools, and every decision is logged with the clock time it was made.

  python3 -I research/realtime_paper.py wait-signal [--minutes 110]      # until a signal, no signal, or timeout
  python3 -I research/realtime_paper.py watch --side long --stop 662.02 --seconds 120
  python3 -I research/realtime_paper.py log entry --contract "11/11 683C" --ask 0.91 --bid 0.89 --qqq 668.70
  python3 -I research/realtime_paper.py log exit --reason trail --ask 1.19 --bid 1.17 --qqq 671.20
  python3 -I research/realtime_paper.py log no_signal | missed --note "..."
  python3 -I research/realtime_paper.py log shadow_exit --reason target --ask 1.86 --bid 1.84 --qqq 690.10
  python3 -I research/realtime_paper.py report

The no-trail shadow (pre-registered 2026-11-12 at the user's request, counted from 2026-11-16): the same entry, the
same stop, 2x target and 90-minute time exit, but no trail. It only differs from the official trade when the trail
fires; then monitoring carries on until the shadow's own exit, logged as `shadow_exit`. The official rules and the
go-live bar don't change.
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
import time as clock
from datetime import datetime, time
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from paper_account import BUDGET, RISK, START, option_size, tradable  # noqa: E402
from paper_orb import BAR, FEES, signal  # noqa: E402

LOG = HERE / "realtime_paper.csv"
FIELDS = ["date", "logged_at_et", "event", "side", "contract", "contracts", "opt_ask", "opt_bid", "qqq", "reason",
          "note"]
NY = "America/New_York"
LAST_ENTRY = time(11, 30)   # a 5-minute close beyond the range on a bar starting by 11:25
GO_LIVE_TRADES = 20
SHADOW_FROM = "2026-11-16"  # the no-trail shadow counts from the first trade after it was pre-registered (11/12)


def now_et() -> pd.Timestamp:
    return pd.Timestamp.now(tz=NY)


def yahoo(interval: str) -> pd.DataFrame:
    """Today's QQQ bars from Yahoo, New York time. The last bar may still be forming."""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/QQQ?interval={interval}&range=1d"
    raw = subprocess.run(["curl", "-sS", "-m", "20", "-A", "Mozilla/5.0", url], capture_output=True, text=True,
                         check=True).stdout
    r = json.loads(raw)["chart"]["result"][0]
    q = r["indicators"]["quote"][0]
    df = pd.DataFrame({k: q[k] for k in ("open", "high", "low", "close")},
                      index=pd.to_datetime(r.get("timestamp", []), unit="s", utc=True))
    return df.dropna().tz_convert(NY).sort_index()


def completed(bars: pd.DataFrame, width: pd.Timedelta, at: pd.Timestamp) -> pd.DataFrame:
    return bars[bars.index + width <= at]


def check_signal(bars: pd.DataFrame, at: pd.Timestamp) -> dict:
    """'signal', 'none' (no close beyond the range by the 11:25 bar) or 'wait'. Only today's bars count: before
    the open Yahoo's one-day chart still holds the previous session."""
    bars = bars[bars.index.date == at.date()]
    day = completed(bars, BAR, at).between_time("09:30", "15:55")
    sig = signal(day)
    if sig is None:
        return dict(state="wait")
    if sig["k"] is not None:
        b = day.iloc[sig["k"]]
        return dict(state="signal", side="long" if sig["side"] == 1 else "short", or_high=sig["or_high"],
                    or_low=sig["or_low"], bar=f"{day.index[sig['k']]:%H:%M}", close=b.close,
                    entry_time=sig["signal_time"])
    return dict(state="none" if at.time() >= LAST_ENTRY else "wait", or_high=sig["or_high"], or_low=sig["or_low"])


def wait_signal(args) -> None:
    if not tradable(f"{now_et():%Y-%m-%d}"):
        sys.exit("Friday or weekend: the playbook doesn't trade today.")
    deadline = clock.time() + 60 * args.minutes
    while True:
        at = now_et()
        res = check_signal(yahoo("5m"), at)
        if res["state"] != "wait":
            print(" ".join(f"{k}={v:.2f}" if isinstance(v, float) else f"{k}={v}" for k, v in res.items()),
                  f"now={at:%H:%M:%S}")
            return
        if clock.time() > deadline:
            print(f"state=still_waiting now={at:%H:%M:%S}")
            return
        clock.sleep(15)


def stop_hit(bars: pd.DataFrame, side: str, stop: float) -> pd.Series | None:
    hit = bars[bars.low <= stop] if side == "long" else bars[bars.high >= stop]
    return None if hit.empty else hit.iloc[0]


def watch(args) -> None:
    since = pd.Timestamp(f"{now_et():%Y-%m-%d} {args.since}", tz=NY) if args.since else None
    deadline = clock.time() + args.seconds
    while True:
        bars = yahoo("1m")
        bars = bars[bars.index.date == now_et().date()]
        if since is not None:
            bars = bars[bars.index >= since.floor("min")]
        hit = stop_hit(bars, args.side, args.stop)
        if hit is not None:
            print(f"state=stop bar={hit.name:%H:%M} low={hit.low:.2f} high={hit.high:.2f} now={now_et():%H:%M:%S}")
            return
        if clock.time() > deadline:
            last = f"{bars.close.iat[-1]:.2f}" if len(bars) else "none"
            print(f"state=ok qqq={last} now={now_et():%H:%M:%S}")
            return
        clock.sleep(15)


def read_log() -> pd.DataFrame:
    if LOG.exists():
        return pd.read_csv(LOG, dtype={"date": str, "contract": str, "reason": str, "note": str})
    return pd.DataFrame(columns=FIELDS)


def trades(log: pd.DataFrame) -> pd.DataFrame:
    """One row per entry with its exit; P&L per contract and for the contracts bought.

    shadow_* is the no-trail shadow: the official exit unless the trail fired, else the logged `shadow_exit`
    (missing while that is still pending)."""
    rows = []
    for date, g in log.groupby("date", sort=True):
        e, x, s = g[g.event == "entry"], g[g.event == "exit"], g[g.event == "shadow_exit"]
        if e.empty:
            continue
        e = e.iloc[0]
        n = int(e.contracts)
        row = dict(date=date, side=e.side, contract=e.contract, contracts=n, entry=e.opt_ask,
                   entry_at=e.logged_at_et)
        if not x.empty:
            x = x.iloc[0]
            per = round((x.opt_bid - e.opt_ask) * 100 - FEES, 2)
            row.update(exit=x.opt_bid, exit_at=x.logged_at_et, reason=x.reason, per_contract=per,
                       pnl=round(per * n, 2))
            sh = s.iloc[0] if not s.empty else (x if x.reason != "trail" else None)
            if sh is not None:
                sper = round((sh.opt_bid - e.opt_ask) * 100 - FEES, 2)
                row.update(shadow_exit=sh.opt_bid, shadow_reason=sh.reason, shadow_per_contract=sper,
                           shadow_pnl=round(sper * n, 2))
        rows.append(row)
    return pd.DataFrame(rows)


def contracts_for(balance: float, ask: float) -> int:
    if ask > RISK * balance / 100 + 1e-9:
        sys.exit(f"Ask {ask:.2f} is over the price cap {RISK * balance / 100:.2f}: pick the next strike out.")
    return option_size(BUDGET, ask)


def log(args) -> None:
    lg = read_log()
    today, at = f"{now_et():%Y-%m-%d}", f"{now_et():%Y-%m-%d %H:%M:%S}"
    done = trades(lg)
    row = dict(date=today, logged_at_et=at, event=args.event, side=args.side, contract=args.contract,
               opt_ask=args.ask, opt_bid=args.bid, qqq=args.qqq, reason=args.reason, note=args.note)
    if args.event == "entry":
        if (lg.date == today).any() and (lg[lg.date == today].event == "entry").any():
            sys.exit(f"{today} already has an entry.")
        closed = done[done.pnl.notna()] if "pnl" in done else done
        balance = START + (closed.pnl.sum() if len(closed) else 0.0)
        row["contracts"] = contracts_for(balance, args.ask)
    if args.event == "exit" and not ((lg.date == today) & (lg.event == "entry")).any():
        sys.exit(f"No entry logged for {today}.")
    if args.event == "shadow_exit":
        day = lg[lg.date == today]
        if not ((day.event == "exit") & (day.reason == "trail")).any():
            sys.exit("The shadow only splits off when the official trade trails out: no trail exit today.")
        if (day.event == "shadow_exit").any():
            sys.exit(f"{today} already has a shadow exit.")
        if args.reason == "trail":
            sys.exit("The shadow has no trail: its exits are stop, target or time.")
    lg = pd.concat([lg, pd.DataFrame([row])], ignore_index=True)
    lg.reindex(columns=FIELDS).to_csv(LOG, index=False)
    print(", ".join(f"{k}={v}" for k, v in row.items() if v is not None and not (isinstance(v, float) and math.isnan(v))))
    if args.event == "exit":
        t = trades(lg).iloc[-1]
        print(f"P&L {t.contracts} x {t.contract}: ${t.pnl:+,.2f} (${t.per_contract:+.2f} a contract)")
        if t.reason == "trail":
            print("Trail exit: keep monitoring for the no-trail shadow (stop, target, time) and log shadow_exit.")
    if args.event == "shadow_exit":
        t = trades(lg).iloc[-1]
        print(f"Shadow P&L {t.contracts} x {t.contract}: ${t.shadow_pnl:+,.2f} "
              f"(official ${t.pnl:+,.2f}; difference ${t.shadow_pnl - t.pnl:+,.2f})")


def report(args) -> None:
    t = trades(read_log())
    print("Real-time paper trades (fills at the live ask and bid; paper only, no real orders)")
    if t.empty:
        print("  none yet")
        print(f"  Next trade: the contract's ask at entry must be <= {RISK * START / 100:.2f}; up to ${BUDGET:,.0f}")
        return
    official = [c for c in ("date", "side", "contract", "contracts", "entry", "entry_at", "exit", "exit_at", "reason",
                            "per_contract", "pnl") if c in t]
    print(t[official].fillna("").to_string(index=False))
    closed = t[t.pnl.notna()] if "pnl" in t else t.iloc[0:0]
    n = len(closed)
    total = closed.pnl.sum() if n else 0.0
    print(f"  {n} closed, {int((closed.pnl > 0).sum()) if n else 0} winners; P&L ${total:+,.2f}; "
          f"balance ${START + total:,.2f}; per contract ${closed.per_contract.sum() if n else 0:+.2f}")
    verdict = ("PASSES" if total > 0 else "FAILS") if n >= GO_LIVE_TRADES else f"{n} of {GO_LIVE_TRADES} trades so far"
    print(f"  Go-live bar (total P&L > 0 after {GO_LIVE_TRADES} trades, set 2026-11-09): {verdict}")
    print(f"  Next trade: the contract's ask at entry must be <= {RISK * (START + total) / 100:.2f}; up to ${BUDGET:,.0f}")
    shadow_report(closed)


def shadow_report(closed: pd.DataFrame) -> None:
    print(f"No-trail shadow (pre-registered 2026-11-12; same entries; stop, 2x target, 90-minute time, no trail; "
          f"counts from {SHADOW_FROM}):")
    w = closed[closed.date >= SHADOW_FROM]
    if w.empty:
        print("  no trades in the window yet")
        return
    if "shadow_pnl" not in w:
        w = w.assign(shadow_exit=float("nan"), shadow_reason=None, shadow_pnl=float("nan"))
    cols = ["date", "contract", "reason", "pnl", "shadow_reason", "shadow_exit", "shadow_pnl"]
    print(w[cols].rename(columns={"reason": "official", "pnl": "official_pnl", "shadow_reason": "shadow"})
          .fillna("pending").to_string(index=False))
    done = w[w.shadow_pnl.notna()]
    pending = w[w.shadow_pnl.isna()]
    split = int((done.reason == "trail").sum())
    print(f"  {len(done)} trades: official ${done.pnl.sum():+,.2f}, shadow ${done.shadow_pnl.sum():+,.2f} "
          f"(they differ only on the {split} trail-exit day{'s' if split != 1 else ''})"
          + (f"; pending shadow exits: {', '.join(pending.date)}" if len(pending) else ""))


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    w = sub.add_parser("wait-signal")
    w.add_argument("--minutes", type=float, default=110)
    s = sub.add_parser("watch")
    s.add_argument("--side", required=True, choices=["long", "short"])
    s.add_argument("--stop", required=True, type=float)
    s.add_argument("--since", help="HH:MM ET, the entry time")
    s.add_argument("--seconds", type=float, default=120)
    lg = sub.add_parser("log")
    lg.add_argument("event", choices=["entry", "exit", "shadow_exit", "no_signal", "missed"])
    lg.add_argument("--side", choices=["long", "short"])
    lg.add_argument("--contract")
    lg.add_argument("--ask", type=float)
    lg.add_argument("--bid", type=float)
    lg.add_argument("--qqq", type=float)
    lg.add_argument("--reason", choices=["stop", "target", "trail", "time"])
    lg.add_argument("--note", default="")
    sub.add_parser("report")
    args = p.parse_args(argv)
    {"wait-signal": wait_signal, "watch": watch, "log": log, "report": report}[args.cmd](args)


if __name__ == "__main__":
    main()
