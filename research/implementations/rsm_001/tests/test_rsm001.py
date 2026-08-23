from __future__ import annotations

from validate_rsm_001 import run_validation


def test_rsm001_synthetic_validation() -> None:
    report = run_validation()
    assert report["status"] == "PASSED_SYNTHETIC_VERIFICATION"
    assert report["valid_rows"] > 0

