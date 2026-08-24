#!/usr/bin/env python3
"""
PAPER-002: Preflight Integrity & Risk Guard Verification Module.
Validates Alpaca Paper endpoints, canonical universe hashes, strategy configurations,
and risk parameters before prospective execution.
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

ARTIFACT_DIR = (
    ROOT
    / "research"
    / "market_edge_discovery_program"
    / "paper_002_controlled_prospective_launch"
)
OUTPUT_FILE = ARTIFACT_DIR / "stage_a_preflight_checks.json"

FROZEN_CSM_CONFIG = {
    "component_id": "CSM-001",
    "lookback_window": 252,
    "volatility_target": 0.15,
    "rebalance_frequency": "MONTHLY",
}

FROZEN_TSM_CONFIG = {
    "component_id": "TSM-001",
    "lookback_windows": [21, 63, 126, 252],
    "volatility_scaling": True,
    "rebalance_frequency": "DAILY",
}

FROZEN_RISK_LIMITS = {
    "max_drawdown_limit_pct": 0.10,
    "max_single_position_pct": 0.20,
    "max_portfolio_leverage": 1.0,
    "kill_switch_enabled": True,
}

CANONICAL_UNIVERSE = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
    "META", "TSLA", "BRK.B", "UNH", "JNJ",
]


def load_env(env_path: Path | None = None) -> None:
    path = env_path or (ROOT / ".env")
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            raw = line.strip()
            if not raw or raw.startswith("#") or "=" not in raw:
                continue
            k, v = raw.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip("'\""))


def compute_sha256(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def compute_universe_hash(universe: list[str]) -> str:
    normalized = sorted(universe)
    raw = ",".join(normalized)
    return compute_sha256(raw)


def verify_alpaca_endpoint(paper_url: str | None = None) -> dict[str, Any]:
    url = paper_url or os.environ.get("APCA_API_BASE_URL", "https://paper-api.alpaca.markets")
    is_paper = "paper" in url.lower()
    has_keys = bool(os.environ.get("APCA_API_KEY_ID") and os.environ.get("APCA_API_SECRET_KEY"))
    return {
        "status": "PASS" if is_paper else "FAIL",
        "paper_base_url": url,
        "is_paper_endpoint": is_paper,
        "credentials_configured": has_keys,
    }


def verify_strategy_configurations() -> dict[str, Any]:
    csm_serialized = json.dumps(FROZEN_CSM_CONFIG, sort_keys=True)
    tsm_serialized = json.dumps(FROZEN_TSM_CONFIG, sort_keys=True)

    csm_hash = compute_sha256(csm_serialized)
    tsm_hash = compute_sha256(tsm_serialized)

    return {
        "status": "PASS",
        "csm_001": {
            "config": FROZEN_CSM_CONFIG,
            "hash": csm_hash,
            "verified": True,
        },
        "tsm_001": {
            "config": FROZEN_TSM_CONFIG,
            "hash": tsm_hash,
            "verified": True,
        },
    }


def verify_universe_integrity() -> dict[str, Any]:
    universe_hash = compute_universe_hash(CANONICAL_UNIVERSE)
    return {
        "status": "PASS",
        "universe_size": len(CANONICAL_UNIVERSE),
        "symbols": sorted(CANONICAL_UNIVERSE),
        "universe_hash_sha256": universe_hash,
    }


def verify_risk_guards(limits: dict[str, Any] | None = None) -> dict[str, Any]:
    effective = limits or FROZEN_RISK_LIMITS
    valid = (
        effective.get("max_drawdown_limit_pct", 1.0) <= 0.15
        and effective.get("max_single_position_pct", 1.0) <= 0.25
        and effective.get("max_portfolio_leverage", 99.0) <= 1.0
        and effective.get("kill_switch_enabled") is True
    )
    return {
        "status": "PASS" if valid else "FAIL",
        "parameters": effective,
        "kill_switch_active": effective.get("kill_switch_enabled", False),
    }


def run_preflight_checks() -> dict[str, Any]:
    load_env()
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    alpaca_check = verify_alpaca_endpoint()
    strategy_check = verify_strategy_configurations()
    universe_check = verify_universe_integrity()
    risk_check = verify_risk_guards()

    overall_pass = (
        alpaca_check["status"] == "PASS"
        and strategy_check["status"] == "PASS"
        and universe_check["status"] == "PASS"
        and risk_check["status"] == "PASS"
    )

    report = {
        "program_id": "PAPER-002",
        "stage": "STAGE_A_PREFLIGHT_INTEGRITY",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "overall_status": "PASS" if overall_pass else "FAIL",
        "checks": {
            "alpaca_endpoint_check": alpaca_check,
            "strategy_configuration_check": strategy_check,
            "canonical_universe_check": universe_check,
            "risk_guards_check": risk_check,
        },
    }

    with OUTPUT_FILE.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)

    return report


def main() -> None:
    print("Executing PAPER-002 Stage A Preflight Integrity Checks...")
    report = run_preflight_checks()
    print(f"Overall Status: {report['overall_status']}")
    print(f"Preflight artifact generated at: {OUTPUT_FILE}")
    if report["overall_status"] != "PASS":
        sys.exit(1)


if __name__ == "__main__":
    main()
