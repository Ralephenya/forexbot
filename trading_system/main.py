"""
Main trading system orchestration
"""
import yaml
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from logger import setup_logger
from database import Database
from data_feed import DataFeed
from indicators import calculate_all_indicators
from strategy import StrategyB
from position_manager import PositionManager
from risk_manager import RiskManager
from trade_logger import TradeLogger

logger = logging.getLogger(__name__)


def load_config(config_path: str = "config.yaml") -> dict:
    """
    Load configuration from YAML file
    
    Args:
        config_path: Path to config file
        
    Returns:
        Configuration dictionary
    """
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config


def calculate_sleep_time() -> int:
    """
    Calculate sleep time until next 15-minute candle
    
    Returns:
        Sleep time in seconds
    """
    now = datetime.utcnow()
    
    # Calculate next 15-minute mark
    minutes = now.minute
    next_15 = ((minutes // 15) + 1) * 15
    
    if next_15 >= 60:
        next_time = now.replace(hour=now.hour + 1, minute=0, second=0, microsecond=0)
    else:
        next_time = now.replace(minute=next_15, second=0, microsecond=0)
    
    # Add buffer (wait 1 minute after candle close to ensure it's complete)
    next_time += timedelta(minutes=1)
    
    sleep_seconds = (next_time - now).total_seconds()
    
    # Ensure minimum sleep time
    if sleep_seconds < 60:
        sleep_seconds = 60
    
    return int(sleep_seconds)


def main():
    """Main trading loop"""
    try:
        # Load configuration
        config_path = Path(__file__).parent / "config.yaml"
        if not config_path.exists():
            logger.error(f"Config file not found: {config_path}")
            sys.exit(1)
        
        config = load_config(str(config_path))
        
        # Setup logger
        logger_instance = setup_logger(config.get('logging', {}))
        logger.info("=" * 70)
        logger.info("AUTOMATED TRADING SYSTEM - STRATEGY B")
        logger.info("=" * 70)
        
        # Initialize components
        logger.info("Initializing components...")
        
        # Database
        db = Database(config['database']['path'])
        
        # Broker client — MetaAPI (cloud, no MT5 install needed)
        # Reads METAAPI_TOKEN and METAAPI_ACCOUNT_ID from environment variables.
        # Set these in your .env file or docker-compose.yml.
        from metaapi_client import MetaApiClient
        broker = MetaApiClient()
        
        # Data feed
        data_config = config['data']
        data_feed = DataFeed(broker, data_config['symbol'], data_config['timeframe'])
        
        # Strategy
        strategy = StrategyB(config)
        
        # Position manager
        position_manager = PositionManager(db, broker)
        
        # Risk manager
        risk_manager = RiskManager(config, db)
        
        # Trade logger
        trade_logger = TradeLogger(config.get('logging', {}).get('file', './logs/trading.log').replace('.log', '_trades.log'))
        
        logger.info("All components initialized successfully")
        logger.info(f"Trading instrument: {data_config['symbol']}")
        logger.info(f"Timeframe: {data_config['timeframe']}")
        logger.info(f"Demo mode: {config['risk']['demo_mode']}")
        
        # Main trading loop
        logger.info("Starting main trading loop...")
        
        last_signal_check = datetime.utcnow()
        
        while True:
            try:
                # Check kill switch
                if risk_manager.is_kill_switch_enabled():
                    logger.info("Kill switch is enabled. Sleeping...")
                    time.sleep(300)  # Check every 5 minutes
                    continue
                
                # Check daily loss limit
                if not risk_manager.can_trade():
                    logger.warning("Trading not allowed (risk limits)")
                    trade_logger.log_info("Daily loss limit reached. Trading paused.")
                    time.sleep(3600)  # Check again in 1 hour
                    continue
                
                # Get account info
                try:
                    account_info = broker.get_account_info()
                    balance = float(account_info.get('balance', 0))
                    logger.debug(f"Account balance: ${balance:.2f}")
                except Exception as e:
                    logger.error(f"Error getting account info: {e}")
                    time.sleep(60)
                    continue
                
                instrument = data_config['symbol']
                
                # Check if it's time for signal check (every 15 minutes)
                now = datetime.utcnow()
                minutes_since_check = (now - last_signal_check).total_seconds() / 60
                should_check_signal = minutes_since_check >= 15
                
                # Always check for closed positions (every minute)
                # Check if any DB positions were closed by broker (TP/SL hit)
                db_positions = position_manager.db.get_open_trades()
                broker_positions = broker.get_open_positions(symbol=instrument)
                
                for db_pos in db_positions:
                    if db_pos['instrument'] == instrument:
                        # Check if position still exists in broker
                        if not broker_positions:
                            # Position was closed, get last known price
                            try:
                                current_price = broker.get_current_price(instrument)
                                exit_price = current_price['bid'] if db_pos['direction'] == 'BUY' else current_price['ask']
                                
                                # Calculate P&L
                                entry_price = db_pos['entry_price']
                                direction = db_pos['direction']
                                units = db_pos['units']
                                
                                pip_value = 0.0001
                                if direction == "BUY":
                                    pips = ((exit_price - entry_price) / pip_value)
                                else:
                                    pips = ((entry_price - exit_price) / pip_value)
                                
                                lots = units / 100000
                                pnl = pips * 0.10 * lots / 0.01
                                
                                # Close position in DB
                                position_manager.close_position(db_pos['id'], exit_price, "TP/SL")
                                
                                # Log closure
                                trade_logger.log_position_closed(pips, pnl, "TP/SL")
                            except Exception as e:
                                logger.debug(f"Error syncing position closure: {e}")
                
                # Check if we have open position
                has_position = position_manager.has_open_position(instrument)
                
                if has_position:
                    # Monitor existing position (every minute)
                    position = position_manager.get_open_position(instrument)
                    logger.debug(f"Open position: {position}")
                    
                    # Get current position status from broker
                    try:
                        broker_positions = broker.get_open_positions(symbol=instrument)
                        if broker_positions:
                            broker_pos = broker_positions[0]
                            entry_price = position['entry_price']
                            current_price = broker_pos['price_current']
                            
                            # Calculate current P&L in pips
                            pip_value = 0.0001
                            if position['direction'] == "BUY":
                                pips = ((current_price - entry_price) / pip_value)
                            else:
                                pips = ((entry_price - current_price) / pip_value)
                            
                            # Calculate P&L in dollars
                            lots = position['units'] / 100000  # Convert units to lots
                            pnl = pips * 0.10 * lots / 0.01  # $0.10 per pip per 0.01 lot
                            
                            # Log monitoring update
                            trade_logger.log_position_monitoring(pips, pnl, current_price)
                    except Exception as e:
                        logger.debug(f"Error monitoring position: {e}")
                    
                    # TP/SL is handled by broker automatically
                
                # Check for new signals (every 15 minutes)
                if should_check_signal and not has_position:
                    # No position - check for new signal
                    logger.info("Fetching market data for signal check...")
                    
                    # Get historical data for indicators
                    df = data_feed.get_candle_history(count=100)
                    
                    if df.empty:
                        logger.warning("No market data available")
                    else:
                        # Calculate indicators
                        logger.debug("Calculating indicators...")
                        df = calculate_all_indicators(
                            df,
                            rsi_period=config['strategy']['rsi_period'],
                            atr_period=config['strategy']['atr_period'],
                            ema_period=config['strategy']['ema_period'],
                            atr_median_window=config['strategy']['atr_median_window']
                        )
                        
                        # Generate signal
                        signal = strategy.generate_signal(df)
                        
                        if signal and signal['action'] in ['BUY', 'SELL']:
                            # Log signal
                            trade_logger.log_signal(signal['action'], signal['entry_price'], instrument)
                            
                            # Check max open positions
                            open_count = len(position_manager.db.get_open_trades())
                            if not risk_manager.check_max_open_positions(open_count):
                                logger.warning("Max open positions reached, skipping trade")
                            else:
                                # Calculate position size (in lots)
                                position_size_lots = config['risk']['position_size']
                                
                                # Validate position size
                                if not risk_manager.validate_position_size(int(position_size_lots * 100000)):
                                    logger.warning("Position size validation failed")
                                else:
                                    # Position size in lots (MT5 uses lots, not units)
                                    volume_lots = position_size_lots
                                    if signal['action'] == 'SELL':
                                        volume_lots = -volume_lots
                                    
                                    try:
                                        # Place order
                                        logger.info(f"Placing {signal['action']} order: {abs(volume_lots)} lots")
                                        order = broker.place_market_order(
                                            instrument=instrument,
                                            units=volume_lots,
                                            direction=signal['action'],
                                            take_profit=signal['take_profit'],
                                            stop_loss=signal['stop_loss']
                                        )
                                        
                                        # Track position
                                        trade_id = position_manager.open_position(order, signal)
                                        
                                        # Log position opened
                                        trade_logger.log_position_opened(abs(volume_lots), instrument)
                                        trade_logger.log_tp_sl(signal['take_profit'], signal['stop_loss'])
                                        
                                        logger.info(f"Order placed successfully: Trade ID {trade_id}")
                                        last_signal_check = datetime.utcnow()  # Reset timer
                                        
                                    except Exception as e:
                                        logger.error(f"Error placing order: {e}")
                                        trade_logger.log_error(f"Order placement failed: {str(e)[:50]}")
                        else:
                            logger.debug("No trading signal generated")
                            last_signal_check = datetime.utcnow()  # Reset timer even if no signal
                
                # Sleep for 1 minute (monitor positions every minute)
                time.sleep(60)
                
            except KeyboardInterrupt:
                logger.info("Received interrupt signal, shutting down...")
                break
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                trade_logger.log_error(f"Main loop error: {str(e)[:50]}")
                time.sleep(60)  # Wait 1 minute before retry
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

