"""
MetaAPI REST client — replaces MT5Client for cloud/Linux deployment.

MetaAPI connects to your existing XM MT5 account via their cloud service,
so no MT5 terminal installation is needed.

Register at: https://app.metaapi.cloud
Set env vars: METAAPI_TOKEN, METAAPI_ACCOUNT_ID
"""
import os
import time
import logging
import pandas as pd
import requests
from datetime import datetime, timezone
from typing import Dict, List, Optional
from broker_interface import BrokerInterface

logger = logging.getLogger(__name__)

# MetaAPI REST API base URLs
_TRADE_API = "https://mt-client-api-v1.london.agiliumtrade.ai"
_MARKET_API = "https://mt-market-data-client-api-v1.london.agiliumtrade.ai"

# MetaAPI timeframe map (minutes → MetaAPI string)
_TIMEFRAME_MAP = {
    1: "1m", 5: "5m", 15: "15m", 30: "30m",
    60: "1h", 240: "4h", 1440: "1d",
    "M1": "1m", "M5": "5m", "M15": "15m", "M30": "30m",
    "H1": "1h", "H4": "4h", "D1": "1d",
}


class MetaApiClient(BrokerInterface):
    """
    Synchronous MetaAPI REST client for the trading bot.
    Implements BrokerInterface so it's a drop-in replacement for MT5Client.
    """

    def __init__(
        self,
        token: Optional[str] = None,
        account_id: Optional[str] = None,
        timeout: int = 30,
    ):
        self.token = token or os.environ["METAAPI_TOKEN"]
        self.account_id = account_id or os.environ["METAAPI_ACCOUNT_ID"]
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({
            "auth-token": self.token,
            "Content-Type": "application/json",
        })
        self.connected = False
        self._connect()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _trade_url(self, path: str) -> str:
        return f"{_TRADE_API}/users/current/accounts/{self.account_id}{path}"

    def _market_url(self, path: str) -> str:
        return f"{_MARKET_API}/users/current/accounts/{self.account_id}{path}"

    def _get(self, url: str, params: Optional[Dict] = None) -> Dict:
        resp = self._session.get(url, params=params, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def _post(self, url: str, body: Dict) -> Dict:
        resp = self._session.post(url, json=body, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def _connect(self):
        """Verify connection by fetching account info."""
        try:
            info = self._get(self._trade_url("/account-information"))
            self.connected = True
            logger.info(
                f"MetaAPI connected — balance: ${info.get('balance', 0):.2f}, "
                f"equity: ${info.get('equity', 0):.2f}"
            )
        except Exception as e:
            logger.error(f"MetaAPI connection failed: {e}")
            self.connected = False

    def ensure_connected(self) -> bool:
        if not self.connected:
            self._connect()
        return self.connected

    # ------------------------------------------------------------------
    # BrokerInterface implementation
    # ------------------------------------------------------------------

    def get_account_info(self) -> Dict:
        if not self.ensure_connected():
            raise ConnectionError("MetaAPI not connected")
        data = self._get(self._trade_url("/account-information"))
        return {
            "balance": data.get("balance", 0),
            "equity": data.get("equity", 0),
            "margin": data.get("margin", 0),
            "free_margin": data.get("freeMargin", 0),
            "margin_level": data.get("marginLevel", 0),
            "currency": data.get("currency", "USD"),
            "server": data.get("broker", "XM"),
            "leverage": data.get("leverage", 500),
            "company": data.get("brokerName", "XM"),
        }

    def get_current_price(self, instrument: str) -> Dict:
        if not self.ensure_connected():
            raise ConnectionError("MetaAPI not connected")
        data = self._get(
            self._market_url(f"/symbols/{instrument}/current-price"),
            params={"keepSubscription": "false"},
        )
        return {
            "bid": data.get("bid", 0),
            "ask": data.get("ask", 0),
            "last": data.get("last", data.get("bid", 0)),
            "volume": data.get("volume", 0),
            "time": datetime.now(timezone.utc),
        }

    def place_market_order(
        self,
        instrument: str,
        units,
        direction: str,
        take_profit: Optional[float] = None,
        stop_loss: Optional[float] = None,
    ) -> Dict:
        if not self.ensure_connected():
            raise ConnectionError("MetaAPI not connected")

        # units can be lots (float) or raw units (int) — normalise to lots
        volume = abs(float(units))
        if volume > 10:            # raw units passed (e.g. 1000), convert to lots
            volume = volume / 100_000

        volume = max(round(volume, 2), 0.01)

        action = "ORDER_TYPE_BUY" if direction.upper() == "BUY" else "ORDER_TYPE_SELL"
        body: Dict = {
            "actionType": action,
            "symbol": instrument,
            "volume": volume,
            "comment": "ForexBot-StrategyB",
        }
        if take_profit:
            body["takeProfit"] = take_profit
        if stop_loss:
            body["stopLoss"] = stop_loss

        result = self._post(self._trade_url("/trade"), body)

        if result.get("error"):
            raise Exception(f"Order rejected: {result.get('description', result)}")

        return {
            "order_id": result.get("orderId", ""),
            "deal_id": result.get("dealId", ""),
            "instrument": instrument,
            "volume": volume,
            "price": result.get("openPrice", 0),
            "time": datetime.now(timezone.utc),
            "take_profit": take_profit,
            "stop_loss": stop_loss,
            "position_id": result.get("positionId", ""),
            "retcode": result.get("numericCode", 0),
            "comment": result.get("description", ""),
        }

    def get_open_positions(self, symbol: Optional[str] = None) -> List[Dict]:
        if not self.ensure_connected():
            raise ConnectionError("MetaAPI not connected")
        positions = self._get(self._trade_url("/positions"))
        result = []
        for pos in positions:
            if symbol and pos.get("symbol") != symbol:
                continue
            result.append({
                "ticket": pos.get("id", ""),
                "symbol": pos.get("symbol", ""),
                "type": pos.get("type", "").replace("POSITION_TYPE_", ""),
                "volume": pos.get("volume", 0),
                "price_open": pos.get("openPrice", 0),
                "price_current": pos.get("currentPrice", 0),
                "profit": pos.get("profit", 0),
                "swap": pos.get("swap", 0),
                "tp": pos.get("takeProfit"),
                "sl": pos.get("stopLoss"),
                "time_open": pos.get("time", ""),
                "comment": pos.get("comment", ""),
            })
        return result

    def close_position(self, position_id) -> Dict:
        if not self.ensure_connected():
            raise ConnectionError("MetaAPI not connected")
        body = {
            "actionType": "POSITION_CLOSE_ID",
            "positionId": str(position_id),
        }
        result = self._post(self._trade_url("/trade"), body)
        if result.get("error"):
            raise Exception(f"Close failed: {result.get('description', result)}")
        return {
            "order_id": result.get("orderId", ""),
            "deal_id": result.get("dealId", ""),
            "position_id": position_id,
            "price": result.get("closePrice", 0),
            "time": datetime.now(timezone.utc),
            "retcode": result.get("numericCode", 0),
            "comment": result.get("description", ""),
        }

    def get_candles(
        self,
        instrument: str,
        count: int,
        granularity,
        from_time: Optional[str] = None,
    ) -> pd.DataFrame:
        if not self.ensure_connected():
            raise ConnectionError("MetaAPI not connected")

        tf = _TIMEFRAME_MAP.get(granularity, "15m")
        params: Dict = {"limit": count}
        if from_time:
            params["startTime"] = from_time

        data = self._get(
            self._market_url(f"/symbols/{instrument}/candles/{tf}"),
            params=params,
        )

        candles = data if isinstance(data, list) else data.get("candles", data)
        if not candles:
            return pd.DataFrame()

        df = pd.DataFrame(candles)
        df["time"] = pd.to_datetime(df.get("time", df.get("brokerTime", None)))
        df.set_index("time", inplace=True)
        df.rename(
            columns={
                "openPrice": "open",
                "highPrice": "high",
                "lowPrice": "low",
                "closePrice": "close",
                "tickVolume": "volume",
            },
            inplace=True,
        )

        for col in ["open", "high", "low", "close", "volume"]:
            if col not in df.columns:
                df[col] = 0.0

        return df[["open", "high", "low", "close", "volume"]]

    def shutdown(self):
        self._session.close()
        self.connected = False
        logger.info("MetaAPI client closed")
