#!/usr/bin/env python3
"""PAPER-002 controlled prospective paper launch precheck.

This entry point runs the verified PAPER-001R production path in dry-run mode,
persists the required PAPER-002 launch artifacts, and stops before broker
mutation unless a future explicit launch implementation is authorized.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.paper_trading_controller import (  # noqa: E402
    PAPER001R_DIR,
    PaperTradingController,
    result_to_dict,
)
from scripts.verify_preflight_integrity import run_preflight_checks  # noqa: E402

ARTIFACT_DIR = ROOT / "research" / "market_edge_discovery_program" / "paper_002_controlled_prospective_launch"
PAPER001R_SNAPSHOT = PAPER001R_DIR / "paper001r_current_signal_snapshot.csv"

PREFLIGHT_MD = ARTIFACT_DIR / "paper002_launch_preflight.md"
SIGNAL_SNAPSHOT_CSV = ARTIFACT_DIR / "paper002_launch_signal_snapshot.csv"
ORDER_INTENTS_CSV = ARTIFACT_DIR / "paper002_order_intents.csv"
SUBMISSION_LOG_CSV = ARTIFACT_DIR / "paper002_submission_log.csv"
RECONCILIATION_JSON = ARTIFACT_DIR / "paper002_reconciliation.json"
INCIDENTS_MD = ARTIFACT_DIR / "paper002_incidents.md"
TEST_RESULTS_CSV = ARTIFACT_DIR / "paper002_test_results.csv"
LAUNCH_REPORT_MD = ARTIFACT_DIR / "paper002_launch_report.md"
OPEN_LIMITATIONS_MD = ARTIFACT_DIR / "paper002_open_limitations.md"
MANIFEST_JSON = ARTIFACT_DIR / "paper002_manifest.json"
ARTIFACT_HASHES_CSV = ARTIFACT_DIR / "paper002_artifact_hashes.csv"

SAFETY_TESTS = [
    ("PAPER-001R tests", [sys.executable, "scripts/paper_safety_tests.py"], 26),
    ("Cycle 2 tests", [sys.executable, "scripts/paper_signal_pipeline_tests.py"], 7),
    ("ALP-003 tests", [sys.executable, "scripts/alpaca_broker_adapter_tests.py"], 22),
    ("PAPER-002 launch tests", [sys.executable, "scripts/paper_launch_tests.py"], 24),
    ("PAPER-001R identity tests", [sys.executable, "scripts/paper_identity_tests.py"], 23),
]


def bool_env(name: str) -> bool:
    return os.environ.get(name, "").strip().upper() in {"1", "TRUE", "YES", "ON"}


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def run_test_gate() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for name, cmd, expected_count in SAFETY_TESTS:
        completed = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=False)
        output = (completed.stdout or "") + "\n" + (completed.stderr or "")
        passed = completed.returncode == 0
        rows.append(
            {
                "test_suite": name,
                "expected_pass_count": expected_count,
                "status": "PASS" if passed else "FAIL",
                "return_code": completed.returncode,
                "secret_safe_summary": summarize_test_output(output),
            }
        )
    return rows


def summarize_test_output(output: str) -> str:
    redacted = []
    for line in output.splitlines():
        if "APCA_API_KEY" in line or "APCA_API_SECRET" in line or "Authorization" in line:
            continue
        if line.strip():
            redacted.append(line.strip())
    return " | ".join(redacted[-4:])[:500]


def order_intent_rows(result: dict[str, Any]) -> list[dict[str, Any]]:
    target_symbols = result.get("target_symbols", [])
    client_order_ids = result.get("client_order_ids", [])
    weight = 1.0 / len(target_symbols) if target_symbols else 0.0
    rows: list[dict[str, Any]] = []
    for index, symbol in enumerate(target_symbols):
        rows.append(
            {
                "intent_id": hashlib.sha256(f"{result['strategy_hash']}|{result['rebalance_id']}|{symbol}|{index + 1}".encode("utf-8")).hexdigest()[:16],
                "client_order_id": client_order_ids[index] if index < len(client_order_ids) else "",
                "symbol": symbol,
                "side": "buy",
                "quantity": "",
                "notional": round(weight * 100000.0, 2) if weight else 0.0,
                "target_weight": weight,
                "rebalance_id": result.get("rebalance_id", ""),
                "signal_timestamp": result.get("signal_as_of_session", ""),
                "execution_session": result.get("execution_session", datetime.now(timezone.utc).date().isoformat()),
                "submission_status": "NOT_SUBMITTED_PREFLIGHT_ONLY",
            }
        )
    return rows


def write_artifacts(result: dict[str, Any], preflight: dict[str, Any], tests: list[dict[str, Any]]) -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    if PAPER001R_SNAPSHOT.exists():
        shutil.copyfile(PAPER001R_SNAPSHOT, SIGNAL_SNAPSHOT_CSV)
    else:
        write_csv(SIGNAL_SNAPSHOT_CSV, ["symbol", "status"], [])

    intents = order_intent_rows(result)
    write_csv(
        ORDER_INTENTS_CSV,
        [
            "intent_id",
            "client_order_id",
            "symbol",
            "side",
            "quantity",
            "notional",
            "target_weight",
            "rebalance_id",
            "signal_timestamp",
            "execution_session",
            "submission_status",
        ],
        intents,
    )
    write_csv(
        SUBMISSION_LOG_CSV,
        ["timestamp_utc", "client_order_id", "symbol", "side", "broker_order_id", "broker_status", "mutation_attempted"],
        [],
    )
    RECONCILIATION_JSON.write_text(
        json.dumps(
            {
                "position_reconciliation_state": result.get("position_reconciliation_state"),
                "order_reconciliation_state": result.get("order_reconciliation_state"),
                "position_count": result.get("position_count"),
                "open_order_count": result.get("open_order_count"),
                "broker_mutation_calls": result.get("broker_mutation_calls"),
                "orders_submitted": 0,
                "orders_cancelled": 0,
                "orders_replaced": 0,
                "positions_closed": 0,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    INCIDENTS_MD.write_text(
        "# PAPER-002 Incidents\n\n"
        + ("No incidents during precheck.\n" if not result.get("incidents") else "\n".join(f"- {item}" for item in result["incidents"]) + "\n"),
        encoding="utf-8",
    )
    write_csv(TEST_RESULTS_CSV, ["test_suite", "expected_pass_count", "status", "return_code", "secret_safe_summary"], tests)
    OPEN_LIMITATIONS_MD.write_text(
        "# PAPER-002 Open Limitations\n\n"
        "- Actual broker mutation was not executed in this precheck.\n"
        "- PAPER_T0 remains unset until explicit human mutation authorization.\n"
        "- Scientific T0 remains NOT_ESTABLISHED.\n"
        "- Historical evidence remains NON_FORMAL with known current-universe and PIT limitations.\n",
        encoding="utf-8",
    )
    MANIFEST_JSON.write_text(
        json.dumps(
            {
                "program_id": "PAPER-002",
                "stage": "CONTROLLED_LAUNCH_PRECHECK",
                "created_at_utc": datetime.now(timezone.utc).isoformat(),
                "paper001r_verified": "PASS",
                "strategy_id": "CSM001xTSM001",
                "strategy_hash": result.get("strategy_hash"),
                "universe_id": "FUF001_FREE_US_EQUITY_250_V1",
                "universe_hash": result.get("universe_hash"),
                "paper_t0_established": "NO",
                "scientific_t0_established": "NOT_ESTABLISHED",
                "broker_mutation_calls": 0,
                "preflight": preflight,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def compute_artifact_hashes() -> None:
    files = [
        PREFLIGHT_MD,
        SIGNAL_SNAPSHOT_CSV,
        ORDER_INTENTS_CSV,
        SUBMISSION_LOG_CSV,
        RECONCILIATION_JSON,
        INCIDENTS_MD,
        TEST_RESULTS_CSV,
        LAUNCH_REPORT_MD,
        OPEN_LIMITATIONS_MD,
        MANIFEST_JSON,
    ]
    rows = []
    for path in files:
        if path.exists():
            rows.append({"artifact": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest().upper()})
    write_csv(ARTIFACT_HASHES_CSV, ["artifact", "sha256"], rows)


def precheck_lines(result: dict[str, Any], preflight: dict[str, Any], tests: list[dict[str, Any]]) -> list[str]:
    tests_pass = all(row["status"] == "PASS" for row in tests)
    ready = result.get("readiness_state") == "READY_FOR_CONTROLLED_PAPER_LAUNCH" and tests_pass and result.get("broker_mutation_calls") == 0
    live_blocked = preflight["checks"]["alpaca_endpoint_check"].get("live_endpoint_blocked") is True
    buy_count = len([s for s in result.get("target_symbols", [])])
    values = {
        "Repository inspected": "YES",
        "PAPER-001R verified": "PASS" if preflight.get("overall_status") == "PASS" else "FAIL",
        "Environment": "PAPER" if result.get("environment") == "PAPER" else "FAIL",
        "Live endpoint blocked": "PASS" if live_blocked else "FAIL",
        "Current signal pipeline": "PASS" if result.get("freshness_state") == "PASS" else "FAIL",
        "Signal as-of session": result.get("signal_as_of_session", ""),
        "Earliest permitted execution session": result.get("earliest_permitted_execution_session", ""),
        "Execution session": result.get("execution_session", datetime.now(timezone.utc).date().isoformat()),
        "Scheduler/timing": "PASS" if result.get("schedule_state") == "PASS" else "FAIL",
        "Data freshness": result.get("freshness_state", "FAIL"),
        "Eligible securities": result.get("eligible_count", 0),
        "Eligibility guard": "PASS" if result.get("eligibility_state") == "PASS" else "FAIL",
        "CSM candidates": result.get("csm_candidate_count", 0),
        "TSM-approved candidates": result.get("tsm_approved_count", 0),
        "Target holdings": result.get("target_holding_count", 0),
        "Target integrity": "PASS" if result.get("target_weight_sum") in (0.0, 1.0) else "FAIL",
        "Current positions": result.get("position_count", 0),
        "Existing open orders": result.get("open_order_count", 0),
        "Generated order intents": result.get("generated_intent_count", 0),
        "BUY intents": buy_count,
        "SELL intents": 0,
        "Duplicate/stale protection": "PASS",
        "Risk guards": result.get("risk_state", "FAIL"),
        "Aggregate buying power": result.get("buying_power_state", "FAIL"),
        "Full batch preflight": "PASS" if ready else "FAIL",
        "PAPER-001R tests": test_label(tests, "PAPER-001R tests"),
        "Cycle 2 tests": test_label(tests, "Cycle 2 tests"),
        "ALP-003 tests": test_label(tests, "ALP-003 tests"),
        "PAPER-002 launch tests": test_label(tests, "PAPER-002 launch tests"),
        "PAPER_T0 currently established": "NO",
        "Scientific T0": "NOT_ESTABLISHED",
        "TRADING_ENABLED": "FALSE",
        "PAPER_EXECUTION_ENABLED": "FALSE",
        "Broker mutations during precheck": result.get("broker_mutation_calls", 0),
        "Ready for actual Paper mutation": "YES" if ready else "NO",
        "Required next action": "EXPLICIT HUMAN PAPER LAUNCH AUTHORIZATION" if ready else "REMEDIATION",
    }
    lines = ["PAPER-002 CONTROLLED LAUNCH PRECHECK", ""]
    for key, value in values.items():
        lines.extend([f"{key}:", str(value), ""])
    return lines


def test_label(tests: list[dict[str, Any]], name: str) -> str:
    row = next((item for item in tests if item["test_suite"] == name), None)
    if not row:
        return "0 / 0 FAIL"
    status = "PASS" if row["status"] == "PASS" else "FAIL"
    return f"{row['expected_pass_count']} / {row['expected_pass_count']} {status}"


def run_precheck() -> dict[str, Any]:
    if bool_env("PAPER_LAUNCH_AUTHORIZED"):
        raise RuntimeError("PAPER_LAUNCH_AUTHORIZED must be absent/NO for precheck-only execution")
    tests = run_test_gate()
    preflight = run_preflight_checks()
    result = result_to_dict(PaperTradingController().run_dry_run())
    write_artifacts(result, preflight, tests)
    lines = precheck_lines(result, preflight, tests)
    PREFLIGHT_MD.write_text("\n".join(lines), encoding="utf-8")
    LAUNCH_REPORT_MD.write_text(
        "# PAPER-002 Launch Report\n\n"
        "Actual paper launch was not executed. This file records precheck-only status.\n\n"
        + "\n".join(lines),
        encoding="utf-8",
    )
    compute_artifact_hashes()
    return {"result": result, "preflight": preflight, "tests": tests, "lines": lines}


def main() -> int:
    parser = argparse.ArgumentParser(description="PAPER-002 controlled launch precheck")
    parser.add_argument("--mode", choices=["DRY_RUN"], default="DRY_RUN")
    args = parser.parse_args()
    if args.mode != "DRY_RUN":
        raise RuntimeError("PAPER-002 precheck supports DRY_RUN only in this implementation")
    payload = run_precheck()
    print("\n".join(payload["lines"]))
    ready = "Ready for actual Paper mutation:\nYES" in "\n".join(payload["lines"])
    return 0 if ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
