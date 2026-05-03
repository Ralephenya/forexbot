"""
Hard guardrails — code-level risk limits that Claude cannot talk its way past.

These run BEFORE any order reaches MT5. If any check fails, the trade is blocked
and the reason is logged. No exceptions, no overrides from the prompt layer.
"""
import logging
from datetime import datetime, time
from typing import Optional

logger = logging.getLogger(__name__)

# Hard-coded absolute maximums — not configurable from YAML
ABSOLUTE_MAX_LOTS = 0.10          # Never more than 0.10 lots per trade regardless of config
ABSOLUTE_MAX_DAILY_LOSS = 100.0   # Never lose more than $100/day regardless of config
ABSOLUTE_MAX_OPEN = 3             # Never more than 3 open positions total


class GuardrailViolation(Exception):
    """Raised when a guardrail check fails."""
    pass


class Guardrails:
    def __init__(self, config: dict):
        self.risk = config.get("risk", {})
        self.allowed_symbols = config.get("allowed_symbols", ["EURUSD", "GBPJPY", "USDJPY", "AUDUSD", "GBPUSD"])
        self.max_lots = min(float(self.risk.get("position_size", 0.01)), ABSOLUTE_MAX_LOTS)
        self.max_daily_loss = min(float(self.risk.get("max_daily_loss", 50.0)), ABSOLUTE_MAX_DAILY_LOSS)
        self.max_open = min(int(self.risk.get("max_open_positions", 1)), ABSOLUTE_MAX_OPEN)
        self.demo_mode = self.risk.get("demo_mode", True)

    def check_all(
        self,
        action: str,
        symbol: str,
        lots: float,
        stop_loss: Optional[float],
        take_profit: Optional[float],
        current_open_count: int,
        todays_pnl: float,
    ) -> None:
        """
        Run all guardrail checks. Raises GuardrailViolation if any fail.
        Call this before placing ANY order.
        """
        self._check_action(action)
        self._check_symbol(symbol)
        self._check_lots(lots)
        self._check_sl_required(stop_loss)
        self._check_tp_required(take_profit)
        self._check_open_positions(current_open_count)
        self._check_daily_loss(todays_pnl)
        self._check_market_hours()
        logger.info(f"All guardrails passed: {action} {lots} lots {symbol}")

    def _check_action(self, action: str):
        if action not in ("BUY", "SELL"):
            raise GuardrailViolation(f"Invalid action '{action}' — must be BUY or SELL")

    def _check_symbol(self, symbol: str):
        if symbol not in self.allowed_symbols:
            raise GuardrailViolation(
                f"Symbol '{symbol}' not in whitelist {self.allowed_symbols}"
            )

    def _check_lots(self, lots: float):
        if lots <= 0:
            raise GuardrailViolation(f"Lot size must be positive, got {lots}")
        if lots > self.max_lots:
            raise GuardrailViolation(
                f"Lot size {lots} exceeds max {self.max_lots} (absolute cap: {ABSOLUTE_MAX_LOTS})"
            )

    def _check_sl_required(self, stop_loss: Optional[float]):
        if stop_loss is None or stop_loss <= 0:
            raise GuardrailViolation("Stop loss is required — no order without SL")

    def _check_tp_required(self, take_profit: Optional[float]):
        if take_profit is None or take_profit <= 0:
            raise GuardrailViolation("Take profit is required — no order without TP")

    def _check_open_positions(self, current_open_count: int):
        if current_open_count >= self.max_open:
            raise GuardrailViolation(
                f"Max open positions reached: {current_open_count}/{self.max_open}"
            )

    def _check_daily_loss(self, todays_pnl: float):
        if todays_pnl < 0 and abs(todays_pnl) >= self.max_daily_loss:
            raise GuardrailViolation(
                f"Daily loss limit hit: ${todays_pnl:.2f} (limit: -${self.max_daily_loss:.2f})"
            )

    def _check_market_hours(self):
        """Block trading during weekend close (Sat 22:00 — Sun 22:00 UTC)."""
        now = datetime.utcnow()
        weekday = now.weekday()  # 0=Mon … 6=Sun
        t = now.time()

        if weekday == 5:  # Saturday — always closed
            raise GuardrailViolation("Market closed — Saturday")
        if weekday == 6 and t < time(22, 0):  # Sunday before 22:00 UTC
            raise GuardrailViolation("Market closed — Sunday before 22:00 UTC")
