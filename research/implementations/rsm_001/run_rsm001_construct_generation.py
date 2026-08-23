from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

from rsm001_residual_momentum_model import RSM001ResidualMomentumModel


THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[2]
MONTHLY_RETURNS_FILE = REPO_ROOT / "data" / "rsm_001" / "monthly_returns.csv"
FACTOR_RETURNS_FILE = REPO_ROOT / "data" / "rsm_001" / "fama_french_3_factor_monthly.csv"
OUTPUT_DIR = REPO_ROOT / "output" / "rsm_001"
STATE_FILE = OUTPUT_DIR / "rsm001_residual_momentum_state.csv"
GENERATION_REPORT_FILE = OUTPUT_DIR / "rsm001_generation_report.json"


def _repo_relative(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT)).replace("\\", "/")


def _hash_frame(frame: pd.DataFrame) -> str:
    payload = frame.to_csv(index=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def generate_construct_state() -> dict[str, object]:
    if not MONTHLY_RETURNS_FILE.exists():
        raise FileNotFoundError(f"Missing monthly returns file: {MONTHLY_RETURNS_FILE}")
    if not FACTOR_RETURNS_FILE.exists():
        raise FileNotFoundError(f"Missing factor returns file: {FACTOR_RETURNS_FILE}")

    monthly_returns = pd.read_csv(MONTHLY_RETURNS_FILE, index_col=0, parse_dates=True)
    factor_returns = pd.read_csv(FACTOR_RETURNS_FILE, index_col=0, parse_dates=True)

    model = RSM001ResidualMomentumModel()
    first = model.transform(monthly_returns, factor_returns).frame
    second = model.transform(monthly_returns, factor_returns).frame
    first_hash = _hash_frame(first)
    second_hash = _hash_frame(second)
    if first_hash != second_hash:
        raise AssertionError("RSM-001 empirical generation is not deterministic.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    first.to_csv(STATE_FILE, index=False)
    persisted = pd.read_csv(STATE_FILE, parse_dates=["month"])
    persisted_hash = _hash_frame(persisted)
    valid = first[first["rsm_valid_observation"]]
    report = {
        "construct_id": "RSM-001",
        "stage": "IM-001 construct generation",
        "monthly_returns_file": _repo_relative(MONTHLY_RETURNS_FILE),
        "factor_returns_file": _repo_relative(FACTOR_RETURNS_FILE),
        "output_file": _repo_relative(STATE_FILE),
        "rows": int(first.shape[0]),
        "valid_rows": int(first["rsm_valid_observation"].sum()),
        "unique_tickers": int(first["ticker"].nunique()),
        "first_month": str(pd.to_datetime(first["month"]).min().date()),
        "last_month": str(pd.to_datetime(first["month"]).max().date()),
        "first_valid_month": str(pd.to_datetime(valid["month"]).min().date()) if len(valid) else None,
        "last_valid_month": str(pd.to_datetime(valid["month"]).max().date()) if len(valid) else None,
        "in_memory_deterministic_hash": first_hash,
        "persisted_artifact_hash": persisted_hash,
        "deterministic_hash": persisted_hash,
        "status": "COMPLETE",
    }
    GENERATION_REPORT_FILE.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(generate_construct_state(), indent=2))
