from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.alpaca_broker_adapter import AlpacaBrokerAdapter
from engine.paper_trading_controller import PaperControllerConfig, PaperTradingController
from telegram_notifier import TelegramNotifier


def run_telegram_status(now: datetime | None = None, *, send_message: bool = True) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    config = PaperControllerConfig()
    controller = PaperTradingController(config)
    broker = AlpacaBrokerAdapter.from_environment()

    # Read-only verification
    if broker.paper_base_url != "https://paper-api.alpaca.markets":
        raise RuntimeError("BLOCKED_NON_PAPER_ENVIRONMENT")

    # Read account state
    acc_status, account = broker.get_account()
    pos_status, positions = broker.get_positions()
    ord_status, orders = broker.get_open_orders()

    equity = float(account.get("equity", 100000.0)) if isinstance(account, dict) else 100000.0
    cash = float(account.get("cash", 100000.0)) if isinstance(account, dict) else 100000.0
    positions_count = len(positions) if isinstance(positions, list) else 0
    open_orders_count = len(orders) if isinstance(orders, list) else 0

    # Run dry run precheck
    result = controller.run_dry_run(now=now)

    notifier = TelegramNotifier()
    msg_sent = False

    if send_message and notifier.enabled:
        if result.readiness_state == "BLOCKED" and result.incidents:
            msg_sent = notifier.send_csm_tsm_block_alert(
                alert_type="PRECHECK_BLOCK",
                state=result.readiness_state,
                block_reason=result.block_reason,
                incidents=result.incidents,
            )
        elif result.monthly_rebalance_due:
            msg_sent = notifier.send_csm_tsm_monthly_signal(
                signal_session=result.signal_as_of_session,
                eligible_count=result.eligible_count,
                csm_candidates=result.csm_candidate_count,
                tsm_approved=result.tsm_approved_count,
                target_holdings=result.target_holding_count,
                target_weight=result.target_weight_sum,
                identity_state=result.identity_readiness_state,
                data_state=result.freshness_state,
                earliest_execution=result.earliest_permitted_execution_session or result.execution_session,
                orders_submitted=result.orders_submitted,
                status="SIGNAL_READY_WAITING_FOR_T+1",
            )
        else:
            msg_sent = notifier.send_csm_tsm_daily_status(
                account_equity=equity,
                cash=cash,
                positions_count=positions_count,
                open_orders_count=open_orders_count,
                system_state="PASS" if result.identity_readiness_state == "PASS" else "FAIL",
                controller_state=result.readiness_state,
                rebalance_due=result.monthly_rebalance_due,
                next_signal=result.next_legitimate_signal_session,
                earliest_execution=result.earliest_legitimate_execution_session,
                action_today="NONE",
            )

    return {
        "status": "SUCCESS",
        "equity": equity,
        "cash": cash,
        "positions_count": positions_count,
        "open_orders_count": open_orders_count,
        "readiness_state": result.readiness_state,
        "identity_readiness_state": result.identity_readiness_state,
        "monthly_rebalance_due": result.monthly_rebalance_due,
        "next_signal": result.next_legitimate_signal_session,
        "earliest_execution": result.earliest_legitimate_execution_session,
        "telegram_enabled": notifier.enabled,
        "telegram_sent": msg_sent,
        "broker_mutations": broker.broker_mutation_calls,
        "orders_submitted": result.orders_submitted,
    }


def main() -> int:
    try:
        res = run_telegram_status()
        print(f"Telegram status reporter finished: {res['readiness_state']} (Telegram sent: {res['telegram_sent']})")
        return 0
    except Exception as exc:
        print(f"Telegram status reporter failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
