"""
MetaTrader 5 client implementation for XM broker
"""
import MetaTrader5 as mt5
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from broker_interface import BrokerInterface

logger = logging.getLogger(__name__)


class MT5Client(BrokerInterface):
    """MetaTrader 5 client implementation for XM"""
    
    def __init__(self, account: int, password: str, server: str, path: str = ""):
        """
        Initialize MT5 client
        
        Args:
            account: MT5 account number
            password: MT5 account password
            server: Server name (e.g., "XM-Demo", "XM-Real")
            path: Path to MT5 terminal executable (empty for default)
        """
        self.account = account
        self.password = password
        self.server = server
        self.path = path
        self.connected = False
        self.magic_number = 234000  # Strategy B identifier
        
        # Initialize MT5
        self._initialize()
    
    def _initialize(self) -> bool:
        """Initialize MT5 connection"""
        try:
            # Initialize MT5
            if self.path:
                if not mt5.initialize(path=self.path):
                    logger.error(f"MT5 initialization failed: {mt5.last_error()}")
                    return False
            else:
                if not mt5.initialize():
                    logger.error(f"MT5 initialization failed: {mt5.last_error()}")
                    return False
            
            # Login
            if not mt5.login(self.account, password=self.password, server=self.server):
                logger.error(f"MT5 login failed: {mt5.last_error()}")
                mt5.shutdown()
                return False
            
            account_info = mt5.account_info()
            if account_info is None:
                logger.error("Failed to get account info")
                return False
            
            self.connected = True
            logger.info(f"MT5 connected successfully - Account: {self.account}, Server: {self.server}")
            logger.info(f"Account balance: ${account_info.balance:.2f}, Equity: ${account_info.equity:.2f}")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing MT5: {e}")
            return False
    
    def ensure_connected(self) -> bool:
        """
        Ensure MT5 connection is active, reconnect if needed
        
        Returns:
            True if connected
        """
        if not self.connected:
            return self._initialize()
        
        # Check if still connected by getting account info
        account_info = mt5.account_info()
        if account_info is None:
            logger.warning("MT5 connection lost, reconnecting...")
            self.connected = False
            return self._initialize()
        
        return True
    
    def get_account_info(self) -> Dict:
        """Get account information"""
        if not self.ensure_connected():
            raise Exception("MT5 not connected")
        
        account_info = mt5.account_info()
        if account_info is None:
            raise Exception(f"Failed to get account info: {mt5.last_error()}")
        
        return {
            'balance': account_info.balance,
            'equity': account_info.equity,
            'margin': account_info.margin,
            'free_margin': account_info.margin_free,
            'margin_level': account_info.margin_level,
            'currency': account_info.currency,
            'server': account_info.server,
            'leverage': account_info.leverage,
            'company': account_info.company
        }
    
    def get_current_price(self, instrument: str) -> Dict:
        """Get current bid/ask price"""
        if not self.ensure_connected():
            raise Exception("MT5 not connected")
        
        tick = mt5.symbol_info_tick(instrument)
        if tick is None:
            raise Exception(f"Failed to get price for {instrument}: {mt5.last_error()}")
        
        return {
            'bid': tick.bid,
            'ask': tick.ask,
            'last': tick.last,
            'volume': tick.volume,
            'time': datetime.fromtimestamp(tick.time)
        }
    
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
            instrument: Trading instrument (e.g., "EURUSD")
            units: Position size in lots (will be converted to volume)
            direction: 'BUY' or 'SELL'
            take_profit: Take profit price level
            stop_loss: Stop loss price level
            
        Returns:
            Dictionary with order details
        """
        if not self.ensure_connected():
            raise Exception("MT5 not connected")
        
        # Get symbol info
        symbol_info = mt5.symbol_info(instrument)
        if symbol_info is None:
            raise Exception(f"Symbol {instrument} not found: {mt5.last_error()}")
        
        # Ensure symbol is available for trading
        if not symbol_info.visible:
            if not mt5.symbol_select(instrument, True):
                raise Exception(f"Failed to select symbol {instrument}")
        
        # Get current price
        tick = mt5.symbol_info_tick(instrument)
        if tick is None:
            raise Exception(f"Failed to get tick for {instrument}")
        
        # Determine order type and price
        # units is in lots (can be negative for SELL)
        volume = abs(units)  # Volume is always positive in MT5
        
        if direction.upper() == "BUY" or units > 0:
            order_type = mt5.ORDER_TYPE_BUY
            price = tick.ask
        else:  # SELL
            order_type = mt5.ORDER_TYPE_SELL
            price = tick.bid
        
        # Normalize volume to lot size
        lot_size = symbol_info.volume_min
        volume = round(volume / lot_size) * lot_size
        volume = max(volume, symbol_info.volume_min)
        volume = min(volume, symbol_info.volume_max)
        
        # Prepare request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": instrument,
            "volume": volume,
            "type": order_type,
            "price": price,
            "deviation": 10,
            "magic": self.magic_number,
            "comment": "Strategy B",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # Add TP/SL if provided
        if take_profit:
            request["tp"] = take_profit
        if stop_loss:
            request["sl"] = stop_loss
        
        # Send order
        result = mt5.order_send(request)
        
        if result is None:
            raise Exception(f"Order send failed: {mt5.last_error()}")
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            raise Exception(f"Order failed: {result.retcode} - {result.comment}")
        
        # Get position info
        position = mt5.positions_get(symbol=instrument)
        position_info = position[0] if position and len(position) > 0 else None
        
        return {
            'order_id': result.order,
            'deal_id': result.deal,
            'instrument': instrument,
            'volume': volume,
            'price': result.price,
            'time': datetime.fromtimestamp(result.time),
            'take_profit': take_profit if take_profit else None,
            'stop_loss': stop_loss if stop_loss else None,
            'position_id': position_info.ticket if position_info else None,
            'retcode': result.retcode,
            'comment': result.comment
        }
    
    def get_open_positions(self, symbol: Optional[str] = None) -> List[Dict]:
        """Get all open positions"""
        if not self.ensure_connected():
            raise Exception("MT5 not connected")
        
        if symbol:
            positions = mt5.positions_get(symbol=symbol)
        else:
            positions = mt5.positions_get()
        
        if positions is None:
            if mt5.last_error()[0] == mt5.RES_S_OK:  # No positions
                return []
            raise Exception(f"Failed to get positions: {mt5.last_error()}")
        
        result = []
        for pos in positions:
            if pos.magic == self.magic_number:  # Only our strategy's positions
                result.append({
                    'ticket': pos.ticket,
                    'symbol': pos.symbol,
                    'type': 'BUY' if pos.type == mt5.ORDER_TYPE_BUY else 'SELL',
                    'volume': pos.volume,
                    'price_open': pos.price_open,
                    'price_current': pos.price_current,
                    'profit': pos.profit,
                    'swap': pos.swap,
                    'tp': pos.tp,
                    'sl': pos.sl,
                    'time_open': datetime.fromtimestamp(pos.time),
                    'comment': pos.comment
                })
        
        return result
    
    def close_position(self, position_id: int) -> Dict:
        """Close a specific position"""
        if not self.ensure_connected():
            raise Exception("MT5 not connected")
        
        # Get position
        positions = mt5.positions_get(ticket=position_id)
        if positions is None or len(positions) == 0:
            raise Exception(f"Position {position_id} not found")
        
        position = positions[0]
        
        # Get symbol info
        symbol_info = mt5.symbol_info(position.symbol)
        if symbol_info is None:
            raise Exception(f"Symbol {position.symbol} not found")
        
        # Get current price
        tick = mt5.symbol_info_tick(position.symbol)
        if tick is None:
            raise Exception(f"Failed to get tick for {position.symbol}")
        
        # Determine close order type (opposite of position)
        if position.type == mt5.ORDER_TYPE_BUY:
            order_type = mt5.ORDER_TYPE_SELL
            price = tick.bid
        else:
            order_type = mt5.ORDER_TYPE_BUY
            price = tick.ask
        
        # Prepare close request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": position.symbol,
            "volume": position.volume,
            "type": order_type,
            "position": position_id,
            "price": price,
            "deviation": 10,
            "magic": self.magic_number,
            "comment": "Strategy B Close",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # Send close order
        result = mt5.order_send(request)
        
        if result is None:
            raise Exception(f"Close order failed: {mt5.last_error()}")
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            raise Exception(f"Close order failed: {result.retcode} - {result.comment}")
        
        return {
            'order_id': result.order,
            'deal_id': result.deal,
            'position_id': position_id,
            'price': result.price,
            'time': datetime.fromtimestamp(result.time),
            'retcode': result.retcode,
            'comment': result.comment
        }
    
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
            instrument: Trading instrument (e.g., "EURUSD")
            count: Number of candles to retrieve
            granularity: Timeframe string (e.g., "M15", "H1") or minutes (15, 60)
            from_time: Start time (ISO format), optional
            
        Returns:
            DataFrame with OHLCV data
        """
        if not self.ensure_connected():
            raise Exception("MT5 not connected")
        
        # Convert granularity to MT5 timeframe
        timeframe_map = {
            'M1': mt5.TIMEFRAME_M1,
            'M5': mt5.TIMEFRAME_M5,
            'M15': mt5.TIMEFRAME_M15,
            'M30': mt5.TIMEFRAME_M30,
            'H1': mt5.TIMEFRAME_H1,
            'H4': mt5.TIMEFRAME_H4,
            'D1': mt5.TIMEFRAME_D1,
        }
        
        # Handle numeric granularity (minutes)
        if isinstance(granularity, (int, str)) and str(granularity).isdigit():
            minutes = int(granularity)
            if minutes == 1:
                timeframe = mt5.TIMEFRAME_M1
            elif minutes == 5:
                timeframe = mt5.TIMEFRAME_M5
            elif minutes == 15:
                timeframe = mt5.TIMEFRAME_M15
            elif minutes == 30:
                timeframe = mt5.TIMEFRAME_M30
            elif minutes == 60:
                timeframe = mt5.TIMEFRAME_H1
            else:
                timeframe = mt5.TIMEFRAME_M15  # Default
        else:
            timeframe = timeframe_map.get(granularity.upper(), mt5.TIMEFRAME_M15)
        
        # Get candles
        if from_time:
            from_dt = pd.to_datetime(from_time)
            rates = mt5.copy_rates_from(instrument, timeframe, from_dt, count)
        else:
            rates = mt5.copy_rates_from_pos(instrument, timeframe, 0, count)
        
        if rates is None or len(rates) == 0:
            raise Exception(f"Failed to get candles: {mt5.last_error()}")
        
        # Convert to DataFrame
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)
        df.rename(columns={
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close',
            'tick_volume': 'volume'
        }, inplace=True)
        
        # Keep only OHLCV columns
        df = df[['open', 'high', 'low', 'close', 'volume']]
        
        return df
    
    def shutdown(self):
        """Shutdown MT5 connection"""
        if self.connected:
            mt5.shutdown()
            self.connected = False
            logger.info("MT5 connection closed")

