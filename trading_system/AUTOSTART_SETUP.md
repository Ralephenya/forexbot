# Auto-Start Setup Guide

This guide explains how to set up the trading system to start automatically when your PC boots up.

## Method 1: Windows Task Scheduler (Recommended)

### Quick Setup (PowerShell Script)

1. **Right-click** on `setup_autostart.ps1`
2. Select **"Run with PowerShell"** (or "Run as Administrator" if needed)
3. The script will create a scheduled task that starts the trading system at login

### Manual Setup

1. Open **Task Scheduler** (search for it in Windows)
2. Click **"Create Basic Task"** in the right panel
3. Name it: `TradingSystem_StrategyB`
4. Trigger: **"When I log on"**
5. Action: **"Start a program"**
6. Program/script: `C:\Development\Agent\trading_system\start_trading_system.bat`
7. Start in: `C:\Development\Agent\trading_system`
8. Check **"Open the Properties dialog..."** and click Finish
9. In Properties:
   - Check **"Run whether user is logged on or not"** (optional)
   - Check **"Run with highest privileges"**
   - Under **"Conditions"**: Uncheck "Start the task only if the computer is on AC power"
   - Under **"Settings"**: 
     - Check "Allow task to be run on demand"
     - Check "Run task as soon as possible after a scheduled start is missed"
     - Set "If the task fails, restart every: 1 minute" (up to 3 times)

## Method 2: Startup Folder

1. Press `Win + R` to open Run dialog
2. Type: `shell:startup` and press Enter
3. Create a shortcut to `start_trading_system.bat` in this folder
4. The trading system will start when you log in

## Method 3: Windows Service (Advanced)

For running as a background service (requires additional setup), you can use NSSM (Non-Sucking Service Manager) or similar tools.

## Important Notes

### MetaTrader 5 Auto-Start

**You MUST also set up MT5 to auto-start**, otherwise the trading system won't work:

1. Open MetaTrader 5
2. Go to **Tools → Options → Expert Advisors**
3. Enable **"Allow automated trading"**
4. Set MT5 to start with Windows:
   - Press `Win + R`
   - Type: `shell:startup`
   - Create a shortcut to your MT5 terminal executable
   - Or use Task Scheduler to start MT5 before the trading system

### Recommended Startup Order

1. **First**: MetaTrader 5 (needs time to connect)
2. **Then**: Trading System (waits 30-60 seconds after MT5 starts)

You can modify `start_trading_system.bat` to add a delay:

```batch
timeout /t 30 /nobreak >nul
python main.py
```

### Testing Auto-Start

1. Restart your computer
2. Log in
3. Check if both MT5 and the trading system start automatically
4. Check `logs/trades.log` to verify it's running

### Disabling Auto-Start

**Task Scheduler Method:**
- Open Task Scheduler
- Find `TradingSystem_StrategyB`
- Right-click → Disable (or Delete)

**Startup Folder Method:**
- Press `Win + R` → `shell:startup`
- Delete the shortcut

## Troubleshooting

### Trading System Starts But Can't Connect to MT5

- Ensure MT5 starts BEFORE the trading system
- Add a delay in the startup script (see above)
- Check that MT5 is logged in automatically

### Task Doesn't Run

- Check Task Scheduler → Task Scheduler Library → Your Task → History
- Ensure "Run whether user is logged on or not" is NOT checked (if you want to see the window)
- Check that the path to the batch file is correct

### Python Not Found

- Ensure Python is in your system PATH
- Or use full path to Python in the batch file: `C:\Python311\python.exe main.py`















