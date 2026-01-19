"""
Technical indicator calculations
"""
import pandas as pd
import numpy as np
import logging
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange
from ta.trend import EMAIndicator

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


def calculate_all_indicators(
    df: pd.DataFrame,
    rsi_period: int = 14,
    atr_period: int = 14,
    ema_period: int = 20,
    atr_median_window: int = 20
) -> pd.DataFrame:
    """
    Calculate all indicators and add to DataFrame
    
    Args:
        df: DataFrame with OHLCV data
        rsi_period: RSI period
        atr_period: ATR period
        ema_period: EMA period
        atr_median_window: Window for volatility regime detection
        
    Returns:
        DataFrame with indicators added
    """
    df = df.copy()
    
    # Calculate indicators
    df['rsi'] = calculate_rsi(df, rsi_period)
    df['atr'] = calculate_atr(df, atr_period)
    df['ema'] = calculate_ema(df, ema_period)
    df['is_high_volatility'] = determine_volatility_regime(
        df, atr_period, atr_median_window
    )
    
    return df




















