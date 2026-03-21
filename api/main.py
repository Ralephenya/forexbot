"""
ForexBot Mobile API — v2
FastAPI backend that exposes trading data AND places/closes trades via MetaAPI.

Environment variables required:
  METAAPI_TOKEN       — from https://app.metaapi.cloud
  METAAPI_ACCOUNT_ID  — your MT5 account ID in MetaAPI

Optional:
  FOREXBOT_DB_PATH    — path to SQLite DB (default: trading_system/data/trades.db)
"""
import os
import sys
import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict

import httpx
from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ForexBot Mobile API",
    description="REST API for the ForexBot mobile app — trade anywhere",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------
DB_PATH = os.environ.get(
    "FOREXBOT_DB_PATH",
    str(Path(__file__).parent.parent / "trading_system" / "data" / "trades.db"),
)

METAAPI_TOKEN = os.environ.get("METAAPI_TOKEN", "")
METAAPI_ACCOUNT_ID = os.environ.get("METAAPI_ACCOUNT_ID", "")

_TRADE_API = "https://mt-client-api-v1.london.agiliumtrade.ai"
_MARKET_API = "https://mt-market-data-client-api-v1.london.agiliumtrade.ai"

_TIMEFRAME_MAP = {
    "M1": "1m", "M5": "5m", "M15": "15m", "M30": "30m",
    "H1": "1h", "H4": "4h", "D1": "1d",
}

SUPPORTED_INSTRUMENTS = [
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "GBPJPY",
    "USDCAD", "USDCHF", "NZDUSD", "EURGBP", "EURJPY",
]


# --------------------------------------------------------------------------
# MetaAPI async helpers
# --------------------------------------------------------------------------

def _meta_headers() -> Dict:
    return {"auth-token": METAAPI_TOKEN, "Content-Type": "application/json"}


async def _meta_get(path: str, base: str = _TRADE_API, params: Optional[Dict] = None) -> Dict:
    url = f"{base}/users/current/accounts/{METAAPI_ACCOUNT_ID}{path}"
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(url, headers=_meta_headers(), params=params)
        resp.raise_for_status()
        return resp.json()


async def _meta_post(path: str, body: Dict, base: str = _TRADE_API) -> Dict:
    url = f"{base}/users/current/accounts/{METAAPI_ACCOUNT_ID}{path}"
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(url, headers=_meta_headers(), json=body)
        resp.raise_for_status()
        return resp.json()


# --------------------------------------------------------------------------
# SQLite helpers
# --------------------------------------------------------------------------

