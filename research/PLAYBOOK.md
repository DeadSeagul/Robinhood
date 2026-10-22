# Options Day-Trading Playbook

> **Status (2026-10-15): live trading is paused at the user's request. Paper trades only.** No real orders are placed. Every trading day the 5-minute ORB signal is scored after the close of its 90-minute window by [`paper_orb.py`](paper_orb.py), on QQQ shares and on the playbook option contract, and logged in [`paper_trades.csv`](paper_trades.csv). Practice drills continue in [`REPLAY.md`](REPLAY.md). Real-money trading resumes only if the user asks.

Account: Robinhood **Agentic** (••••2243), $54.62 as of 2026-10-15 (started at $100).
Instruments: QQQ options first (plus liquid stocks in play). Sizing: **max $20 premium per trade** (user sized down on 2026-10-08; was the full account).

## What the research says

### Outside evidence
- **Most day traders lose.** Taiwan full-market study: 82% of day traders lost money; under 1% were predictably profitable after costs. ([Barber, Lee, Liu, Odean](https://www.truewealth.ch/en/blog/day-trading-how-many-traders-lose-money))
- **Retail 0DTE buyers lose on average.** Retail long 0DTE positions lost ~53–61% of their value on average; ~60% of the losses were transaction costs. Option *buyers* pay the variance risk premium. ([Neudata review](https://neudata.co/literature-reviews/zero-day-to-expiry-options-a-losing-bet-for-retail-traders), [WealthManagement](https://www.wealthmanagement.com/equities/retail-investors-are-in-love-with-same-day-options))
- **Opening range breakout (ORB) has a small edge on the underlying.** A 5-minute ORB on QQQ had a 24% hit rate and +0.13R per trade; the edge is much stronger on "stocks in play" (unusual volume + news). ([Zarattini & Aziz](https://concretumgroup.com/a-profitable-day-trading-strategy-for-the-u-s-equity-market/), [CXO summary](https://www.cxoadvisory.com/technical-trading/day-trading-with-an-opening-range-breakout-strategy)). An independent replication found gross edge but ~zero net of costs. ([replication](https://www.mql5.com/en/blogs/post/776235))
- **Intraday momentum.** The first half-hour's SPY return predicts the last half-hour's (weak but persistent, stronger on volatile/high-volume/news days). ([Gao, Han, Li, Zhou via Alpha Architect](https://alphaarchitect.com/2014/08/attention-prop-traders-the-first-half-hour-of-trading-predicts-the-last-half-hour/)). A "noise area" breakout with a VWAP trailing stop on SPY returned ~19.6%/yr 2007–2024. ([Zarattini, Aziz, Barbon](https://concretumgroup.com/beat-the-market-an-effective-intraday-momentum-strategy-for-sp500-etf-spy/))
- **Levels.** Day traders mark prior-day high/low/close, pre-market high/low, pivot points (P = (H+L+C)/3, R1 = 2P−L, S1 = 2P−H), VWAP and round numbers.

### Our own backtest (`backtest.py`, `options_sim.py`)
60 sessions of 5-minute bars, 2026-07-15 → 2026-10-06. **Small sample: treat as a sanity check, not proof.**

**When SPY moves.** Average absolute 30-minute move:

| Slot (ET) | 9:30 | 10:00 | 11:00 | 12:30 | 13:30 | 14:00 | 15:30 |
|---|---|---|---|---|---|---|---|
| SPY | $1.26 | $1.09 | $0.89 | $0.58 | $0.49 | $0.52 | $0.75 |
| QQQ | $2.51 | $1.69 | $1.25 | $0.82 | $0.72 | $0.66 | $1.05 |

Moves are 2–3x bigger in the first hour than at 1:30–2:30pm. That's why today's 2:07pm call bled out.

**ORB on the underlying** (first close beyond the range, stop at the other side, 90-minute window):

| | 5-min ORB | 15-min ORB | 30-min ORB |
|---|---|---|---|
| SPY: reached +$0.50 / +$1.00 | 78% / 61% | 78% / 59% | 75% / 60% |
| SPY: avg P/L per share | **+$0.28** | +$0.11 | +$0.02 |
| QQQ: avg P/L per share | **+$0.33** | −$0.16 | −$0.42 |

The 5-minute ORB was the best variant. Longer opening ranges were worse.

**ORB traded with ≤$0.20 options** (Black-Scholes, flat IV, 1¢ spread, ~8¢ fees per round trip):

| Variant | Win rate | Avg $/contract | Total over 59 trades |
|---|---|---|---|
| SPY 0DTE, TP +100% / SL −50% | 31% | −$1.26 | −$74 |
| SPY 1DTE, TP +100% / SL −35% | 31% | −$1.27 | −$75 |
| QQQ 0DTE, TP +100% / SL −35% | 37% | +$0.18 | +$11 |
| **QQQ 1DTE, TP +100% / SL −35%** | 37% | **+$0.84** | **+$50** |
| QQQ 1DTE, TP +100% / SL −50% | 41% | +$0.62 | +$36 |

- Filters I tried (trade only in the direction vs prior close; only narrow opening ranges) made results **worse**.
- **By weekday** (re-run 2026-10-09 on 2026-07-17 → 2026-10-08, QQQ, TP +100% / SL −35%; 11–12 trades per weekday, so every cell is noise):

  | | Mon | Tue | Wed | Thu | Fri | Total |
  |---|---|---|---|---|---|---|
  | 0DTE, total $ | +25 | −19 | −3 | −7 | −5 | **−10** |
  | 1DTE, total $ | +28 | −22 | +20 | 0 | +2 | **+29** |

  Fridays weren't worse than other days. The clearer pattern is that same-day contracts did worse than next-day ones overall. The model also understates Friday's problem: Friday's next expiry is Monday, and the weekend makes those contracts more expensive. Under a $20 cap that pushes the strike far out of the money. On 2026-10-09 the Monday puts under $0.20 were $19 out of the money and traded fewer than 1,000 contracts, so they failed the volume filter.
- The "noise area" momentum rule **lost money** in this window (30% win rate on SPY and QQQ).
- Prior-day levels: on the first touch, prior-day **lows broke ~80% of the time**. Prior-day highs and closes held about 40% of the time.

**Bottom line:** cheap SPY options on these rules lost money. QQQ, especially 1-day expiries, was roughly breakeven to slightly positive. That's within noise, so **there is no proven edge here**. Expect to lose a bit on average, and keep risk small.

## Full-account sizing check
I re-ran the simulation with one trade using about $90 of premium, and allowed contracts closer to the money (ask ≤ $0.90).
- **QQQ, ask ≤ $0.90:** 39–42% win rate, about +7–8% average return per trade. Next-day (1DTE) contracts never pulled the account below ~$79 in this sample.
- **SPY** still lost money at every price cap.
- **Worst single trade was about −$43 to −$45**, even with a −35% stop, because prices are only checked every 5 minutes and can jump past the stop.
- **Small sample and a flat-volatility model.** Real results will likely be worse. Two or three bad trades in a row could cut the account in half.

## Popular "guru" rules, tested (`folklore_tests.py`)
On 2026-10-08 the user shared a Reddit list of day-trading strategies. I tested the ones that can be checked with price data, on the same 60 sessions. All values are $/share; |t| < 2 means indistinguishable from noise.

| Rule | SPY | QQQ | Verdict |
|---|---|---|---|
| ORB only **with** the 1H 100-EMA trend | −$0.04 (n=28) | +$0.02 (n=20) | No help. On SPY, trades *against* the trend did better (+$0.53, n=16, t=1.6), the opposite of the claim, and still noise |
| "9:45 reversal": fade the first 15 minutes | −$0.31 | −$0.02 | No edge, slightly negative |
| "First hour trend lock" until the close | +$0.13 | $0.00 | No edge |
| Stop-hunt reversal at prior-day high/low | −$0.23 (n=19) | −$0.46 (n=14) | Fading failed breaks lost money. The breaks kept going more often than not |
| "Broken parabolic" short after 4+ green 5-min bars | +$0.01 | −$0.19 | No edge |

The rest can't be tested with our data:
- **Needs order-book or tape data we don't have:** Level 2 bids, dark-pool prints, "market maker refill zones."
- **Wrong or made up:**
  - "80% of earnings moves fade": research finds the opposite, post-earnings drift.
  - "Merger arb above the deal price is a free short": a price above the offer usually means the market expects a higher bid.
  - "Options chain spoofing": spoofing is illegal market manipulation, not a signal.
- **Real but not tradable on demand:** max-pain pinning near expiry is real but small; gamma squeezes can't be predicted.

**Conclusion:** none of these beat the plain 5-min ORB. No changes to the rules.

## Trading rules (autonomous mode; paused since 2026-10-15, kept for paper scoring)
On 2026-10-07 the user authorized Claude to **place options orders without per-trade approval**. On 2026-10-08 the user **sized down to $20 per trade** (1 contract, ask ≤ $0.20; a −35% stop costs about $7). These are the limits:

1. **Underlying: QQQ only. Monday–Thursday only; no trading on Fridays** (user decision, 2026-10-09).
   - **Next-day (1DTE) contracts only. No same-day (0DTE) contracts.** If no next-day contract passes the filters below, there is no trade that day.
2. **Contract:**
   - the nearest-to-the-money strike with ask ≤ $0.20 (1 contract ≤ $20)
   - bid/ask spread ≤ $0.03
   - option volume > 1,000 today
3. **Setup: 5-minute ORB.**
   - Opening range = 9:30–9:35 high/low.
   - Signal = first 5-minute close above the high (buy a call) or below the low (buy a put).
   - The signal must come by **11:30am ET**.
   - Skip if the opening bar is more than ~2× its usual size, or a major scheduled release (CPI, FOMC, jobs report) is due within 30 minutes.
4. **Entry:** limit at the ask. If not filled within ~2 minutes, re-price once; otherwise skip.
5. **Exits:**
   - **Target:** sell at +100%.
   - **Trail:** once up +50%, sell if it falls back to +30%.
   - **Stop:** sell at −35%.
   - **Time stop:** sell 90 minutes after entry, and by 3:30pm ET at the latest.
   - Never hold overnight.
6. **Limits:**
   - One position at a time.
   - Max 2 entries per day.
   - **Stop for the day after the first losing trade.**
   - If the account falls below **$50**, stop trading on my own and ask the user.
7. **No entries after 11:30am ET.**
8. **Reporting:** report every entry and exit to the user (chat + push notification) with the fill price and P/L.

## Daily levels checklist (before 9:40am ET)
- Prior day high / low / close and pivot P, R1, S1
- Pre-market high/low if available; gap vs prior close
- VWAP as the day goes; round numbers ($5/$10 increments on SPY/QQQ)
- Economic calendar and big-cap earnings that day

## Pre-market news read (from 2026-10-23)

On 2026-10-22 the user asked me to read the news each morning, since it shows how the market may act that day. The schedule:

| When | What happens |
|---|---|
| 8:50am ET, weekdays | I read the overnight and pre-market news: futures and why they're moving, the economic calendar, Fed speakers, oil and yields, and earnings from the biggest QQQ holdings. |
| Before 9:30 | I log a call in [`news_log.py`](news_log.py): a **bias** (up, down or none) for QQQ from the 9:30 open to 12:00, and **vol** (normal or high). The log is committed before the open. |
| 1:17pm | The daily task scores the call. |

How the news read is kept honest:
- **The gap doesn't count.** Futures already show it, so the bias is about where QQQ goes after the open.
- **Late reads are excluded.** A read logged at or after 9:30 ET is marked late and never scored.
- **No forced calls.** "None" is allowed when the news doesn't clearly point one way.
- **The ORB rules don't change because of the news.** Instead, `news_log.py stats` splits ORB results into signals that agree with the news bias, signals against it, and days with no bias. If agreeing signals beat disagreeing ones over a real sample (20+ calls, and better than a coin flip), the bias becomes a filter.
- **Dates get checked.** Search tools can mislabel them. On 10/22, a summary put that day's selloff on 10/21. The read checks headline claims against prices.
- **The news isn't used in the blind practice drills.** Past headlines give away how the day went.

## Trade log
| Date | Trade | Entry | Exit | P/L | Note |
|---|---|---|---|---|---|
| 2026-10-07 | SPY shares (fractional, $95) | $777.62 | $777.45 | −$0.02 | Midday test trade |
| 2026-10-07 | SPY 10/7 $779 call ×1 | $0.17 | $0.09 | −$8.00 (+fees) | 2:07pm entry after Fed minutes; no follow-through, time decay |
| 2026-10-08 | QQQ 10/9 $745 put ×1 (5-min ORB short, autonomous) | $0.69 | $0.45 | −$24.00 (+fees) | 9:50 bar closed $752.42 below OR low $753.11; QQQ snapped back into the range within 3 min (failed breakdown) and broke the OR high by 10:21. Broker-side stop filled 10:19. Lesson: a signal that is already back inside the range at entry time is a warning sign. |
| 2026-10-09 | QQQ 10/9 $740 put ×1 (5-min ORB short, autonomous, $20 size) | $0.20 | $0.13 | −$7.00 (−$7.09 with fees) | OR 751.31–752.86 (narrow, $1.55). 9:40 bar closed $749.38 below the OR low; still below at entry. The 10/12 puts ≤ $0.20 traded < 1,000 contracts, so I used the 0DTE $740 put (delta −0.07). First order at $0.19 didn't fill; re-priced once to $0.20. QQQ never got back inside the range, but it went sideways ($748.6–749.7). The put lost 35% in 14 minutes from time decay and falling implied volatility alone, and the broker stop filled at 9:59. Lesson below. |

| 2026-10-12 | **No trade** (Mon). Put signal skipped by the volume filter | – | – | $0 | OR 747.10–749.79. 10:05 bar closed $745.74 below the OR low. The next-day (10/13) puts ≤ $0.20 were the $731 put ($0.19, 1¢ spread, 253 volume) and the $730 put ($0.16, 301 volume): none had > 1,000 volume, so no trade. **Shadow trade** (not placed): the $731 put bought at $0.19 at 10:10 never traded above $0.19, slid to $0.13 by 10:25 and hit the $0.12 stop around 10:40, so about −$7. QQQ stalled at $745.2–747 after the break, the same pattern as 10/9. The volume filter saved ~$7 today. |
| 2026-10-13 | **No trade** (Tue). Call signal skipped by the volume filter | – | – | $0 | Gap down −0.85% (open 739.53). OR 738.84–740.58; 9:35 bar closed $742.84 above the OR high. The next-day (10/14) calls ≤ $0.20 were the $757 ($0.20, 202 volume), $758 ($0.16, 106) and $760 ($0.10, 246), so no trade. **Shadow trade:** the $757 call bought at $0.20 peaked at $0.24 and hit the $0.13 stop at ~10:15, so about −$7. QQQ topped at $744.20 and drifted back to $741. That's the third ORB signal in a row that stalled right after the break (10/9, 10/12, 10/13). The volume filter has saved ~$14 over two days. |
| 2026-10-14 | **No trade** (Wed). Call signal skipped by the volume filter | – | – | $0 | Gap down −0.7%. OR 736.90–739.03; 9:45 bar closed $740.18 above the OR high. The next-day (10/15) calls ≤ $0.20 were the $754 ($0.20, 164 volume) and $755 ($0.17, 335), so no trade. **Shadow trade:** the $754 call bought at $0.20 at 9:50 fell through the $0.13 stop by 9:55 (the bar low was $0.11), so about −$7 to −$9. QQQ reversed from $740.19 to $735.90 within 10 minutes, back through the OR low, and drifted to $734 by 11:20. |

| 2026-10-15 | QQQ 10/16 $740 call ×1 (5-min ORB long, autonomous, first trade under the next-day-only rule) | $0.17 | $0.11 | −$6.00 (−$6.09 with fees) | Fourth straight down day (−2.0% on 10/14, −1.2% gap down). OR 717.01–719.42 (normal size). 9:35 bar closed $720.47 above the OR high; QQQ $720.10 at entry. The $740 call was the nearest strike ≤ $0.20 with > 1,000 volume ($0.18 ask, 3,445 volume; the $739 was $0.21). QQQ topped near $720.9, fell back inside the range by 9:47 and the broker stop filled at 9:49:55. Stop for the day after the first loss. |

**Live ORB scorecard, 2026-10-08 → 10-15: 6 signals, 6 failed or stalled** (10/8 put, 10/9 put, 10/12 put, 10/13 call, 10/14 call, 10/15 call). Three were real trades (−$37 total) and three were shadow trades (≈ −$21 avoided). Six is still a small sample, but every live signal so far has reversed or stalled within 15 minutes. The account ($54.62) is now one stopped trade away from the $50 floor.

**First paper result, 2026-10-16 (Friday; scored for the record only, since the playbook skips Fridays).** The short signal at 9:40 was right: QQQ fell from 722.43 to 717.75 by the 90-minute time stop, +1.33R on shares, and never got near the share stop at 725.94. The ≤ $0.20 option still lost. The Monday 695 put ($0.17) hit its −35% stop at 10:45, when QQQ bounced to 723.6. The 702 and 710 puts hit −35% on the same bounce. All three were back above their entry prices by 11:05–11:10. **So the −35% option stop sits much closer than the share stop.** A normal pullback inside a working trade is enough to hit it. One day isn't enough to change the rules, but the paper log tracks it: shares 1 of 7, options 0 of 7.

**Lesson from 2026-10-09.** A $0.20 same-day option that is $9 out of the money needs QQQ to keep moving right away. If QQQ just stalls, time decay and falling volatility take about 1¢ a minute in the first half hour, so the −35% stop (7¢) is hit in roughly 15 minutes even when the signal hasn't failed. My backtest assumed flat volatility, so it didn't capture this; expect real 0DTE results to be worse than `options_sim.py` shows. Tally so far: 3 option trades, all losses (2 of them under the autonomous rules); account $100 → $60.71.
