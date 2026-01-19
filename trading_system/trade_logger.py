"""
Simple trade logger for formatted output
"""
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional


class TradeLogger:
    """Simple formatted trade logger"""
    
    def __init__(self, log_file: str = "./logs/trades.log"):
        """
        Initialize trade logger
        
        Args:
            log_file: Path to log file
        """
        self.log_file = log_file
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup simple file handler
        self.logger = logging.getLogger('trade_logger')
        self.logger.setLevel(logging.INFO)
        self.logger.handlers.clear()
        
        # File handler (append mode)
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Also output to console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def _format_time(self) -> str:
        """Format current time as [HH:MM]"""
        return datetime.utcnow().strftime('[%H:%M]')
    
    def log_signal(self, action: str, price: float, instrument: str = "EURUSD"):
        """Log signal generation"""
        message = f"{self._format_time()} Signal generated: {action} at {price:.4f}"
        self.logger.info(message)
    
    def log_position_opened(self, lots: float, instrument: str = "EURUSD"):
        """Log position opened"""
        message = f"{self._format_time()} Position opened: {lots:.2f} lots"
        self.logger.info(message)
    
    def log_tp_sl(self, tp: float, sl: float):
        """Log TP/SL levels"""
        message = f"{self._format_time()} TP: {tp:.4f}, SL: {sl:.4f}"
        self.logger.info(message)
    
    def log_position_monitoring(self, pips: float, pnl: float, current_price: Optional[float] = None):
        """Log position monitoring update"""
        pips_str = f"{pips:+.1f}" if pips >= 0 else f"{pips:.1f}"
        pnl_str = f"+${pnl:.2f}" if pnl >= 0 else f"-${abs(pnl):.2f}"
        message = f"{self._format_time()} Position monitoring: {pips_str} pips ({pnl_str})"
        if current_price:
            message += f" @ {current_price:.4f}"
        self.logger.info(message)
    
    def log_position_closed(self, pips: float, pnl: float, exit_reason: str = "TP/SL"):
        """Log position closed"""
        pips_str = f"{pips:+.1f}" if pips >= 0 else f"{pips:.1f}"
        pnl_str = f"+${pnl:.2f}" if pnl >= 0 else f"-${abs(pnl):.2f}"
        message = f"{self._format_time()} Position closed: {pips_str} pips ({pnl_str}) - {exit_reason}"
        self.logger.info(message)
    
    def log_info(self, message: str):
        """Log general info message"""
        self.logger.info(f"{self._format_time()} {message}")
    
    def log_error(self, message: str):
        """Log error message"""
        self.logger.error(f"{self._format_time()} ERROR: {message}")