def _get_conn():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Ensure schema exists
    cur = conn.cursor()
    cur.executescript("""
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
            status TEXT NOT NULL DEFAULT 'OPEN',
            strategy_name TEXT,
            broker_ticket TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS daily_summary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL UNIQUE,
            total_pnl REAL,
            trades_count INTEGER,
            win_rate REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS system_state (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    return conn


def _rows(rows) -> List[Dict]:
    return [dict(r) for r in rows]


# --------------------------------------------------------------------------
# Pydantic models
# --------------------------------------------------------------------------

class Trade(BaseModel):
    id: int
    timestamp: str
    instrument: str
    direction: str
    entry_price: float
    exit_price: Optional[float] = None
    units: int
    take_profit: Optional[float] = None
    stop_loss: Optional[float] = None
    pnl: Optional[float] = None
    pips: Optional[float] = None
    exit_reason: Optional[str] = None
    status: str
    strategy_name: Optional[str] = None
    broker_ticket: Optional[str] = None
    created_at: Optional[str] = None


class PlaceTradeRequest(BaseModel):
    instrument: str
    direction: str             # BUY or SELL
    volume: float = 0.01       # lots
    take_profit: Optional[float] = None
    stop_loss: Optional[float] = None
    strategy_name: Optional[str] = "Manual"


class AccountSummary(BaseModel):
    today_pnl: float
    today_trades: int
    today_wins: int
    today_win_rate: float
    open_trades: int
    total_closed_trades: int
    all_time_pnl: float
    all_time_win_rate: float
    bot_status: str
    kill_switch: bool
    last_updated: str


class LiveAccount(BaseModel):
    balance: float
    equity: float
    margin: float
    free_margin: float
    margin_level: float
    currency: str
    leverage: int
    server: str
    open_positions: int


# --------------------------------------------------------------------------
# Health
# --------------------------------------------------------------------------

@app.get("/health")
async def health():
    meta_ok = bool(METAAPI_TOKEN and METAAPI_ACCOUNT_ID)
    return {
        "status": "ok",
        "db_path": DB_PATH,
        "db_exists": Path(DB_PATH).exists(),
        "metaapi_configured": meta_ok,
    }


# --------------------------------------------------------------------------
# Live broker data (MetaAPI)
# --------------------------------------------------------------------------

@app.get("/live/account", response_model=LiveAccount)
async def get_live_account():
    """Real-time account balance and equity from MetaAPI/XM."""
    if not METAAPI_TOKEN:
        raise HTTPException(status_code=503, detail="MetaAPI not configured — set METAAPI_TOKEN")
    try:
        data = await _meta_get("/account-information")
        positions = await _meta_get("/positions")
        return LiveAccount(
            balance=data.get("balance", 0),
            equity=data.get("equity", 0),
            margin=data.get("margin", 0),
            free_margin=data.get("freeMargin", 0),
            margin_level=data.get("marginLevel", 0),
            currency=data.get("currency", "USD"),
            leverage=data.get("leverage", 500),
            server=data.get("broker", "XM"),
            open_positions=len(positions) if isinstance(positions, list) else 0,
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"MetaAPI error: {str(e)}")


@app.get("/live/positions")
async def get_live_positions():
    """Real-time open positions directly from MetaAPI (not just DB)."""
    if not METAAPI_TOKEN:
        raise HTTPException(status_code=503, detail="MetaAPI not configured")
    try:
        positions = await _meta_get("/positions")
        if not isinstance(positions, list):
            positions = []
        result = []
        for pos in positions:
            result.append({
                "ticket": pos.get("id", ""),
                "symbol": pos.get("symbol", ""),
                "direction": pos.get("type", "").replace("POSITION_TYPE_", ""),
                "volume": pos.get("volume", 0),
                "entry_price": pos.get("openPrice", 0),
                "current_price": pos.get("currentPrice", 0),
                "profit": pos.get("profit", 0),
                "swap": pos.get("swap", 0),
                "take_profit": pos.get("takeProfit"),
                "stop_loss": pos.get("stopLoss"),
                "open_time": pos.get("time", ""),
                "comment": pos.get("comment", ""),
            })
        return result
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"MetaAPI error: {str(e)}")


@app.get("/live/price/{instrument}")
async def get_live_price(instrument: str):
    """Get current bid/ask price for an instrument."""
    if not METAAPI_TOKEN:
        raise HTTPException(status_code=503, detail="MetaAPI not configured")
    try:
        data = await _meta_get(
            f"/symbols/{instrument.upper()}/current-price",
            base=_MARKET_API,
            params={"keepSubscription": "false"},
        )
        return {
            "instrument": instrument.upper(),
            "bid": data.get("bid", 0),
            "ask": data.get("ask", 0),
            "spread": round((data.get("ask", 0) - data.get("bid", 0)) * 10000, 1),
            "time": data.get("time", datetime.utcnow().isoformat()),
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"MetaAPI error: {str(e)}")


@app.get("/live/prices")
async def get_live_prices(instruments: str = Query(default="EURUSD,GBPUSD,USDJPY")):
    """Get prices for multiple instruments at once."""
    if not METAAPI_TOKEN:
        raise HTTPException(status_code=503, detail="MetaAPI not configured")
    symbols = [s.strip().upper() for s in instruments.split(",")]
    results = []
    for symbol in symbols:
        try:
            data = await _meta_get(
                f"/symbols/{symbol}/current-price",
                base=_MARKET_API,
                params={"keepSubscription": "false"},
            )
            results.append({
                "instrument": symbol,
                "bid": data.get("bid", 0),
                "ask": data.get("ask", 0),
                "spread": round((data.get("ask", 0) - data.get("bid", 0)) * 10000, 1),
            })
        except Exception:
            results.append({"instrument": symbol, "bid": None, "ask": None, "error": True})
    return results


# --------------------------------------------------------------------------
# Trade placement & closing (MetaAPI)
# --------------------------------------------------------------------------

@app.post("/live/trade")
async def place_trade(req: PlaceTradeRequest):
    """
    Place a market order via MetaAPI → XM broker.

    Body: { instrument, direction, volume, take_profit, stop_loss, strategy_name }
    """
    if not METAAPI_TOKEN:
        raise HTTPException(status_code=503, detail="MetaAPI not configured")

    instrument = req.instrument.upper()
    direction = req.direction.upper()
    if direction not in ("BUY", "SELL"):
        raise HTTPException(status_code=400, detail="direction must be BUY or SELL")
    if instrument not in SUPPORTED_INSTRUMENTS:
        raise HTTPException(status_code=400, detail=f"Unsupported instrument: {instrument}")

    volume = max(round(req.volume, 2), 0.01)
    action = "ORDER_TYPE_BUY" if direction == "BUY" else "ORDER_TYPE_SELL"

    body: Dict = {
        "actionType": action,
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
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"MetaAPI error: {str(e)}")

    if result.get("error"):
        raise HTTPException(status_code=400, detail=result.get("description", "Order rejected"))

    # Also record in local DB for trade history
    now = datetime.utcnow().isoformat()
    open_price = result.get("openPrice", 0)
    units_raw = int(volume * 100_000)
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO trades
            (timestamp, instrument, direction, entry_price, units, take_profit,
             stop_loss, status, strategy_name, broker_ticket)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'OPEN', ?, ?)
    """, (
        now, instrument, direction, open_price,
        units_raw, req.take_profit, req.stop_loss,
        req.strategy_name or "Manual",
        result.get("positionId", ""),
    ))
    conn.commit()
    trade_id = cur.lastrowid
    conn.close()

    return {
        "success": True,
        "trade_id": trade_id,
        "broker_ticket": result.get("positionId", ""),
        "order_id": result.get("orderId", ""),
        "instrument": instrument,
        "direction": direction,
        "volume": volume,
        "entry_price": open_price,
        "take_profit": req.take_profit,
        "stop_loss": req.stop_loss,
    }


