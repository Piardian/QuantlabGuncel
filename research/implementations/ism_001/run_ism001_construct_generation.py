from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

from ism001_industry_momentum_model import ISM001IndustryMomentumModel


THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[2]
INDUSTRY_RETURNS_FILE = REPO_ROOT / "data" / "ism_001" / "ken_french_49_industry_value_weighted_monthly.csv"
OUTPUT_DIR = REPO_ROOT / "output" / "ism_001"
STATE_FILE = OUTPUT_DIR / "ism001_industry_momentum_state.csv"
GENERATION_REPORT_FILE = OUTPUT_DIR / "ism001_generation_report.json"


def _repo_relative(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT)).replace("\\", "/")


def _hash_frame(frame: pd.DataFrame) -> str:
    payload = frame.to_csv(index=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def generate_construct_state() -> dict[str, object]:
    if not INDUSTRY_RETURNS_FILE.exists():
        raise FileNotFoundError(f"Missing ISM-001 industry returns file: {INDUSTRY_RETURNS_FILE}")

    industry_returns = pd.read_csv(INDUSTRY_RETURNS_FILE, index_col=0, parse_dates=True)
    model = ISM001IndustryMomentumModel()
    first = model.transform(industry_returns).frame
    second = model.transform(industry_returns).frame
    first_hash = _hash_frame(first)
    second_hash = _hash_frame(second)
    if first_hash != second_hash:
        raise AssertionError("ISM-001 empirical generation is not deterministic.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    first.to_csv(STATE_FILE, index=False)
    persisted = pd.read_csv(STATE_FILE, parse_dates=["month"])
    persisted_hash = _hash_frame(persisted)
    valid = first[first["ism_valid_observation"]]
    report = {
        "construct_id": "ISM-001",
        "stage": "IM-001 construct generation",
        "industry_returns_file": _repo_relative(INDUSTRY_RETURNS_FILE),
        "output_file": _repo_relative(STATE_FILE),
        "rows": int(first.shape[0]),
        "valid_rows": int(first["ism_valid_observation"].sum()),
        "unique_industries": int(first["industry_id"].nunique()),
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
