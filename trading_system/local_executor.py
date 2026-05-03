"""
Local executor daemon — the HAND that acts on Cowork-Claude's decisions.

Claude (brain) writes to intent.json in the shared workspace folder.
This daemon watches for new intents, runs guardrails, and calls MT5.
Claude never touches MT5 directly. The daemon never decides what to trade.

Run once and leave it running on your laptop:
    python local_executor.py
    python local_executor.py --dry-run       # shadow mode — no real orders
    python local_executor.py --workspace C:\\jarvis-trader
"""
import sys
import json
import time
import yaml
import logging
import argparse
from pathlib import Path
from datetime import datetime, date

sys.path.insert(0, str(Path(__file__).parent))

from guardrails import Guardrails, GuardrailViolation
from mt5_client import MT5Client
from database import Database
from position_manager import PositionManager
from trade_logger import TradeLogger


def setup_logging(log_dir: Path):
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_dir / "executor.log"),
            logging.StreamHandler(),
        ],
    )


def load_config(path: Path) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def get_todays_pnl(db: Database) -> float:
    today = date.today().isoformat()
    return db.get_daily_pnl(today)


def touch_heartbeat(workspace: Path):
    """Write a timestamp so Cowork-Claude can check the daemon is alive."""
    hb = workspace / "executor_heartbeat.txt"
    hb.write_text(datetime.utcnow().isoformat())


def read_intent(intent_path: Path) -> dict | None:
    """Read and parse intent.json. Returns None if missing or malformed."""
    if not intent_path.exists():
        return None
    try:
        data = json.loads(intent_path.read_text(encoding="utf-8"))
        return data
    except Exception as e:
        logging.getLogger(__name__).warning(f"Could not parse intent.json: {e}")
        return None


def archive_intent(intent_path: Path, result: dict):
    """Move processed intent into intent_archive/ with result appended."""
    archive_dir = intent_path.parent / "intent_archive"
    archive_dir.mkdir(exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    archive = archive_dir / f"intent_{ts}.json"
    result["archived_at"] = datetime.utcnow().isoformat()
    archive.write_text(json.dumps(result, indent=2), encoding="utf-8")
    intent_path.unlink()


def write_result(workspace: Path, result: dict):
    """Append execution result to trade_log.jsonl for Cowork to read."""
    log_path = workspace / "trade_log.jsonl"
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(result) + "\n")


def execute_intent(
    intent: dict,
    broker: MT5Client,
    db: Database,
    position_manager: PositionManager,
    guardrails: Guardrails,
    trade_logger: TradeLogger,
    dry_run: bool,
    logger: logging.Logger,
) -> dict:
    """
    Validate and execute a single trade intent from Cowork-Claude.

    intent.json schema:
    {
        "action":       "BUY" | "SELL" | "CLOSE" | "HOLD",
        "symbol":       "EURUSD",
        "lots":         0.01,
        "stop_loss":    1.0800,
        "take_profit":  1.0900,
        "rationale":    "RSI oversold + EMA support",
        "confidence":   "A" | "A+" | "B",
        "generated_at": "2026-05-03T10:00:00"
    }
    """
    action = intent.get("action", "HOLD").upper()
    symbol = intent.get("symbol", "")
    lots = float(intent.get("lots", 0))
    stop_loss = intent.get("stop_loss")
    take_profit = intent.get("take_profit")
    rationale = intent.get("rationale", "")
    confidence = intent.get("confidence", "?")
    generated_at = intent.get("generated_at", "?")

    result = {
        "intent": intent,
        "executed_at": datetime.utcnow().isoformat(),
        "status": "pending",
        "message": "",
        "order": None,
    }

    logger.info(f"Intent received: {action} {lots} lots {symbol} [{confidence}] — {rationale}")

    # HOLD or CLOSE are informational — no order needed for HOLD
    if action == "HOLD":
        result["status"] = "skipped"
        result["message"] = "HOLD — no action taken"
        logger.info("Action is HOLD — no order placed")
        return result

    if action == "CLOSE":
        try:
            positions = broker.get_open_positions(symbol=symbol)
            if not positions:
                result["status"] = "skipped"
                result["message"] = f"CLOSE requested but no open position for {symbol}"
                logger.info(result["message"])
                return result

            closed = []
            for pos in positions:
                res = broker.close_position(pos["ticket"])
                closed.append(res)
                db_pos = position_manager.get_open_position(symbol)
                if db_pos:
                    position_manager.close_position(db_pos["id"], res["price"], "Cowork-CLOSE")
                trade_logger.log_position_closed(0, 0, "Cowork-CLOSE")
                logger.info(f"Closed position {pos['ticket']} for {symbol}")

            result["status"] = "closed"
            result["message"] = f"Closed {len(closed)} position(s) for {symbol}"
            result["order"] = closed
        except Exception as e:
            result["status"] = "error"
            result["message"] = f"Close failed: {e}"
            logger.error(result["message"])
        return result

    # BUY / SELL — run guardrails first
    open_count = len(db.get_open_trades())
    todays_pnl = get_todays_pnl(db)

    try:
        guardrails.check_all(
            action=action,
            symbol=symbol,
            lots=lots,
            stop_loss=stop_loss,
            take_profit=take_profit,
            current_open_count=open_count,
            todays_pnl=todays_pnl,
        )
    except GuardrailViolation as e:
        result["status"] = "blocked"
        result["message"] = f"GUARDRAIL: {e}"
        logger.warning(f"Trade blocked — {e}")
        trade_logger.log_error(f"Guardrail blocked {action} {symbol}: {e}")
        return result

    if dry_run:
        result["status"] = "dry_run"
        result["message"] = f"DRY RUN — would place {action} {lots} lots {symbol} SL={stop_loss} TP={take_profit}"
        logger.info(result["message"])
        trade_logger.log_signal(action, intent.get("entry_price", 0), symbol)
        return result

    # Place the order
    direction_lots = lots if action == "BUY" else -lots
    try:
        order = broker.place_market_order(
            instrument=symbol,
            units=direction_lots,
            direction=action,
            take_profit=take_profit,
            stop_loss=stop_loss,
        )
        signal = {
            "action": action,
            "entry_price": order["price"],
            "take_profit": take_profit,
            "stop_loss": stop_loss,
            "confidence": confidence,
        }
        trade_id = position_manager.open_position(order, signal)
        trade_logger.log_signal(action, order["price"], symbol)
        trade_logger.log_position_opened(lots, symbol)
        trade_logger.log_tp_sl(take_profit, stop_loss)

        result["status"] = "executed"
        result["message"] = f"Order placed — trade ID {trade_id}, order {order['order_id']}, filled @ {order['price']:.4f}"
        result["order"] = order
        logger.info(result["message"])
    except Exception as e:
        result["status"] = "error"
        result["message"] = f"Order failed: {e}"
        logger.error(result["message"])
        trade_logger.log_error(f"Order failed: {str(e)[:80]}")

    return result


