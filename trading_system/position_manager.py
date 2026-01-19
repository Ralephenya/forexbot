"""
Position management module
"""
import logging
from datetime import datetime
from typing import Optional, Dict, List
from database import Database

logger = logging.getLogger(__name__)


class PositionManager:
    """Manage trading positions"""
    
    def __init__(self, database: Database, broker):
        """
        Initialize position manager
        
        Args:
            database: Database instance
            broker: Broker client instance
        """
        self.db = database
        self.broker = broker
    
    def has_open_position(self, instrument: Optional[str] = None) -> bool:
        """
        Check if there's an open position
        
        Args:
            instrument: Optional instrument filter
            
        Returns:
            True if position exists
        """
        open_trades = self.db.get_open_trades()
        
        if instrument:
            open_trades = [t for t in open_trades if t['instrument'] == instrument]
        
        return len(open_trades) > 0
    
    def get_open_position(self, instrument: Optional[str] = None) -> Optional[Dict]:
        """
        Get current open position
        
        Args:
            instrument: Optional instrument filter
            
        Returns:
            Position dictionary or None
        """
        open_trades = self.db.get_open_trades()
        
        if instrument:
            open_trades = [t for t in open_trades if t['instrument'] == instrument]
        
        if open_trades:
            return open_trades[0]
        
        return None
    
    def open_position(self, order_response: Dict, signal: Dict) -> int:
        """
        Store new position in database
        
        Args:
            order_response: Order response from broker
            signal: Signal dictionary
            
        Returns:
            Trade ID
        """
        trade_data = {
            'timestamp': order_response.get('time', datetime.utcnow().isoformat()),
            'instrument': order_response.get('instrument'),
            'direction': signal.get('direction'),
            'entry_price': order_response.get('price', signal.get('entry_price')),
            'units': abs(order_response.get('volume', 0)) if 'volume' in order_response else abs(order_response.get('units', 0)),
            'take_profit': signal.get('take_profit'),
            'stop_loss': signal.get('stop_loss'),
            'status': 'OPEN',
            'strategy_name': 'strategy_b'
        }
        
        trade_id = self.db.save_trade(trade_data)
        logger.info(f"Position opened: Trade ID {trade_id}")
        return trade_id
    
    def close_position(self, trade_id: int, exit_price: float, exit_reason: str):
        """
        Mark position as closed
        
        Args:
            trade_id: Trade ID
            exit_price: Exit price
            exit_reason: Reason for exit (TP, SL, MANUAL, etc.)
        """
        # Get trade details
        trades = self.db.get_trade_history(limit=1000)
        trade = next((t for t in trades if t['id'] == trade_id), None)
        
        if not trade:
            logger.error(f"Trade {trade_id} not found")
            return
        
        # Calculate P&L
        entry_price = trade['entry_price']
        direction = trade['direction']
        units = trade['units']
        
        # Calculate pips
        pip_value = 0.0001
        if direction == "BUY":
            pips = ((exit_price - entry_price) / pip_value)
        else:
            pips = ((entry_price - exit_price) / pip_value)
        
        # Calculate P&L (for EUR/USD, 1 pip = $0.10 per 0.01 lot)
        pnl = pips * 0.10 * units / 0.01
        
        # Update trade
        self.db.update_trade(trade_id, {
            'exit_price': exit_price,
            'pnl': pnl,
            'pips': pips,
            'exit_reason': exit_reason,
            'status': 'CLOSED'
        })
        
        logger.info(f"Position closed: Trade ID {trade_id}, P&L: ${pnl:.2f}, Pips: {pips:.1f}")
        
        # Note: Trade logger will be called from main.py after this
    
    def sync_with_broker(self, instrument: str):
        """
        Sync positions with broker (check for TP/SL hits)
        
        Args:
            instrument: Trading instrument
        """
        try:
            # Get broker positions
            broker_positions = self.broker.get_open_positions()
            broker_pos = next((p for p in broker_positions if p['instrument'] == instrument), None)
            
            # Get database positions
            db_positions = self.db.get_open_trades()
            db_pos = next((p for p in db_positions if p['instrument'] == instrument), None)
            
            # If broker has no position but DB does, position was closed
            if db_pos and not broker_pos:
                # Position was closed (likely by TP/SL)
                # We need to get the close price from broker history or use last known price
                logger.info(f"Position {db_pos['id']} appears to be closed by broker")
                # Note: In production, you'd query broker for the close transaction
                # For now, we'll mark it as closed when we detect it's missing
            
            # If broker has position but DB doesn't, sync it
            if broker_pos and not db_pos:
                logger.warning("Broker has position not in database, syncing...")
                # This shouldn't happen in normal operation, but handle it
                
        except Exception as e:
            logger.error(f"Error syncing with broker: {e}")






