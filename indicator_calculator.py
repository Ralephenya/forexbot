"""
Indicator Calculator Module
Calculates Daily VWAP with Standard Deviation Bands AND RSI
VWAP resets daily at 00:00 UTC
Hybrid Strategy: VWAP + RSI Confirmation
"""

import pandas as pd
import numpy as np
import logging
from ta.momentum import RSIIndicator
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def calculate_daily_vwap(df, std_multiplier=1.5):
    """
    Calculate Daily VWAP with standard deviation bands
    VWAP resets at 00:00 UTC each day
    
    Args:
        df: pandas.DataFrame with 'datetime', 'open', 'high', 'low', 'close' columns
        std_multiplier: Multiplier for standard deviation bands (default: 1.5)
    
    Returns:
        pandas.DataFrame with added 'vwap', 'vwap_upper', 'vwap_lower' columns
    """
    try:
        if df.empty:
            raise ValueError("DataFrame is empty")
        
        required_cols = ['datetime', 'high', 'low', 'close']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"DataFrame must have columns: {required_cols}")
        
        logger.info(f"Calculating Daily VWAP for {len(df)} data points...")
        
        # Make a copy to avoid modifying original
        df = df.copy()
        
        # Ensure datetime is timezone-aware
        df['datetime'] = pd.to_datetime(df['datetime'], utc=True)
        df = df.sort_values('datetime').reset_index(drop=True)
        
        # Add date column (UTC date)
        df['date'] = df['datetime'].dt.date
        
        # Calculate typical price (H+L+C)/3
        df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3.0
        
        # For forex, we don't have volume, so we use tick volume (equal volume per candle)
        # This makes VWAP equivalent to a typical price moving average
        df['volume'] = 1.0
        
        # Initialize VWAP columns
        df['vwap'] = np.nan
        df['vwap_upper'] = np.nan
        df['vwap_lower'] = np.nan
        
        # Calculate VWAP for each day
        unique_dates = df['date'].unique()
        logger.info(f"Calculating VWAP for {len(unique_dates)} trading days...")
        
        for date in unique_dates:
            # Get all candles for this day
            day_mask = df['date'] == date
            day_data = df[day_mask].copy()
            
            if len(day_data) == 0:
                continue
            
            # Calculate cumulative VWAP for the day
            # VWAP = Σ(Price × Volume) / Σ(Volume)
            typical_price = day_data['typical_price'].values
            volume = day_data['volume'].values
            
            # Cumulative sum of (price * volume) and cumulative sum of volume
            cum_price_volume = np.cumsum(typical_price * volume)
            cum_volume = np.cumsum(volume)
            
            # Calculate VWAP (avoid division by zero)
            vwap_values = np.where(cum_volume > 0, cum_price_volume / cum_volume, typical_price)
            
            # Calculate standard deviation of prices from VWAP
            # For each point, calculate distance from current VWAP
            std_values = []
            for i in range(len(day_data)):
                if i == 0:
                    std_values.append(0.0)
                else:
                    # Calculate std of typical prices up to this point
                    prices_so_far = typical_price[:i+1]
                    vwap_current = vwap_values[i]
                    distances = np.abs(prices_so_far - vwap_current)
                    std = np.std(distances) if len(distances) > 1 else 0.0
                    std_values.append(std)
            
            std_values = np.array(std_values)
            
            # Calculate bands
            vwap_upper = vwap_values + (std_multiplier * std_values)
            vwap_lower = vwap_values - (std_multiplier * std_values)
            
            # Assign to dataframe
            day_indices = day_data.index
            df.loc[day_indices, 'vwap'] = vwap_values
            df.loc[day_indices, 'vwap_upper'] = vwap_upper
            df.loc[day_indices, 'vwap_lower'] = vwap_lower
        
        # Drop temporary columns
        df = df.drop(['date', 'typical_price', 'volume'], axis=1)
        
        # Count NaN values
        vwap_nans = df['vwap'].isna().sum()
        logger.info(f"Daily VWAP calculated. NaN values: {vwap_nans} (expected at start)")
        
        return df
        
    except Exception as e:
        logger.error(f"Error calculating Daily VWAP: {str(e)}")
        import traceback
        logger.debug(traceback.format_exc())
        raise


