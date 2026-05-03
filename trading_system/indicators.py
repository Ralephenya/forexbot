"""
Technical indicator calculations
"""
import pandas as pd
import numpy as np
import logging
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange
from ta.trend import EMAIndicator, MACD

logger = logging.getLogger(__name__)


def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate RSI (Relative Strength Index)
    
    Args:
        df: DataFrame with OHLCV data
        period: RSI period (default 14)
        
    Returns:
        Series with RSI values
    """
    if 'close' not in df.columns:
        raise ValueError("DataFrame must have 'close' column")
    
    rsi_indicator = RSIIndicator(close=df['close'], window=period)
    rsi = rsi_indicator.rsi()
    
    return rsi


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate ATR (Average True Range)
    
    Args:
        df: DataFrame with OHLCV data
        period: ATR period (default 14)
        
    Returns:
        Series with ATR values
    """
    required_cols = ['high', 'low', 'close']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"DataFrame must have {required_cols} columns")
    
    atr_indicator = AverageTrueRange(
        high=df['high'],
        low=df['low'],
        close=df['close'],
        window=period
    )
    atr = atr_indicator.average_true_range()
    
    return atr


def calculate_ema(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """
    Calculate EMA (Exponential Moving Average)
    
    Args:
        df: DataFrame with OHLCV data
        period: EMA period (default 20)
        
    Returns:
        Series with EMA values
    """
    if 'close' not in df.columns:
        raise ValueError("DataFrame must have 'close' column")
    
    ema_indicator = EMAIndicator(close=df['close'], window=period)
    ema = ema_indicator.ema_indicator()
    
    return ema


def determine_volatility_regime(
    df: pd.DataFrame,
    atr_period: int = 14,
    median_window: int = 20
) -> pd.Series:
    """
    Determine volatility regime (high/low) based on ATR vs median ATR
    
    Args:
        df: DataFrame with OHLCV data
        atr_period: ATR calculation period
        median_window: Window for median ATR calculation
        
    Returns:
        Series of boolean values (True = high volatility, False = low volatility)
    """
    if 'atr' not in df.columns:
        df = df.copy()
        df['atr'] = calculate_atr(df, atr_period)
    
    # Calculate rolling median of ATR
    atr_median = df['atr'].rolling(window=median_window).median()
    
    # High volatility when current ATR > median ATR
    is_high_volatility = df['atr'] > atr_median
    
    return is_high_volatility


def calculate_macd(
    df: pd.DataFrame,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9
) -> pd.DataFrame:
    """
    Calculate MACD, Signal line, and Histogram.

    MACD is one of the best momentum confirmation tools.
    When MACD crosses above signal → momentum shifting bullish.
    When MACD crosses below signal → momentum shifting bearish.

    Args:
        df: DataFrame with OHLCV data
        fast: Fast EMA period
        slow: Slow EMA period
        signal: Signal line period

    Returns:
        DataFrame with macd, macd_signal, macd_hist columns added
    """
    if 'close' not in df.columns:
        raise ValueError("DataFrame must have 'close' column")

    macd_indicator = MACD(
        close=df['close'],
        window_fast=fast,
        window_slow=slow,
        window_sign=signal
    )

    df = df.copy()
    df['macd']        = macd_indicator.macd()
    df['macd_signal'] = macd_indicator.macd_signal()
    df['macd_hist']   = macd_indicator.macd_diff()

    return df


def calculate_all_indicators(
    df: pd.DataFrame,
    rsi_period: int = 14,
    atr_period: int = 14,
    ema_period: int = 20,
    atr_median_window: int = 20,
    add_confluence_indicators: bool = True
) -> pd.DataFrame:
    """
    Calculate all indicators and add to DataFrame.

    Args:
        df: DataFrame with OHLCV data
        rsi_period: RSI period
        atr_period: ATR period
        ema_period: EMA period
        atr_median_window: Window for volatility regime detection
        add_confluence_indicators: Add EMA50/200 and MACD for confluence scoring

    Returns:
        DataFrame with indicators added
    """
    df = df.copy()

    # Core indicators (always calculated)
    df['rsi'] = calculate_rsi(df, rsi_period)
    df['atr'] = calculate_atr(df, atr_period)
    df['ema'] = calculate_ema(df, ema_period)
    df['is_high_volatility'] = determine_volatility_regime(
        df, atr_period, atr_median_window
    )

    # Confluence indicators (hedge fund grade)
    if add_confluence_indicators and len(df) >= 200:
        # Higher timeframe trend proxies — need 200+ candles
        df['ema_50']  = calculate_ema(df, 50)
        df['ema_200'] = calculate_ema(df, 200)
        df = calculate_macd(df)
    elif add_confluence_indicators and len(df) >= 50:
        # Fallback: only EMA50 if not enough data for EMA200
        df['ema_50'] = calculate_ema(df, 50)
        df = calculate_macd(df)

    return df




















