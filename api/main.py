"""
ForexBot Mobile API
FastAPI backend that exposes trading data for the mobile app
"""
import sys
import os
import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add trading_system to path so we can reuse DB logic
sys.path.insert(0, str(Path(__file__).parent.parent / "trading_system"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ForexBot Mobile API",
    description="REST API for the ForexBot mobile app",
    version="1.0.0",
)

# Allow all origins so Expo app on phone can connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------------------------
# Database path — matches the trading system default
# --------------------------------------------------------------------------
DB_PATH = os.environ.get(
    "FOREXBOT_DB_PATH",
    str(Path(__file__).parent.parent / "trading_system" / "data" / "trades.db"),
)


def get_conn():
    """Return a SQLite connection with row_factory set."""
    if not Path(DB_PATH).exists():
        # Create the directory and an empty DB so the API doesn't crash
        Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("""
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
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS daily_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL UNIQUE,
                total_pnl REAL,
                trades_count INTEGER,
                win_rate REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS system_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        return conn

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def rows_to_dicts(rows) -> List[Dict]:
    return [dict(r) for r in rows]


# --------------------------------------------------------------------------
# Models
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
    created_at: Optional[str] = None


class DailySummaryItem(BaseModel):
    date: str
    total_pnl: float
    trades_count: int
    win_rate: float


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


# --------------------------------------------------------------------------
# Health check
# --------------------------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok", "db_path": DB_PATH, "db_exists": Path(DB_PATH).exists()}


# --------------------------------------------------------------------------
# Account / Dashboard summary
# --------------------------------------------------------------------------
@app.get("/account", response_model=AccountSummary)
def get_account():
    """High-level dashboard data for the mobile app home screen."""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    conn = get_conn()
    cur = conn.cursor()

    # Today's closed trades
    cur.execute(
        "SELECT pnl FROM trades WHERE DATE(timestamp) = ? AND status = 'CLOSED'",
        (today,),
    )
    today_closed = rows_to_dicts(cur.fetchall())
    today_pnl = sum(t["pnl"] or 0 for t in today_closed)
    today_trades = len(today_closed)
    today_wins = sum(1 for t in today_closed if (t["pnl"] or 0) > 0)
    today_win_rate = (today_wins / today_trades * 100) if today_trades > 0 else 0.0

    # Open trades count
    cur.execute("SELECT COUNT(*) as cnt FROM trades WHERE status = 'OPEN'")
    open_trades = cur.fetchone()["cnt"]

    # All-time stats
    cur.execute("SELECT pnl FROM trades WHERE status = 'CLOSED'")
    all_closed = rows_to_dicts(cur.fetchall())
    all_time_pnl = sum(t["pnl"] or 0 for t in all_closed)
    all_wins = sum(1 for t in all_closed if (t["pnl"] or 0) > 0)
    all_time_win_rate = (all_wins / len(all_closed) * 100) if all_closed else 0.0

    # System state
    cur.execute("SELECT value FROM system_state WHERE key = 'kill_switch'")
    kill_row = cur.fetchone()
    kill_switch = (kill_row["value"].lower() == "true") if kill_row else False

    cur.execute("SELECT value FROM system_state WHERE key = 'bot_status'")
    status_row = cur.fetchone()
    bot_status = status_row["value"] if status_row else "UNKNOWN"

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
# Trades
# --------------------------------------------------------------------------
@app.get("/trades", response_model=List[Trade])
def get_trades(
    status: Optional[str] = Query(None, description="Filter by status: OPEN or CLOSED"),
    instrument: Optional[str] = Query(None, description="Filter by instrument e.g. EURUSD"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Return trade history with optional filters."""
    conn = get_conn()
    cur = conn.cursor()

    conditions = []
    params = []

    if status:
        conditions.append("status = ?")
        params.append(status.upper())

    if instrument:
        conditions.append("instrument = ?")
        params.append(instrument.upper())

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    params += [limit, offset]

    cur.execute(
        f"SELECT * FROM trades {where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
        params,
    )
    trades = rows_to_dicts(cur.fetchall())
    conn.close()
    return trades


@app.get("/trades/open", response_model=List[Trade])
def get_open_trades():
    """Return all currently open trades."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM trades WHERE status = 'OPEN' ORDER BY created_at DESC")
    trades = rows_to_dicts(cur.fetchall())
    conn.close()
    return trades


@app.get("/trades/{trade_id}", response_model=Trade)
def get_trade(trade_id: int):
    """Return a single trade by ID."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM trades WHERE id = ?", (trade_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Trade not found")
    return dict(row)


# --------------------------------------------------------------------------
# Daily P&L chart data
# --------------------------------------------------------------------------
@app.get("/pnl/daily")
def get_daily_pnl(days: int = Query(30, ge=1, le=365)):
    """
    Return daily P&L for the last N days — used for the chart on the dashboard.
    """
    conn = get_conn()
    cur = conn.cursor()

    since = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")

    cur.execute(
        """
        SELECT
            DATE(timestamp) as date,
            SUM(pnl) as total_pnl,
            COUNT(*) as trades_count,
            SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins
        FROM trades
        WHERE status = 'CLOSED' AND DATE(timestamp) >= ?
        GROUP BY DATE(timestamp)
        ORDER BY date ASC
        """,
        (since,),
    )
    rows = rows_to_dicts(cur.fetchall())
    conn.close()

    # Fill in missing dates with zero P&L so the chart looks nice
    result = {}
    for row in rows:
        result[row["date"]] = {
            "date": row["date"],
            "pnl": round(row["total_pnl"] or 0, 4),
            "trades": row["trades_count"],
            "wins": row["wins"] or 0,
        }

    # Build continuous date range
    chart_data = []
    for i in range(days):
        d = (datetime.utcnow() - timedelta(days=days - 1 - i)).strftime("%Y-%m-%d")
        chart_data.append(result.get(d, {"date": d, "pnl": 0, "trades": 0, "wins": 0}))

    return {"days": days, "data": chart_data}


# --------------------------------------------------------------------------
# Instruments list
# --------------------------------------------------------------------------
@app.get("/instruments")
def get_instruments():
    """Return distinct instruments that have been traded."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT instrument FROM trades ORDER BY instrument")
    instruments = [r["instrument"] for r in cur.fetchall()]
    conn.close()
    return {"instruments": instruments}


# --------------------------------------------------------------------------
# Kill switch control
# --------------------------------------------------------------------------
@app.post("/killswitch/{state}")
def set_kill_switch(state: str):
    """
    Toggle the kill switch — set to 'on' or 'off'.
    The trading system reads this from system_state table.
    """
    if state not in ("on", "off"):
        raise HTTPException(status_code=400, detail="State must be 'on' or 'off'")

    value = "true" if state == "on" else "false"
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO system_state (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
        ("kill_switch", value),
    )
    conn.commit()
    conn.close()
    return {"kill_switch": state, "message": f"Kill switch turned {state}"}


# --------------------------------------------------------------------------
# Run with: uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
# --------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
