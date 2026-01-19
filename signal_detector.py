"""
Signal Detector Module
Detects buy/sell signals based on RSI strategy
"""

import pandas as pd
import logging
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def filter_trading_hours(df):
    """
    Filter dataframe to only include London session hours (8 AM - 5 PM UTC)
    
    Args:
        df: pandas.DataFrame with 'datetime' column
    
    Returns:
        pandas.DataFrame filtered to trading hours
    """
    try:
        if 'datetime' not in df.columns:
            raise ValueError("DataFrame must have 'datetime' column")
        
        # Ensure datetime is timezone-aware
        df = df.copy()
        df['datetime'] = pd.to_datetime(df['datetime'], utc=True)
        
        # Extract hour
        df['hour'] = df['datetime'].dt.hour
        
        # Filter to trading hours
        filtered = df[(df['hour'] >= config.TRADING_START_HOUR) & (df['hour'] < config.TRADING_END_HOUR)].copy()
        filtered = filtered.drop('hour', axis=1)
        
        logger.info(f"Filtered to trading hours: {len(filtered)} rows (from {len(df)} total)")
        
        return filtered
        
    except Exception as e:
        logger.error(f"Error filtering trading hours: {str(e)}")
        raise


def detect_buy_signals(df):
    """
    Detect BUY signals based on VWAP + RSI Hybrid strategy:
    - Price closes BELOW Lower Band (VWAP - 2.0 SD) AND
    - RSI ≤ 30 (oversold confirmation)
    - BOTH conditions must be true (higher quality signals)
    
    Args:
        df: pandas.DataFrame with 'close', 'vwap_lower', and 'rsi_14' columns
    
    Returns:
        pandas.Series with boolean buy signals
    """
    try:
        required_cols = ['close', 'vwap_lower', 'rsi_14']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"DataFrame must have columns: {required_cols}")
        
        # BUY signal: price below VWAP lower band AND RSI oversold
        vwap_signal = df['close'] < df['vwap_lower']
        rsi_signal = df['rsi_14'] <= config.RSI_BUY_THRESHOLD
        
        # Both conditions must be true
        buy_signals = vwap_signal & rsi_signal
        
        # Remove NaN values
        buy_signals = buy_signals.fillna(False)
        
        signal_count = buy_signals.sum()
        vwap_only = vwap_signal.sum()
        rsi_only = rsi_signal.sum()
        logger.info(f"Detected {signal_count} BUY signals (VWAP + RSI hybrid)")
        logger.info(f"  VWAP only: {vwap_only}, RSI only: {rsi_only}, Combined: {signal_count}")
        
        return buy_signals
        
    except Exception as e:
        logger.error(f"Error detecting BUY signals: {str(e)}")
        raise


def detect_sell_signals(df):
    """
    Detect SELL signals based on VWAP + RSI Hybrid strategy:
    - Price closes ABOVE Upper Band (VWAP + 2.0 SD) AND
    - RSI ≥ 70 (overbought confirmation)
    - BOTH conditions must be true (higher quality signals)
    
    Args:
        df: pandas.DataFrame with 'close', 'vwap_upper', and 'rsi_14' columns
    
    Returns:
        pandas.Series with boolean sell signals
    """
    try:
        required_cols = ['close', 'vwap_upper', 'rsi_14']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"DataFrame must have columns: {required_cols}")
        
        # SELL signal: price above VWAP upper band AND RSI overbought
        vwap_signal = df['close'] > df['vwap_upper']
        rsi_signal = df['rsi_14'] >= config.RSI_SELL_THRESHOLD
        
        # Both conditions must be true
        sell_signals = vwap_signal & rsi_signal
        
        # Remove NaN values
        sell_signals = sell_signals.fillna(False)
        
        signal_count = sell_signals.sum()
        vwap_only = vwap_signal.sum()
        rsi_only = rsi_signal.sum()
        logger.info(f"Detected {signal_count} SELL signals (VWAP + RSI hybrid)")
        logger.info(f"  VWAP only: {vwap_only}, RSI only: {rsi_only}, Combined: {signal_count}")
        
        return sell_signals
        
    except Exception as e:
        logger.error(f"Error detecting SELL signals: {str(e)}")
        raise


def add_signals(df):
    """
    Add buy and sell signals to dataframe
    
    Args:
        df: pandas.DataFrame with indicator columns
    
    Returns:
        pandas.DataFrame with added signal columns
    """
    try:
        logger.info("Detecting trading signals...")
        
        # Filter to trading hours first
        df_trading = filter_trading_hours(df)
        
        # Detect signals
        buy_signals = detect_buy_signals(df_trading)
        sell_signals = detect_sell_signals(df_trading)
        
        # Add signals to original dataframe (initialize as False)
        df['buy_signal'] = False
        df['sell_signal'] = False
        
        # Map signals back to original dataframe
        df.loc[df_trading.index, 'buy_signal'] = buy_signals
        df.loc[df_trading.index, 'sell_signal'] = sell_signals
        
        total_signals = df['buy_signal'].sum() + df['sell_signal'].sum()
        logger.info(f"Total signals detected: {total_signals} (BUY: {df['buy_signal'].sum()}, SELL: {df['sell_signal'].sum()})")
        
        return df
        
    except Exception as e:
        logger.error(f"Error adding signals: {str(e)}")
        raise


def main():
    """Main function to detect signals"""
    import os
    
    try:
        logger.info("=" * 70)
        logger.info("SIGNAL DETECTOR")
        logger.info("=" * 70)
        
        # Load data with indicators
        if not os.path.exists(config.INDICATORS_FILE):
            raise FileNotFoundError(f"Indicators file not found: {config.INDICATORS_FILE}")
        
        logger.info(f"Loading data from {config.INDICATORS_FILE}...")
        df = pd.read_csv(config.INDICATORS_FILE)
        df['datetime'] = pd.to_datetime(df['datetime'], utc=True)
        
        logger.info(f"Loaded {len(df)} rows")
        
        # Add signals
        df = add_signals(df)
        
        # Save data with signals
        os.makedirs(os.path.dirname(config.SIGNALS_FILE), exist_ok=True)
        df.to_csv(config.SIGNALS_FILE, index=False)
        logger.info(f"Data with signals saved to {config.SIGNALS_FILE}")
        
        logger.info("Signal detection completed successfully")
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        raise


if __name__ == "__main__":
    main()

