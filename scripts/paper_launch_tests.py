from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch
import pytest

from scripts.verify_preflight_integrity import (
    CANONICAL_UNIVERSE,
    FROZEN_RISK_LIMITS,
    compute_sha256,
    compute_universe_hash,
    run_preflight_checks,
    verify_alpaca_endpoint,
    verify_risk_guards,
    verify_strategy_configurations,
    verify_universe_integrity,
)
from scripts.paper_controlled_launch import (
    SNAPSHOT_FILE,
    enforce_stop_gate,
    ensure_preflight_report,
    generate_signal_snapshot,
    query_alpaca_account,
    query_alpaca_positions,
)


def test_universe_hash_determinism() -> None:
    hash1 = compute_universe_hash(CANONICAL_UNIVERSE)
    hash2 = compute_universe_hash(list(reversed(CANONICAL_UNIVERSE)))
    assert hash1 == hash2
    assert len(hash1) == 64


def test_alpaca_paper_endpoint_validation() -> None:
    res = verify_alpaca_endpoint("https://paper-api.alpaca.markets")
    assert res["status"] == "PASS"
    assert res["is_paper_endpoint"] is True

    res_live = verify_alpaca_endpoint("https://api.alpaca.markets")
    assert res_live["status"] == "FAIL"
    assert res_live["is_paper_endpoint"] is False


def test_strategy_configuration_integrity() -> None:
    res = verify_strategy_configurations()
    assert res["status"] == "PASS"
    assert "csm_001" in res
    assert "tsm_001" in res
    assert res["csm_001"]["verified"] is True
    assert res["tsm_001"]["verified"] is True


def test_risk_guards_validation() -> None:
    res = verify_risk_guards(FROZEN_RISK_LIMITS)
    assert res["status"] == "PASS"
    assert res["kill_switch_active"] is True

    invalid_limits = {
        "max_drawdown_limit_pct": 0.50,
        "max_single_position_pct": 0.80,
        "max_portfolio_leverage": 2.0,
        "kill_switch_enabled": False,
    }
    invalid_res = verify_risk_guards(invalid_limits)
    assert invalid_res["status"] == "FAIL"


def test_preflight_checks_execution(tmp_path: Path) -> None:
    report = run_preflight_checks()
    assert report["overall_status"] == "PASS"
    assert report["program_id"] == "PAPER-002"
    assert "checks" in report


def test_signal_snapshot_generation() -> None:
    rows = generate_signal_snapshot(CANONICAL_UNIVERSE)
    assert len(rows) == len(CANONICAL_UNIVERSE)
    assert SNAPSHOT_FILE.exists()
    assert rows[0]["status"] == "STAGE_A_READY"
    assert "target_weight" in rows[0]


def test_stop_gate_halt_behavior(capsys: pytest.CaptureFixture[str]) -> None:
    enforce_stop_gate(approved=False, dry_run=True)
    captured = capsys.readouterr().out
    assert "HUMAN APPROVAL REQUIRED - LAUNCH HALTED" in captured

    enforce_stop_gate(approved=True, dry_run=True)
    captured_approved = capsys.readouterr().out
    assert "İnsan onayı doğrulandı" in captured_approved