@app.delete("/live/trade/{position_id}")
async def close_trade(position_id: str):
    """Close an open position by its MetaAPI position ID (broker ticket)."""
    if not METAAPI_TOKEN:
        raise HTTPException(status_code=503, detail="MetaAPI not configured")

    body = {"actionType": "POSITION_CLOSE_ID", "positionId": position_id}
    try:
        result = await _meta_post("/trade", body)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"MetaAPI error: {str(e)}")

    if result.get("error"):
        raise HTTPException(status_code=400, detail=result.get("description", "Close failed"))

    close_price = result.get("closePrice", 0)

    # Update DB — find the trade by broker_ticket and close it
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM trades WHERE broker_ticket = ? AND status = 'OPEN' LIMIT 1",
        (position_id,),
    )
    row = cur.fetchone()
    if row:
        trade = dict(row)
        entry = trade.get("entry_price", 0) or 0
        direction = trade.get("direction", "BUY")
        units = trade.get("units", 0)
        pip_val = 0.0001 if "JPY" not in trade.get("instrument", "") else 0.01
        if direction == "BUY":
            pips = (close_price - entry) / pip_val
        else:
            pips = (entry - close_price) / pip_val
        lots = units / 100_000
        pnl = round(pips * 10 * lots, 2)

        cur.execute("""
            UPDATE trades
            SET status = 'CLOSED', exit_price = ?, pips = ?, pnl = ?,
                exit_reason = 'Manual Close'
            WHERE id = ?
        """, (close_price, round(pips, 1), pnl, trade["id"]))
        conn.commit()

    conn.close()

    return {
        "success": True,
        "position_id": position_id,
        "close_price": close_price,
        "order_id": result.get("orderId", ""),
    }


# --------------------------------------------------------------------------
# Dashboard summary (SQLite)
# --------------------------------------------------------------------------

@app.get("/account", response_model=AccountSummary)
def get_account():
    today = datetime.utcnow().strftime("%Y-%m-%d")
    conn = _get_conn()
    cur = conn.cursor()

    cur.execute("SELECT pnl FROM trades WHERE DATE(timestamp) = ? AND status = 'CLOSED'", (today,))
    today_closed = _rows(cur.fetchall())
    today_pnl = sum(t["pnl"] or 0 for t in today_closed)
    today_trades = len(today_closed)
    today_wins = sum(1 for t in today_closed if (t["pnl"] or 0) > 0)
    today_win_rate = (today_wins / today_trades * 100) if today_trades else 0.0

    cur.execute("SELECT COUNT(*) as cnt FROM trades WHERE status = 'OPEN'")
    open_trades = cur.fetchone()["cnt"]

    cur.execute("SELECT pnl FROM trades WHERE status = 'CLOSED'")
    all_closed = _rows(cur.fetchall())
    all_time_pnl = sum(t["pnl"] or 0 for t in all_closed)
    all_wins = sum(1 for t in all_closed if (t["pnl"] or 0) > 0)
    all_time_win_rate = (all_wins / len(all_closed) * 100) if all_closed else 0.0

    cur.execute("SELECT value FROM system_state WHERE key = 'kill_switch'")
    kill_row = cur.fetchone()
    kill_switch = (kill_row["value"].lower() == "true") if kill_row else False

    cur.execute("SELECT value FROM system_state WHERE key = 'bot_status'")
    status_row = cur.fetchone()
    bot_status = status_row["value"] if status_row else "RUNNING"

    conn.close()
    return AccountSummary(
        today_pnl=round(today_pnl, 4),
        today_trades=today_trades,
        today_wins=today_wins,
        today_win_rate=round(today_win_rate, 1),
        open_trades=open_trades,
        total_closed_trades=len(all_closed),
        all_time_pnl=round(all_time_pnl, 4),
        all_time_win_rate=round(all_time_win_rate, 1),
        bot_status=bot_status,
        kill_switch=kill_switch,
        last_updated=datetime.utcnow().isoformat() + "Z",
    )


