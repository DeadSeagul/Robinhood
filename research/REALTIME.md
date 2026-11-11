# Real-time paper trading

On 2026-11-09 the user asked whether to go live with real money. I recommended three steps, and the user agreed ("Let's do what you recommended"):
1. Paper trade in real time first.
2. Fix the bar for going live now, before any results.
3. Only then go live, small.

Everything here is **paper**. No real orders are placed.

## Why real time

Until now, `paper_orb.py` scored each day after the market had moved. The rules are mechanical, so hindsight can't change a trade. The fills are a different matter: an entry at the 5-minute bar's open + $0.01 flatters the result when that bar runs. On 11/4 and 11/5 the option nearly doubled inside the entry bar.

In real time, the decision is made at the moment of the signal. The entry pays the live **ask** and the exit gets the live **bid**. Both are logged with the clock time they were taken, in [`realtime_paper.csv`](realtime_paper.csv) by [`realtime_paper.py`](realtime_paper.py). The after-the-fact scoring keeps running, so the two logs side by side show how much the old fills flattered the results.

## The rules

These are the $10,000 options account's rules ([`paper_account.py`](paper_account.py), [`PLAYBOOK.md`](PLAYBOOK.md)). Only the fills change.

- **When:** Monday to Thursday, the QQQ 5-minute opening-range breakout. The signal is the first 5-minute close beyond the 9:30 bar's range, on a bar starting by 11:25.
- **Contract:** the next trading day's expiry, call for long and put for short. Take the nearest-to-the-money strike whose **ask** at entry is at most the cap `realtime_paper.py report` prints (1% of the real-time book ÷ 100, about $1.00). Walk every listed strike: $1 strikes are common.
- **Size:** as many contracts as $1,000 buys at that ask (the user's budget from 2026-11-10). The log works it out.
- **Exits:**
  - QQQ trades through the other side of the opening range (the stop).
  - Target: the option at 2× the entry ask. Treat this as a resting limit sell, so it counts as filled if any option print reaches it.
  - Trail: armed once the bid reaches 1.5× the entry; sell at the bid when it falls back to 1.3×.
  - Time: 90 minutes after entry.
  - Every exit except the target sells at the bid.
- **Lateness:** if the session starts more than 5 minutes after the entry time, the trade is logged as `missed` and not taken late.

## The routine

Each Monday to Thursday, after the 8:50am news read is pushed:

1. **Wait for the signal.** Run `python3 -I research/realtime_paper.py wait-signal --minutes 110` in the background, with a Bash background timeout of 7,200,000 ms. If it prints `state=still_waiting`, run it again.
2. **No signal:** `log no_signal`, commit and push. Done for the day.
3. **Signal:** within a minute or two of the entry time:
   1. List the next expiry's strikes with Robinhood `get_option_instruments`. The cursor is base64 of `p=<strike>`, which starts the list just above that strike.
   2. Read live asks with `get_option_quotes`, walking out from the money.
   3. Log the entry: `log entry --side S --contract "M/D KKKC" --ask A --bid B --qqq Q`.
   4. Commit, push, and send a push note.
4. **Monitor:** run `watch --side S --stop X --since HH:MM --seconds 120` in the background, and repeat until the trade ends:
   - If it prints `state=stop`, quote the option and exit at the bid.
   - Otherwise check the option's quote. Also check its minute bars since the last check, in case the target printed.
   - Apply the target, trail and time rules.
5. **Exit:**
   1. `log exit --reason R --ask A --bid B --qqq Q`, then `report`.
   2. Commit and push.
   3. Send a push note with the result.

## The go-live bar (fixed 2026-11-09, before any real-time trade)

- **When it's judged:** after **20** closed real-time paper trades.
- **To pass:** the real-time book's total P&L must be **above $0** after fees.
- **No rule changes** during those 20 trades. Bug fixes are allowed but get written down.
- **What passing means:** the user's own words from the start apply: "These are screening thresholds, not proof of future profitability." Twenty trades is a small sample.
- **If it fails:** no live trading. Report it and stop there.
- **If it passes:** ask the user. Live trading starts only after their explicit go-ahead at that time and a deposit they make themselves. The live terms agreed now:
  - **$100 per trade**: one contract of about $1.
  - **At most 3 trades in any 5 business days.** The account is a limited-margin account under $25,000, so the pattern-day-trader limit likely applies; the user is checking.
  - **Stop trading** if the live account falls 30% below the starting deposit.
  - **Stops:** a broker-side stop goes in as a backstop, in case the session drops mid-trade.

## Voided entries (removed from the log; not counted toward the 20)

- **2026-11-11:** short signal (9:40 bar closed 685.69 below the 686.81 OR low). Paper entry logged at 09:45:25: 9 × 11/12 670P at the ask 1.04 (bid 1.02, QQQ 684.33). At 09:46 the user said "The market is closed today. Don't trade", so the entry was voided and monitoring stopped. Mark at the void, 09:46:43: 670P bid 1.01 / ask 1.03, QQQ 684.32, so about −$0.03 per contract before fees. (US stock and option markets were open on Veterans Day; only the bond market was closed.) No result is scored for the day.
