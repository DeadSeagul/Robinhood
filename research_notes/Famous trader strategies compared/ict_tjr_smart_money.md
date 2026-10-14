# ICT / TJR "Smart Money Concepts" Day Trading: Rules, Track Records, and Independent Evidence

Research date: 2026-10-14. Tags used: **[EDUCATOR]** = the educator's own claim or description; **[3P-DESC]** = third-party description or interpretation of the method (not verification); **[3P-VERIFY]** = third-party test, record, or reporting that bears on whether something is true; inferences are kept in the "Inferences" subsections. Most ICT primary material is in long YouTube lectures (Huddleston's channel) that could not be fetched or transcribed in this session. Concept definitions below therefore come mostly from secondary codifications (LuxAlgo, Build Alpha, StatOasis, open-source code), and this is stated where it applies.

## 1. Core concepts and their definitions (as ICT/SMC educators use them)

### Takeaway
The vocabulary is consistent across sources: liquidity pools above highs and below lows, a sweep of a pool, a displacement or market-structure shift, a 3-candle fair value gap, and entries in "discount" for longs and "premium" for shorts, inside fixed New York-time windows. The exact numeric thresholds are not consistent. Educators do not fix swing length, FVG minimum size, what counts as a "fill", killzone boundaries (they vary by 30–90 minutes), or OTE band edges, so every one of these is a free parameter in a backtest.

### Cited Findings
**Origin and framing**
- [3P-DESC] SMC builds on ICT (Michael J. Huddleston) methodology, which he popularized through the 2010s and early 2020s. The label "Smart Money Concepts" came from the wider online community, not from Huddleston. LuxAlgo traces the underlying ideas back to Wyckoff's composite-operator accumulation and distribution, and states there is "no rigorous public evidence that the full SMC framework carries an edge by itself." — [LuxAlgo, Smart Money Concepts](https://www.luxalgo.com/library/concept/smart-money-concepts/)
- [EDUCATOR] ICT's official site describes him as "Author of many of the trading concepts Traders are using in Forex today." It offers an "ICT Free Library" and "ICT Mentorship Core Content", which link to a YouTube playlist. No prices, performance claims, or CFTC Rule 4.41 hypothetical-performance disclaimers appear on the home page. — [theinnercircletrader.com](https://theinnercircletrader.com/)

