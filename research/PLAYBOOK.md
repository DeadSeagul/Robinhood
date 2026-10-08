# Options Day-Trading Playbook

Account: Robinhood **Agentic** (••••2243), ~$92 as of 2026-10-07 close of trading.
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

## Trading rules (autonomous mode)
On 2026-10-07 the user authorized Claude to **place options orders without per-trade approval**. On 2026-10-08 the user **sized down to $20 per trade** (1 contract, ask ≤ $0.20; a −35% stop costs about $7). These are the limits:

1. **Underlying: QQQ only.** Prefer contracts expiring the next trading day (1DTE); same-day (0DTE) is OK.
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

## Trade log
| Date | Trade | Entry | Exit | P/L | Note |
|---|---|---|---|---|---|
| 2026-10-07 | SPY shares (fractional, $95) | $777.62 | $777.45 | −$0.02 | Midday test trade |
| 2026-10-07 | SPY 10/7 $779 call ×1 | $0.17 | $0.09 | −$8.00 (+fees) | 2:07pm entry after Fed minutes; no follow-through, time decay |
| 2026-10-08 | QQQ 10/9 $745 put ×1 (5-min ORB short, autonomous) | $0.69 | $0.45 | −$24.00 (+fees) | 9:50 bar closed $752.42 below OR low $753.11; QQQ snapped back into the range within 3 min (failed breakdown) and broke the OR high by 10:21. Broker-side stop filled 10:19. Lesson: a signal that is already back inside the range at entry time is a warning sign. |
