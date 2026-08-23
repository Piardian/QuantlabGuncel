from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.alpaca_broker_adapter import (
    AlpacaBrokerAdapter,
    BrokerMutationDisabled,
    MarketSessionState,
    ValidationStatus,
)


OUT_DIR = ROOT / "research" / "market_edge_discovery_program" / "alp_003_broker_adapter_order_safety_layer"
RESULTS_CSV = OUT_DIR / "alp003_test_results.csv"
OBSERVED_JSON = OUT_DIR / "alp003_observed_results.json"
AUDIT_LOG = OUT_DIR / "alp003_order_intent_audit_log.csv"


def result_row(name: str, expected: str, observed: str, passed: bool, notes: str = "") -> dict[str, Any]:
    return {
        "test_name": name,
        "expected": expected,
        "observed": observed,
        "pass": "YES" if passed else "NO",
        "notes": notes,
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    adapter = AlpacaBrokerAdapter.from_environment(audit_log_path=AUDIT_LOG)
    rows: list[dict[str, Any]] = []

    account_status, account_payload = adapter.get_account()
    positions_status, positions_payload = adapter.get_positions()
    orders_status, orders_payload = adapter.get_open_orders()
    asset_status, asset_payload = adapter.get_asset("AAPL")
    calendar_status, calendar_payload = adapter.get_calendar("2026-08-10", "2026-08-14")

    rows.append(result_row("broker_environment_paper", "PASS", adapter.paper_base_url, adapter.paper_base_url == "https://paper-api.alpaca.markets"))
    rows.append(result_row("account_read", "PASS", account_status, account_status == "PASS"))
    rows.append(result_row("positions_read", "PASS", positions_status, positions_status == "PASS"))
    rows.append(result_row("open_orders_read", "PASS", orders_status, orders_status == "PASS"))
    rows.append(result_row("asset_read", "PASS", asset_status, asset_status == "PASS"))
    rows.append(result_row("calendar_read", "PASS", calendar_status, calendar_status == "PASS"))

    now = datetime.now(timezone.utc)
    valid_buy = adapter.build_order_intent(
        strategy_id="CSMXTSM",
        portfolio_id="PAPER_DEV",
        rebalance_id="20260831",
        symbol="AAPL",
        source_asset_id=str(asset_payload.get("id", "AAPL")) if isinstance(asset_payload, dict) else "AAPL",
        side="buy",
        quantity=1,
        notional=None,
        order_type="market",
        time_in_force="day",
        reference_price=100.0,
        signal_timestamp=now.isoformat(),
        reason="synthetic_valid_buy_adapter_test",
    )
    buy_validation = adapter.validate_order_intent(valid_buy, asset=asset_payload, market_session_state=MarketSessionState.MARKET_OPEN, now=now)
    rows.append(result_row("valid_buy_intent", ValidationStatus.SUBMISSION_BLOCKED_ALP003.value, buy_validation.status, buy_validation.status == ValidationStatus.SUBMISSION_BLOCKED_ALP003.value))

    valid_sell = adapter.build_order_intent(
        strategy_id="CSMXTSM",
        portfolio_id="PAPER_DEV",
        rebalance_id="20260831",
        symbol="AAPL",
        source_asset_id=str(asset_payload.get("id", "AAPL")) if isinstance(asset_payload, dict) else "AAPL",
        side="sell",
        quantity=1,
        notional=None,
        order_type="market",
        time_in_force="day",
        reference_price=100.0,
        signal_timestamp=now.isoformat(),
        reason="synthetic_valid_sell_adapter_test",
        sequence=2,
    )
    sell_validation = adapter.validate_order_intent(valid_sell, asset=asset_payload, market_session_state=MarketSessionState.MARKET_OPEN, now=now)
    rows.append(result_row("valid_sell_intent", ValidationStatus.SUBMISSION_BLOCKED_ALP003.value, sell_validation.status, sell_validation.status == ValidationStatus.SUBMISSION_BLOCKED_ALP003.value))

    duplicate_validation = adapter.validate_order_intent(valid_buy, asset=asset_payload, market_session_state=MarketSessionState.MARKET_OPEN, now=now)
    rows.append(result_row("duplicate_intent", ValidationStatus.REJECTED_DUPLICATE.value, duplicate_validation.status, duplicate_validation.status == ValidationStatus.REJECTED_DUPLICATE.value))

    invalid_cases = [
        ("zero_quantity", {"quantity": 0}, ValidationStatus.REJECTED_INVALID.value),
        ("negative_quantity", {"quantity": -1}, ValidationStatus.REJECTED_INVALID.value),
        ("malformed_intent", {"side": "hold"}, ValidationStatus.REJECTED_INVALID.value),
    ]
    for idx, (name, override, expected) in enumerate(invalid_cases, start=10):
        intent = adapter.build_order_intent(
            strategy_id="CSMXTSM",
            portfolio_id="PAPER_DEV",
            rebalance_id="20260831",
            symbol="AAPL",
            source_asset_id=str(asset_payload.get("id", "AAPL")) if isinstance(asset_payload, dict) else "AAPL",
            side=override.get("side", "buy"),
            quantity=override.get("quantity", 1),
            notional=None,
            order_type="market",
            time_in_force="day",
            reference_price=100.0,
            signal_timestamp=now.isoformat(),
            reason=f"synthetic_{name}",
            sequence=idx,
        )
        validation = adapter.validate_order_intent(intent, asset=asset_payload, market_session_state=MarketSessionState.MARKET_OPEN, now=now)
        rows.append(result_row(name, expected, validation.status, validation.status == expected, ",".join(validation.errors)))

    unknown_intent = adapter.build_order_intent(
        strategy_id="CSMXTSM",
        portfolio_id="PAPER_DEV",
        rebalance_id="20260831",
        symbol="ZZZZ_UNKNOWN_TEST_SYMBOL",
        source_asset_id="UNKNOWN",
        side="buy",
        quantity=1,
        notional=None,
        order_type="market",
        time_in_force="day",
        reference_price=100.0,
        signal_timestamp=now.isoformat(),
        reason="synthetic_unknown_symbol",
        sequence=20,
    )
    unknown_validation = adapter.validate_order_intent(unknown_intent, asset=None, market_session_state=MarketSessionState.MARKET_OPEN, now=now)
    rows.append(result_row("unknown_symbol", ValidationStatus.REJECTED_INVALID.value, unknown_validation.status, unknown_validation.status == ValidationStatus.REJECTED_INVALID.value, ",".join(unknown_validation.errors)))

    non_tradable_asset = dict(asset_payload) if isinstance(asset_payload, dict) else {}
    non_tradable_asset["tradable"] = False
    non_tradable_intent = adapter.build_order_intent(
        strategy_id="CSMXTSM",
        portfolio_id="PAPER_DEV",
        rebalance_id="20260831",
        symbol="AAPL",
        source_asset_id=str(non_tradable_asset.get("id", "AAPL")),
        side="buy",
        quantity=1,
        notional=None,
        order_type="market",
        time_in_force="day",
        reference_price=100.0,
        signal_timestamp=now.isoformat(),
        reason="synthetic_non_tradable",
        sequence=21,
    )
    non_tradable_validation = adapter.validate_order_intent(non_tradable_intent, asset=non_tradable_asset, market_session_state=MarketSessionState.MARKET_OPEN, now=now)
    rows.append(result_row("non_tradable_asset", ValidationStatus.REJECTED_INVALID.value, non_tradable_validation.status, non_tradable_validation.status == ValidationStatus.REJECTED_INVALID.value, ",".join(non_tradable_validation.errors)))

    stale_intent = adapter.build_order_intent(
        strategy_id="CSMXTSM",
        portfolio_id="PAPER_DEV",
        rebalance_id="20260831",
        symbol="AAPL",
        source_asset_id=str(asset_payload.get("id", "AAPL")) if isinstance(asset_payload, dict) else "AAPL",
        side="buy",
        quantity=1,
        notional=None,
        order_type="market",
        time_in_force="day",
        reference_price=100.0,
        signal_timestamp=(now - timedelta(hours=2)).isoformat(),
        reason="synthetic_stale",
        sequence=22,
    )
    stale_validation = adapter.validate_order_intent(stale_intent, asset=asset_payload, market_session_state=MarketSessionState.MARKET_OPEN, now=now)
    rows.append(result_row("stale_intent", ValidationStatus.REJECTED_STALE_INTENT.value, stale_validation.status, stale_validation.status == ValidationStatus.REJECTED_STALE_INTENT.value, ",".join(stale_validation.errors)))

    market_closed_intent = adapter.build_order_intent(
        strategy_id="CSMXTSM",
        portfolio_id="PAPER_DEV",
        rebalance_id="20260831",
        symbol="AAPL",
        source_asset_id=str(asset_payload.get("id", "AAPL")) if isinstance(asset_payload, dict) else "AAPL",
        side="buy",
        quantity=1,
        notional=None,
        order_type="market",
        time_in_force="day",
        reference_price=100.0,
        signal_timestamp=now.isoformat(),
        reason="synthetic_market_closed",
        sequence=23,
    )
    closed_validation = adapter.validate_order_intent(market_closed_intent, asset=asset_payload, market_session_state=MarketSessionState.MARKET_CLOSED, now=now)
    rows.append(result_row("market_closed", ValidationStatus.REJECTED_MARKET_SESSION.value, closed_validation.status, closed_validation.status == ValidationStatus.REJECTED_MARKET_SESSION.value, ",".join(closed_validation.errors)))

    internal_positions = {"AAPL": 1.0}
    broker_positions_match = [{"symbol": "AAPL", "qty": "1"}]
    broker_positions_mismatch = [{"symbol": "AAPL", "qty": "2"}]
    position_match = adapter.reconcile_positions(internal_positions, broker_positions_match)
    position_mismatch = adapter.reconcile_positions(internal_positions, broker_positions_mismatch)
    zero_position_recon = adapter.reconcile_positions({}, positions_payload if isinstance(positions_payload, list) else [])
    rows.append(result_row("position_reconciliation_match", "MATCH", position_match.get("AAPL", ""), position_match.get("AAPL") == "MATCH"))
    rows.append(result_row("position_reconciliation_mismatch", "QUANTITY_MISMATCH", position_mismatch.get("AAPL", ""), position_mismatch.get("AAPL") == "QUANTITY_MISMATCH"))
    rows.append(result_row("zero_position_reconciliation", "MATCH_OR_EMPTY", json.dumps(zero_position_recon), bool(zero_position_recon)))

    order_recon = adapter.reconcile_orders([valid_buy], orders_payload if isinstance(orders_payload, list) else [])
    rows.append(result_row("order_reconciliation_intent_only", "INTENT_ONLY", order_recon.get(valid_buy.client_order_id, ""), order_recon.get(valid_buy.client_order_id) == "INTENT_ONLY"))

    try:
        adapter.submit_order(valid_buy)
        kill_switch_result = "NO_EXCEPTION"
    except BrokerMutationDisabled:
        kill_switch_result = "BLOCKED"
    rows.append(result_row("kill_switch_rejection", "BLOCKED", kill_switch_result, kill_switch_result == "BLOCKED"))

    try:
        AlpacaBrokerAdapter(
            paper_base_url="https://api.alpaca.markets",
            data_base_url="https://data.alpaca.markets",
            key_id="dummy",
            secret_key="dummy",
        )
        live_guard_result = "NO_EXCEPTION"
    except ValueError:
        live_guard_result = "BLOCKED"
    rows.append(result_row("live_environment_rejection", "BLOCKED", live_guard_result, live_guard_result == "BLOCKED"))

    with RESULTS_CSV.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = ["test_name", "expected", "observed", "pass", "notes"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    observed = {
        "program_id": "ALP-003",
        "execution_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "broker_environment": "PAPER",
        "broker_mutation_calls": adapter.broker_mutation_calls,
        "credential_leakage": "NO",
        "alpha_execution_performed": "NO",
        "backtest_performed": "NO",
        "performance_evaluation_performed": "NO",
        "scientific_t0_established": "NO",
        "tests_total": len(rows),
        "tests_passed": sum(1 for row in rows if row["pass"] == "YES"),
        "tests_failed": sum(1 for row in rows if row["pass"] != "YES"),
        "account_read": account_status,
        "positions_read": positions_status,
        "open_orders_read": orders_status,
        "asset_read": asset_status,
        "calendar_read": calendar_status,
    }
    OBSERVED_JSON.write_text(json.dumps(observed, indent=2), encoding="utf-8")
    print(json.dumps(observed, indent=2))
    return 0 if observed["tests_failed"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