def main():
    parser = argparse.ArgumentParser(description="Local MT5 executor daemon")
    parser.add_argument("--workspace", type=str, default="./workspace", help="Shared folder path (same folder Cowork uses)")
    parser.add_argument("--config", type=str, default="config.yaml", help="Config file")
    parser.add_argument("--dry-run", action="store_true", help="Shadow mode — no real orders")
    parser.add_argument("--poll", type=int, default=10, help="Poll interval in seconds (default: 10)")
    args = parser.parse_args()

    workspace = Path(args.workspace).expanduser().resolve()
    workspace.mkdir(parents=True, exist_ok=True)

    config_path = Path(__file__).parent / args.config
    if not config_path.exists():
        print(f"ERROR: Config not found: {config_path}")
        sys.exit(1)

    config = load_config(config_path)
    log_dir = workspace / "logs"
    setup_logging(log_dir)
    logger = logging.getLogger(__name__)

    dry_run = args.dry_run or config.get("risk", {}).get("demo_mode", True)

    logger.info("=" * 60)
    logger.info("LOCAL EXECUTOR DAEMON STARTING")
    logger.info(f"Workspace: {workspace}")
    logger.info(f"Dry-run: {dry_run}")
    logger.info("=" * 60)

    # Connect MT5
    mt5_cfg = config.get("mt5", {})
    try:
        broker = MT5Client(
            account=mt5_cfg["account"],
            password=mt5_cfg["password"],
            server=mt5_cfg["server"],
            path=mt5_cfg.get("path", ""),
        )
        logger.info("MT5 connected")
    except Exception as e:
        logger.error(f"MT5 connection failed: {e}")
        logger.error("Make sure MetaTrader 5 is running on this machine.")
        sys.exit(1)

    db = Database(config["database"]["path"])
    position_manager = PositionManager(db, broker)
    guardrails = Guardrails(config)
    trade_logger = TradeLogger(
        config.get("logging", {}).get("file", "./logs/trading.log").replace(".log", "_trades.log")
    )

    intent_path = workspace / "intent.json"

    logger.info(f"Watching {intent_path} — poll every {args.poll}s")
    logger.info("Ctrl+C to stop\n")

    try:
        while True:
            touch_heartbeat(workspace)

            intent = read_intent(intent_path)
            if intent is not None:
                logger.info(f"New intent detected — processing...")
                result = execute_intent(
                    intent=intent,
                    broker=broker,
                    db=db,
                    position_manager=position_manager,
                    guardrails=guardrails,
                    trade_logger=trade_logger,
                    dry_run=dry_run,
                    logger=logger,
                )
                write_result(workspace, result)
                archive_intent(intent_path, result)
                logger.info(f"Intent processed: {result['status']} — {result['message']}\n")

            time.sleep(args.poll)

    except KeyboardInterrupt:
        logger.info("Daemon stopped by user")
    finally:
        broker.shutdown()
        logger.info("MT5 connection closed")


if __name__ == "__main__":
    main()
