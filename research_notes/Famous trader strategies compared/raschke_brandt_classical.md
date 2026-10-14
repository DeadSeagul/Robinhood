# Linda Bradford Raschke, Peter Brandt and Classical Technical Setups: Rules, Track Records, Independent Evidence

Research date: 2026-10-14. Labels used throughout: **[CLAIM]** = the trader's own claim; **[3P]** = third-party report or verification; **[INF]** = my inference. Book text for *Street Smarts* was read from a full-text copy hosted at vdoc.pub (an unofficial copy of Connors & Raschke, 1995), so rule wording below is from the book itself, not from blog summaries. Brandt's stop rules were read from his own scanned pages of *Diary of a Professional Commodity Trader* (2011, pp. 48-51) plus 2016 member Q&A that he posted on peterlbrandt.com.

---

## 1. Raschke / Connors "Street Smarts" (1995): exact mechanical rules

### Takeaway
*Street Smarts* gives fully specified, bar-based rules for Turtle Soup, Turtle Soup Plus One, 80-20s, Momentum Pinball, the Holy Grail, ADX Gapper, Whiplash, 3-Day Unfilled Gap, ID/NR4 and the 6/100 HV + NR4/ID setup. They were written for futures (prices in "ticks", night sessions ignored) and need translating for stocks. Several popular web summaries get details wrong. For example, the Holy Grail uses a 20-period **EMA**, not an SMA, and Turtle Soup requires the prior 20-day low to be **at least 4 sessions old** (3 sessions for Plus One).

### Cited Findings

