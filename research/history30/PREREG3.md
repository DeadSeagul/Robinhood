# Part 3: which strategy has the best edge on QQQ? Fixed before running

Written 2026-11-19, before any of these strategies was run on this data. The user asked: "so can you run different
strategies on the QQQ for the last 20 years and see which one has the best edge?"

The user's standing rules apply:
- "Do not optimize hundreds of parameter combinations and present only the best result. Document every test."
- "Use only information available at the time of each simulated decision."
- "These are screening thresholds, not proof of future profitability."

So the list is fixed here, each strategy uses its standard textbook settings with no tuning, and every result is
reported. Everything is traded as QQQ shares. The options question is separate, and nothing changes the paper rules.

## Data

- **Daily strategies:** QQQ daily open/high/low/close and dividends, from Yahoo Finance. Trading runs
  2006-11-20 → 2026-11-18 (20 years); earlier days are used only to warm up the averages. Dividends are added on their ex-date.
- **Intraday strategies:** QQQ 5-minute SIP bars from Alpaca, 2016-01-04 → 2026-11-18, regular hours. This is all the
  minute history the free data has, so intraday strategies get about 11 years, not 20.

## Trading rules shared by all

- **Daily:** a signal uses closes up to day t−1 and is acted on at the **open of day t**. That's stricter than buying at
  the same close the signal was computed on, which uses a price you don't yet know. Exposure is tracked separately
  for the night and the trading day, so a position held overnight earns the overnight move, dividend included.
- **Costs:** 0.02% (2 basis points) per side on every buy and sell, for both daily and intraday trades, covering the spread and slippage.
  Results are shown before and after costs.
- **No leverage:** 100% of capital per position, long or short.

## The strategies

| # | Name | Rule |
|---|---|---|
| D0 | Buy and hold | Benchmark, not a test. |
| D1 | 200-day trend filter | Hold when the close is above its 200-day average; otherwise cash. |
| D2 | Golden cross | Hold when the 50-day average is above the 200-day average. |
| D3 | 20-day breakout | Buy when the close beats the prior 20 closes' high; sell when it falls below the prior 10 closes' low. |
| D4 | RSI(2) pullback (Connors) | Buy when 2-day RSI < 10 and the close is above the 200-day average; sell when the close is above its 5-day average. |
| D5 | Bollinger reversion | Buy when the close is below the 20-day average minus 2 standard deviations; sell when it closes above the 20-day average. |
| D6 | IBS | Buy when (close − low) / (high − low) < 0.2; hold one day. |
| D7 | Turn of the month | Hold from the open of the month's last trading day to the close of the next month's 3rd trading day. |
| D8 | Overnight only | Buy every close, sell the next open. |
| D9 | Daytime only | Buy every open, sell the same close. |
| I1 | Our 5-min ORB | `paper_orb.signal` + `share_trade`: first close beyond the 9:30 bar's range by 11:25, entry next bar, stop at the other side, 2R target, 90-minute exit. Monday–Friday. |
| I2 | First-candle ORB to the close (Zarattini & Aziz 2023) | Trade the direction of the 9:30 candle (none if open = close), entry at the 9:35 open, stop at that candle's low/high, target 10R, else exit at 4:00. Rules as stated in the paper. |
| I3 | Intraday momentum (Gao, Han, Li & Zhou 2018) | The return from the prior close to 10:00 sets the side. Enter at 3:30pm, exit at 4:00. |
| I4 | Gap fade | If the open gaps ≥ 0.5% from the prior close, trade against it at the open. Exit at the prior close if reached, else at 4:00. |
| I5 | Prior-day high/low sweep reversal (a mechanical take on the TJR/ICT idea) | 9:35–10:55: a 5-minute bar trades above the prior day's high and closes back below it → short at the next open, stop at that bar's high, target 2R, exit by noon (mirror for lows). First signal of the day only. |

In every intraday rule, a bar that touches both the stop and the target counts as the stop.

## Measures

- **Daily strategies:**
  - Growth per year, worst drawdown, Sharpe ratio, share of time in the market and number of trades.
  - **Edge:** the alpha against buy-and-hold, from a daily regression of the strategy's returns on QQQ's, annualized, with its t. That is the return the timing adds beyond simply being in QQQ part of the time.
- **Intraday strategies:** trades, win rate, mean return per trade after costs, its t, the sum of returns and the growth per year compounding each trade at 1x.
- **Halves:**
  - daily: 2006-11 → 2016-11 and 2016-11 → 2026-11;
  - intraday: 2016-01 → 2021-06 and 2021-07 → 2026-11.

## How "best edge" is decided

- **Bar for a real edge:** 14 tests are run (D1–D9, I1–I5). By luck alone, one of 14 could reach |t| = 2.
  - So a result counts as a real edge only if its t (alpha t for daily strategies, per-trade t for intraday ones) is **≥ 3.0 after costs**. That's the 5% level corrected for 14 tests.
  - It must also be positive in **both halves**.
- **The ranking:** all 14 are ranked by that t, and the top one is "best". Whether or not it clears the bar is reported as is.
- **If none passes:** the answer is that none showed an edge that beats luck. Nothing is re-run with other settings to find one.
