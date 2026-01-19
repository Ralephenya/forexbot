"""
SMS notification module using Twilio
"""
import logging
from datetime import datetime
from typing import Optional, Dict
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
import time

logger = logging.getLogger(__name__)


class Notifier:
    """SMS notifications via Twilio"""
    
    def __init__(self, config: dict):
        """
        Initialize notifier
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.notification_config = config.get('notifications', {})
        self.enabled = self.notification_config.get('enabled', False)
        
        # Rate limiting
        self.last_notification_time = {}
        self.min_notification_interval = 60  # 1 minute
        
        if self.enabled and self.notification_config.get('provider') == 'twilio':
            try:
                self.client = Client(
                    self.notification_config.get('twilio_account_sid'),
                    self.notification_config.get('twilio_auth_token')
                )
                self.from_number = self.notification_config.get('twilio_from_number')
                self.phone_number = self.notification_config.get('phone_number')
                logger.info("Twilio client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio: {e}")
                self.enabled = False
        else:
            self.client = None
            self.from_number = None
            self.phone_number = None
    
    def _can_send_notification(self, notification_type: str) -> bool:
        """
        Check if we can send notification (rate limiting)
        
        Args:
            notification_type: Type of notification
            
        Returns:
            True if notification can be sent
        """
        if not self.enabled:
            return False
        
        now = time.time()
        last_time = self.last_notification_time.get(notification_type, 0)
        
        if now - last_time < self.min_notification_interval:
            return False
        
        self.last_notification_time[notification_type] = now
        return True
    
    def send_sms(self, message: str, notification_type: str = "general") -> bool:
        """
        Send SMS notification
        
        Args:
            message: Message to send
            notification_type: Type of notification (for rate limiting)
            
        Returns:
            True if sent successfully
        """
        if not self.enabled or not self.client:
            logger.debug(f"SMS disabled, would send: {message}")
            return False
        
        if not self._can_send_notification(notification_type):
            logger.debug(f"Rate limited for {notification_type}")
            return False
        
        try:
            self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=self.phone_number
            )
            logger.info(f"SMS sent: {message[:50]}...")
            return True
        except TwilioException as e:
            logger.error(f"Failed to send SMS: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending SMS: {e}")
            return False
    
    def notify_signal(self, signal_type: str, price: float, instrument: str = "EUR_USD"):
        """Notify about trading signal"""
        message = f"Trading Signal: {signal_type} {instrument} @ {price:.5f}"
        self.send_sms(message, "signal")
    
    def notify_order_placed(self, order_details: dict, signal: dict = None):
        """Notify about order placement"""
        instrument = order_details.get('instrument', 'EURUSD')
        volume = order_details.get('volume', order_details.get('units', 0))
        direction_str = signal.get('direction', 'BUY') if signal else ("BUY" if volume > 0 else "SELL")
        price = order_details.get('price', 0)
        tp = order_details.get('take_profit', signal.get('take_profit', 0)) if signal else order_details.get('take_profit', 0)
        sl = order_details.get('stop_loss', signal.get('stop_loss', 0)) if signal else order_details.get('stop_loss', 0)
        regime = signal.get('volatility_regime', '') if signal else ''
        
        # Calculate pips
        pip_value = 0.0001
        tp_pips = ((tp - price) / pip_value) if direction_str == "BUY" else ((price - tp) / pip_value)
        sl_pips = ((price - sl) / pip_value) if direction_str == "BUY" else ((sl - price) / pip_value)
        
        mode_text = f"Mode: {regime} Vol {'Mean Reversion' if regime == 'HIGH' else 'Breakout'}" if regime else ""
        
        message = f"🟢 {instrument} {direction_str}\n"
        if mode_text:
            message += f"{mode_text}\n"
        message += f"Entry: {price:.5f}\n"
        message += f"TP: {tp:.5f} (+{tp_pips:.1f} pips)\n"
        message += f"SL: {sl:.5f} (-{sl_pips:.1f} pips)\n"
        message += f"Time: {datetime.utcnow().strftime('%H:%M')} UTC"
        
        self.send_sms(message, "order")
    
    def notify_position_closed(self, position: dict, pnl: float):
        """Notify about position closure"""
        instrument = position.get('instrument', 'EUR_USD')
        pnl_str = f"+${pnl:.2f}" if pnl >= 0 else f"-${abs(pnl):.2f}"
        
        message = f"Position Closed: {instrument} P&L: {pnl_str}"
        self.send_sms(message, "position")
    
    def notify_error(self, error_message: str):
        """Notify about errors"""
        message = f"Trading System Error: {error_message[:100]}"
        self.send_sms(message, "error")
    
    def notify_daily_summary(self, pnl: float, trades_count: int, win_count: int = None, loss_count: int = None, win_rate: float = None, week_pnl: float = None, week_wins: int = None, week_losses: int = None):
        """Send end-of-day summary"""
        pnl_str = f"+${pnl:.2f}" if pnl >= 0 else f"-${abs(pnl):.2f}"
        date_str = datetime.utcnow().strftime('%Y-%m-%d')
        
        message = f"📊 Strategy B Daily\nDate: {date_str}\n"
        message += f"Signals: {trades_count}\n"
        if win_count is not None and loss_count is not None:
            message += f"Trades: {win_count}W-{loss_count}L\n"
        message += f"P&L: {pnl_str}\n"
        if win_rate is not None:
            message += f"Win Rate: {win_rate:.1f}%\n"
        if week_pnl is not None:
            week_str = f"+${week_pnl:.2f}" if week_pnl >= 0 else f"-${abs(week_pnl):.2f}"
            message += f"Week: {week_str}"
            if week_wins is not None and week_losses is not None:
                message += f" ({week_wins}W-{week_losses}L)"
        
        self.send_sms(message, "summary")