**General money management (Ch. 3)** — [Street Smarts text](https://vdoc.pub/documents/street-smarts-high-probability-short-term-trading-strategies-4m242dmrshc0)
- Enter the full position at once and do not add to winners. Place the initial protective stop 1-2 ticks beyond the most recent high or low, scale out as price moves favorably, and consider exiting everything on a parabolic move or range-expansion bar (a possible climax).

**Turtle Soup, buys (Ch. 4; sells are the mirror image)** — [Street Smarts text](https://vdoc.pub/documents/street-smarts-high-probability-short-term-trading-strategies-4m242dmrshc0)
1. Today must make a new 20-day low ("the lower the better").
2. The previous 20-day low must have been made at least 4 trading sessions earlier.
3. After price trades below the prior 20-day low, place a buy stop 5-10 ticks above that prior low, good for today only.
4. If filled, immediately place a GTC sell stop 1 tick under today's low.
5. Trail the stop as the trade becomes profitable.
6. Re-entry: if stopped out on day 1 or 2, you may re-enter with a buy stop at the original entry price.
- The book reports about 15-20 setups per month across a 30-futures-market portfolio and notes that many do not reverse.
- Secondary sources disagree on the "age" condition. [LuxAlgo](https://www.luxalgo.com/library/concept/turtle-soup/) says ≥4 sessions, while a Traders' summary (per search snippet) says ≥3. The book uses 4 for Turtle Soup and 3 for Plus One.

**Turtle Soup Plus One (Ch. 5)** — [Street Smarts text](https://vdoc.pub/documents/street-smarts-high-probability-short-term-trading-strategies-4m242dmrshc0)
1. Day 1: a new 20-bar low, with the previous 20-bar low at least 3 sessions earlier. Day 1 must **close at or below** that previous 20-bar low.
2. Day 2: place a buy stop at the earlier 20-day low. Cancel if not filled on day 2.
3. If filled, place a protective sell stop 1 tick under the lower of the day-1 and day-2 lows.
4. Take partial profits within 2-6 bars and trail the rest.

**What Turtle Soup fades: Turtle System 1** — [MQL5 article (secondary)](https://www.mql5.com/en/articles/23448)
- System 1 entered on a breakout of the prior 20-day high or low and exited on a 10-day opposite extreme. It had a "skip rule": skip the signal if the previous System 1 breakout was a winner. System 2 used 55-day breakouts with 20-day exits and no skip rule.
- LuxAlgo says Turtle Soup was named after Dennis's Turtles ([LuxAlgo](https://www.luxalgo.com/library/concept/turtle-soup/)).

**80-20's (Ch. 6), a day trade** — [Street Smarts text](https://vdoc.pub/documents/street-smarts-high-probability-short-term-trading-strategies-4m242dmrshc0)
1. Buy setup: yesterday **opened in the top 20%** of its daily range and **closed in the bottom 20%**. Sell setup: opened in the bottom 20% and closed in the top 20%.
2. Today, price should trade at least 5-15 ticks below yesterday's low. This is a guideline, not a hard rule.
3. Place a buy stop at yesterday's low. Once filled, put the initial stop near today's low.
4. Trail the stop. This is a day trade only, and night-session data are ignored.
- Book statistic (Moore Research): after a close in the top or bottom 10% of the range, there is an 80-90% chance of follow-through the next morning, but the next day closes higher or lower only about 50% of the time.
- Web summaries garble this rule. A [Scribd summary](https://www.scribd.com/document/194332066/80-20-S-from-Street-Smarts-High-Probability-Short-Term-Trading-Strategies-Raschke) states it inconsistently, and [Forex.academy](https://www.forex.academy/analysis-of-the-connors-rashckes-80-20-strategy/) and [RoboForex](https://roboforex.com/blog/education/trading-strategies-that-were-a-revolution-three-strategies-of-linda-raschke/) use different variants. Treat the book wording above as canonical.

**Momentum Pinball (Ch. 7)** — [Street Smarts text](https://vdoc.pub/documents/street-smarts-high-probability-short-term-trading-strategies-4m242dmrshc0)
1. Compute the 1-period ROC (close − prior close), then a **3-period RSI of that ROC**. This is the "LBR/RSI".
2. Buy setup: day-1 LBR/RSI < 30. Sell setup: day-1 LBR/RSI > 70.
3. Day 2: place a buy stop above the **first-hour high**. If filled, place a sell stop at the first-hour low. Re-entry at the original price is allowed if stopped out.
4. If the trade closes with a profit, hold overnight with a tight stop and exit on morning follow-through, no later than the next day's close.

**2-Period ROC pivot (Ch. 8)** — [Street Smarts text](https://vdoc.pub/documents/street-smarts-high-probability-short-term-trading-strategies-4m242dmrshc0)
- ROC2 = close − close two days ago. Pivot = yesterday's close + ROC2. Go home long or short when the close crosses the pivot on a signal flip, and exit the next day.
- The book's December 1994 S&P example went 8 of 11. The authors state this "is not a mechanical system."

**The "Anti" (Ch. 9)** — [Street Smarts text](https://vdoc.pub/documents/street-smarts-high-probability-short-term-trading-strategies-4m242dmrshc0)
- Indicators: fast line = 7-period %K stochastic (smoothing 4); slow line = 10-period %D.
- Buy setup: %D is in a definite uptrend, %K pulls back toward it, and %K then hooks back up.
- Triggers:
  - (a) Once %K and %D have had opposing slopes for at least 3 days, place a buy stop 1 tick above the prior bar's high, trailing it down bar by bar.
  - (b) Alternatively, buy a break of a trendline drawn across the retracement highs.
- Stop just below the entry bar. Exit into a climax within 3-4 bars; typical hold is 3-4 days.
- The Anti must be preceded by an impulse move ([street-smarts-tradestation blog](https://street-smarts-tradestation.blogspot.com/2008/03/what-is-anti-setup.html)).

**3-10 oscillator** — [Street Smarts text](https://vdoc.pub/documents/street-smarts-high-probability-short-term-trading-strategies-4m242dmrshc0)
- Described in the Anti chapter as a "3-10" moving-average oscillator with a 16-period SMA of itself as the slow line. Raschke used it before switching to the 7/10 stochastic for the Anti.

**Holy Grail (Ch. 10)** — [Street Smarts text](https://vdoc.pub/documents/street-smarts-high-probability-short-term-trading-strategies-4m242dmrshc0)
1. The 14-period ADX must initially be above 30 and rising.
2. Wait for price to retrace to the **20-period EMA**. ADX often turns down during the pullback.
3. When price touches the 20-EMA, place a buy stop above the high of the previous bar.
4. Once filled, place the protective stop at the newly formed swing low. Trail it, with the recent swing high as the target.
5. If stopped out, re-enter at the original entry price.
6. After a successful trade, ADX must turn back up above 30 before another pullback qualifies.
- The authors warn that an ADX turn-down usually signals consolidation, not reversal.
- Galen Woods ([TradingSetupsReview](https://tradingsetupsreview.com/the-holy-grail-trading-setup)) uses an SMA and enters at the high of the bar that touches the MA. That page gives no stop or exit rules and no statistics, only two hand-picked examples. TradingView scripts vary on whether ADX must stay above 30 during the pullback ([TradingView](https://my.tradingview.com/script/hawl3ybg-Holy-Grail-Setup-with-Confidence-Opacity)).

**ADX Gapper (Ch. 11)** — [Street Smarts text](https://vdoc.pub/documents/street-smarts-high-probability-short-term-trading-strategies-4m242dmrshc0)
- Indicators: 12-period ADX > 30, plus 28-period DMI. For buys +DI > −DI (sells mirror).
- Buy setup: today **opens below yesterday's low**. Place a buy stop near yesterday's low, with the stop at today's low.
- Exit before the close, or hold overnight if the trade closes strongly. The book cites Larry Williams' "Oops" research and about 2-4 trades per week across all markets.

**Whiplash (Ch. 12)** — [Street Smarts text](https://vdoc.pub/documents/street-smarts-high-probability-short-term-trading-strategies-4m242dmrshc0)
- Setup: a gap below the prior low, then a close above the open and in the top 50% of the day's range.
- Buy market-on-close. If the next day opens below the entry close, exit immediately; otherwise trail.

**3-Day Unfilled Gap Reversal (Ch. 13)** — [Street Smarts text](https://vdoc.pub/documents/street-smarts-high-probability-short-term-trading-strategies-4m242dmrshc0)
- After a gap-down day that does not fill, keep a buy stop 1 tick above that day's high for 3 sessions. The stop goes at the gap-day low.

**ID/NR4 (Ch. 19, credited to Toby Crabel)** — [Street Smarts text, offset 100k](https://vdoc.pub/documents/street-smarts-high-probability-short-term-trading-strategies-4m242dmrshc0)
- Setup: NR4 = narrowest range of the last 4 days; ID = inside day; ID/NR4 = both.
- The next day only: place a buy stop 1 tick above and a sell stop 1 tick below the setup bar.
- On the entry day only, after a buy fills, add a sell stop 1 tick below the ID/NR4 bar. This **reverses** the position if the breakout fails.
- Trail the stop. If the trade is not profitable within 2 days, exit market-on-close.
- The book says Crabel's original was a day trade, but its own research favors holding longer. Raschke uses **NR7** to switch into "breakout mode" the following day.

**6/100 HV + ID or NR4 (Ch. 20)** — [Street Smarts text](https://vdoc.pub/documents/street-smarts-high-probability-short-term-trading-strategies-4m242dmrshc0)
- Setup: 6-day historical volatility / 100-day historical volatility < 0.50, and day 1 is an inside day or NR4.
- Day 2: bracket stops 1 tick beyond the day-1 extremes, with a same-day reversal stop. Exit within 1-4 days.
- The book says an earlier work used 10/100 for intermediate-term moves.

**Other intraday or indicator rules in the book** — [Street Smarts text](https://vdoc.pub/documents/street-smarts-high-probability-short-term-trading-strategies-4m242dmrshc0)
- Wolfe Waves: 5-minute S&P examples, about 3-6 setups per week.
- Morning News Reversals: 8:30 ET releases in bonds and currencies.
- 5-minute S&P TICK divergence: TICK below −350 on the morning low, a lower price low about 90 minutes later with a higher TICK low, then buy when TICK improves by 100, with the stop at the day's low.
- Arms Index 5-day MA: above 1.20 is a buy; below 0.80 is a sell.
- A/D "Market Buster":
  - Signal: 3-period RSI of the 3-day average of NYSE advances − declines.
  - Trend filter: 100-day EMA.
  - Exit after 3 days or on a 2% stop.
- Climax patterns ("Spike and Ledge", "Three Little Indians") are explicitly subjective and not backtestable.

### Inferences
- [INF] The most mechanical, backtestable setups are Turtle Soup, Turtle Soup +1, 80-20s, Momentum Pinball, Holy Grail, ADX Gapper, Whiplash, 3-Day Unfilled Gap, ID/NR4 and 6/100 HV. The Anti is semi-mechanical because trigger (b) uses a discretionary trendline. Wolfe Waves and the climax patterns are discretionary.
- [INF] Translating "ticks" to US stocks:
  - The 5-10 tick entry offset and 1-tick stops were set in futures tick units. For QQQ, SPY or mega-caps, reasonable equivalents are $0.01-$0.05 or a small fraction of ATR (for example 0.05-0.1 × ATR).
  - The offset choice should be fixed in advance and tested for sensitivity, not optimized.
- [INF] Overnight gaps in stocks matter for every stop-entry rule. If the open gaps beyond the trigger, a realistic backtest fills at the open, not at the trigger price.
- [INF] The ID/NR4 bracket-and-reverse rule and the 80-20 rule cannot be simulated correctly on daily bars alone. Which side fills first, and whether the reversal stop triggers, needs intraday (for example 5-minute) data.
- [INF] Street Smarts' "ignore night session" maps naturally to regular-trading-hours (9:30-16:00 ET) bars for US equities.
- [INF] The Holy Grail rules are timeframe-agnostic ("bar", "swing low"), but the book's parameters (ADX 14 > 30, 20-EMA) were presented with daily futures examples.

### Gaps
- Larry Williams' "Oops" rules are cited in Street Smarts but were not extracted from his own text.
- No exact price input (close vs. midpoint) was confirmed for the 3-10 oscillator in the book text read.
- The book publisher and edition were not confirmed. Wikipedia lists 1995 in its citation and 1996 in its text ([Wikipedia](https://en.wikipedia.org/wiki/Linda_Bradford_Raschke)).

---

## 2. Raschke's track record: what is verified vs. self-reported

### Takeaway
Her regulatory history is consistently reported by multiple sources and her own site: options market maker from 1981, CTA from 1992, CPO from 2002, retired from CTA/CPO roles in 2015. Her performance is not publicly documented in audited form. The main quantitative claim, a #17 of about 4,500 five-year BarclayHedge ranking, appears on her site and in secondary profiles without fund name, dates, returns or a primary BarclayHedge citation.

### Cited Findings
- [CLAIM] Career timeline ([lindaraschke.net bio](https://lindaraschke.net/bio-linda/)):
  - 1981: began as an options market maker on the Pacific Coast and Philadelphia exchanges.
  - 1992: registered CTA.
  - 2002: launched her own hedge fund as CPO.
  - 2015: retired as CTA/CPO and now trades her own account.
  - The site claims her fund ranked "17th out of 4,500 for best 5-year performance by BarclaysHedge" with no date, fund name or return figures. The site gives no audited track record, NFA IDs or losing-year disclosure.
- [3P] Wikipedia's account:
  - 1992: CTA registration and founding of LBRGroup, Inc.
  - Principal trader for 6800 Capital LLC hedge funds.
  - 1998: Watermark Fund (Cayman).
  - 2002: LBR Asset Management, with CPO registration.
  - The Granat Fund focused on drawdown management.
  - Partner in FuturePath Trading, LLC from 2009 to 2014.
  - Retired from institutional roles in 2015.
  - Featured in Schwager's *The New Market Wizards* (1992); IFTA Lifetime Achievement Award, 2024.
  - The BarclayHedge ranking ("17th of ~4,500, late 2000s") is cited to a 2017 Wyckoff Stock Market Institute article, not to BarclayHedge. Some citations on the page do not match their claims. ([Wikipedia](https://en.wikipedia.org/wiki/Linda_Bradford_Raschke); [Wyckoff SMI 2017](https://wyckoffsmi.com/wyckoffs-finest-linda-bradford-raschke/))
- [3P/unverified] "Only one losing year" across her managed-money career is a claim on a commercial profile site ([CompleteTradersEdge](https://completetradersedge.com/linda-raschke-turtle-soup-pattern-trader/)). I could not corroborate it.
- [3P] She is profiled in Lo & Hasanhodzic, *The Heretics of Finance* (2009/2010), ch. 10 ([O'Reilly](https://www.oreilly.com/library/view/the-heretics-of/9781576603161/ch10.html)). That is an interview, not a performance audit.
- [3P] Low-quality "net worth" sites give conflicting firm names and figures. They are unreliable and excluded ([search result example](https://ftp.richardgraygallery.com/posts/linda-raschke-net-worth-updated-2026.html)).

### Inferences
- [INF] CTA/CPO registration with the NFA is a regulatory status, not performance verification. Registered CTAs must provide performance capsules in disclosure documents to prospective clients, but those documents are not public. The public evidence is therefore: registration (verifiable via NFA BASIC), a self-reported ranking, and the 1992 Schwager interview.
- [INF] Her published *Street Smarts* setups are not the same as her fund's strategy. Nothing public links Granat or LBR fund returns to these specific setups.

### Gaps
- NFA BASIC was not queried directly (interactive site), so NFA IDs and exact registration and withdrawal dates are unconfirmed here.
- I found no public annual return series, drawdowns or audited statements for LBR Asset Management, Granat or Watermark.
- I did not find the BarclayHedge source document for the #17 ranking.
- I did not retrieve what Schwager (1992) documented about her returns.

---

## 3. Peter Brandt's classical charting method: rules

### Takeaway
Brandt trades breakouts from classical chart patterns (the Schabacker / Edwards & Magee tradition) on daily and weekly charts.
- **Patterns:** he increasingly restricts himself to patterns with **horizontal boundaries**.
- **Entry:** on the breakout.
- **Initial stop:** the **Last Day Rule**.
- **Risk:** small, typically about 0.5-1% of capital per trade.
- **Target:** a measured-move target, aiming for roughly 4:1 reward-to-risk, managed with the **3-Day Trailing Stop Rule** once about 70% of the target is reached.

His primary text documents the stop and exit rules precisely. "Minimum pattern duration" and "textbook pattern" criteria are mostly documented in secondary summaries.

### Cited Findings

**Background**
- [CLAIM] Entered the business in 1976 at ContiCommodity. Founded Factor Trading Co. in 1980. Wrote *Trading Commodity Futures with Classical Chart Patterns* (1990) and *Diary of a Professional Commodity Trader* (Wiley, 2011). Still publishing in 2026, with posts dated Apr-Sep 2026. ([peterlbrandt.com About](https://www.peterlbrandt.com/?p=1195))

**Last Day Rule (LDR), primary source** — [Brandt scanned pages + Member Q&A, posted 2016](https://peterlbrandt.com/wp-content/uploads/2016/03/3-Day-Trailing-Stop-Rule-3DTSR.pdf)
- November 2016 Q&A: the LDR stop is "the low of the day of the breakout as long as at least half of the bar is below the boundary line. Otherwise ... the low of the last full day within the pattern."
- He has since tightened it. He often uses the **open of the breakout day** when filled early. His example: soybean oil LDR low 34.20, open 34.44, stops used 34.39/34.14.
- May 2016 Q&A modifications:
  - On an extreme wide-bodied breakout bar, he looks for an intraday reaction high or low on an intraday chart instead of risking to the bar's far end.
  - He moves stops faster, using the "Retest Failure Rule".
  - His goal is a "break-even trade within a week after trade entry."

**Continuation patterns** — [Diary pp. 48-49](https://peterlbrandt.com/wp-content/uploads/2016/03/3-Day-Trailing-Stop-Rule-3DTSR.pdf)
- A breakout of a continuation pattern has its own LDR, and he may move the protective stop to that new LDR.
- He prefers continuation patterns lasting no more than 3-4 weeks.

**Targets** — [Diary p. 48](https://peterlbrandt.com/wp-content/uploads/2016/03/3-Day-Trailing-Stop-Rule-3DTSR.pdf); [Brandt on X, 2018](https://x.com/peterlbrandt/status/961052548021940224)
- Besides pattern measured moves, he uses "swing objectives" (equal legs) and point-and-figure counts. "There is no guarantee that any market will reach its target."
- On X: "Target always. 3-day trailing stop rule once 70% to target has been achieved. Otherwise, pivot points and MAs."
- Trendline violations carry no measured-move target; other constructions do ([peterlbrandt.com, Trendlines tag](https://www.peterlbrandt.com/tag/trendlines/)).

**3-Day Trailing Stop Rule (3DTSR), primary** — [Diary pp. 49-50](https://peterlbrandt.com/wp-content/uploads/2016/03/3-Day-Trailing-Stop-Rule-3DTSR.pdf)
- It uses three days of price action. For a long:
  1. The **high day**: the highest day of the move, updated as new highs are made.
  2. The **setup day**: any day that closes below the low of the high day.
  3. The **trigger day**: exit when the setup day's low is penetrated.
- His motivating example: initial risk $800 per $100,000 (**0.8%**) with a target of $3,200 (**4:1**). Leaving the LDR stop in place while ahead $2,400 meant risking $3,200 to make $800, which he calls "insane money management".

**Weekend Rule (Donchian)** — [Diary p. 51](https://peterlbrandt.com/wp-content/uploads/2016/03/3-Day-Trailing-Stop-Rule-3DTSR.pdf)
- A decisive new high or low on a Friday tends to follow through on Monday and Tuesday.
- For Friday breakouts of weekly-chart patterns, he may extend risk "from six-tenths or eight-tenths of 1 percent to a full 1 or 2 percent."
- [INF] The scan wording is ambiguous: "1 or 2" may be "1 or 1.2".

**Pattern quality**
- [CLAIM] On X: "Chart patterns that breakout of a clear horizontal boundary are generally more reliable than patterns breaking out of a diagonal boundary." Patterns with few large "spindles" (wide bars) are also more reliable. ([Brandt on X, 2021](https://twitter.com/peterlbrandt/status/1397183251051995138?lang=en))

**Schwager's *Unknown Market Wizards* (2020) chapter, via a secondary Russian-language review** — [Smart-Lab review, 2023](https://smart-lab.ru/blog/reviews/889963.php)
- He now trades only horizontal-boundary breakouts (rectangles, ascending/descending triangles) and no longer trades symmetrical triangles or trendline breaks.
- Risk is about **0.5%** of equity per trade, with stops moved to break-even or better within 2-3 days.
- Target is about 2% of equity (about 1:4).
- He takes at most one re-entry after a stop, never on the same day.
- Friday rule: liquidate trades showing an open loss at Friday's close.
- No adding to winners. He cuts size after losing streaks.
- About 10-15% of trades produce all profits.
- He calls himself "a glorified order enterer" and says classical charting has lost much of its edge. He treats stocks and futures the same way.
- This is a translation of a review, so treat it as [3P-secondary].

**Grok-written description that Brandt posted** — [Brandt Substack, 2025-03-28](https://brandtp.substack.com/p/my-trading-as-described-by-grok)
- It says max 1% risk per trade, daily or weekly charts and not intraday, a 3DTSR trigger at 70% of target, half-position partial profits, and about 42% win rate.
- This is AI-generated text Brandt published; he did not clearly endorse each figure.

**Pattern duration**
- [3P-secondary] A Substack summary claims Brandt's "sweet spot" is 8-26 weeks, with long patterns judged on weekly bars ([Phorosox Substack](https://phorosoxbeta.substack.com/p/methodology-2-the-pattern-rules)).
- [3P-secondary] Entry is described as a decisive close beyond the boundary, or a breakout plus retest; the hard stop is entered immediately ([Phorosox Substack](https://phorosoxbeta.substack.com/p/methodology-2-the-pattern-rules); [How to Invest Like Peter Brandt](https://pictureperfectportfolios.com/how-to-invest-like-peter-brandt-commodities-trader-and-chartist/)).

### Inferences
- [INF] Brandt's method is partly mechanizable, but the pattern-recognition step (what counts as a "textbook" rectangle or H&S) is discretionary. A backtest must impose an objective definition, which will not equal Brandt's selection. Possible elements:
  - a horizontal boundary touched at least 2-3 times within a tolerance (for example 0.5 × ATR);
  - a minimum duration (for example ≥8-12 weeks on daily bars);
  - an entry on a close beyond the boundary;
  - an LDR stop, a measured-move target and the 3DTSR at 70% of target.
- [INF] The method is calibrated to daily and weekly bars and multi-week patterns. Applying it to 5-minute bars would be a different strategy, not a test of Brandt.
- [INF] His positive expectancy comes from a low hit rate with large winners: about 10-15% of trades produce all profits, by secondary report. Tests should therefore report expectancy and payoff ratio, not win rate, and need large samples.

### Gaps
- I could not confirm from Brandt's own text the "minimum 8-12 weeks" or "textbook" criteria, or an explicit hit-rate figure.
- The exact original book wording of the LDR (Diary, ch. 3) was read only in his later Q&A paraphrase.
- I found no primary statement of the "≤1% per trade" rule beyond the 0.6-0.8% typical risk in the Diary scan and the 0.5% in the UMW review.

---

## 4. Brandt's track record: what is verified vs. self-reported

### Takeaway
Brandt reports very high long-run compounded returns, with figures of 41.6%, 41.56%, 58% and 77.8% depending on the period and method. The record has two segments: roughly 1981-1995, then a hiatus, then roughly 2006/2007 onward. Jack Schwager reported 58% ACROR over 27 years with about 53% annualized volatility. No independent audit report is publicly posted. Critics on trading forums dispute the "audited" label, and the figures differ by computation method (tax-based vs. VAMI).

### Cited Findings
- [CLAIM] Amazon author materials ([Amazon author page](https://www.amazon.com/Peter-L.-Brandt/e/B004H3HI7E)):
  - Average annual compounded return of **41.56% based on IRS tax reporting** and **77.8% based on VAMI**, through 2009.
  - 14 profitable and 4 unprofitable years; best year **+604.7%**, worst **−8.4%**.
  - Retired from full-time trading in May 1995 and inactive until January 2007.
  - (As summarized by search; I did not fetch the page directly.)
- [CLAIM] His 2016 drawdown page lists Factor LLC at **ACROR 41.6%, MAR 1.8, Gain-to-Pain 2.4**. The period appears only in an image. He says he has spent more time in or recovering from drawdowns than at new highs. ([peterlbrandt.com, Trading Drawdowns](https://www.peterlbrandt.com/trading-drawdown/))
- [CLAIM] On X he describes a roughly decade-long break for non-profit work and a return to trading in 2006 ([Brandt on X](https://x.com/PeterLBrandt/status/2081199519182856376)). This differs slightly from the January 2007 date above.
- [3P] Schwager, *Unknown Market Wizards* (2020):
  - Records begin in late 1981.
  - **58% average annual compounded return** over the 27 years traded, two segments separated by an 11-year hiatus.
  - **About 53% average annualized volatility**, which Schwager attributes to aggressive sizing; he uses Brandt as an example of the Sharpe ratio understating performance.
  - ([Perlego listing/excerpt](https://www.perlego.com/book/1990325/unknown-market-wizards-the-best-traders-youve-never-heard-of-pdf))
- [3P-secondary] A review of the chapter lists Sharpe 1.11, Sortino 3.00 and Gain-to-Pain 2.81 ([Smart-Lab review](https://smart-lab.ru/blog/reviews/889963.php)). The same review reports his own descriptions of bad years: 1988 ("got sloppy"), about 1993-1995 (lost his edge, closed his account), and 2013 (impatient after starting to manage outside money).
- [3P-contested] An EliteTrader thread alleges:
  - Brandt retracted an "audited 41.6%" claim and replaced it with "attestation";
  - the figures rest on about 18 years of tax reports;
  - records are missing for 1995-2007.
  - The thread also reports Brandt's response: Schwager reviewed about 18 years of monthly statements reconciled with CFTC performance tables and IRS statements, finding compound returns in the low 50s.
  - These are forum claims, partly disputed in the same thread, and I could not trace the original location of Brandt's statement. ([EliteTrader thread](https://www.elitetrader.com/et/threads/information-about-peter-brandt.320673/))
- [3P] Benzinga and blogs repeat "41% at last audit" without the audit document ([Benzinga](https://benzinga.com/z/9572095)).

### Inferences
- [INF] The 41.56% (IRS) vs. 77.8% (VAMI) gap is consistent with money-weighted vs. time-weighted return differences. Large returns on small capital early on, and deposits or withdrawals, inflate VAMI chain-linked returns relative to dollar-based measures.
- [INF] A +604.7% best year with 53% volatility implies highly leveraged, concentrated futures trading in the early 1980s. That is not comparable to a 1%-risk-per-trade framework applied to QQQ or SPY today.
- [INF] Fourteen profitable plus four losing years equals 18 years. This matches the "18 years of records" in both the critique and the Schwager-review statement: roughly 1981-1995 plus 2007-2009 or later.
- [INF] Strength of evidence: Brandt's record has the stronger third-party check of the two traders (Schwager's statement-level review for a published book). Neither trader has a publicly posted independent audit.
- [INF] Brandt himself says classical charting has lost much of its edge, which is relevant to expectations for out-of-sample tests.

### Gaps
- I found no year-by-year return table from a primary source (Diary appendix tables not retrieved).
- No audit or attestation letter is publicly available.
- No CFTC/NFA registration history for Factor Trading was confirmed.
- I found no performance data after 2019-2020.

---

## 5. Independent and academic evidence on these setup families

### Takeaway
The academic literature finds some statistical information in chart patterns and price-range rules. Examples: Lo-Mamaysky-Wang 2000; Savin-Weller-Zvingelis 2007 for head-and-shoulders. Little of it survives as a stand-alone, cost-adjusted, data-snooping-adjusted trading profit, especially intraday on US equity ETFs (Marshall-Cahan-Cahan 2008: none of 7,846 five-minute SPY rules significant after correction).

I found **no rigorous independent test** of the Holy Grail, and **no independent equity test** of Turtle Soup. Practitioner opening-range-breakout (ORB) results on QQQ reproduce gross but appear to vanish net of realistic costs. Published-anomaly decay averages about 58% post-publication (McLean-Pontiff 2016), which matters for setups published in 1990 and 1995.

### Cited Findings

**Chart patterns**
- **Lo, Mamaysky & Wang (2000), *Journal of Finance* 55(4)** ([NBER w7613](https://www.nber.org/papers/w7613); [MIT page](https://web.mit.edu/~alo/www/Papers/techanal.html))
  - Method: automated pattern recognition with nonparametric kernel regression on a large set of US stocks, 1962-1996. They compared unconditional daily return distributions with distributions conditioned on head-and-shoulders, double bottoms and similar patterns.
  - Conclusion: "several technical indicators do provide incremental information and may have some practical value."
  - The CFA Digest summary says effects were strongest for Nasdaq stocks, and that patterns optimal for detecting anomalies need not be optimal for trading profits ([CFA Digest](https://rpc.cfainstitute.org/-/media/documents/article/cfa-digest/2001/dig-v31-n1-811-pdf.pdf)).
  - [INF] This is a distributional test, not a cost-adjusted trading backtest.
- **Savin, Weller & Zvingelis (2007), *Journal of Financial Econometrics* 5(2):243-265** ([IDEAS/RePEc](https://ideas.repec.org/a/oup/jfinec/v5yi2p243-265.html); [working paper PDF](https://www.biz.uiowa.edu/faculty/gsavin/papers/HSrevision_paw_10%2019%2006.pdf))
  - Data: head-and-shoulders patterns in US stocks, 1990-1999.
  - "little or no support" for stand-alone profitability.
  - Pattern-conditioned strategies earned **5-7% per year risk-adjusted excess returns**, and adding them to the market portfolio raises excess return at fixed risk.
  - Part of the post-pattern underperformance is negative momentum ([CXO summary](https://www.cxoadvisory.com/technical-trading/testing-the-head-and-shoulders-pattern/)).
- **Bulkowski** ([Traders.com 2009](https://www.traders.com/Documentation/FEEDbk_docs/2009/05/Bulkowski.html); [ThePatternSite](https://thepatternsite.com/FailureRates.html); [LuxAlgo on failure definitions](https://www.luxalgo.com/library/concept/pattern-failure-statistics/))
  - Data: 13,932 patterns, 1991-2008, mostly 23 common types.
  - Patterns now fail 2-4× more often than in the past. In the 1990s bull market the average failure rate (failing to climb at least 10%) was 14%.
  - Failure is defined as reversing before a 5% move, which is not comparable with other definitions.
  - Limitations:
    - self-published, not peer-reviewed;
    - patterns identified by the author, so selection is not blind;
    - results depend on market, era and definitions;
    - no transaction costs or significance tests reported in the summaries found.

**Data snooping and decay**
- **Sullivan, Timmermann & White (1999), *Journal of Finance* 54(5):1647-1691** ([LSE Research Online](https://researchonline.lse.ac.uk/id/eprint/119144); [FMG DP303](https://www.fmg.ac.uk/publications/discussion-papers/data-snooping-technical-trading-rule-performance-and-bootstrap))
  - Applied White's Reality Check bootstrap to a universe of 7,846 rules (extending Brock-Lakonishok-LeBaron 1992) on about 100 years of daily DJIA.
  - The best rule appears significant in-sample, before costs, even after the snooping adjustment.
  - A secondhand account reports that on 1987-1996 out-of-sample data the best rule earned an insignificant 8.63% per year before costs ([AgEcon paper citing STW](https://ageconsearch.umn.edu/record/19039/files/cp05pa01.pdf)). Not verified against the original.
- **Marshall, Cahan & Cahan (2008), *Journal of Empirical Finance* 15(2):199-210** ([IDEAS/RePEc](https://ideas.repec.org/a/eee/empfin/v15y2008i2p199-210.html); [CXO summary](https://cxoadvisory.com/technical-trading/technical-analysis-anathema-to-the-academic-world))
  - Data: 7,846 intraday rules in five families on **5-minute SPDR (SPY) data, 2002-2003**.
  - Before correction, 42 rules were significant at 1% and 163 at 5%. **After the data-snooping correction, none were significant.**
  - The channel-breakout family was the most profitable.
- **McLean & Pontiff (2016), *Journal of Finance*** ([Gwern-hosted PDF](https://Www.Gwern.net/doc/economics/2016-mclean.pdf); [Ivey PDF](https://ivey.uwo.ca/media/3775549/pontiff.pdf))
  - Across 97 cross-sectional return predictors, portfolio returns are **26% lower out-of-sample and 58% lower post-publication**.
  - Earlier drafts reported different numbers (10%/35%, 25%/56%).
  - [INF] These are cross-sectional stock anomalies, not time-series bar setups, so the decay magnitude is an analogy, not a direct estimate for Street Smarts setups.

**Turtle Soup / false breakouts**
- **Oxford Strat** ([Oxford Strat](https://oxfordstrat.com/?p=5614)): tested a Turtle Soup Plus One-style rule on 42 futures, 1980-2011.
  - Rules: channel 10-100; time exit 1-40 days; 6×ATR(20) stop; quick exit 1 tick under the prior bar low; $0 and $100 round-turn cost cases.
  - Headline statistics are only in images, and the site's rating is "D". The page carries a CFTC 4.41 hypothetical-results disclaimer.
- **ProRealCode** ([ProRealCode](https://prorealcode.com/prorealtime-trading-strategies/turtle-soup)): a forex M30 implementation was "profitable over the long run on most pairs" but with a "bad" profit factor.
- **LuxAlgo** ([LuxAlgo](https://www.luxalgo.com/library/concept/turtle-soup/)): says results are regime-dependent (better in rotational markets, poor in persistent trends). No sample is given.
- I found no published test on US stocks or ETFs.

**Holy Grail**
- No independent quantified backtest was found. Existing write-ups are anecdotal: two hand-picked examples on [TradingSetupsReview](https://tradingsetupsreview.com/the-holy-grail-trading-setup). TradingView "ADX" scripts with large claimed returns are different rules, on BTC, with small samples (24 trades) ([TradingView](https://www.tradingview.com/script/qnirD0Kg/)).

**NR7 / inside day (Crabel 1990)**
- Crabel's book is the origin of NR4/NR7 and ORB. The underlying idea is that volatility contraction precedes expansion ([StockCharts ChartSchool](https://chartschool.stockcharts.com/table-of-contents/trading-strategies-and-models/trading-strategies/narrow-range-day-nr7); [Crabel text, partial](https://dokumen.pub/day-trading-with-short-term-price-patterns-and-opening-range-breakout-0934380171.html)).
- A claim that NR7 plus inside day gives a 73% "shock day" probability has no sample or definition ([TLAP](https://tlap.io/en/toby-crabels-seven-day-ranges)).
- QuantifiedStrategies' NR7 backtest could not be retrieved (bot wall).
- I found no peer-reviewed SPY NR7 test.

**Opening-range breakout**
- **Holmberg, Lönnbark & Lundström (2013), *Finance Research Letters* 10(1):27-33** ([IDEAS/RePEc](https://ideas.repec.org/a/eee/finlet/v10y2013i1p27-33.html)): ORB yields "significantly higher returns than zero" and a success rate above a "fair game". Keywords indicate crude oil futures. Magnitudes and sample were not retrieved.
- **Zarattini & Aziz (SSRN 4416622, April 2023)** ([CXO summary](https://www.cxoadvisory.com/technical-trading/day-trading-with-an-opening-range-breakout-strategy)):
  - Instrument and period: QQQ, January 2016 to 17 February 2023.
  - Rules:
    - Direction comes from the first 5-minute bar: buy at the second bar's open if it was up, short if down, and skip if it was flat.
    - Stop at the other side of the first bar; target 10R; otherwise exit at the close.
    - Size each trade to risk 1% of equity, with leverage capped at 4×.
  - Costs: commission $0.0005/share, no spread or slippage.
  - Reported results: 24% hit rate, +0.13R per trade, about 33% per year at 4× leverage ([Krueger replication](https://www.mql5.com/en/blogs/post/776235)).
- **Independent replication** (T. Krueger, MQL5 blog, 25 Sep 2026; [MQL5](https://www.mql5.com/en/blogs/post/776235)):
  - Data: NQ, SPX, Dow, DAX and FTSE CFDs, January 2015 to June 2026, minute data.
  - Gross results reproduce: NQ +0.131R (t = 2.9), SPX +0.119R (t = 2.4).
  - **Net of spread and slippage, no market is distinguishable from zero**: NQ +0.002R, SPX −0.081R.
  - The rule is negative in 2015-2017 in every market, and NQ out-of-sample 2021-2026 is at most +0.06R.
  - This is a blog, not peer-reviewed.

**Larry Williams volatility breakout**
- Rule: buy at open + k × prior day range, sell at open − k × prior range, with k usually below 1. Williams dates it to 1982 and published it in *Long-Term Secrets to Short-Term Trading* (1999). A secondary source says Williams has written that it works less well recently. ([LuxAlgo](https://www.luxalgo.com/library/concept/volatility-breakout/))
- The only S&P "evidence" found is a broker's promotional backtest with no period, k or costs disclosed ([WH SelfInvest](https://whselfinvest.com/en-be/trading-platform/free-trading-strategies/tradingsystem/56-volatility-break-out-larry-williams-free)).
- I found no peer-reviewed test.

**In-book statistics**
- Street Smarts cites Moore Research tendencies:
  - After top- or bottom-10% closes: 80-90% next-morning follow-through, but about 50% next-day close direction.
  - Sugar closed opposite a WR7 bar 60% of the time.
  - These are described as tendencies, not mechanical systems ([Street Smarts text](https://vdoc.pub/documents/street-smarts-high-probability-short-term-trading-strategies-4m242dmrshc0)).

### Inferences
- [INF] Base-rate expectation for QQQ/SPY/mega-cap backtests: modest gross edges may appear, and edges at 5-minute frequency are likely to be consumed by spread and slippage. The closest analogues are Marshall et al. on 5-minute SPY and the ORB replication.
- [INF] Turtle Soup, 80-20s, ADX Gapper, Whiplash and Oops are short-term reversal or fade rules. Raschke's "ticks" plus re-entry logic implies high trade counts and cost sensitivity. Cost modeling (half-spread plus slippage per side) should be explicit.
- [INF] Testing about 10+ Street Smarts variants, each with parameter choices, on the same data creates the multiple-testing problem STW addressed. Mitigations include a Reality Check or SPA test, pre-registered parameters (the book's), holdout periods, and comparison against a random-entry baseline (as in the ORB replication).
- [INF] Publication dates for decay analysis: Crabel 1990, Street Smarts 1995, Williams 1999, Brandt 1990 and 2011, Zarattini-Aziz 2023. Pre- vs. post-publication splits are feasible for daily US equity data back to the 1990s.

### Gaps
- No independent Holy Grail or Turtle Soup backtest on US equities or ETFs with sample sizes was found.
- The NR7 backtests that were found are not retrievable or not verifiable.
- I did not retrieve the full-text magnitudes for LMW (2000), STW (1999) out-of-sample, or Holmberg et al. (2013).
- I found no peer-reviewed test of Larry Williams' volatility breakout on S&P instruments.

---

## 6. Daily vs. 5-minute bars: which rules apply naturally where

### Takeaway
Many Street Smarts setups are explicitly a **daily setup with intraday execution**: 80-20s, Momentum Pinball, ADX Gapper, ID/NR4's bracket-and-reverse, and Crabel/ORB. The book also has natively intraday patterns (Wolfe Waves, the TICK divergence and Three Little Indians on 5- to 30-minute charts). Brandt's method is daily or weekly only. A faithful backtest therefore needs daily bars for setup detection and 5-minute bars for fills.

### Cited Findings
**Daily setup, intraday execution:**
- **80-20s:** daily setup, intraday stop at the prior low, flat by the close ("day trade only") ([Street Smarts text](https://vdoc.pub/documents/street-smarts-high-probability-short-term-trading-strategies-4m242dmrshc0)).
- **Momentum Pinball:** daily LBR/RSI setup, **first-hour range** breakout, overnight hold only if profitable ([Street Smarts text](https://vdoc.pub/documents/street-smarts-high-probability-short-term-trading-strategies-4m242dmrshc0)).
- **ADX Gapper:** daily ADX/DMI filter, intraday gap-open trigger, exit before the close or hold if strong ([Street Smarts text](https://vdoc.pub/documents/street-smarts-high-probability-short-term-trading-strategies-4m242dmrshc0)).
- **ID/NR4 and 6/100 HV:** daily setup, next-day bracket stops with same-day reversal; Crabel's original was a day trade ([Street Smarts text](https://vdoc.pub/documents/street-smarts-high-probability-short-term-trading-strategies-4m242dmrshc0)).

**Natively intraday in the book:**
- **Wolfe Waves:** 5-minute and 60-minute S&P examples, about 3-6 five-minute S&P setups per week.
- **TICK divergence:** 5-minute S&P.
- **Three Little Indians:** shown on 30-minute and 5-tick charts.
- **Morning News Reversals:** 8:30 ET releases in bonds and currencies.
- Source: [Street Smarts text](https://vdoc.pub/documents/street-smarts-high-probability-short-term-trading-strategies-4m242dmrshc0).

**Daily (multi-day hold):**
- **Turtle Soup** is daily ("20-day low", "good for today only"). **Plus One** is phrased in "bars".
- **Holy Grail, Anti, 2-period ROC, Whiplash (MOC entry) and 3-Day Unfilled Gap** are daily.
- Source: [Street Smarts text](https://vdoc.pub/documents/street-smarts-high-probability-short-term-trading-strategies-4m242dmrshc0).

**Brandt:** daily and weekly charts, not intraday, per the Brandt-posted Grok description ([Brandt Substack](https://brandtp.substack.com/p/my-trading-as-described-by-grok)). He uses intraday charts only to refine stops on wide-bodied breakout bars ([Brandt Q&A 2016](https://peterlbrandt.com/wp-content/uploads/2016/03/3-Day-Trailing-Stop-Rule-3DTSR.pdf)).

**ORB on QQQ:** uses the first 5-minute bar of the RTH session ([CXO](https://www.cxoadvisory.com/technical-trading/day-trading-with-an-opening-range-breakout-strategy)).

### Inferences
- [INF] Mapping to US equity RTH on 5-minute bars:
  - **"First hour"** = the first 12 five-minute bars (9:30-10:30 ET).
  - **"Open"** = the 9:30 print.
  - **Futures "night session ignored"** = drop pre-market and after-hours bars.
  - **The 8:30 ET news-reversal rule** does not map cleanly to equity ETFs, which open at 9:30. A test would use the 9:30 open after 8:30 releases, or ES/NQ futures.
- [INF] Running the Holy Grail or Turtle Soup Plus One directly on 5-minute bars changes their meaning. "20-bar low" becomes about 100 minutes, and ADX(14) > 30 on 5-minute bars is a different regime filter. Such tests are legitimate variants, not replications. Raschke is widely reported to apply her patterns across timeframes, but I found no primary text giving 5-minute parameters for the Holy Grail.
- [INF] A suggested backtest priority for daily plus 5-minute QQQ/SPY/mega-caps, most mechanical first:
  1. ID/NR4 and NR7 bracket (daily setup, 5-minute fills);
  2. Turtle Soup and Turtle Soup Plus One (daily);
  3. 80-20s (daily setup, 5-minute fills, flat by the close);
  4. Momentum Pinball (daily setup, 5-minute first-hour range);
  5. Holy Grail (daily; 5-minute as a variant);
  6. ADX Gapper and Whiplash (daily setup, 5-minute fills for the gapper);
  7. Brandt horizontal-boundary breakouts with LDR and 3DTSR (daily/weekly only, after objectively defining patterns);
  8. Williams volatility breakout and ORB (5-minute) as benchmarks, with costs.
- [INF] Include a same-period random-entry or opposite-direction control and realistic per-side costs. The ORB literature shows a gross edge of about 0.1R can be fully offset by spread and slippage.

### Gaps
- I found no primary Raschke statement of intraday parameters for the Holy Grail or Turtle Soup. Her later courses and workshop manuals (for example [Trading Techniques Workshop Manual 2008](https://www.studocu.com/en-us/document/georgia-military-college/organizational-behavior/trading-techniques-workshop-manual-2008-by-linda-raschke/146329007)) were not reviewed.
- No source quantified how much of each setup's edge, if any, comes from futures-specific microstructure (for example night-session gaps, tick sizes) rather than generalizing to equity ETFs.
