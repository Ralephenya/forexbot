"""
Abstract broker interface
"""
from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, List, Optional


class BrokerInterface(ABC):
    """Abstract base class for broker implementations"""
    
    @abstractmethod
    def get_account_info(self) -> Dict:
        """
        Get account information (balance, margin, etc.)
        
        Returns:
            Dictionary with account information
        """
        pass
    
    @abstractmethod
    def get_current_price(self, instrument: str) -> Dict:
        """
        Get current bid/ask price
        
        Args:
            instrument: Trading instrument (e.g., EUR_USD)
            
        Returns:
            Dictionary with bid, ask, and timestamp
        """
        pass
    
    @abstractmethod
    def place_market_order(
        self,
        instrument: str,
        units: int,
        direction: str,
        take_profit: Optional[float] = None,
        stop_loss: Optional[float] = None
    ) -> Dict:
        """
        Place a market order
        
        Args:
            instrument: Trading instrument
            units: Number of units (positive for buy, negative for sell)
            direction: 'BUY' or 'SELL'
            take_profit: Take profit price level
            stop_loss: Stop loss price level
            
        Returns:
            Dictionary with order details
        """
        pass
    
    @abstractmethod
    def get_open_positions(self) -> List[Dict]:
        """
        Get all open positions
        
        Returns:
            List of position dictionaries
        """
        pass
    
    @abstractmethod
    def close_position(self, position_id: str) -> Dict:
        """
        Close a specific position
        
        Args:
            position_id: Position ID to close
            
        Returns:
            Dictionary with close order details
        """
        pass
    
    @abstractmethod
    def get_candles(
        self,
        instrument: str,
        count: int,
        granularity: str,
        from_time: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get historical candle data
        
        Args:
            instrument: Trading instrument
            count: Number of candles to retrieve
            granularity: Timeframe (e.g., M15, H1)
            from_time: Start time (ISO format), optional
            
        Returns:
            DataFrame with OHLCV data
        """
        pass




















