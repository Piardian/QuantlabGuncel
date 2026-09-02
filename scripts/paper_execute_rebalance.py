#!/usr/bin/env python3
"""PAPER-002 Controlled Paper Rebalance Executor.

Submits the 25 target stock buy orders to Alpaca Paper for the August 31, 2026
monthly signal, establishes PAPER_T0, and sends Telegram execution reports.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.alpaca_broker_adapter import AlpacaBrokerAdapter, BrokerMode
from engine.paper_trading_controller import PaperControllerConfig, PaperTradingController


def main() -> int:
    print("=" * 70)
    print("PAPER-002 CONTROLLED PROSPECTIVE REBALANCE EXECUTION")
    print("=" * 70)

    config = PaperControllerConfig(
        trading_enabled=True,
        paper_execution_enabled=True,
    )

    controller = PaperTradingController(config)
    now = datetime.now(timezone.utc)

    # 1. Verification of environment before execution
    broker_check = AlpacaBrokerAdapter.from_environment(
        broker_mode=BrokerMode.PAPER_MUTATION,
        trading_enabled=True,
    )
    if broker_check.paper_base_url != "https://paper-api.alpaca.markets":
        print("FATAL: Live trading endpoint detected. Halting execution immediately.", file=sys.stderr)
        return 1

    print(f"Environment: {broker_check.paper_base_url} (VERIFIED PAPER)")
    acc_status, account = broker_check.get_account()
    equity = float(account.get("equity", 0.0)) if isinstance(account, dict) else 0.0
    cash = float(account.get("cash", 0.0)) if isinstance(account, dict) else 0.0
    print(f"Initial Account Equity: ${equity:,.2f}")
    print(f"Initial Account Cash:   ${cash:,.2f}")

    # 2. Execute rebalance
    print("\nSubmitting 25 target equity orders (each ~$4,000 notional)...")
    res, submission_results = controller.execute_paper_rebalance(now=now)

    print(f"\nSubmissions Completed: {len(submission_results)} orders")
    for item in submission_results:
        symbol = item.get("symbol", "")
        notional = item.get("notional", 0.0)
        status = item.get("submission_status", "")
        broker_id = item.get("broker_order_id", "")
        broker_status = item.get("broker_order_status", "")
        print(f"  - {symbol:<6} | Notional: ${notional:,.2f} | Status: {status:<4} | BrokerID: {broker_id} ({broker_status})")

    print("\nExecution Summary:")
    print(f"  Orders Submitted: {res.orders_submitted}")
    print(f"  Broker Mutations: {res.broker_mutation_calls}")
    print(f"  PAPER_T0 State:   {res.paper_t0_established}")

    # 3. Post-execution account check
    acc_status2, account2 = broker_check.get_account()
    pos_status2, positions2 = broker_check.get_positions()
    ord_status2, orders2 = broker_check.get_open_orders()

    pos_count = len(positions2) if isinstance(positions2, list) else 0
    ord_count = len(orders2) if isinstance(orders2, list) else 0
    print(f"  Current Positions Count:   {pos_count}")
    print(f"  Current Open Orders Count: {ord_count}")

    # 4. Save submission log
    log_path = ROOT / "research" / "market_edge_discovery_program" / "paper_002_controlled_prospective_launch" / "paper002_submission_log.csv"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    import csv
    if submission_results:
        with log_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(submission_results[0].keys()))
            writer.writeheader()
            writer.writerows(submission_results)
        print(f"\nSubmission log written to {log_path}")

    return 0 if res.orders_submitted == 25 else 1


if __name__ == "__main__":
    raise SystemExit(main())
