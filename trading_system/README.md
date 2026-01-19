# Automated Trading System - Strategy B (XM/MT5)

An automated forex trading system implementing Strategy B (regime-switching mean reversion/breakout) with XM broker via MetaTrader 5.

## Features

- **Strategy B Implementation**: Regime-switching strategy that adapts to volatility conditions
  - High volatility: Mean reversion (RSI-based)
  - Low volatility: Breakout (EMA-based)
- **MetaTrader 5 Integration**: Full MT5 Python API implementation for XM broker
- **Risk Management**: Daily loss limits, position sizing, kill switch
- **Simple Logging**: Formatted trade log file with real-time updates
- **SQLite Database**: Trade history and system state tracking
- **Structured Logging**: Rotating file logs with console output
- **Production Ready**: Built for real money trading after demo validation

## Architecture

```
trading_system/
├── config.yaml                 # Configuration
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container definition (optional)
├── docker-compose.yml          # Service orchestration (optional)
├── trading_system.service      # Systemd service file
├── main.py                     # Main orchestration loop
├── data_feed.py                # MT5 market data retrieval
├── indicators.py               # Technical indicators (RSI, ATR, EMA)
├── strategy.py                 # Strategy B logic
├── broker_interface.py         # Abstract broker interface
├── mt5_client.py               # MT5 implementation
├── position_manager.py         # Trade tracking
├── trade_logger.py             # Simple formatted trade logging
├── risk_manager.py             # Risk controls
├── database.py                 # SQLite database
└── logger.py                   # Logging setup
```

## Setup Instructions

### 1. Prerequisites

- **Python 3.10+**
- **MetaTrader 5 Terminal** installed on your system
- **XM Demo Account** (for testing) or Live Account
- Windows/Linux/MacOS (MT5 must be running)

### 2. XM Account Setup

