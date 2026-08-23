from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

from ism001_industry_momentum_model import ISM001IndustryMomentumModel


ROOT = Path(__file__).resolve().parents[3]


def _hash_frame(frame: pd.DataFrame) -> str:
    payload = frame.to_csv(index=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _synthetic_industry_returns() -> pd.DataFrame:
    months = pd.date_range("2010-01-31", periods=48, freq="ME")
    data = {}
    for idx in range(49):
        trend_component = np.linspace(-0.012, 0.018, len(months)) * (0.35 + idx * 0.012)
        seasonal_component = np.sin(np.arange(len(months)) / (4.0 + idx * 0.02)) * 0.002
        data[f"IND{idx:02d}"] = trend_component + seasonal_component + idx * 0.00015
    return pd.DataFrame(data, index=months)


def run_validation() -> dict[str, object]:
    model = ISM001IndustryMomentumModel()
    returns = _synthetic_industry_returns()
    first = model.transform(returns).frame
    second = model.transform(returns).frame

    expected_columns = [
        "month",
        "industry_id",
        "industry_name",
        "industry_return",
        "industry_return_12_1",
        "ism_rank",
        "ism_eligible_count",
        "ism_score",
        "ism_state",
        "ism_valid_observation",
    ]
    if list(first.columns) != expected_columns:
        raise AssertionError("ISM-001 output schema mismatch.")
    if _hash_frame(first) != _hash_frame(second):
        raise AssertionError("ISM-001 execution is not deterministic.")

    valid = first[first["ism_valid_observation"]]
    if valid.empty:
        raise AssertionError("Synthetic validation produced no valid observations.")
    if not valid["ism_score"].between(0, 1).all():
        raise AssertionError("ISM score must be bounded between 0 and 1.")
    if set(valid["ism_state"].unique()) - {"TOP_DECILE", "BOTTOM_DECILE", "MIDDLE"}:
        raise AssertionError("Unexpected ISM valid state label.")

    sampled_months = valid["month"].drop_duplicates().iloc[:: max(1, valid["month"].nunique() // 10)]
    monotonicity_violations = 0
    for month in sampled_months:
        sample = valid[valid["month"] == month].sort_values("industry_return_12_1")
        if len(sample) > 1 and (sample["ism_score"].diff().dropna() < -1e-12).any():
            monotonicity_violations += 1
    if monotonicity_violations:
        raise AssertionError("ISM rank monotonicity check failed.")

    rejected = False
    try:
        ISM001IndustryMomentumModel(formation_start_lag_months=11).transform(returns)
    except ValueError:
        rejected = True
    if not rejected:
        raise AssertionError("Frozen formation window guard failed.")

    data_file = ROOT / "data" / "ism_001" / "ken_french_49_industry_value_weighted_monthly.csv"

    return {
        "rows": int(len(first)),
        "valid_rows": int(first["ism_valid_observation"].sum()),
        "first_valid_month": str(valid["month"].min().date()),
        "last_valid_month": str(valid["month"].max().date()),
        "unique_industries": int(first["industry_id"].nunique()),
        "deterministic_hash": _hash_frame(first),
        "rank_monotonicity_violations": int(monotonicity_violations),
        "industry_returns_file_exists": bool(data_file.exists()),
        "repository_data_status": "AVAILABLE" if data_file.exists() else "BLOCKED_EXTERNAL_DATA_REQUIRED",
        "status": "PASSED_SYNTHETIC_VERIFICATION",
    }


if __name__ == "__main__":
    report = run_validation()
    for key, value in report.items():
        print(f"{key}: {value}")
