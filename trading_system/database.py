"""
Database module for storing trades and system state
"""
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)


class Database:
    """SQLite database for trade history and system state"""
    
    def __init__(self, db_path: str):
        """
        Initialize database connection
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        db_dir = Path(db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        self._init_schema()
    
    def _get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_schema(self):
        """Initialize database schema"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Trades table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                instrument TEXT NOT NULL,
                direction TEXT NOT NULL,
                entry_price REAL NOT NULL,
                exit_price REAL,
                units INTEGER NOT NULL,
                take_profit REAL,
                stop_loss REAL,
                pnl REAL,
                pips REAL,
                exit_reason TEXT,
                status TEXT NOT NULL,
                strategy_name TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Daily summary table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL UNIQUE,
                total_pnl REAL,
                trades_count INTEGER,
                win_rate REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # System state table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {self.db_path}")
    
    def save_trade(self, trade_data: dict) -> int:
        """
        Save trade to database
        
        Args:
            trade_data: Dictionary with trade information
            
        Returns:
            Trade ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO trades (
                timestamp, instrument, direction, entry_price, exit_price,
                units, take_profit, stop_loss, pnl, pips, exit_reason,
                status, strategy_name
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trade_data.get('timestamp'),
            trade_data.get('instrument'),
            trade_data.get('direction'),
            trade_data.get('entry_price'),
            trade_data.get('exit_price'),
            trade_data.get('units'),
            trade_data.get('take_profit'),
            trade_data.get('stop_loss'),
            trade_data.get('pnl'),
            trade_data.get('pips'),
            trade_data.get('exit_reason'),
            trade_data.get('status', 'OPEN'),
            trade_data.get('strategy_name')
        ))
        
        trade_id = cursor.lastrowid
        conn.commit()
        conn.close()
        logger.debug(f"Trade saved with ID: {trade_id}")
        return trade_id
    
    def update_trade(self, trade_id: int, trade_data: dict):
        """
        Update existing trade
        
        Args:
            trade_id: Trade ID to update
            trade_data: Dictionary with fields to update
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        updates = []
        values = []
        for key, value in trade_data.items():
            if key in ['exit_price', 'pnl', 'pips', 'exit_reason', 'status']:
                updates.append(f"{key} = ?")
                values.append(value)
        
        if updates:
            values.append(trade_id)
            query = f"UPDATE trades SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, values)
            conn.commit()
        
        conn.close()
        logger.debug(f"Trade {trade_id} updated")
    
    def get_daily_pnl(self, date: Optional[str] = None) -> float:
        """
        Calculate daily P&L
        
        Args:
            date: Date string (YYYY-MM-DD), defaults to today
            
        Returns:
            Total P&L for the day
        """
        if date is None:
            date = datetime.utcnow().strftime('%Y-%m-%d')
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COALESCE(SUM(pnl), 0) as total_pnl
            FROM trades
            WHERE DATE(timestamp) = ? AND status = 'CLOSED'
        """, (date,))
        
        result = cursor.fetchone()
        total_pnl = result['total_pnl'] if result else 0.0
        conn.close()
        return total_pnl
    
    def get_trade_history(self, limit: int = 100) -> List[Dict]:
        """
        Get recent trade history
        
        Args:
            limit: Maximum number of trades to return
            
        Returns:
            List of trade dictionaries
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM trades
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        trades = [dict(row) for row in rows]
        conn.close()
        return trades
    
    def get_open_trades(self) -> List[Dict]:
        """
        Get all open trades
        
        Returns:
            List of open trade dictionaries
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM trades
            WHERE status = 'OPEN'
            ORDER BY created_at DESC
        """)
        
        rows = cursor.fetchall()
        trades = [dict(row) for row in rows]
        conn.close()
        return trades
    
    def update_system_state(self, key: str, value: str):
        """
        Update system state
        
        Args:
            key: State key
            value: State value
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO system_state (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (key, value))
        
        conn.commit()
        conn.close()
        logger.debug(f"System state updated: {key} = {value}")
    
    def get_system_state(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get system state value
        
        Args:
            key: State key
            default: Default value if key doesn't exist
            
        Returns:
            State value or default
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT value FROM system_state WHERE key = ?", (key,))
        result = cursor.fetchone()
        conn.close()
        
        return result['value'] if result else default




















