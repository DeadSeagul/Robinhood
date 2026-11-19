# TJR's day-trading strategy, from two of his videos (read 2026-11-19)

The user asked on 2026-11-19 to "look at videos of tjr explaining day trading strategies". Claude can't watch video,
so this comes from auto-generated transcripts of two of his YouTube videos on sozai.app:

- "My UPDATED Day Trading Strategy (2026)": https://sozai.app/transcript/updated-day-trading-strategy-2026/
- "Path to Profitability: TJR's Strategy Explained": https://sozai.app/transcript/path-to-profitability-tjr-strategy/

**Limits of these sources:**
- The transcripts are auto-captions, with recognition errors and repeated lines.
- Only about the first 35 minutes of each page could be read word for word. The rest of each page is an AI summary, and nothing below comes from those summaries unless it says so.
- Neither page showed the YouTube link or the publish date.

## His method, in his order

1. **Higher-timeframe direction.** Before the open he reads the 4-hour and 1-hour "order flow", meaning which way the trend runs.
2. **Mark the "draws on liquidity".** These are levels where resting orders sit:
   - previous day high/low;
   - Asia and London session highs/lows;
   - 1-hour and 4-hour highs/lows.

   A level that was already swept with no reaction is "pretty useless" to him.
3. **Manipulation.** Price pushes through one of those levels, for example "Step one, manipulation, right? We push above London session highs on the S&P 500."
4. **Confirmation the move reversed:** "I'm looking for a fiveminut break of structure or a 5minute inverse fair value gap."
   - A break of structure in an uptrend is a close below the most recent low.
   - An inverse fair value gap is a price gap that the market closes back through.
5. **Continuation confluence.** Price comes back into a 5-minute equilibrium (the 50% level of the move) or a fair value gap, then continues.
6. **Entry on the 1-minute chart.** He doesn't enter on the first signal: "I'm not just going to enter right here when I see the inverse value gap. No, I want to see some form of a retrace."
   - He waits for a small pullback, then a 1-minute break of structure back in the new direction.
7. **Stop:** beyond the high (or low) of the sweep: "We can put our stop above the second high."
8. **Target:** the next draw on liquidity in the trade's direction: "we need to set take profits based off of these draws in liquidity."
9. **SMT divergence.** He compares the S&P 500 with the NASDAQ.
   - If one makes a new high and the other doesn't, he trades the one that failed.
   - He calls that "the leading index".

**Other points:**
- **Markets:** the S&P 500 and NASDAQ charts. The AI summary says ES and NQ futures.
- **Session:** the New York open, 9:30am ET. The AI summary says he stops if the setup doesn't line up by about 10:30. That isn't in the part we could read.
- **No-trade days:** he skips days that don't set up ("today we actually didn't get an opportunity... I didn't place any trades").
- **Discretion:** in the "Path to Profitability" video he refuses to give a fixed checklist: "I'm not just going to give you like step one, step two, step three." He says strategy, risk management and psychology matter equally.

## His performance claims (unverified)

- **Profit:** "over $700,000 from this strategy alone" in 2026, about a 64% daily win rate, and an average reward-to-risk of "1 to 2.33".
- **Inconsistency:** later in the same video he says "1 to 1.33".
- **Trade sizes:** he says winners average about $22,000 and losers about $16,000. Those don't fit 1:2.33.
- **Verification:** none of this is checked. His results come from his own journal screenshots.

## How it compares with what we tested

- **Earlier tests:** on 2026-10-14 we coded the sweep → structure shift → fair-value-gap model this resembles (`research/FAMOUS_SETUPS.md`).
  - On 58 sessions across 63 stocks: 23 trades, +0.23R a trade, t = 0.9, which is noise.
  - It fired on QQQ or SPY only once.
- **The ICT Silver Bullet**, a close cousin, lost 0.08R a trade over 1,957 trades (t = −3.0).
- **What wasn't tested:** his version adds discretion (higher-timeframe bias, SMT, "no reaction" levels) that can't be coded exactly. So these tests don't prove or disprove his trading. They show that the mechanical core didn't show an edge on our data.
