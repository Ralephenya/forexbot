"""
Risk management module
"""
import logging
from datetime import datetime
from typing import Dict
from database import Database

logger = logging.getLogger(__name__)


class RiskManager:
    """Risk management and safety features"""
    
    def __init__(self, config: dict, database: Database):
        """
        Initialize risk manager
        
        Args:
            config: Configuration dictionary
            database: Database instance
        """
        self.config = config
        self.risk_config = config.get('risk', {})
        self.db = database
    
    def check_daily_loss(self) -> float:
        """
        Calculate today's P&L
        
        Returns:
            Total P&L for today
        """
        today = datetime.utcnow().strftime('%Y-%m-%d')
        daily_pnl = self.db.get_daily_pnl(today)
        return daily_pnl
    
    def can_trade(self) -> bool:
        """
        Check if trading is allowed based on all risk constraints
        
        Returns:
            True if trading is allowed
        """
        # Check kill switch
        if self.is_kill_switch_enabled():
            logger.warning("Kill switch is enabled")
            return False
        
        # Check daily loss limit
        daily_pnl = self.check_daily_loss()
        max_daily_loss = self.risk_config.get('max_daily_loss', 5.0)  # Positive value
        
        # Check if loss exceeds limit (daily_pnl is negative when losing)
        if daily_pnl < 0 and abs(daily_pnl) >= max_daily_loss:
            logger.warning(f"Daily loss limit reached: ${daily_pnl:.2f} (limit: -${max_daily_loss:.2f})")
            return False
        
        # Check demo mode
        if not self.risk_config.get('demo_mode', True):
            logger.warning("Not in demo mode - ensure this is intentional")
        
        return True
    
    def is_kill_switch_enabled(self) -> bool:
        """
        Check if kill switch is enabled
        
        Returns:
            True if kill switch is enabled
        """
        kill_switch = self.db.get_system_state('kill_switch', 'false')
        return kill_switch.lower() == 'true'
    
    def set_kill_switch(self, enabled: bool):
        """
        Enable/disable kill switch
        
        Args:
            enabled: True to enable kill switch
        """
        self.db.update_system_state('kill_switch', 'true' if enabled else 'false')
        logger.info(f"Kill switch {'enabled' if enabled else 'disabled'}")
    
    def validate_position_size(self, units: int) -> bool:
        """
        Validate position size is within limits
        
        Args:
            units: Position size in units
            
        Returns:
            True if position size is valid
        """
        max_position_size = self.risk_config.get('position_size', 0.01)
        
        # Convert units to lots (for EUR/USD, 1 lot = 100,000 units)
        lots = abs(units) / 100000
        
        if lots > max_position_size:
            logger.warning(f"Position size {lots:.4f} lots exceeds max {max_position_size} lots")
            return False
        
        return True
    
    def check_max_open_positions(self, current_count: int) -> bool:
        """
        Check if we can open another position
        
        Args:
            current_count: Current number of open positions
            
        Returns:
            True if we can open another position
        """
        max_open = self.risk_config.get('max_positions', 1)
        
        if current_count >= max_open:
            logger.warning(f"Max open positions reached: {current_count} >= {max_open}")
            return False
        
        return True
    
    def calculate_position_size(self, account_balance: float) -> int:
        """
        Calculate position size based on risk parameters
        
        Args:
            account_balance: Account balance
            
        Returns:
            Position size in units
        """
        max_position_size_lots = self.risk_config.get('position_size', 0.01)
        
        # Convert lots to units (1 lot = 100,000 units for EUR/USD)
        units = int(max_position_size_lots * 100000)
        
        return units






