# TRADING SYSTEM STATUS

> This file is the shared memory between Cowork-Claude (brain) and the local executor daemon (hand).
> Claude reads this at the start of every tick and rewrites the "Last Analysis" section after each cycle.
> The executor daemon writes results to trade_log.jsonl — Claude reads that too.

---

## System State

- **Last tick:** _not yet run_
- **Executor heartbeat:** _waiting_
- **Phase:** SHADOW (dry-run only — no real orders until phase changes to PAPER or LIVE)

---

## Account Snapshot

- **Balance:** _unknown_
- **Equity:** _unknown_
- **Open positions:** _none_
- **Today's P&L:** $0.00
- **Weekly P&L:** $0.00

---

## Open Positions

_None_

---

## Last Analysis

**Time:** _not yet run_  
**Symbol:** EURUSD  
**Signal:** HOLD  
**Rationale:** _Initial state — no analysis run yet_  
**Confidence:** —  

---

## Trade Journal (last 5 closed trades)

_No closed trades yet_

---

## Active Rules (from weekly review)

1. Only take A or A+ confluence setups — B-grade signals are logged but not executed
2. Max 1 position open at a time during shadow phase
3. No trading during high-impact news (check forexfactory.com calendar)
4. Stop for the day if daily loss exceeds $50

---

## Notes / Observations

_Use this section to log anything worth remembering across sessions._