**Liquidity (buy-side / sell-side), liquidity pools, equal highs/lows**
- [3P-DESC] Buy-side liquidity (BSL) is resting orders above highs, and sell-side liquidity (SSL) is resting orders below lows. A liquidity pool is a cluster of resting orders, such as stops above old highs or below old lows. Equal highs and lows are listed as liquidity to mark, without a numeric definition. — [LuxAlgo SMC](https://www.luxalgo.com/library/concept/smart-money-concepts/)
- [3P-DESC] One open-source codification: "liquidity" exists when several swing highs (or lows) fall within `range_percent` (default 0.01) of each other. The function returns the level and the index of the candle that sweeps it. — [joshyattridge/smart-money-concepts (MIT, ~2.1k stars)](https://github.com/joshyattridge/smart-money-concepts)
- [3P-VERIFY, academic] The stop-hunt premise has partial empirical grounding in FX. Osler (NY Fed) found that stop-loss and take-profit orders at a large FX dealing bank cluster at round numbers. Stop-loss orders tend to sit just beyond round levels, while take-profits cluster at the round number itself. — [NY Fed Staff Report 125](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr125.pdf). Exchange-rate trends are "unusually rapid" when rates reach levels where stop-loss orders cluster, which is consistent with "price cascades" — [NY Fed Staff Report 150](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr150.pdf)

**Liquidity sweep / stop hunt / Judas swing**
- [3P-DESC] Judas swing: "a false push that runs stops beyond an obvious level before reversing." The London open "often" sets the day's high or low this way. — [LuxAlgo Killzones](https://www.luxalgo.com/library/concept/killzones/)
- [3P-DESC] Mechanical sweep definitions in use:
  - Price trades below the lowest low of the prior N bars and closes back above it on the same bar. Build Alpha adds a minimum sweep depth of 0.25×ATR(14) and enters at the next bar's open. — [Build Alpha (D. Bergstrom, 27 Jul 2026)](https://www.buildalpha.com/backtest-ict-and-smc/)
  - StatOasis uses "price breaks below the N-bar low intraday but closes back above it." — [StatOasis](https://statoasis.com/overfit/research/ict-backtest-what-survives)
  - A Silver Bullet backtest uses a bar that "takes out the prior 2-hour extreme and closes back inside." — [GitHub silver-bullet-backtest](https://github.com/cjosh4toyotas-stack/silver-bullet-backtest)

**Market structure: BOS, CHoCH, MSS, displacement**
- [3P-DESC] Displacement: "a fast structure-breaking move that leaves a fresh imbalance behind." — [LuxAlgo SMC](https://www.luxalgo.com/library/concept/smart-money-concepts/)
- [3P-DESC] Build Alpha confirms a swing high only after N bars on each side (High[N] = Highest(High, 2N+1)). The BOS level is tradeable on its first break only, with a buy stop at the swing high. — [Build Alpha](https://www.buildalpha.com/backtest-ict-and-smc/)
- [3P-DESC] In the Python package, a swing high is the highest high within `swing_length` bars before and after (default 50). `bos_choch` can confirm breaks on the close (`close_break=True`, the default) or on the wick. — [joshyattridge/smart-money-concepts](https://github.com/joshyattridge/smart-money-concepts)
- [3P-DESC] A TJR-inspired TradingView script defines displacement as a candle whose body is larger than an ATR multiple and which breaks short-term structure in the opposite direction. The script states it is not affiliated with TJR. — [TradingView search results (TJR Smart Money Model [JOAT])](https://tw.tradingview.com/scripts/liquidity/)
- (Common usage, not sourced to a primary ICT text here:
  - BOS is a break in the direction of the trend.
  - CHoCH or MSS is the first break against the prevailing swing sequence.
  - ICT's MSS is usually taught as requiring displacement and a sweep first. See Gaps.)

**Fair value gap (FVG), consequent encroachment, inversion FVG**
- [3P-DESC] Bullish FVG: "If the third candle's low sits above the first candle's high, the span between those two levels is a bullish fair value gap." A bearish FVG lies between candle 1's low and candle 3's high.
  - The gap's midpoint is called "consequent encroachment" (CE). "Many models treat a touch of the midpoint as 'filled enough.'"
  - An inversion FVG (IFVG) is one that price closes through: "the zone's role inverts."
  - Source: [LuxAlgo FVG](https://www.luxalgo.com/library/concept/fair-value-gap/)
- [3P-DESC] Build Alpha's mechanical FVG:
  - Zone runs from High[2] to Low[0].
  - It stays valid while price closes above the gap bottom and has not traded back to the top edge.
  - Minimum size is 0.35×ATR(14).
  - Entry is a buy limit at the fill level, with a 50% midpoint entry as a variant.
  - Source: [Build Alpha](https://www.buildalpha.com/backtest-ict-and-smc/)
- [3P-DESC] A methodological caveat: every 3-bar sequence with even a one-tick displacement technically qualifies. "Filled" can mean a wick touch, a close, or a full traverse, which are "three different rules with three different equity curves." — summarized in search results citing [fxnx.com](https://fxnx.com/en/blog/smart-money-concepts-work-backtest-evidence) and [StatOasis](https://statoasis.com/overfit/research/ict-backtest-what-survives)

**Order block, breaker**
- [3P-DESC] Order block (OB): "the last opposing candles before strong moves." — [LuxAlgo SMC](https://www.luxalgo.com/library/concept/smart-money-concepts/)
- [3P-DESC] StatOasis's mechanical OB: a down-close bar followed within K bars by an up-impulse larger than M×ATR20. The bar's range is the zone, and entry is on the first retrace into it. — [StatOasis](https://statoasis.com/overfit/research/ict-backtest-what-survives)
- [3P-DESC] Critics note that order blocks are inferred from the chart, since no one outside the exchange sees the actual order data, and that several SMC terms relabel older Wyckoff ideas. — [tradingwyckoff.com](https://tradingwyckoff.com/en/smart-money-concepts/)

**Premium / discount / equilibrium; OTE**
- [3P-DESC] Premium and discount split a dealing range at its 50% level (equilibrium): buy in discount, sell in premium. — [SnapPChart TJR guide](https://www.snappchart.app/blog/beginner-playbook/tjr-ict-trading-strategy); [LuxAlgo SMC](https://www.luxalgo.com/library/concept/smart-money-concepts/)
- [3P-DESC] OTE (optimal trade entry) is the 61.8%–79% retracement band of the impulse leg, with 70.5% as the "sweet spot". The 70.5% label is credited to Huddleston by Backtrex, but no primary source was found. One set of ICT notes uses 62%–70.9%. — [Backtrex OTE](https://backtrex.com/en/blog/ict-optimal-trade-entry-ote-fibonacci-guide); [Scribd ICT notes](https://www.scribd.com/document/739283923/Inner-Circle-Trader-Notes)
- [3P-DESC] StatOasis coded OTE as "after an upward structure shift, enter on a retrace into the 61.8%–78.6% Fibonacci band of the last swing leg," with a 50.0%–70.5% band as a control. — [StatOasis](https://statoasis.com/overfit/research/ict-backtest-what-survives)

**Killzones (all New York time)**
- [3P-DESC] LuxAlgo's windows:
  - Asian: 20:00–00:00. The page's intro says 8–10 pm instead.
  - London open: 02:00–05:00.
  - New York AM: 07:00–10:00, with an index-futures variant of 08:30–11:00.
  - London close: 10:00–12:00.
  - New York PM: 13:30–16:00.
  - Boundaries "differ by 30 to 90 minutes" across sources.
  - Source: [LuxAlgo Killzones](https://www.luxalgo.com/library/concept/killzones/)
- [3P-DESC] Other sources give NY AM as 08:30–11:00 ([Backtrex](https://backtrex.com/en/blog/ict-kill-zone-times-sessions), [TradingView session script](https://www.tradingview.com/scripts/ictkillzone/)) or 08:00–11:00 ([Metalsmine post](https://www.metalsmine.com/thread/1345607-understanding-ict-kill-zones-tflab-free)). One indicator uses 07:00–10:00 for forex and 08:30–11:00 for non-forex.

**Silver Bullet**
- [3P-DESC] The Silver Bullet uses three one-hour NY-time windows: 03:00–04:00 (London), 10:00–11:00 (AM), and 14:00–15:00 (PM). An FVG that forms and is tested inside the window "can set up the trade," with price "targeting liquidity."
  - LuxAlgo's indicator page is dated 4 Jul 2023 and says ICT favors a "Super-Strict" FVG mode.
  - Its "Minimum Trade Framework" is 40 ticks for futures and indices (10 NQ/ES points).
  - Source: [LuxAlgo ICT Silver Bullet](https://www.luxalgo.com/library/indicator/ICT-Silver-Bullet)
- [3P-DESC] A fan-channel summary ("ICT Gems") describes a goal of "at least five handles" rather than the full daily range. This conflicts with LuxAlgo's 40 ticks. — search summary of [ICT Gems – Blending Silver Bullets and Macros](https://www.youtube.com/watch?v=qHongB4cMpQ) (channel @ictgems1102, a fan channel, not ICT's own)

**Power of three, midnight open, PDH/PDL, session highs/lows**
- [3P-DESC] Power of three is the accumulation–manipulation–distribution cycle used to read the day around the killzones. The "midnight New York open" is used as a time-anchored reference price. — [LuxAlgo Killzones](https://www.luxalgo.com/library/concept/killzones/)
- [3P-DESC] The ICT 2022 model, per third-party guides:
  - Daily bias, then mark the midnight range.
  - Wait for a liquidity sweep, then an MSS with displacement, then enter on the FVG during a killzone.
  - Targets are opposing liquidity, for example an intraday high first and the previous-day high as the final objective.
  - Guides disagree on stop placement (beyond the sweep wick vs. the displacement-leg swing) and on minimum R:R (one guide says 1:3).
  - Sources: [AlgoKings ICT 2022 model](https://www.algokings.net/learn/ict-2022-model/); [ICTTraders](https://icttraders.net/ict-2022-model-complete-trading-strategy-explained-step-by-step/); [TradingStrategyGuides NQ](https://tradingstrategyguides.com/the-complete-guide-to-trading-the-ict-2022-model-in-nq-futures/)
- [3P-DESC] Previous-day and session highs/lows are coded as `previous_high_low(time_frame="1D")` and `sessions(...)`, the latter with built-in Asian, London-open, NY and London-close kill zones. — [joshyattridge/smart-money-concepts](https://github.com/joshyattridge/smart-money-concepts)

### Inferences
- Every concept reduces to a few OHLC primitives:
  - Swing points (parameter N).
  - Levels: PDH/PDL, session H/L, equal highs/lows within tolerance.
  - Sweep: wick beyond a level plus a close back inside, optionally with a depth filter in ATR.
  - Displacement: body size > k×ATR and/or a close beyond a swing.
  - 3-bar FVG, with minimum size in ATR or ticks.
  - Fibonacci bands of the impulse leg.
  - Clock windows.
  
  The discretionary content sits mostly in which level is the "draw on liquidity" and in the daily bias.
- Concepts that need overnight (ETH/Globex) futures data, which a QQQ/SPY regular-hours (09:30–16:00 ET) dataset lacks:
  - Asia session H/L (20:00–00:00 ET) and London H/L (02:00–05:00 ET).
  - The midnight open.
  - The London Silver Bullet (03:00–04:00).
  - The 08:30–09:30 part of the NY AM killzone, including the 08:30 ET news reaction.
  - The ICT "true day" framing.
  - PDH/PDL computed on the 23-hour futures session, which differs from RTH PDH/PDL.
- Concepts fully computable from RTH bars:
  - RTH PDH/PDL and the prior-day close.
  - The opening range and intraday swing highs/lows.
  - The 10:00–11:00 and 14:00–15:00 Silver Bullet windows.
  - FVG, BOS/MSS, equilibrium/OTE within intraday legs.
  - Hourly highs/lows.
  - ES-vs-NQ divergence ("SMT"), proxied by SPY vs QQQ.
- Partial proxies:
  - SPY/QQQ extended-hours bars (04:00–09:30 ET) can approximate the pre-market H/L, but they are thin.
  - Index futures bars would be needed to replicate Asia/London levels faithfully.

### Gaps
- No primary-source (Huddleston lecture or transcript) definitions were retrievable for MSS vs. CHoCH, breaker block, mitigation block, BISI/SIBI, power of three, the midnight-open rule, or the exact OTE band edges. YouTube pages could not be fetched; only titles via oEmbed were available. The breaker definition (commonly a failed order block that is later traded from the other side) is unsourced here.
- No source gave an ICT-official numeric minimum FVG size, swing length, or "fill" definition. These appear to be left to discretion.

## 2. TJR's specific model as he describes it publicly

### Takeaway
In his own videos, TJR (YouTube @TJRTrades, identified by third parties as Tyler Riches) describes a discretionary ICT-derived routine traded at the New York open on ES and NQ:
1. Mark draws on liquidity: PDH/PDL, Asia, London, hourly and 4H highs/lows.
2. Wait for a sweep.
3. Require a 5-minute BOS or inverse FVG against the sweep.
4. Wait for a 5-minute pullback into equilibrium or an FVG.
5. Enter on a 1-minute counter-BOS-then-BOS, with the stop beyond the swept or second high/low and targets at the next liquidity levels.

He explicitly declines to give a rigid step list, and he gives no fixed risk percentage.

### Cited Findings
- [EDUCATOR] In "Path to Profitability: TJR's Strategy Explained" (YouTube, channel "TJR" @TJRTrades; upload date not retrieved), per the SozAI transcript:
  - **Discretion:** He calls his approach "the ideation and the thought process," which involves discretion.
  - **Instruments:** S&P 500 and Nasdaq, with the S&P used as the "leading index" in the example.
  - **Timeframes:** 4H for trend, 1H for order flow and draws, 5m for continuation confluence, 1m for entry confirmation.
  - **Draws on liquidity:** Previous day high and low, Asia high and low, London high and low, hourly highs and lows. A draw already taken with no reaction is "pretty useless for us."
  - **Confirmation:** A lower-timeframe BOS or an inverse FVG after the sweep. Bearish SMT divergence between the indices is supporting evidence.
  - **Continuation confluences:** Equilibrium and FVGs.
  - **Entry:** "I entered this trade once we inverse this gap right here."
  - **Stop:** "I put my stop loss above these highs."
  - **Targets:** Three take-profits at liquidity levels.
  - **Not stated:** Order blocks, risk per trade, R:R rule, and fixed times.
  - Source: [SozAI transcript](https://sozai.app/transcript/path-to-profitability-tjr-strategy/); video: [YouTube TEp3a-7GUds](https://www.youtube.com/watch?v=TEp3a-7GUds)
- [EDUCATOR] In "My UPDATED Day Trading Strategy (2026)" (TJR; transcript covers trades from 1 Jan to 1 Jun 2026):
  1. **Draws:** Mark session highs and lows (London, Asia), 1H and 4H highs and lows, and the daily low as "draws on liquidity."
  2. **Sweep:** Wait for a sweep of one of them by either ES or NQ. The sweep gives the market "the opportunity to fill orders."
  3. **Confirmation:** A 5-minute BOS or a 5-minute inverse FVG in the opposite direction.
  4. **Continuation:** A 5-minute retrace into equilibrium or an FVG fill. He does not use OTE or the 79% level.
  5. **Entry:** On the 1-minute chart, wait for a counter-BOS, then a break back in the trade direction. Entering early on the 5m signal "is going to cause you guys to get a horrible entry."
  - **Alignment filter:** ES and NQ must agree on the 5-minute chart, or he skips the trade. If they are not aligned by about 10:20 ET, "call it a freaking day."
  - **Stop:** Above the second high for shorts, or under the second low for longs.
  - **Targets:** Hourly, session, London, Asia and 4H levels, with partials and a stop moved to breakeven after TP1. Example setups ran about 1:1 to 1:3.4.
  - **Trade count:** "the less trades, the better."
  - **Pre-market:** No pre-market entries.
  - **Purpose:** The strategy is "less about what trade to take and more about what trades it stops us from taking."
  - Source: [SozAI transcript, My UPDATED Day Trading Strategy (2026)](https://sozai.app/transcript/updated-day-trading-strategy-2026/)
- [EDUCATOR] Self-reported statistics in the same 2026 video:
  - About 64% daily win rate (64.29% on Tradezella).
  - Average winner about $22,000 and average loser about $16,000.
  - Average R:R stated as 1:2.33, with 1:1.33 elsewhere in the transcript.
  - $874,782 year to date. The page summary says "$700,000."
  - No losing month in 2026 so far.
  - He "upped the risk at the end."
  - Broker not named. No prop-firm accounts mentioned.
  - Source: [SozAI transcript](https://sozai.app/transcript/updated-day-trading-strategy-2026/)
- [3P-DESC] SnapPChart (8 Aug 2026, not affiliated with TJR):
  - He trades NQ and ES E-mini futures. The E-mini detail is from third-party profiles.
  - Streamed trades happen at the NYSE open (~09:30 ET) via his whop.com live trading room.
  - He charts on TradingView and sells a "TJR Indicators" bundle.
  - The article finds no published broker, risk per trade, or prop-firm usage.
  - Source: [SnapPChart](https://www.snappchart.app/blog/beginner-playbook/tjr-ict-trading-strategy)
- [3P-DESC] A TJR-inspired TradingView script (not affiliated) codes the Asia high and low as liquidity. A sweep is a wick beyond the Asia range and a close back inside. The script then requires a displacement candle that breaks structure, an OB or FVG retrace entry, an HTF bias filter, and optional SMT. — [TradingView (TJR Trades Indicator / TJR Smart Money Model listings)](https://cn.tradingview.com/scripts/search/stop%20hunt/page-9)
- [3P-DESC] Business lines named by third parties:
  - YouTube, mentorship and courses, indicator bundles, brand deals, and TJR LLC. — [Bangor Magazine](https://thebangormagazine.com/tjr-net-worth/) (low-quality aggregator)
  - A co-founded prop firm, 1of1 Funding (TradeLocker listing gives a 2023 founding, TJR as founder, a 100% profit split, and $6k–$200k accounts). — [TradeLocker](https://tradelocker.com/hub/prop-firms/1of1-funding)
  - A promotional video, "TJR Day In The Life With Alpha Futures," published on prop firm Alpha Futures' YouTube channel (verified via YouTube oEmbed; commercial terms unknown). — [YouTube 2ck4zNDRV4I](https://www.youtube.com/watch?v=2ck4zNDRV4I)

### Inferences
- TJR's 2026 description is the most mechanizable of the sources (spelled out as a rule set in Section 3).
- Ambiguous points that need a parameter choice:
  - Which swing defines the 5m BOS (most recent opposing 5m swing after the sweep).
  - Whether "equilibrium" is 50% of the sweep-to-BOS leg.
  - What "second high/low" means for the stop. Most plausibly it is the lower high or higher low formed by the 1m counter-move, or the sweep extreme; the transcript does not settle this.
  - Which liquidity level counts as the target.
- His own dollar averages (+$22k / −$16k ≈ 1.38:1 payoff) fit the "1:1.33" figure better than "1:2.33." At a 64% win rate, a 1.38 payoff implies positive expectancy if the numbers are accurate. These are unaudited self-reports (see Section 4).
- His ES/NQ alignment requirement maps onto SPY/QQQ for an ETF test. His draws on Asia and London levels and 1H/4H levels built from 23-hour futures need futures data. An RTH-only test would have to drop those levels or substitute pre-market H/L.

### Gaps
- No primary TJR written course or rulebook was retrieved. Course and website pages (whop.com, tjrtrades) were not fetched, and his X posts could not be accessed.
- Upload dates of the two TJR videos were not retrieved.
- No stated risk-per-trade percentage, max daily loss, or fixed R:R found in his own words.
- Whether he currently trades personal brokerage accounts, prop/funded accounts, or both could not be confirmed. The 2026 video mentions Tradezella journaling and no prop accounts.

## 3. Explicit step-by-step rules (Silver Bullet; sweep → MSS → FVG; TJR variant) and where discretion remains

### Takeaway
Both ICT models can be written as deterministic rules on 1m/5m bars. The educators leave five things unspecified: the "draw on liquidity" (target), daily bias, minimum displacement or FVG size, entry point within the FVG (edge vs. 50% CE), and stop anchor. These have to be set as parameters and swept, with costs and out-of-sample testing. The one transparent, ongoing mechanical Silver Bullet backtest on NQ/ES is currently losing money on small samples.

### Cited Findings
- [3P-DESC] Silver Bullet entry variants:
  - A buy limit at the top of a bullish FVG (bottom for shorts). — [TradingView explainer](https://pl.tradingview.com/chart/EURUSD/jOkVQBxm-What-Is-the-ICT-Silver-Bullet-Strategy-and-How-Does-It-Work)
  - Entry inside the gap at its midpoint, or on a candle that trades into the gap and closes back inside. The target is liquidity on the other side, and there is no trade if that is under 2:1. Invalidation: "price closes below the gap instead of holding it." — [ChartingLens](https://chartinglens.com/blog/ict-silver-bullet-strategy)
- [3P-VERIFY] A transparent mechanical Silver Bullet test on NQ/ES 5-minute bars (rules v1.1, 18 Aug 2026; results updated 14 Oct 2026):
  - **Windows:** 03–04, 10–11 and 14–15 NY time.
  - **Sweep:** A bar takes out the prior 2-hour extreme and closes back inside, scanned from 30 minutes before the window.
  - **FVG:** The first FVG of at least 0.5 pt inside the window after the sweep, on a "displacement candle closing in bias direction."
  - **Entry:** Limit at the near gap edge, which must fill inside the window.
  - **Stop:** 1 tick beyond the sweep extreme; trades skipped if risk exceeds 60 pts.
  - **Exit:** Target 2R, time exit after 2 hours, and a same-bar stop-and-target counted as a loss.
  - **Size and costs:** One trade per window, $10 round trip, 1 contract.
  - **Results:**

    | Market | Trades | Win rate | Profit factor | Net P&L |
    |---|---|---|---|---|
    | NQ | 37 (8 target / 26 stop / 3 time) | 29.7% | 0.61 | −$5,645 |
    | ES | 42 | 31.0% | 0.77 (R-based) | −$2,758 |

  - **Data:** Jun–Oct 2026, delayed Yahoo/IBKR. The author warns the sample is "not statistically meaningful." An earlier snapshot reported NQ at 27 trades, 25.9% win rate, PF 0.51.
  - Source: [GitHub cjosh4toyotas-stack/silver-bullet-backtest](https://github.com/cjosh4toyotas-stack/silver-bullet-backtest)
- [3P-DESC] Build Alpha's recommended validation is to compare each ICT rule against random entries with the same frequency, apply ATR-scaled size filters, and test both edge and 50% fills. The article takes no position on whether the concepts work. — [Build Alpha](https://www.buildalpha.com/backtest-ict-and-smc/)

### Inferences
**Rule set A: ICT Silver Bullet (NY AM), testable on 1m bars (5m variant in brackets); my codification**
1. **Session and window:** Use America/New_York time. Look for setups only from 10:00:00 to 10:59:59. Optionally add a PM window from 14:00 to 14:59.
2. **Liquidity levels** (computed before 10:00): RTH PDH/PDL, the 09:30–10:00 opening-range H/L, and any intraday swing high or low (N=3–5 bars each side) formed since 09:30. If futures data is available, add the overnight H/L, London H/L and Asia H/L.
3. **Sweep:** A bar's high exceeds a level's buy-side liquidity and the bar (or one of the next k ≤ 3 bars) closes back below it. Optional depth filter ≥ 0.1–0.25×ATR(14). The mirror case applies for sell-side. A buy-side sweep implies a short bias, and vice versa.
4. **Displacement / MSS:** After the sweep, a bar closes beyond the most recent opposing swing (a swing low for shorts). Optionally require that bar's body ≥ 1.0–1.5×ATR(14) or ≥ 2× the median body. The bars must leave a 3-candle FVG in the trade direction. Example for a short: High[t] < Low[t−2], gap = [High[t], Low[t−2]]. Minimum gap size ≥ x ticks or 0.1–0.35×ATR.
5. **Entry:** A limit at the FVG near edge, or a variant at CE (50%). It must fill before 11:00, otherwise cancel.
6. **Stop:** One tick beyond the sweep extreme (variant: beyond FVG candle 1, or beyond the displacement swing). Skip if the stop is larger than a cap.
7. **Target:** The nearest opposing liquidity level (an unswept intraday swing, PDH/PDL, or opening-range extreme). Require target distance ≥ 2R, otherwise skip (variant: fixed 2R). Use LuxAlgo's "minimum trade framework" of 40 ticks (10 points) for NQ/ES, or scale it for QQQ/SPY by price ratio.
8. **Invalidation:** A close beyond the far side of the FVG before fill cancels the setup. Use a time stop (end of window plus X minutes, or a 2-hour max), one trade per window, and same-bar stop/target counted as a loss.

**Rule set B: ICT 2022-style sweep → MSS → FVG, any killzone; my codification**
- Same as A, except the window is 09:30–11:00 (RTH-only) or 08:30–11:00 (futures).
- Add an optional bias filter: trade shorts only after a BSL sweep when price is in the premium (above 50%) of the prior day's or overnight range, and longs only in the discount.
- Optional OTE filter: the entry must lie in the 61.8%–79% retracement of the displacement leg.

**Rule set C: TJR 2026 variant on 5m plus 1m bars (from his transcript); my codification**
1. At 09:30 ET, list the levels: PDH/PDL, Asia/London H/L (futures only), and the prior 1H and 4H swing highs/lows.
2. A level is swept by either ES or NQ (proxy: SPY or QQQ).
3. On 5m, a close beyond the latest opposing 5m swing (BOS), or a 5m close through an FVG created by the sweep leg (inverse FVG).
4. ES and NQ (SPY and QQQ) both show the step-3 condition in the same direction. If no aligned setup by 10:20–10:30 ET, stand aside for the day.
5. On 5m, price retraces into the 50% of the leg from the sweep extreme to the BOS extreme, or into a 5m FVG.
6. On 1m, a counter-move BOS against the trade, then a BOS back in the trade direction. Enter at the close of that bar.
7. Stop beyond the swing high (short) or swing low (long) made in step 6, or beyond the sweep extreme.
8. Targets at successive liquidity levels with partials (e.g., 1/3 at each), and move the stop to breakeven after TP1. No new entries in pre-market.

**Discretion left open by the educators (each needs a parameter or a sweep)**
- Daily bias: ICT and TJR both use HTF order flow.
- Which level is the "draw."
- Swing length N.
- Displacement threshold.
- FVG minimum size and edge vs. CE entry.
- Stop anchor.
- Whether to require SMT divergence.
- News days: TJR waits for "real volume"; 1of1 Funding banned trades within ±5 minutes of major news per [TradeLocker](https://tradelocker.com/hub/prop-firms/1of1-funding).

**Testing hygiene implied by the sources**
- Fill rules: a limit order needs a trade-through.
- Model slippage and commissions.
- Count same-bar stop and target as a loss.
- Benchmark against random entries in the same window at the same frequency and against buy-and-hold.
- Use walk-forward or holdout.
- Correct for multiple testing (Benjamini-Hochberg).

### Gaps
- ICT's own published rule text for the Silver Bullet (originally taught in video lectures and posts; LuxAlgo's page dates the indicator to July 2023) was not retrieved. Whether ICT requires a prior sweep, or only a "draw on liquidity" plus an FVG inside the hour, could not be confirmed from a primary source.
- No source states an official ICT stop or target rule for the Silver Bullet beyond "target liquidity" and a minimum handle count, and the handle count conflicts between sources (5 handles vs. 40 ticks).

## 4. Track record: what is verifiable vs. self-reported

### Takeaway
No audited, broker-statement-verified, or regulator-filed performance record was found for either ICT or TJR.
- **ICT:** His public competition record is described by adversarial third parties as failed: a 2016 "$10k to $1M" attempt and an account reportedly blown in the 2024 Robbins Cup. These accounts are uncited and not confirmed by official standings.
- **TJR:** His performance figures are self-reported journal screenshots. His income demonstrably includes courses, memberships, indicators, sponsorships, and a now reportedly closed prop firm (1of1 Funding). He was the subject of unrebutted but unproven allegations in a March 2026 YouTube exposé.
- **Regulatory:** No regulatory actions or lawsuits against either person were found in the sources reviewed. Registration status was not directly checked in NFA BASIC.

### Cited Findings
**ICT (Michael J. Huddleston)**
- [EDUCATOR] The official site makes no performance claims; content is offered as a free library and mentorship playlist. — [theinnercircletrader.com](https://theinnercircletrader.com/)
- [3P-DESC, source has a commercial interest: a prop firm selling evaluations] Phidias Prop Firm (undated, © 2026) says:
  - Huddleston "failed in his 2016 bid to trade $10,000 to $1 million" and "again blew his account in the 2024 Robbins Cup."
  - ICT has a "zero verified account track record."
  - His content is now free on YouTube after he discontinued a paid mentorship. The 2022 Mentorship is the usual starting point.
  - The channel has ~1.8M subscribers.
  - No sources are cited for the 2016 or 2024 claims.
  - Source: [Phidias, "Is ICT legit"](https://phidiaspropfirm.com/education/is-ict-legit)
- [3P-DESC] A NexusFi forum post (letter to the Robbins Cup organizers) says Huddleston was a participant in "this year's competition," apparently 2024. — [NexusFi](https://nexusfi.com/showthread.php?p=899824)
- [3P-DESC] Videos by YouTuber Patrick Wieland are adversarial commentary, not verification. Titles: "$100,000 Bet Inner Circle Trader Can't Win Robbins Cup...." and "INNER CIRCLE TRADER ADMITS TO BLOWING ROBBINS CUP! PAY ME $500K!!!" — [YouTube j4aUoNxq7gs](https://www.youtube.com/watch?v=j4aUoNxq7gs); [YouTube G8nb_4V82mI](https://www.youtube.com/watch?v=G8nb_4V82mI)
- [3P-DESC] A Robbins/World Cup history summary lists 2024 top performers (e.g., Ryan Michael LaVelle, +138.6% in Futures) and does not mention Huddleston. — [Quantamental Trader substack](https://quantamentaltrader.substack.com/p/world-cup-trading-championship-and)
- [3P-DESC] A fan-oriented biography says Huddleston's teaching led to "a conflict with the Commodity Futures Trading Commission (CFTC)." A magazine profile places this in the late 1990s. Neither gives details or an outcome. — [innercircletrader.org bio](https://innercircletrader.org/uncategorized/biography-of-michael-huddleston-the-inner-circle-trader/); [Stocks & Futures Trading Magazine](https://stocksandfuturestrading.com/the-inner-circle-trader-who-is-michael-huddleston/)
- [3P-DESC] A Forex Peace Army forum post alleging a CFTC investigation is unsourced and disputed in the same thread. Treat it as rumor. — [Forex Peace Army thread](https://www.forexpeacearmy.com/community/threads/theinnercircletrader-com-michael-j-huddleston.47183/)
- [Regulatory context] The NFA requires CTAs giving advice "based on, or tailored to" particular clients' positions to register as Members. CFTC Reg. 4.14 exempts, among others, those advising 15 or fewer persons in 12 months who do not hold themselves out to the public as CTAs. Publishing general, non-personalized educational content is usually analyzed differently from tailored advice; that is my inference, not a sourced finding. — [NFA: who has to register (CTA)](https://www.nfa.futures.org/registration-membership/who-has-to-register/cta.html); [CFTC "Check" registration tool](https://www.cftc.gov/check)

**TJR**
- [EDUCATOR] Self-reported 2026 statistics (64.29% win rate on Tradezella, $874,782 YTD, no losing month through about June 2026) are shown as screenshots in his video. — [SozAI transcript](https://sozai.app/transcript/updated-day-trading-strategy-2026/)
- [3P-DESC] A March 2026 exposé by YouTuber ImanTrading, as reported by Gate.com (reprint of Chain News, 17 Mar 2026), alleges:
  - Live-stream results were entered manually into a journaling app rather than imported from a broker.
  - In late 2021 he solicited and lost college friends' money, with one repaid in July 2022.
  - He sought trade signals from others in 2021.
  - A "Mastermind" course marketed for 30 students at ~$4,000 enrolled 500+.
  - A linked prop firm shut down amid unpaid-profit accusations.
  - Crypto tokens he promoted fell more than 90%, with on-chain buying before promotion.
  
  No response from TJR was reported, and the article says the case is pending "more evidence and responses." — [Gate.com news](https://www.gate.com/news/detail/us-million-dollar-trading-influencer-exposed-for-profiting-from-selling-19536328)
- [3P-DESC, critic with a conflict of interest: the author sells a competing course and alerts] David Jaffee / BestStockStrategy (published 22 Nov 2025, updated 29 Sep 2026) says:
  - TJR has never published verified broker statements.
  - His "live" trades appear to use TradingView's Projection tool.
  - BBB ScamTracker complaints allege 1of1 winners were not paid.
  - Trustpilot 5-star reviews cluster on the same days.
  - It estimates net worth at $15–25M, mostly not from trading.
  - It states "There is no regulatory action against TJR" (uncited).
  - It cites public IRS 990 filings (ProPublica) showing his family runs a nonprofit private school, which the article contrasts with his "broke DoorDash driver" origin story.
  - Source: [BestStockStrategy](https://beststockstrategy.com/tjr-trades-net-worth/)
- [3P-VERIFY, partial] 1of1 Funding status:
  - TheTrustedProp (page updated October 2026) marks "1 of 1 Funding / One Of One Trading" as "CLOSED … Proceed with caution, do not send funds," with no closure date or reason, and says the firm "has not claimed its profile." — [TheTrustedProp](https://thetrustedprop.com/prop-firms/one-of-one-trading/news)
  - Trustpilot showed about 3.4/5 from 978 reviews at the time of the search. — [Trustpilot (AU mirror)](https://au.trustpilot.com/review/oneofonefunding.com?page=8)
  - The founding claim (2023, TJR as founder) comes from a third-party listing. — [TradeLocker](https://tradelocker.com/hub/prop-firms/1of1-funding)
- [3P-DESC] Net worth figures range from $1–5M to "$20M+," the latter a self-claim per one site. They come from low-quality aggregator sites that repeat each other and are unreliable. — e.g., [Millionaire Script](https://millionairescript.com/tjr-tyler-riches-biography/), [Nanofilm Technology](https://nanofilmtechnology.com/celebrities/tjr-net-worth-the-22-year-old-who-claimed-to-make-1-million-a-month/)
- [3P-DESC] No Bloomberg, WSJ, or Business Insider coverage of TJR was found in searches. — search results ([search summary context](https://beststockstrategy.com/tjr-trades-net-worth/))

**Prop-firm context**
- [3P-VERIFY] The CFTC's fraud suit against prop firm My Forex Funds was dismissed in May 2025 on the CFTC's procedural failings, not the merits, and the court ordered the CFTC to pay about $3.1M in expenses. — [Today's General Counsel](https://todaysgeneralcounsel.com/?p=96462)
- [3P-DESC] A third-party estimate says most funded-trader firms earn 70%–95% of revenue from evaluation fees rather than profit share (forum-adjacent blog; not authoritative). — [NexusFi prop firm regulatory status](https://nexusfi.com/a/prop-firms/prop-firm-regulatory-status)

### Inferences
- **What payout certificates and journal screenshots show and do not show.** They do not show net results:
  - A prop-firm payout certificate shows that one funded account received a payout. It does not show how many evaluations were bought and failed, total fees, or results across all accounts.
  - Prop "funded" accounts are commonly simulated, so a payout is a firm's business decision, not proof of exchange-cleared P&L.
  - A journal-app screenshot (e.g., Tradezella) shows net P&L only if the journal is auto-synced from a broker. The ImanTrading allegation concerns exactly this point (manual entry), and it is unresolved.
  - Verifiable evidence would be FCM/broker statements, a third-party verified track record (e.g., audited by a CPA or tracked by a platform with broker read-only access), or official competition standings.
- For both educators, the economically documented revenue sources (YouTube, courses, memberships, indicators, sponsorships, prop-firm ventures) are separable from trading P&L. Trading P&L remains self-reported (TJR) or contested (ICT).
- TJR's ~64% win rate with a ~1.38 payoff, if real, would be strong. A 5-month self-reported sample with discretionary sizing ("upped the risk at the end") cannot establish a persistent edge.

### Gaps
- Official Robbins World Cup 2024 standings for Huddleston were not found. The 2016 "$10k to $1M" claim could not be traced to a primary record.
- NFA BASIC and CFTC/SEC enforcement databases were not queried directly; their search interfaces are JavaScript apps that were not accessible. No CFTC/NFA/SEC action against either person surfaced in web searches. The late-1990s ICT–CFTC "conflict" remains unverified.
- No court records or lawsuits involving TJR, 1of1 Funding, or Huddleston were found. BBB complaint details were not independently retrieved.
- No response from TJR to the March 2026 allegations was found. Absence in search results is not proof that none exists.
- 1of1 Funding's closure date, reason, and payout history are unverified beyond the TrustedProp listing and the exposé's claim.

## 5. Independent evidence: systematic backtests and academic tests of ICT/SMC concepts

### Takeaway
The independent evidence, mostly 2026 working papers and practitioner studies (none peer-reviewed), is null to negative for ICT/SMC rules as literally taught:
- On S&P 500 daily bars, 44 formalized SMC detectors do not beat random entry after multiple-testing correction.
- On ETF daily bars, 0 of 648 ICT backtests beat buy-and-hold.
- In intraday G10 FX, liquidity sweeps tended to predict continuation, not reversal.
- A small, ongoing NQ/ES Silver Bullet test loses money.

No large-sample, peer-reviewed intraday test on ES/NQ/SPY/QQQ 1m/5m bars was found. That is the main gap, and the concepts are taught for exactly that timeframe.

### Cited Findings
- [3P-VERIFY, academic working paper] Tangirala (SSRN, Sep 2026), "Do Smart Money Concepts Predict Returns? Evidence from 44 Formalised Detectors on S&P 500 Daily Bars, 2010–2026":
  - Two open-source Pine Script SMC implementations were translated into 44 detectors and tested on 496 S&P 500 constituents, Jan 2010–Jun 2026.
  - Each trade is compared with its own ticker's unconditional return, using Newey-West inference.
  - Against a zero-return null, 38 of 44 look significant. Against the matched null, with Benjamini-Hochberg correction across 352 hypotheses, "none beats random entry at any horizon."
  - Liquidity-sweep detectors had the largest point estimates, about 11–12 bp over 10 days (p ≥ 0.23).
  - For 10 concepts, an edge large enough to cover an 11 bp round-trip cost is ruled out at 95% confidence.
  - Concepts selected on 3 years of data earned −31 bp out of sample.
  - Source: [SSRN 7483658](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7483658) (abstract via search; full text blocked)
- [3P-VERIFY, academic working paper] Mahadzva (SSRN; dated 1 Jul 2026, posted 14 Sep 2026), "Smart Money or Costly Folklore? A Systematic Evaluation of ICT/Smart-Money-Concepts Trading Rules in G10 FX":
  - Six ICT/SMC rules were tested on EURUSD, GBPUSD, AUDUSD and USDJPY intraday, using walk-forward, bootstrap, permutation and holdout methods.
  - There is no support for the rules as taught.
  - Three liquidity-sweep mechanisms agree that a swept level tends to lead to continuation rather than reversal. The reported flagship EURUSD H1 result has p = 0.0192.
  - Search summaries also describe the FVG rule as one to fade rather than trade.
  - Source: [SSRN 7430998](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7430998) (abstract via search; full text blocked)
- [3P-VERIFY, practitioner study] Ali Casey / StatOasis (3 Sep 2026, updated 17 Sep 2026), daily bars of SPY (1993+), QQQ (1999+), DIA (1998+) and IWM (2000+), long-only, frictionless:
  - **Rules:** Next-bar-open fills and 5/10/20-bar time exits. Benchmarks are buy-and-hold and a 50-seed random entry at matched frequency.
  - **SPY 5-day edge vs. all-bar baseline:**

    | Concept | Edge | t-stat | Events |
    |---|---|---|---|
    | OB | +0.121% | 1.22 | 736 |
    | FVG | −0.005% | −0.08 | 1,122 |
    | Liquidity sweep | +0.119% | 0.94 | 547 |
    | OTE | −0.028% | −0.17 | 206 |

  - Of 32 ICT t-stats across four markets and two horizons, only one exceeded 2 (OTE on DIA at 10 days, t = 2.07).
  - **Backtests:** 0 of 648 beat buy-and-hold net profit. On SPY, buy-and-hold ended at $551,738 vs. $110,040 for the best OB variant (chosen in hindsight).
  - Order blocks beat random entry in a majority of variants on all four markets (55.6%–81.5%).
  - FVG had a positive repeat on QQQ (+3.136%, t = 3.09) and DIA but was negative on IWM.
  - **Stated limits:** Daily bars only, while ICT is taught intraday.
  - Source: [StatOasis](https://statoasis.com/overfit/research/ict-backtest-what-survives)
- [3P-VERIFY, small sample] GitHub NQ/ES 5m Silver Bullet backtest, Jun–Oct 2026 (14 Oct 2026 update): NQ 37 trades, 29.7% win rate, PF 0.61, −$5,645; ES 42 trades, 31.0%, −$2,758, after $10 per trade. The author says the sample is "not statistically meaningful." — [GitHub](https://github.com/cjosh4toyotas-stack/silver-bullet-backtest)
- [3P-DESC, single-author preprint] Kondapally (SSRN, 2025) proposes an FVG "degree" metric. Across 32,202 FVG events, flatter gaps showed stronger subsequent price reactions. Not replicated. — [SSRN 6032676](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6032676)
- [3P-DESC, protocol only] Rehan (SSRN, Oct 2026), "Liquidity Sweeps and Post-Sweep Acceptance in BTC," is a registered-report protocol with no results yet. — [SSRN 7557779](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7557779)
- [3P-DESC, YouTube backtests of TJR's strategy] The following were found, with results unverified or not retrieved:
  - Revelio Trading, "I Coded TJR's Trading Strategy. Does It Work?" and "I Improved TJR's Trading Strategy. Does It Beat the Market?" The AI summary of the second says:
    - The test ran about 10 years across gold, silver, BTC, S&P, Nasdaq and GBPUSD, with 15m session filters on the indices.
    - The simpler V1 beat V2, which added FVGs and OBs.
    - Trailing stops beat fixed TPs, and an ML filter was added.
    - Silver was dropped, and the final index version was long-only.
    - Results were "impressive" after costs, but no numbers were given and there was no buy-and-hold comparison.
    - The video's own description says it may be overfit.
  - Also: "I Turned TJR's Strategy Into A Trading Bot — Here Are The Results" (@algojan) and "I Tested TJR Trading Strategy So You Don't Have To…" (@TheProfitableDev).
  - Sources: [videohighlight summary](https://videohighlight.com/v/8FJbpSY0R3o); [YouTube 4uqeKO6KcJk](https://www.youtube.com/watch?v=4uqeKO6KcJk); [YouTube QgNZlQ5hXpU](https://www.youtube.com/watch?v=QgNZlQ5hXpU); [YouTube wpg2JpIaDr8](https://www.youtube.com/watch?v=wpg2JpIaDr8)
- [Unsubstantiated claims to discount]
  - "FVGs fill ~70%–80% of the time" (no data shown). — [Scribd SMC doc](https://www.scribd.com/document/944813201/Day-05-Smart-Money-Concept); [search summary of Medium/QuantumAlgo](https://medium.com/@QuantumAlgo/i-backtested-2-600-trades-using-smart-money-concepts-heres-what-actually-works-bb3c671098c6) (page returned 403; its "2,600 trades" methodology could not be checked)
  - Order-block strategies "PF 1.3–1.8" (no source). — [Backtrex](https://backtrex.com/en/blog/smart-money-concept-beginners)
  - Silver Bullet "65%–75% win rates." — [Lune](https://lunefi.com/blog/ict-trading-strategy-2026-65-75-win-rates-prop-firm)
  - "50%–65%" independent win rates (unsourced). — [FundingPips](https://fundingpips.com/blog/ict-silver-bullet-strategy-explained)
- [Related base rates, not FVG] Edgeful's opening-gap (prior close to open) fill rates are a different construct from 3-candle FVGs and are time-varying. On ES over a rolling 6 months, gap-ups filled about 59% and gap-downs about 66%. Half-gap targets filled about 72% (up) and 87% (down). — [Edgeful gap fills](https://www.edgeful.com/blog/posts/trading-gap-fills); [Edgeful half vs. full gaps](https://www.edgeful.com/blog/posts/half-gaps-vs-full-gaps)
- [Academic context on retail day trading of index futures] Chague, De Losso and Giovannetti studied 19,646 Brazilians who day traded mini-Ibovespa futures (2013–2015) for at least 300 days. 97% lost money, and only 0.4% earned more than a bank teller's wage (~US$54/day). Versions differ: the SSRN version reports 1.1% earning more than the minimum wage. — [SSRN "Day Trading for a Living?"](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3423101); [FGV repository](https://repositorio.fgv.br/items/e87d04fc-4b4c-4a56-ab5a-1c84c1afde1b)
- [Academic context on stop clustering] Osler's FX order-book evidence (NY Fed SR 125 and SR 150) supports stop-order clustering beyond round numbers and faster trends when those levels are hit. This is a continuation or "cascade" mechanism, which fits the FX finding that sweeps predict continuation better than the ICT reversal reading. — [SR 150](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr150.pdf); [SR 125](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr125.pdf)

### Inferences
- The strongest independent evidence covers daily equity bars and intraday FX, so it does not directly test 1m/5m ES/NQ/SPY/QQQ. Still, the consistent pattern (no edge after multiple-testing control, and sweeps leaning toward continuation) is a reasonable prior: expect the RTH intraday versions to be near zero before costs unless a specific filter proves robust out of sample.
- For a 2R fixed-target design, breakeven win rate before costs is 33.3%. The GitHub NQ result (29.7%) is below that and consistent with zero or negative expectancy, but 37 trades gives a ±~15 percentage-point 95% confidence interval on the win rate, so the test is inconclusive in both directions.
- Testable hypotheses worth running on 5m/1m QQQ/SPY (and NQ/ES if available):
  - (a) Do post-sweep returns at RTH PDH/PDL and opening-range extremes revert or continue at 5/15/30/60-minute horizons, against random-time and random-level controls?
  - (b) Does a 10:00–11:00 FVG-retest entry beat the same entry at random times of day?
  - (c) Does TJR's SPY/QQQ alignment filter improve expectancy relative to unfiltered sweeps?
  - (d) Are results robust across FVG size thresholds, edge vs. CE entry, and swing lengths, after Benjamini-Hochberg or deflated-Sharpe adjustments?

### Gaps
- No peer-reviewed study of ICT/SMC concepts was found. The SSRN papers are 2026 working papers whose full texts were blocked (HTTP 403), so the numbers come from abstracts or search snippets only.
- No large-sample independent test of the Silver Bullet, or of the sweep → MSS → FVG model, on 1m/5m ES/NQ/SPY/QQQ data was found.
- No independent, numerically reported backtest of TJR's specific model was retrievable. The YouTube tests' numbers were not accessible.
- No credible independent statistics on 3-candle FVG fill rates for US index products were found.
