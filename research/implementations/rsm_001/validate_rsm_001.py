from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

from rsm001_residual_momentum_model import RSM001ResidualMomentumModel


ROOT = Path(__file__).resolve().parents[3]


def _hash_frame(frame: pd.DataFrame) -> str:
    payload = frame.to_csv(index=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _synthetic_monthly_returns() -> pd.DataFrame:
    months = pd.date_range("2015-01-31", periods=72, freq="ME")
    base = np.linspace(-0.02, 0.025, len(months))
    data = {}
    for idx in range(30):
        idio = np.sin(np.arange(len(months)) / (3.0 + idx * 0.05)) * (0.002 + idx * 0.0001)
        data[f"T{idx:03d}"] = base * (0.4 + idx * 0.015) + idio + idx * 0.0002
    return pd.DataFrame(data, index=months)


def _synthetic_factors() -> pd.DataFrame:
    months = pd.date_range("2015-01-31", periods=72, freq="ME")
    return pd.DataFrame(
        {
            "mkt_rf": np.linspace(-0.01, 0.015, len(months)),
            "smb": np.sin(np.arange(len(months)) / 5.0) * 0.003,
            "hml": np.cos(np.arange(len(months)) / 7.0) * 0.002,
            "rf": np.full(len(months), 0.001),
        },
        index=months,
    )


def run_validation() -> dict[str, object]:
    model = RSM001ResidualMomentumModel()
    returns = _synthetic_monthly_returns()
    factors = _synthetic_factors()
    first = model.transform(returns, factors).frame
    second = model.transform(returns, factors).frame

    expected_columns = [
        "month",
        "ticker",
        "monthly_return",
        "rf",
        "mkt_rf",
        "smb",
        "hml",
        "excess_return",
        "residual_return",
        "residual_sum_12_1",
        "residual_vol_36m",
        "rsm_score",
        "rsm_rank",
        "rsm_eligible_count",
        "rsm_percentile",
        "rsm_state",
        "rsm_valid_observation",
    ]
    if list(first.columns) != expected_columns:
        raise AssertionError("RSM-001 output schema mismatch.")
    if _hash_frame(first) != _hash_frame(second):
        raise AssertionError("RSM-001 execution is not deterministic.")

    valid = first[first["rsm_valid_observation"]]
    if valid.empty:
        raise AssertionError("Synthetic validation produced no valid observations.")
    if not valid["rsm_percentile"].between(0, 1).all():
        raise AssertionError("RSM percentile must be bounded between 0 and 1.")
    if set(valid["rsm_state"].unique()) - {"TOP_DECILE", "BOTTOM_DECILE", "MIDDLE"}:
        raise AssertionError("Unexpected RSM valid state label.")

    rejected = False
    try:
        RSM001ResidualMomentumModel(regression_window_months=35).transform(returns, factors)
    except ValueError:
        rejected = True
    if not rejected:
        raise AssertionError("Frozen regression window guard failed.")

    missing_factor_rejected = False
    try:
        model.transform(returns, factors.drop(columns=["hml"]))
    except ValueError:
        missing_factor_rejected = True
    if not missing_factor_rejected:
        raise AssertionError("Missing factor guard failed.")

    data_dir = ROOT / "data" / "rsm_001"
    factor_file_exists = (data_dir / "fama_french_3_factor_monthly.csv").exists()
    monthly_returns_file_exists = (data_dir / "monthly_returns.csv").exists()

    return {
        "rows": int(len(first)),
        "valid_rows": int(first["rsm_valid_observation"].sum()),
        "first_valid_month": str(valid["month"].min().date()),
        "last_valid_month": str(valid["month"].max().date()),
        "deterministic_hash": _hash_frame(first),
        "monthly_returns_file_exists": bool(monthly_returns_file_exists),
        "factor_file_exists": bool(factor_file_exists),
        "repository_data_status": "AVAILABLE" if factor_file_exists and monthly_returns_file_exists else "BLOCKED_EXTERNAL_DATA_REQUIRED",
        "status": "PASSED_SYNTHETIC_VERIFICATION",
    }


if __name__ == "__main__":
    report = run_validation()
    for key, value in report.items():
        print(f"{key}: {value}")