# --------------------------------------------------------------------------
# Trade history (SQLite)
# --------------------------------------------------------------------------

@app.get("/trades", response_model=List[Trade])
def get_trades(
    status: Optional[str] = None,
    instrument: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    conn = _get_conn()
    cur = conn.cursor()
    conditions, params = [], []
    if status:
        conditions.append("status = ?")
        params.append(status.upper())
    if instrument:
        conditions.append("instrument = ?")
        params.append(instrument.upper())
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    params += [limit, offset]
    cur.execute(f"SELECT * FROM trades {where} ORDER BY created_at DESC LIMIT ? OFFSET ?", params)
    trades = _rows(cur.fetchall())
    conn.close()
    return trades


@app.get("/trades/open", response_model=List[Trade])
def get_open_trades():
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM trades WHERE status = 'OPEN' ORDER BY created_at DESC")
    trades = _rows(cur.fetchall())
    conn.close()
    return trades


@app.get("/trades/{trade_id}", response_model=Trade)
def get_trade(trade_id: int):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM trades WHERE id = ?", (trade_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Trade not found")
    return dict(row)


# --------------------------------------------------------------------------
# Daily P&L chart
# --------------------------------------------------------------------------

@app.get("/pnl/daily")
def get_daily_pnl(days: int = Query(30, ge=1, le=365)):
    conn = _get_conn()
    cur = conn.cursor()
    since = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
    cur.execute("""
        SELECT DATE(timestamp) as date,
               SUM(pnl) as total_pnl,
               COUNT(*) as trades_count,
               SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins
        FROM trades
        WHERE status = 'CLOSED' AND DATE(timestamp) >= ?
        GROUP BY DATE(timestamp) ORDER BY date ASC
    """, (since,))
    rows_dict = {r["date"]: dict(r) for r in cur.fetchall()}
    conn.close()

    chart_data = []
    for i in range(days):
        d = (datetime.utcnow() - timedelta(days=days - 1 - i)).strftime("%Y-%m-%d")
        row = rows_dict.get(d)
        chart_data.append({
            "date": d,
            "pnl": round(row["total_pnl"] or 0, 4) if row else 0,
            "trades": row["trades_count"] if row else 0,
            "wins": row["wins"] or 0 if row else 0,
        })
    return {"days": days, "data": chart_data}


# --------------------------------------------------------------------------
# Kill switch
# --------------------------------------------------------------------------

@app.post("/killswitch/{state}")
def set_kill_switch(state: str):
    if state not in ("on", "off"):
        raise HTTPException(status_code=400, detail="State must be 'on' or 'off'")
    value = "true" if state == "on" else "false"
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO system_state (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
        ("kill_switch", value),
    )
    conn.commit()
    conn.close()
    return {"kill_switch": state, "message": f"Kill switch turned {state}"}


# --------------------------------------------------------------------------
# Instruments
# --------------------------------------------------------------------------

@app.get("/instruments")
def get_instruments():
    return {"instruments": SUPPORTED_INSTRUMENTS}


# --------------------------------------------------------------------------
# Strategy Parameters (walk-forward optimized)
# --------------------------------------------------------------------------

@app.get("/strategy/params")
def get_strategy_params():
    """Returns the walk-forward optimized confluence strategy parameters."""
    return {
        "strategy": "Strategy B + Confluence Engine",
        "timeframe": "15m",
        "pair": "EUR/USD",
        "confluence": {
            "min_score": 7,
            "max_score": 10,
            "layers": 7,
        },
        "rsi": {
            "period": 14,
            "buy_threshold": 28,
            "sell_threshold": 72,
        },
        "risk": {
            "target_atr_mult": 1.2,
            "stop_atr_mult": 1.2,
            "rr_ratio": 1.0,
            "spread_pips": 1.2,
        },
        "session": {
            "start_utc": 8,
            "end_utc": 17,
            "prime_hours": [8, 9, 10, 13, 14],
        },
        "backtest": {
            "period_months": 12,
            "win_rate_pct": 65.1,
            "profit_factor": 1.72,
            "sharpe_ratio": 20.5,
            "avg_pips_per_month": 190.6,
            "max_drawdown_pips": -783.2,
            "total_trades": 86,
            "data": "GARCH + regime-switching synthetic EUR/USD",
            "method": "4-fold walk-forward optimization",
        },
    }


# --------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