def calculate_rsi(df, period, column='close'):
    """
    Calculate Relative Strength Index (RSI)
    
    Args:
        df: pandas.DataFrame with price data
        period: Period for RSI calculation
        column: Column name to use for calculation (default: 'close')
    
    Returns:
        pandas.Series with RSI values
    """
    try:
        rsi_indicator = RSIIndicator(close=df[column], window=period)
        return rsi_indicator.rsi()
    except Exception as e:
        logger.error(f"Error calculating RSI({period}): {str(e)}")
        raise


def add_indicators(df, std_multiplier=2.0, rsi_period=14):
    """
    Add Daily VWAP and RSI indicators to dataframe (Hybrid Strategy)
    
    Args:
        df: pandas.DataFrame with price data
        std_multiplier: Standard deviation multiplier for VWAP bands (default: 2.0)
        rsi_period: Period for RSI calculation (default: 14)
    
    Returns:
        pandas.DataFrame with added VWAP and RSI indicator columns
    """
    try:
        if df.empty:
            raise ValueError("DataFrame is empty")
        
        logger.info(f"Calculating indicators for {len(df)} data points...")
        logger.info(f"Calculating VWAP (SD={std_multiplier}) and RSI({rsi_period})...")
        
        # Make a copy to avoid modifying original
        df = df.copy()
        
        # Ensure datetime is timezone-aware
        if 'datetime' in df.columns:
            df['datetime'] = pd.to_datetime(df['datetime'], utc=True)
        
        # Calculate Daily VWAP (needs datetime as column, not index)
        df = calculate_daily_vwap(df, std_multiplier)
        
        # Set datetime as index for RSI calculation (ta library works better with index)
        if 'datetime' in df.columns:
            df_indexed = df.set_index('datetime').sort_index()
        else:
            df_indexed = df.copy()
        
        # Calculate RSI
        logger.info(f"Calculating RSI({rsi_period})...")
        df_indexed['rsi_14'] = calculate_rsi(df_indexed, rsi_period)
        
        # Reset index to have datetime as column
        df_result = df_indexed.reset_index()
        
        # Count NaN values
        vwap_nans = df_result['vwap'].isna().sum()
        rsi_nans = df_result['rsi_14'].isna().sum()
        logger.info(f"VWAP calculated. NaN values: {vwap_nans}")
        logger.info(f"RSI({rsi_period}) calculated. NaN values: {rsi_nans}")
        
        return df_result
        
    except Exception as e:
        logger.error(f"Error adding indicators: {str(e)}")
        raise


def main():
    """Main function to calculate indicators"""
    import os
    
    try:
        logger.info("=" * 70)
        logger.info("INDICATOR CALCULATOR - VWAP + RSI HYBRID STRATEGY")
        logger.info("=" * 70)
        
        # Load data
        if not os.path.exists(config.DATA_FILE):
            raise FileNotFoundError(f"Data file not found: {config.DATA_FILE}")
        
        logger.info(f"Loading data from {config.DATA_FILE}...")
        df = pd.read_csv(config.DATA_FILE)
        df['datetime'] = pd.to_datetime(df['datetime'], utc=True)
        
        logger.info(f"Loaded {len(df)} rows")
        
        # Add indicators (both VWAP and RSI for hybrid strategy)
        df = add_indicators(df, std_multiplier=config.VWAP_STD_MULTIPLIER, rsi_period=config.RSI_PERIOD)
        
        # Save enriched data
        os.makedirs(os.path.dirname(config.INDICATORS_FILE), exist_ok=True)
        df.to_csv(config.INDICATORS_FILE, index=False)
        logger.info(f"Data with indicators saved to {config.INDICATORS_FILE}")
        
        logger.info("Indicator calculation completed successfully")
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        raise


if __name__ == "__main__":
    main()
