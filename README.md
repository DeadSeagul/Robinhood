# Robinhood: day-trading research & paper-trading system

A modular Python system that scans, backtests and paper-trades an opening-range-breakout strategy. It reports honestly whether the strategy has an edge after costs. **Paper mode only; there is no live-order code.**

- Design, research, API choices and first results: [`docs/SYSTEM_DESIGN.md`](docs/SYSTEM_DESIGN.md)
- Latest backtest report: [`reports/backtest_report.md`](reports/backtest_report.md); open `reports/dashboard.html` in a browser for the interactive version
- Earlier exploratory research (SPY/QQQ ORB, options simulations, tested "guru" rules): [`research/PLAYBOOK.md`](research/PLAYBOOK.md)

**Current verdict:** no tested variant passes the validation screen (≥100 trades, PF ≥ 1.2, t ≥ 2, DD < 5%). **Do not trade it live.**

## Quick start

```bash
pip install pandas numpy requests pytest
python -m pytest -q
python -m daytrader backtest --data yahoo --cache data_cache --out reports
```

With a free Alpaca paper account (keys in the environment, never in code):

```bash
export APCA_API_KEY_ID=...  APCA_API_SECRET_KEY=...
python -m daytrader backtest --data alpaca --start 2021-01-04 --end 2026-09-30 --out reports
python -m daytrader paper --data alpaca --broker alpaca      # one trading day, paper account
touch KILL_SWITCH                                            # flatten everything and stop
```

## Layout

```
daytrader/        the application (config, data, indicators, scanner, strategy, risk, engine,
                  broker/, backtest, live paper trader, analytics, dashboard, journal)
tests/            22 tests: indicators, sizing, state machine, fill model, no-look-ahead,
                  mode guards, Alpaca adapter, paper-trader replay, kill switch, reconnects
reports/          output of the latest backtest run
research/         exploratory scripts and the options playbook from earlier sessions
docs/             system design and test log
```
