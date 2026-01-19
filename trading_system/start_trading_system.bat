@echo off
REM Trading System Startup Script
REM This script starts the trading system and ensures MT5 is running

cd /d "C:\Development\Agent\trading_system"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Wait for MT5 to start (if auto-starting)
echo Waiting for MetaTrader 5 to initialize...
timeout /t 30 /nobreak >nul

REM Start the trading system
echo Starting Trading System...
echo Make sure MetaTrader 5 is running and logged in!
echo Logs will be saved to: logs\trades.log
echo.
python main.py

pause

