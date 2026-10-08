"""Command line.

  python -m daytrader backtest --data yahoo --cache data_cache --out reports
  python -m daytrader backtest --data csv --csv-dir flatfiles --out reports
  python -m daytrader backtest --data alpaca --start 2024-01-02 --end 2026-09-30   # needs APCA_* keys
  python -m daytrader paper --broker local  --data alpaca           # local simulated fills on live IEX bars
  python -m daytrader paper --broker alpaca --data alpaca           # Alpaca PAPER account
  touch KILL_SWITCH                                                 # flatten everything and stop
"""
from __future__ import annotations

import argparse
import sys
from datetime import date

from .config import AppConfig, env_mode
from .universe import DEFAULT_UNIVERSE


def provider_from(args):
    if args.data == "yahoo":
        from .data.yahoo import YahooProvider
        return YahooProvider(cache_dir=args.cache)
    if args.data == "csv":
        from .data.csvfile import CSVProvider
        return CSVProvider(args.csv_dir)
    from .data.alpaca import AlpacaDataProvider
    return AlpacaDataProvider(feed="sip" if args.cmd == "backtest" else "iex")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="daytrader")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("backtest", "paper"):
        s = sub.add_parser(name)
        s.add_argument("--data", choices=["yahoo", "alpaca", "csv"], default="yahoo")
        s.add_argument("--cache", default="data_cache")
        s.add_argument("--csv-dir", default="flatfiles")
        s.add_argument("--symbols", nargs="*", default=DEFAULT_UNIVERSE)
    sub.choices["backtest"].add_argument("--out", default="reports")
    sub.choices["backtest"].add_argument("--start", type=date.fromisoformat, default=None,
                                         help="first date (alpaca/csv); yahoo always serves the last ~60 days")
    sub.choices["backtest"].add_argument("--end", type=date.fromisoformat, default=None)
    sub.choices["paper"].add_argument("--broker", choices=["local", "alpaca"], default="local")
    sub.choices["paper"].add_argument("--journal", default="journal")
    args = p.parse_args(argv)

    if args.cmd == "backtest":
        from .research import run_all
        print(run_all(provider_from(args), args.symbols, args.out, start=args.start, end=args.end))
        return 0

    mode = env_mode()  # raises unless TRADING_MODE is unset or "paper"
    cfg = AppConfig(mode=mode)
    from .live import PaperTrader
    if args.broker == "alpaca":
        from .broker.alpaca_paper import AlpacaPaperBroker
        broker = AlpacaPaperBroker()
    else:
        from .broker.sim import SimBroker
        broker = SimBroker(cfg.risk.starting_equity, cfg.costs)
    prov = provider_from(args)
    news = prov if hasattr(prov, "news") else None
    report = PaperTrader(cfg, prov, broker, args.symbols, news).run_day(args.journal)
    print(report.text())
    return 0


if __name__ == "__main__":
    sys.exit(main())
