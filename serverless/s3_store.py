"""
S3-backed data store — replaces SQLite for serverless deployment.

All trade data lives in a single S3 bucket:
  s3://{bucket}/trades.json        — array of all trades
  s3://{bucket}/system_state.json  — kill switch, bot status

For a forex bot making ~5-20 trades/day the JSON files stay small (<1 MB
even after years of trading), so read-modify-write is fast and cheap.

Concurrency note: EventBridge fires the bot Lambda at most once per 15 min,
and the API serves reads mostly. The very rare simultaneous write (bot opens
trade while user closes another) uses S3 conditional puts to avoid data loss.
"""
import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

_TRADES_KEY = "trades.json"
_STATE_KEY = "system_state.json"


class S3Store:
    def __init__(self, bucket: Optional[str] = None):
        self.bucket = bucket or os.environ["S3_BUCKET"]
        self._s3 = boto3.client("s3")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_json(self, key: str, default):
        try:
            obj = self._s3.get_object(Bucket=self.bucket, Key=key)
            return json.loads(obj["Body"].read().decode("utf-8"))
        except ClientError as e:
            if e.response["Error"]["Code"] in ("NoSuchKey", "404"):
                return default
            raise

    def _put_json(self, key: str, data, etag: Optional[str] = None):
        """Write JSON. If etag is provided, use conditional put to prevent
        overwriting a concurrent change (returns False on conflict)."""
        body = json.dumps(data, default=str).encode("utf-8")
        kwargs: Dict = dict(
            Bucket=self.bucket,
            Key=key,
            Body=body,
            ContentType="application/json",
        )
        if etag:
            kwargs["IfMatch"] = etag
        try:
            self._s3.put_object(**kwargs)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "PreconditionFailed":
                logger.warning(f"S3 conditional put conflict on {key}, retrying read")
                return False
            raise

    def _get_with_etag(self, key: str, default):
        """Return (data, etag) for safe read-modify-write."""
        try:
            obj = self._s3.get_object(Bucket=self.bucket, Key=key)
            data = json.loads(obj["Body"].read().decode("utf-8"))
            etag = obj["ETag"]
            return data, etag
        except ClientError as e:
            if e.response["Error"]["Code"] in ("NoSuchKey", "404"):
                return default, None
            raise

    def _safe_write(self, key: str, mutate_fn, default, max_retries: int = 3):
        """
        Read-modify-write with optimistic concurrency.
        mutate_fn(data) modifies data in place and returns it.
        """
        for attempt in range(max_retries):
            data, etag = self._get_with_etag(key, default)
            mutated = mutate_fn(data)
            if self._put_json(key, mutated, etag=etag):
                return mutated
        # Last attempt without condition (etag=None) so it always succeeds
        data, _ = self._get_with_etag(key, default)
        mutated = mutate_fn(data)
        self._put_json(key, mutated)
        return mutated

    # ------------------------------------------------------------------
    # Trades
    # ------------------------------------------------------------------

    def get_all_trades(self) -> List[Dict]:
        return self._get_json(_TRADES_KEY, [])

    def get_trades(
        self,
        status: Optional[str] = None,
        instrument: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict]:
        trades = self.get_all_trades()
        if status:
            trades = [t for t in trades if t.get("status") == status.upper()]
        if instrument:
            trades = [t for t in trades if t.get("instrument") == instrument.upper()]
        trades.sort(key=lambda t: t.get("created_at", ""), reverse=True)
        return trades[offset : offset + limit]

    def get_trade_by_id(self, trade_id: int) -> Optional[Dict]:
        for t in self.get_all_trades():
            if t.get("id") == trade_id:
                return t
        return None

    def get_open_trades(self) -> List[Dict]:
        return self.get_trades(status="OPEN", limit=100)

    def save_trade(self, trade_data: Dict) -> int:
        """Append a new trade. Returns the new trade ID."""
        def mutate(trades: list):
            new_id = max((t.get("id", 0) for t in trades), default=0) + 1
            trade_data["id"] = new_id
            trade_data.setdefault("created_at", datetime.utcnow().isoformat())
            trade_data.setdefault("status", "OPEN")
            trades.append(trade_data)
            return trades

        self._safe_write(_TRADES_KEY, mutate, [])
        return trade_data["id"]

    def update_trade(self, trade_id: int, updates: Dict):
        """Update fields on an existing trade."""
        def mutate(trades: list):
            for trade in trades:
                if trade.get("id") == trade_id:
                    trade.update(updates)
                    break
            return trades

        self._safe_write(_TRADES_KEY, mutate, [])

    def update_trade_by_ticket(self, broker_ticket: str, updates: Dict):
        """Update trade by broker ticket (position ID from MetaAPI)."""
        def mutate(trades: list):
            for trade in trades:
                if trade.get("broker_ticket") == broker_ticket:
                    trade.update(updates)
                    break
            return trades

        self._safe_write(_TRADES_KEY, mutate, [])

    # ------------------------------------------------------------------
    # Daily P&L
    # ------------------------------------------------------------------

    def get_daily_pnl(self, days: int = 30) -> List[Dict]:
        """Compute daily P&L from trade history — used for charts."""
        since = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
        all_trades = self.get_all_trades()
        closed = [
            t for t in all_trades
            if t.get("status") == "CLOSED"
            and (t.get("timestamp", "") or "")[:10] >= since
        ]

        by_date: Dict[str, Dict] = {}
        for trade in closed:
            date = (trade.get("timestamp") or "")[:10]
            if not date:
                continue
            if date not in by_date:
                by_date[date] = {"date": date, "pnl": 0.0, "trades": 0, "wins": 0}
            by_date[date]["pnl"] += trade.get("pnl") or 0
            by_date[date]["trades"] += 1
            if (trade.get("pnl") or 0) > 0:
                by_date[date]["wins"] += 1

        # Fill full date range with zeros
        result = []
        for i in range(days):
            d = (datetime.utcnow() - timedelta(days=days - 1 - i)).strftime("%Y-%m-%d")
            row = by_date.get(d, {"date": d, "pnl": 0.0, "trades": 0, "wins": 0})
            row["pnl"] = round(row["pnl"], 4)
            result.append(row)
        return result

    def get_account_summary(self) -> Dict:
        """Compute dashboard summary from trade history."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        all_trades = self.get_all_trades()

        today_closed = [
            t for t in all_trades
            if t.get("status") == "CLOSED" and (t.get("timestamp") or "")[:10] == today
        ]
        today_pnl = sum(t.get("pnl") or 0 for t in today_closed)
        today_wins = sum(1 for t in today_closed if (t.get("pnl") or 0) > 0)
        today_win_rate = (today_wins / len(today_closed) * 100) if today_closed else 0.0

        open_trades = [t for t in all_trades if t.get("status") == "OPEN"]
        all_closed = [t for t in all_trades if t.get("status") == "CLOSED"]
        all_time_pnl = sum(t.get("pnl") or 0 for t in all_closed)
        all_wins = sum(1 for t in all_closed if (t.get("pnl") or 0) > 0)
        all_time_win_rate = (all_wins / len(all_closed) * 100) if all_closed else 0.0

        state = self.get_system_state()

        return {
            "today_pnl": round(today_pnl, 4),
            "today_trades": len(today_closed),
            "today_wins": today_wins,
            "today_win_rate": round(today_win_rate, 1),
            "open_trades": len(open_trades),
            "total_closed_trades": len(all_closed),
            "all_time_pnl": round(all_time_pnl, 4),
            "all_time_win_rate": round(all_time_win_rate, 1),
            "bot_status": state.get("bot_status", "RUNNING"),
            "kill_switch": state.get("kill_switch", False),
            "last_updated": datetime.utcnow().isoformat() + "Z",
        }

    # ------------------------------------------------------------------
    # System state
    # ------------------------------------------------------------------

    def get_system_state(self) -> Dict:
        return self._get_json(_STATE_KEY, {"kill_switch": False, "bot_status": "RUNNING"})

    def update_system_state(self, updates: Dict):
        def mutate(state: dict):
            state.update(updates)
            return state

        self._safe_write(_STATE_KEY, mutate, {"kill_switch": False, "bot_status": "RUNNING"})