1. Create an account at [XM.com](https://www.xm.com)
2. Download and install **MetaTrader 5** terminal
3. Log in to MT5 with your XM credentials:
   - **Demo Server**: XM-Demo
   - **Live Server**: XM-Real
4. Note your account number (visible in MT5 terminal)

### 3. MetaTrader 5 Setup

1. Install MT5 from XM website
2. Log in to your XM account through MT5
3. Ensure MT5 is running (bot requires MT5 to be active)
4. Verify EURUSD is available in Market Watch
5. Test placing a manual trade to ensure everything works

### 4. Twilio Setup (Optional but Recommended)

1. Create an account at [Twilio](https://www.twilio.com)
2. Get your Account SID and Auth Token from dashboard
3. Purchase a phone number (or use trial credits for testing)
4. Note your Twilio phone number

### 5. Configuration

1. Update `config.yaml` with your credentials:

```yaml
mt5:
  account: 12345678  # Your XM account number
  password: "your_password"
  server: "XM-Demo"  # or "XM-Real" for live trading
  path: ""  # Leave empty for default MT5 installation

data:
  source: "mt5"
  symbol: "EURUSD"
  timeframe: 15  # minutes (15 for M15)

strategy:
  name: "strategy_b"
  allowed_hours: [9, 10, 12, 14]  # UTC hours
  blocked_hours: [13, 16]
  rsi_period: 14
  rsi_overbought: 70
  rsi_oversold: 30
  ema_period: 20
  atr_period: 14
  atr_median_window: 20
  high_vol_tp_multiplier: 1.5
  high_vol_sl_multiplier: 1.0
  low_vol_tp_multiplier: 2.0
  low_vol_sl_multiplier: 1.0

risk:
  position_size: 0.01  # lots
  max_daily_loss: 5.0  # USD
  max_positions: 1
  demo_mode: true

database:
  path: "./data/trading.db"

logging:
  level: "INFO"
  file: "./logs/trading.log"
  max_bytes: 10485760  # 10MB
  backup_count: 5
```

### 6. Installation

#### Option A: Direct Python Execution (Recommended)

```bash
cd trading_system

# Install dependencies
pip install -r requirements.txt

# Ensure MT5 terminal is running and logged in

# Run the bot
python main.py
```

#### Option B: Systemd Service (Linux)

```bash
# Edit trading_system.service and update WorkingDirectory path
sudo cp trading_system.service /etc/systemd/system/
sudo systemctl enable trading_system
sudo systemctl start trading_system

# Monitor logs
sudo journalctl -u trading_system -f
```

**Note**: MT5 terminal must be running before starting the service.

#### Option C: Docker (Advanced)

Docker deployment is possible but requires additional setup to connect to MT5:
- MT5 must be installed on host system
- Container must have access to MT5 installation
- More complex setup, not recommended for beginners

## Strategy Logic

### High Volatility Regime (Mean Reversion)
- **Buy Signal**: RSI ≤ 30
- **Sell Signal**: RSI ≥ 70
- **Target**: 1.5x ATR
- **Stop Loss**: 1.0x ATR

### Low Volatility Regime (Breakout)
- **Buy Signal**: Close > EMA(20)
- **Sell Signal**: Close < EMA(20)
- **Target**: 2.0x ATR
- **Stop Loss**: 1.0x ATR

### Time Filtering
- Only trades during allowed hours: 9, 10, 12, 14 UTC
- Avoids blocked hours: 13, 16 UTC
- All times in UTC (London session hours)

### Execution Flow

1. **Every 15 Minutes** (on candle close):
   - Fetch latest EUR/USD data from MT5
   - Calculate RSI(14), ATR(14), EMA(20)
   - Determine volatility regime
   - Generate signal if conditions met
   - Place order via MT5 if signal AND no open position
   - Send SMS notification

2. **Every Minute** (position monitoring):
   - Check if position is still open
   - If closed (TP/SL hit automatically by MT5):
     - Calculate P&L
     - Log to database
     - Send SMS notification

## Trade Logging

All trading activity is logged to `logs/trades.log` in a simple, readable format:

```
[14:15] Signal generated: BUY at 1.0850
[14:15] Position opened: 0.01 lots
[14:15] TP: 1.0862, SL: 1.0842
[14:30] Position monitoring: +5.0 pips (+$0.50) @ 1.0855
[15:00] Position monitoring: +8.2 pips (+$0.82) @ 1.0858
[15:15] Position closed: +12.0 pips (+$1.20) - TP/SL
```

The log file shows:
- Signal generation with entry price
- Position opening with lot size
- TP/SL levels
- Real-time position monitoring (every minute)
- Position closure with final P&L

## Risk Management

1. **Daily Loss Limit**: Trading stops if daily loss exceeds $5 (configurable)
2. **Position Sizing**: Fixed 0.01 lots (micro lot = $0.10 per pip for EUR/USD)
3. **Max Open Positions**: Maximum 1 position at a time
4. **Kill Switch**: Emergency stop via database flag
5. **Demo Mode**: Safe testing environment (default: enabled)

## Database Schema

### Trades Table
- Stores all trade history
- Tracks entry/exit prices, P&L, pips
- Records exit reasons (TP, SL, MANUAL)

### Daily Summary Table
- Daily P&L aggregation
- Trade counts and win rates

### System State Table
- Kill switch status
- Other system state variables

## Monitoring

### Logs
- **File**: `logs/trading.log` (rotating, 10MB max, 5 backups)
- **Console**: Real-time output
- **Level**: INFO (set to DEBUG for detailed logs)

### Database
- **Location**: `data/trading.db`
- View with SQLite browser or command line
- All trades logged automatically

### MT5 Terminal
- View positions in real-time
- Monitor TP/SL levels
- Check account balance and equity
- Visual chart analysis

## Troubleshooting

### MT5 Connection Issues
- **Error**: "MT5 initialization failed"
  - Ensure MT5 terminal is installed and running
  - Check if MT5 is logged in
  - Verify account credentials in config.yaml
  - Check server name (XM-Demo or XM-Real)

### Order Rejections
- **Error**: "Order failed"
  - Check account balance (minimum $10 recommended)
  - Verify position size (0.01 lots = micro lot)
  - Check if market is open (FX market hours)
  - Review MT5 terminal for error messages

### No Signals Generated
- Check time filters (allowed hours: 9, 10, 12, 14 UTC)
- Verify indicator calculations (check logs)
- Review market conditions (may not meet strategy criteria)
- Check if kill switch is enabled

### Log File Issues
- Check that `logs/` directory exists and is writable
- Verify log file permissions
- Check disk space

## Testing Procedure

1. **Start with Demo Account**
   - Always test with XM demo account first
   - Run for at least 1-2 weeks
   - Monitor all trades and signals

2. **Verify Signals**
   - Compare signals with backtest results
   - Check indicator calculations manually
   - Verify TP/SL levels are correct

3. **Monitor Performance**
   - Track win rate
   - Monitor drawdown
   - Verify risk limits are working

4. **Gradual Transition to Live**
   - Start with minimum position size
   - Monitor closely for first week
   - Gradually increase if performance is good

## Safety Features

- ✅ Demo mode by default
- ✅ Daily loss limits ($5 default)
- ✅ Position size limits (0.01 lots)
- ✅ Kill switch capability
- ✅ Error handling and auto-reconnect
- ✅ Structured logging
- ✅ SMS alerts for errors
- ✅ Automatic TP/SL execution by MT5

## Position Sizing

- **Default**: 0.01 lots (micro lot)
- **For EUR/USD**: 1 pip = $0.10 per 0.01 lot
- **With $200 account**: 0.01 lots is safe (max risk ~$5 per trade)
- **Risk per trade**: Approximately 2.5% of account

## Time Zones

- All times in **UTC**
- London session: 9 AM - 5 PM UTC (11 AM - 7 PM SA time)
- Strategy trades during: 9, 10, 12, 14 UTC
- Avoids: 13, 16 UTC

## Future Enhancements

- SMS command interface (kill switch, status check)
- Web dashboard for monitoring
- Multi-pair support
- Advanced risk management
- N8N workflow integration
- Performance analytics dashboard

## Auto-Start Setup

To run the trading system automatically when your PC starts:

1. **Quick Setup**: Run `setup_autostart.ps1` as Administrator
2. **Manual Setup**: See `AUTOSTART_SETUP.md` for detailed instructions
3. **Important**: Also set up MetaTrader 5 to auto-start (see guide)

The system will start automatically on login and begin trading during allowed hours.

## Important Notes

1. **MT5 Must Be Running**: The bot requires MT5 terminal to be running and logged in
2. **Market Hours**: FX market is open 24/5 (closed weekends)
3. **Demo First**: Always test thoroughly in demo mode before live trading
4. **Monitor Closely**: Even in demo, monitor the bot's behavior
5. **Risk Management**: Never risk more than you can afford to lose
6. **Auto-Start**: Ensure MT5 starts BEFORE the trading system (30-60 second delay recommended)

## License

This software is provided as-is for educational and research purposes. Use at your own risk.

## Disclaimer

Trading forex involves substantial risk of loss. This system is provided for educational purposes only. Past performance does not guarantee future results. Always test thoroughly in demo mode before live trading. The authors are not responsible for any financial losses incurred from using this system.
