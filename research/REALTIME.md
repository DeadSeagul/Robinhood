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
6. **No-trail shadow, only when the official exit was the trail:** keep the same monitoring going until the shadow's own exit. That is the QQQ stop, the 2× target (filled if any minute print reaches it), or the 90-minute time exit at the bid. Then `log shadow_exit --reason R --ask A --bid B --qqq Q` (for the target, `--bid` is the target price), commit and push. On any other exit the shadow is the same trade and nothing more is logged.

## No-trail shadow (pre-registered 2026-11-12, counted from 2026-11-16)

On 11/12 the 700C trailed out at the bid 1.11 at 11:02. It then dipped to 0.98 and reached the 1.84 target at 11:09, before the 11:10 time exit. The user asked whether I'd have stayed in. I didn't see a reason to: the trail rule fired. The question is whether the trail is too tight for one-day options, which can swing 20–30% in a couple of minutes. On 11/9 the after-the-fact 683C also trailed out at +$27 before running much higher. On 11/10 the target filled without the trail mattering. One or two trades can't settle that, so on 2026-11-12 the user agreed to track a second exit rule beside the official one:

- **Same entry.** Same contract, same ask, same number of contracts.
- **Exits:** the QQQ stop, the 2× target and the 90-minute time exit. **No trail.**
- **It splits off only when the official trade trails out.** On every other day the two are identical, so only trail-exit days carry information. Expect only a handful of those.
- **Counted from 2026-11-16,** the first trade after this was written. 11/12 itself is left out, because it's the trade that prompted the test. Counting it would build in the hindsight the test is meant to avoid.
- **Nothing official changes.** The official rules, the 20-trade count and the go-live bar stay as fixed on 2026-11-09. `realtime_paper.py report` shows the shadow beside the official result.
- **When it's read:** at the go-live checkpoint, both totals over the same trades are reported. If the no-trail rule is ahead *and* positive, I'll put it to the user as an option for the live rules, with the caveat that it rests on only a few trail days. It is not adopted without the user's say-so.

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

## Pauses

- **2026-11-11:** the 09:45:25 entry (9 × 11/12 670P at the ask 1.04) was briefly voided at 09:46 when the user thought the market was closed (Veterans Day closes only the bond market), then reinstated at 09:48 when the user said to continue. Nothing could have triggered in the gap: QQQ never touched the 689.02 stop, and the 670P's minute highs were 1.03, 1.06 and 1.14, under the 1.56 trail arm and the 2.08 target. The original entry row is kept unchanged.
