# Claude Cowork + MT5 Setup Guide

## What You Need

- Windows laptop (MT5 requires Windows)
- MetaTrader 5 installed and logged into your XM account
- Python 3.10+ installed
- Claude Cowork (claude.com, $20/month Pro plan)

## One-Time Setup

### 1. Install Python Dependencies

```bash
pip install MetaTrader5 pandas numpy pyyaml ta
```

### 2. Configure MT5 Credentials

Edit `config.yaml` and add your MT5 block:

```yaml
mt5:
  account: 12345678          # Your XM account number
  password: "your_password"
  server: "XM-Demo"          # or "XM-Real3" etc.
  path: ""                   # Leave empty — auto-detects MT5

data:
  symbol: EURUSD
  timeframe: M15

risk:
  demo_mode: true            # Set false ONLY when ready to go live
  position_size: 0.01        # Lots — start small!
  max_daily_loss: 50
  max_open_positions: 1

strategy:
  rsi_period: 14
  atr_period: 14
  ema_period: 50
  atr_median_window: 20

database:
  path: ./logs/trades.db

logging:
  file: ./logs/trading.log
  level: INFO
```

### 3. Test the Connection

```bash
cd trading_system
python status.py
```

You should see your account balance and current price.

---

## Claude Cowork Tasks

Open Claude Cowork desktop app and create these tasks:

### Task 1 — Trading Cycle (Every 15 Minutes)

**Name:** Run Trading Cycle  
**Schedule:** Every 15 minutes during market hours  
**Command:**
```
cd C:\path\to\forexbot\trading_system && python run_cycle.py
```

**What it does:** Checks for a BUY/SELL signal and places a trade if conditions are met. Skips if a position is already open.

---

### Task 2 — Daily Report (Every Morning)

**Name:** Daily P&L Report  
**Schedule:** Daily at 08:00 (before London open)  
**Command:**
```
cd C:\path\to\forexbot\trading_system && python daily_report.py
```

**What it does:** Prints yesterday's trade summary — wins, losses, total P&L, pips.

---

### Task 3 — Status Check (On Demand)

**Name:** Check Bot Status  
**Trigger:** Manual / on demand  
**Command:**
```
cd C:\path\to\forexbot\trading_system && python status.py
```

**What it does:** Shows live account balance, equity, open positions, and current spread.

---

## Running Manually (Terminal)

```bash
# Check status
python status.py

# Run one trading cycle (dry run — no orders)
python run_cycle.py --dry-run

# Run one real cycle
python run_cycle.py

# Check a different symbol
python run_cycle.py --symbol GBPJPY

# Daily report
python daily_report.py

# Last 7 days report
python daily_report.py --days 7

# Today so far
python daily_report.py --today
```

---

## Checklist Before Going Live

- [ ] `status.py` shows correct balance and server
- [ ] `run_cycle.py --dry-run` runs without errors
- [ ] MT5 terminal is open and logged in
- [ ] `demo_mode: true` tested for at least 2 weeks
- [ ] Profitable on demo before switching to real
- [ ] Set `demo_mode: false` and `server: XM-Real` only when ready
- [ ] Keep laptop plugged in (charger!) during market hours

---

## Market Hours (UTC)

| Session   | Open  | Close |
|-----------|-------|-------|
| Sydney    | 22:00 | 07:00 |
| Tokyo     | 00:00 | 09:00 |
| London    | 08:00 | 17:00 |
| New York  | 13:00 | 22:00 |

Best liquidity: **London + NY overlap (13:00–17:00 UTC)**
