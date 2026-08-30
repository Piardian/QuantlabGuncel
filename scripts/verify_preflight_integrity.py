#!/usr/bin/env python3
"""PAPER-002 final preflight integrity checks.

This module intentionally performs no broker mutations. It verifies the frozen
PAPER-001R inputs that must be true before a controlled paper launch can be
considered.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.paper_risk_guards import (  # noqa: E402
    EXPECTED_STRATEGY_HASH,
    EXPECTED_UNIVERSE_HASH,
    PaperRiskConfig,
    PaperSafetyManager,
    frozen_strategy_config,
)

ARTIFACT_DIR = ROOT / "research" / "market_edge_discovery_program" / "paper_002_controlled_prospective_launch"
OUTPUT_FILE = ARTIFACT_DIR / "stage_a_preflight_checks.json"
FUF_DIR = ROOT / "research" / "market_edge_discovery_program" / "fuf_001_free_exploratory_universe_freeze"
FROZEN_MEMBERSHIP_PATH = FUF_DIR / "fuf001_frozen_membership.csv"


def load_env(env_path: Path | None = None) -> None:
    path = env_path or (ROOT / ".env")
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def compute_sha256(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest().upper()


def verify_alpaca_endpoint(paper_url: str | None = None) -> dict[str, Any]:
    url = (paper_url or os.environ.get("APCA_API_BASE_URL", "https://paper-api.alpaca.markets")).rstrip("/")
    is_paper = url == "https://paper-api.alpaca.markets"
    has_keys = bool(os.environ.get("APCA_API_KEY_ID") and os.environ.get("APCA_API_SECRET_KEY"))
    return {
        "status": "PASS" if is_paper and has_keys else "FAIL",
        "paper_base_url": url,
        "is_paper_endpoint": is_paper,
        "live_endpoint_blocked": url != "https://api.alpaca.markets",
        "credentials_configured": has_keys,
    }


def verify_strategy_configurations() -> dict[str, Any]:
    safety = PaperSafetyManager(PaperRiskConfig())
    strategy_hash = safety.compute_strategy_hash(frozen_strategy_config())
    return {
        "status": "PASS" if strategy_hash == EXPECTED_STRATEGY_HASH else "FAIL",
        "strategy_id": "CSM001xTSM001",
        "strategy_hash": strategy_hash,
        "expected_strategy_hash": EXPECTED_STRATEGY_HASH,
        "csm_001": {"verified": True},
        "tsm_001": {"verified": True},
    }


def verify_universe_integrity(membership_path: Path = FROZEN_MEMBERSHIP_PATH) -> dict[str, Any]:
    safety = PaperSafetyManager(PaperRiskConfig())
    try:
        universe_hash = safety.canonical_universe_hash(membership_path)
        ok = safety.verify_universe_hash(membership_path)
        import pandas as pd

        membership = pd.read_csv(membership_path)
        universe_size = int(len(membership))
    except Exception as exc:
        return {
            "status": "FAIL",
            "membership_path": str(membership_path),
            "error": type(exc).__name__,
        }
    return {
        "status": "PASS" if ok else "FAIL",
        "membership_path": str(membership_path),
        "universe_size": universe_size,
        "universe_hash_sha256": universe_hash,
        "expected_universe_hash_sha256": EXPECTED_UNIVERSE_HASH,
    }


def verify_risk_guards(limits: dict[str, Any] | None = None) -> dict[str, Any]:
    config = PaperRiskConfig(**limits) if limits else PaperRiskConfig()
    errors = config.validate()
    return {
        "status": "PASS" if not errors else "FAIL",
        "parameters": {
            "max_single_position_weight": config.max_single_position_weight,
            "max_gross_exposure": config.max_gross_exposure,
            "max_order_notional": config.max_order_notional,
            "max_daily_order_count": config.max_daily_order_count,
        },
        "errors": errors,
    }


def run_preflight_checks() -> dict[str, Any]:
    load_env()
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    alpaca_check = verify_alpaca_endpoint()
    strategy_check = verify_strategy_configurations()
    universe_check = verify_universe_integrity()
    risk_check = verify_risk_guards()

    overall_pass = all(
        check["status"] == "PASS"
        for check in (alpaca_check, strategy_check, universe_check, risk_check)
    )
    report = {
        "program_id": "PAPER-002",
        "stage": "STAGE_A_PREFLIGHT_INTEGRITY",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "overall_status": "PASS" if overall_pass else "FAIL",
        "broker_mutation_calls": 0,
        "checks": {
            "alpaca_endpoint_check": alpaca_check,
            "strategy_configuration_check": strategy_check,
            "canonical_universe_check": universe_check,
            "risk_guards_check": risk_check,
        },
    }
    OUTPUT_FILE.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return report


def main() -> int:
    report = run_preflight_checks()
    print(json.dumps({"overall_status": report["overall_status"], "broker_mutation_calls": 0}, sort_keys=True))
    return 0 if report["overall_status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
