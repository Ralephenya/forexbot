"""
API Lambda Handler — wraps FastAPI with Mangum for API Gateway.

All routes are the same as api/main.py but data comes from S3Store
instead of SQLite. MetaAPI calls (live prices, trade placement) are
unchanged.
"""
import sys
import os
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent.parent / "trading_system"))

from s3_store import S3Store

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Config ──────────────────────────────────────────────────────────────────
METAAPI_TOKEN = os.environ.get("METAAPI_TOKEN", "")
METAAPI_ACCOUNT_ID = os.environ.get("METAAPI_ACCOUNT_ID", "")
_TRADE_API = "https://mt-client-api-v1.london.agiliumtrade.ai"
_MARKET_API = "https://mt-market-data-client-api-v1.london.agiliumtrade.ai"

SUPPORTED_INSTRUMENTS = [
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "GBPJPY",
    "USDCAD", "USDCHF", "NZDUSD", "EURGBP", "EURJPY",
]

# ── FastAPI app ──────────────────────────────────────────────────────────────
app = FastAPI(title="ForexBot API", version="3.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def store() -> S3Store:
    return S3Store()


# ── MetaAPI helpers ──────────────────────────────────────────────────────────

def _meta_headers():
    return {"auth-token": METAAPI_TOKEN, "Content-Type": "application/json"}


async def _meta_get(path: str, base: str = _TRADE_API, params: Optional[Dict] = None):
    url = f"{base}/users/current/accounts/{METAAPI_ACCOUNT_ID}{path}"
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(url, headers=_meta_headers(), params=params)
        resp.raise_for_status()
        return resp.json()


async def _meta_post(path: str, body: Dict, base: str = _TRADE_API):
    url = f"{base}/users/current/accounts/{METAAPI_ACCOUNT_ID}{path}"
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(url, headers=_meta_headers(), json=body)
        resp.raise_for_status()
        return resp.json()


# ── Pydantic models ──────────────────────────────────────────────────────────

class PlaceTradeRequest(BaseModel):
    instrument: str
    direction: str
    volume: float = 0.01
    take_profit: Optional[float] = None
    stop_loss: Optional[float] = None
    strategy_name: Optional[str] = "Manual"


# ── Health ───────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "storage": "s3",
        "bucket": os.environ.get("S3_BUCKET", "not_set"),
        "metaapi_configured": bool(METAAPI_TOKEN and METAAPI_ACCOUNT_ID),
    }


# ── Dashboard ────────────────────────────────────────────────────────────────

@app.get("/account")
def get_account():
    return store().get_account_summary()


# ── Daily P&L chart ──────────────────────────────────────────────────────────

@app.get("/pnl/daily")
def get_daily_pnl(days: int = Query(30, ge=1, le=365)):
    data = store().get_daily_pnl(days)
    return {"days": days, "data": data}


# ── Trade history ────────────────────────────────────────────────────────────

