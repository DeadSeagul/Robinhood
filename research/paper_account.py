"""A $10,000 paper account that trades the playbook's QQQ ORB signals, sized from the account balance.

On 2026-10-30 the user asked: "Say you had $10,000. Trade based on that amount." The real account holds about
$55 and live trading is paused, so this is paper only. The signals are the ones paper_orb.py logs in
paper_trades.csv. This file decides how big each trade is and keeps the running balance.

Two books, each starting at $10,000, trade the same Monday-Thursday signals (the playbook skips Fridays):

  shares   QQQ shares, long or short. Shorting needs a margin account, and a margin account under $25,000 is a
           pattern-day-trader account: at most 3 day trades in any 5 business days, so a 4th signal is skipped.
           Size: risk 1% of the balance between entry and the stop (the other side of the opening range),
           capped at 2x the balance in buying power. $0.01 a share of slippage each way, no commission.
  options  The playbook's next-day call or put, bought in a cash account (no day-trade limit). Up to 1% of the
           balance goes into premium, which is also the most the trade can lose. At $10,000 that's $100, so the
           contract is the nearest-to-the-money one whose 5-minute open at entry is <= $0.99, bought as many
           times as the budget allows. Exits are the playbook's: QQQ share stop, +100% target, trail, 90 minutes.

These rules were fixed before the shares book was replayed on the signals already logged. The options book can't
be replayed, because every past day would need a different contract than the $0.20 one that was scored. Both
books count forward from 2026-11-02.

  python3 -I research/paper_account.py report [--since 2026-11-02]
  python3 -I research/paper_account.py option 2026-11-02 --option-bars FILE --contract "11/3 712C" [--bars FILE]
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
MARGIN = 2.0
SLIP = 0.01
PDT_TRADES, PDT_DAYS = 3, 5
FORWARD = "2026-11-02"


def tradable(date: str) -> bool:
    """The playbook trades Monday to Thursday."""
    return pd.Timestamp(date).dayofweek < 4


def share_size(balance: float, entry: float, stop: float) -> int:
    by_risk = math.floor(RISK * balance / abs(entry - stop) + 1e-9)
    by_cash = math.floor(MARGIN * balance / entry + 1e-9)
    return max(0, min(by_risk, by_cash))


def option_size(budget: float, entry: float) -> int:
    return max(0, math.floor(budget / round(entry * 100, 6) + 1e-9))


def shares_book(orb: pd.DataFrame, since: str) -> pd.DataFrame:
    rows, balance, taken = [], START, []
    for r in orb.sort_values("date").itertuples():
        if r.date < since or not tradable(r.date) or r.side not in ("long", "short") or pd.isna(r.share_exit):
            continue
        window = pd.bdate_range(end=pd.Timestamp(r.date), periods=PDT_DAYS)
        if sum(pd.Timestamp(t) in window for t in taken) >= PDT_TRADES:
            rows.append(dict(date=r.date, side=r.side, shares=0, pnl=0.0, balance=balance,
                             note="skipped: would be a 4th day trade in 5 days (PDT)"))
            continue
        sign = 1 if r.side == "long" else -1
        n = share_size(balance, r.share_entry, r.or_low if sign == 1 else r.or_high)
        pnl = round(n * (sign * (r.share_exit - r.share_entry) - 2 * SLIP), 2)
        balance = round(balance + pnl, 2)
        taken.append(r.date)
        rows.append(dict(date=r.date, side=r.side, shares=n, entry=r.share_entry, exit=r.share_exit,
                         reason=r.share_reason, r=r.share_r, pnl=pnl, balance=balance, note=""))
    return pd.DataFrame(rows)


def read_options() -> pd.DataFrame:
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
    book = read_options()
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
          f"({res['opt_reason']}), P&L ${pnl:+,.2f}, options balance ${book.balance.iat[-1]:,.2f}")


def report(args) -> None:
    orb = pd.read_csv(ORB_LOG, dtype={"date": str})
    print(f"$10,000 paper account, signals from {args.since} (Monday-Thursday only; paper, no real orders)")
    sh = shares_book(orb, args.since)
    print("\nShares book (margin account, 1% risk to the stop, 2x buying power, 3 day trades per 5 days):")
    if sh.empty:
        print("  no trades yet")
    else:
        print(sh.fillna("").to_string(index=False))
        t = sh[sh.shares > 0]
        print(f"  {len(t)} trades, {int((t.pnl > 0).sum())} winners, {int((sh.shares == 0).sum())} skipped for the "
              f"day-trade limit; P&L ${t.pnl.sum():+,.2f}; balance ${sh.balance.iat[-1]:,.2f}")
    book = read_options()
    book = book[book.date >= args.since]
    print("\nOptions book (cash account, up to 1% of the balance in premium):")
    if book.empty:
        print("  no trades yet")
    else:
        print(book.to_string(index=False))
        print(f"  {len(book)} trades, {int((book.pnl > 0).sum())} winners; P&L ${book.pnl.sum():+,.2f}; "
              f"balance ${START + book.pnl.sum():,.2f}")
    budget = RISK * (START + read_options().pnl.sum())
    print(f"  Next options budget: ${budget:,.0f}, so the contract's 5-minute open at entry must be "
          f"<= {budget / 100 - 0.01:.2f}")


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("report")
    r.add_argument("--since", default=FORWARD)
    o = sub.add_parser("option")
    o.add_argument("date")
    o.add_argument("--option-bars", required=True)
    o.add_argument("--contract", required=True)
    o.add_argument("--bars", default=str(DEFAULT_BARS))
    args = p.parse_args(argv)
    {"report": report, "option": option}[args.cmd](args)


if __name__ == "__main__":
    main()
