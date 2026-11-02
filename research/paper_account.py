"""A $10,000 paper account that trades the playbook's QQQ ORB signals with options only, sized from the balance.

On 2026-10-30 the user asked: "Say you had $10,000. Trade based on that amount." On 2026-11-02 they added:
"Only do options." The real account holds about $55 and live trading is paused, so this is paper only. The
signals are the ones paper_orb.py logs in paper_trades.csv. QQQ's chart still decides the direction, the entry
time and the stop. This file picks the size of each options trade and keeps the running balance.

The rules, fixed before the first trade on 2026-11-02:
  - Monday to Thursday signals only (the playbook skips Fridays). A cash account, so there's no day-trade limit.
  - Up to 1% of the balance goes into premium, which is also the most a trade can lose. At $10,000 that's $100,
    so the contract is the nearest-to-the-money next-day call (long) or put (short) whose 5-minute open at entry
    is <= $0.99, bought as many times as the budget allows.
  - Entry at that bar's open + $0.01, $0.09 fees per contract. Exits are the playbook's: the QQQ share stop (the
    other side of the opening range), +100% target, the trail (arm at +50%, sell at +30%) or 90 minutes.

  python3 -I research/paper_account.py report
  python3 -I research/paper_account.py option 2026-11-02 --option-bars FILE --contract "11/3 707C" [--bars FILE]
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from paper_orb import DEFAULT_BARS, FEES, LOG as ORB_LOG, load_bars, option_trade  # noqa: E402

OPT_LOG = HERE / "paper_account_options.csv"
OPT_FIELDS = ["date", "side", "contract", "contracts", "opt_entry", "opt_exit", "opt_reason", "pnl", "balance"]
START = 10_000.0
RISK = 0.01


def tradable(date: str) -> bool:
    """The playbook trades Monday to Thursday."""
    return pd.Timestamp(date).dayofweek < 4


def option_size(budget: float, entry: float) -> int:
    return max(0, math.floor(budget / round(entry * 100, 6) + 1e-9))


def read_book() -> pd.DataFrame:
    if OPT_LOG.exists():
        return pd.read_csv(OPT_LOG, dtype={"date": str, "contract": str})
    return pd.DataFrame(columns=OPT_FIELDS)


def option(args) -> None:
    if not tradable(args.date):
        sys.exit(f"{args.date} is a Friday; the playbook skips Fridays.")
    orb = pd.read_csv(ORB_LOG, dtype={"date": str})
    hit = orb[orb.date == args.date]
    if hit.empty or hit.side.iat[0] not in ("long", "short"):
        sys.exit(f"No ORB signal logged for {args.date}; score the day with paper_orb.py first.")
    r = hit.iloc[0]
    book = read_book()
    book = book[book.date != args.date]
    budget = RISK * (START + book[book.date < args.date].pnl.sum())
    bars = load_bars(Path(args.bars))
    day = bars[bars.index.date == pd.Timestamp(args.date).date()].between_time("09:30", "15:55")
    side = 1 if r.side == "long" else -1
    t0 = pd.Timestamp(f"{args.date} {r.entry_time}", tz="America/New_York")
    res = option_trade(load_bars(Path(args.option_bars)), t0, und=day, side=side,
                       und_stop=r.or_low if side == 1 else r.or_high)
    if "opt_exit" not in res:
        sys.exit(f"Can't score {args.contract}: {res.get('opt_reason', 'no option bars at the entry time')}.")
    n = option_size(budget, res["opt_entry"])
    if n < 1:
        sys.exit(f"{args.contract} costs {res['opt_entry']:.2f} at entry, over the ${budget:.0f} budget: "
                 f"pick a contract whose 5-minute open is <= {budget / 100 - 0.01:.2f}.")
    pnl = round(n * ((res["opt_exit"] - res["opt_entry"]) * 100 - FEES), 2)
    row = dict(date=args.date, side=r.side, contract=args.contract, contracts=n, **res, pnl=pnl)
    book = pd.concat([book, pd.DataFrame([row])], ignore_index=True).sort_values("date")
    book["balance"] = (START + book.pnl.astype(float).cumsum()).round(2)
    book.reindex(columns=OPT_FIELDS).to_csv(OPT_LOG, index=False)
    print(f"{args.date} {r.side} {n} x {args.contract}: in {res['opt_entry']:.2f}, out {res['opt_exit']:.2f} "
          f"({res['opt_reason']}), P&L ${pnl:+,.2f}, balance ${book.balance.iat[-1]:,.2f}")


def report(args) -> None:
    book = read_book()
    print("$10,000 paper account, options only (Monday-Thursday ORB signals; paper, no real orders)")
    if book.empty:
        print("  no trades yet")
    else:
        print(book.to_string(index=False))
        print(f"  {len(book)} trades, {int((book.pnl > 0).sum())} winners; P&L ${book.pnl.sum():+,.2f}; "
              f"balance ${START + book.pnl.sum():,.2f}")
    budget = RISK * (START + book.pnl.sum())
    print(f"  Next budget: ${budget:,.0f}, so the contract's 5-minute open at entry must be <= {budget / 100 - 0.01:.2f}")


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("report")
    o = sub.add_parser("option")
    o.add_argument("date")
    o.add_argument("--option-bars", required=True)
    o.add_argument("--contract", required=True)
    o.add_argument("--bars", default=str(DEFAULT_BARS))
    args = p.parse_args(argv)
    {"report": report, "option": option}[args.cmd](args)


if __name__ == "__main__":
    main()
