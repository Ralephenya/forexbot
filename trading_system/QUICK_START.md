# Quick Start Guide

## ✅ MT5 Location Found!

**MT5 Terminal Path:** `C:\Program Files\XM Global MT5\terminal64.exe`

**Status:** MT5 is currently RUNNING ✅

## Running the Trading System

### Step 1: Ensure MT5 is Running and Logged In

1. **Check MT5 Terminal:**
   - Look for the MT5 window on your screen
   - Bottom right should show "Connected" or your account number
   - If not connected:
     - Click "File → Login to Trade Account"
     - Login: `334467853`
     - Password: `Bikojr13!#`
     - Server: `XMGlobal-MT5 9`

### Step 2: Start the Trading System

**Option A: Double-click to run**
- Double-click `start_trading_system.bat`

**Option B: Command line**
```bash
cd C:\Development\Agent\trading_system
python main.py
```

### Step 3: Watch the Output

The system will:
1. Connect to MT5
2. Check account balance
3. Start monitoring for trading signals
4. Log all activity to:
   - Console window (real-time)
   - `logs\trading.log` (detailed system log)
   - `logs\trades.log` (formatted trade log)

## Viewing Logs

### Trade Log (Simple Format)
```
logs\trades.log
```
Example:
```
[14:15] Signal generated: BUY at 1.0850
[14:15] Position opened: 0.01 lots
[14:15] TP: 1.0862, SL: 1.0842
[14:30] Position monitoring: +5.0 pips (+$0.50)
```

### System Log (Detailed)
```
logs\trading.log
```
Contains detailed debugging and system information.

## Auto-Start Setup

To start automatically when PC boots:

1. **Run the setup script:**
   - Right-click `setup_autostart.ps1`
   - Select "Run with PowerShell" (or "Run as Administrator")

2. **Also set MT5 to auto-start:**
   - Press `Win + R`
   - Type: `shell:startup`
   - Create shortcut to: `C:\Program Files\XM Global MT5\terminal64.exe`

## Troubleshooting

### "MT5 initialization failed"
- Make sure MT5 terminal is running
- Make sure you're logged into your XM account in MT5
- Check credentials in `config.yaml`

### "No signals generated"
- Check allowed trading hours (9, 10, 12, 14 UTC)
- Market conditions may not meet strategy criteria
- Check `logs\trading.log` for details

### System not starting
- Check Python is installed: `python --version`
- Install dependencies: `pip install -r requirements.txt`
- Check `logs\trading.log` for error messages

## Current Status

✅ Dependencies installed
✅ MT5 terminal found and running
✅ Configuration ready
✅ Ready to trade!

Just run `python main.py` or double-click `start_trading_system.bat`

