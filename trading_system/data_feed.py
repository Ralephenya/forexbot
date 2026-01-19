"""
Market data feed module for MT5
"""
import logging
import time
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


class DataFeed:
    """MT5 market data feed"""
    
    def __init__(self, broker_client, symbol: str, timeframe: str):
        """
        Initialize data feed
        
        Args:
            broker_client: Broker client instance (MT5)
            symbol: Trading instrument (e.g., EURUSD)
            timeframe: Timeframe (e.g., 15 for M15, or "M15")
        """
        self.broker = broker_client
        self.symbol = symbol
        self.timeframe = timeframe
        self.cache = {}  # Cache for recent candles
        self.cache_size = 100
    
    def fetch_candles(self, count: int = 100, from_time: Optional[str] = None) -> pd.DataFrame:
        """
        Fetch historical candles from MT5
        
        Args:
            count: Number of candles to fetch
            from_time: Start time (ISO format), optional
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            # Use broker's get_candles method
            df = self.broker.get_candles(self.symbol, count, self.timeframe, from_time)
            
            # Update cache
            cache_key = f"{count}_{from_time}"
            self.cache[cache_key] = {
                'data': df,
                'timestamp': datetime.utcnow()
            }
            
            # Limit cache size
            if len(self.cache) > 10:
                oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]['timestamp'])
                del self.cache[oldest_key]
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching candles: {e}")
            raise
    
    def get_latest_candle(self) -> Optional[pd.Series]:
        """
        Get the most recent completed candle
        
        Returns:
            Series with latest candle data or None
        """
        try:
            # Fetch last 2 candles (to ensure we have the latest completed one)
            df = self.fetch_candles(count=2)
            
            if df.empty:
                return None
            
            # Return the second-to-last candle (most recent completed)
            # The last candle might still be forming
            if len(df) >= 2:
                return df.iloc[-2]
            else:
                return df.iloc[-1]
                
        except Exception as e:
            logger.error(f"Error getting latest candle: {e}")
            return None
    
    def get_candle_history(self, count: int = 100) -> pd.DataFrame:
        """
        Get historical candle data
        
        Args:
            count: Number of candles to retrieve
            
        Returns:
            DataFrame with OHLCV data
        """
        return self.fetch_candles(count=count)
    
    def is_cache_valid(self, cache_key: str, max_age_seconds: int = 60) -> bool:
        """
        Check if cached data is still valid
        
        Args:
            cache_key: Cache key
            max_age_seconds: Maximum age in seconds
            
        Returns:
            True if cache is valid
        """
        if cache_key not in self.cache:
            return False
        
        cache_age = (datetime.utcnow() - self.cache[cache_key]['timestamp']).total_seconds()
        return cache_age < max_age_seconds