@app.get("/trades")
def get_trades(
    status: Optional[str] = None,
    instrument: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    return store().get_trades(status=status, instrument=instrument, limit=limit, offset=offset)


@app.get("/trades/open")
def get_open_trades():
    return store().get_open_trades()


@app.get("/trades/{trade_id}")
def get_trade(trade_id: int):
    trade = store().get_trade_by_id(trade_id)
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    return trade


# ── Live broker data ─────────────────────────────────────────────────────────

@app.get("/live/account")
async def get_live_account():
    if not METAAPI_TOKEN:
        raise HTTPException(503, "MetaAPI not configured")
    try:
        data, positions = await _meta_get("/account-information"), await _meta_get("/positions")
        return {
            "balance": data.get("balance", 0),
            "equity": data.get("equity", 0),
            "margin": data.get("margin", 0),
            "free_margin": data.get("freeMargin", 0),
            "margin_level": data.get("marginLevel", 0),
            "currency": data.get("currency", "USD"),
            "leverage": data.get("leverage", 500),
            "server": data.get("broker", "XM"),
            "open_positions": len(positions) if isinstance(positions, list) else 0,
        }
    except Exception as e:
        raise HTTPException(503, f"MetaAPI error: {e}")


@app.get("/live/positions")
async def get_live_positions():
    if not METAAPI_TOKEN:
        raise HTTPException(503, "MetaAPI not configured")
    try:
        positions = await _meta_get("/positions")
        return [
            {
                "ticket": p.get("id", ""),
                "symbol": p.get("symbol", ""),
                "direction": p.get("type", "").replace("POSITION_TYPE_", ""),
                "volume": p.get("volume", 0),
                "entry_price": p.get("openPrice", 0),
                "current_price": p.get("currentPrice", 0),
                "profit": p.get("profit", 0),
                "swap": p.get("swap", 0),
                "take_profit": p.get("takeProfit"),
                "stop_loss": p.get("stopLoss"),
                "open_time": p.get("time", ""),
                "comment": p.get("comment", ""),
            }
            for p in (positions if isinstance(positions, list) else [])
        ]
    except Exception as e:
        raise HTTPException(503, f"MetaAPI error: {e}")


@app.get("/live/price/{instrument}")
async def get_live_price(instrument: str):
    if not METAAPI_TOKEN:
        raise HTTPException(503, "MetaAPI not configured")
    try:
        data = await _meta_get(
            f"/symbols/{instrument.upper()}/current-price",
            base=_MARKET_API,
            params={"keepSubscription": "false"},
        )
        bid, ask = data.get("bid", 0), data.get("ask", 0)
        return {
            "instrument": instrument.upper(),
            "bid": bid,
            "ask": ask,
            "spread": round((ask - bid) * 10000, 1),
            "time": data.get("time", datetime.utcnow().isoformat()),
        }
    except Exception as e:
        raise HTTPException(503, f"MetaAPI error: {e}")


@app.get("/live/prices")
async def get_live_prices(instruments: str = Query(default="EURUSD,GBPUSD,USDJPY")):
    if not METAAPI_TOKEN:
        raise HTTPException(503, "MetaAPI not configured")
    results = []
    for symbol in [s.strip().upper() for s in instruments.split(",")]:
        try:
            data = await _meta_get(
                f"/symbols/{symbol}/current-price",
                base=_MARKET_API,
                params={"keepSubscription": "false"},
            )
            bid, ask = data.get("bid", 0), data.get("ask", 0)
            results.append({"instrument": symbol, "bid": bid, "ask": ask,
                            "spread": round((ask - bid) * 10000, 1)})
        except Exception:
            results.append({"instrument": symbol, "bid": None, "ask": None, "error": True})
    return results


# ── Trade placement & closing ────────────────────────────────────────────────

@app.post("/live/trade")
async def place_trade(req: PlaceTradeRequest):
    if not METAAPI_TOKEN:
        raise HTTPException(503, "MetaAPI not configured")

    instrument = req.instrument.upper()
    direction = req.direction.upper()
    if direction not in ("BUY", "SELL"):
        raise HTTPException(400, "direction must be BUY or SELL")
    if instrument not in SUPPORTED_INSTRUMENTS:
        raise HTTPException(400, f"Unsupported instrument: {instrument}")

    volume = max(round(req.volume, 2), 0.01)
    body: Dict = {
        "actionType": "ORDER_TYPE_BUY" if direction == "BUY" else "ORDER_TYPE_SELL",
        "symbol": instrument,
        "volume": volume,
        "comment": f"ForexBot-{req.strategy_name or 'Manual'}",
    }
    if req.take_profit:
        body["takeProfit"] = req.take_profit
    if req.stop_loss:
        body["stopLoss"] = req.stop_loss

    try:
        result = await _meta_post("/trade", body)
    except Exception as e:
        raise HTTPException(503, f"MetaAPI error: {e}")

    if result.get("error"):
        raise HTTPException(400, result.get("description", "Order rejected"))

    # Record in S3
    trade_id = store().save_trade({
        "timestamp": datetime.utcnow().isoformat(),
        "instrument": instrument,
        "direction": direction,
        "entry_price": result.get("openPrice", 0),
        "units": int(volume * 100_000),
        "take_profit": req.take_profit,
        "stop_loss": req.stop_loss,
        "status": "OPEN",
        "strategy_name": req.strategy_name or "Manual",
        "broker_ticket": str(result.get("positionId", "")),
    })

    return {
        "success": True,
        "trade_id": trade_id,
        "broker_ticket": result.get("positionId", ""),
        "instrument": instrument,
        "direction": direction,
        "volume": volume,
        "entry_price": result.get("openPrice", 0),
        "take_profit": req.take_profit,
        "stop_loss": req.stop_loss,
    }


@app.delete("/live/trade/{position_id}")
async def close_trade(position_id: str):
    if not METAAPI_TOKEN:
        raise HTTPException(503, "MetaAPI not configured")

    try:
        result = await _meta_post("/trade", {
            "actionType": "POSITION_CLOSE_ID",
            "positionId": position_id,
        })
    except Exception as e:
        raise HTTPException(503, f"MetaAPI error: {e}")

    if result.get("error"):
        raise HTTPException(400, result.get("description", "Close failed"))

    close_price = result.get("closePrice", 0)

    # Update S3
    s = store()
    open_trades = s.get_open_trades()
    for trade in open_trades:
        if trade.get("broker_ticket") == position_id:
            instrument = trade.get("instrument", "EURUSD")
            pip = 0.01 if "JPY" in instrument else 0.0001
            entry = trade.get("entry_price", 0) or 0
            direction = trade.get("direction", "BUY")
            pips = ((close_price - entry) if direction == "BUY" else (entry - close_price)) / pip
            lots = (trade.get("units", 1000)) / 100_000
            pnl = round(pips * 10 * lots, 2)
            s.update_trade(trade["id"], {
                "status": "CLOSED",
                "exit_price": close_price,
                "pips": round(pips, 1),
                "pnl": pnl,
                "exit_reason": "Manual Close",
            })
            break

    return {"success": True, "position_id": position_id, "close_price": close_price}


# ── Kill switch ──────────────────────────────────────────────────────────────

@app.post("/killswitch/{state}")
def set_kill_switch(state: str):
    if state not in ("on", "off"):
        raise HTTPException(400, "State must be 'on' or 'off'")
    store().update_system_state({"kill_switch": state == "on"})
    return {"kill_switch": state}


# ── Instruments ──────────────────────────────────────────────────────────────

@app.get("/instruments")
def get_instruments():
    return {"instruments": SUPPORTED_INSTRUMENTS}


# ── Mangum adapter (API Gateway → Lambda) ────────────────────────────────────
handler = Mangum(app, lifespan="off")
