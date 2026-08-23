from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

from csm001_momentum_model import CSM001MomentumModel


ROOT = Path(__file__).resolve().parents[3]


def _hash_frame(frame: pd.DataFrame) -> str:
    payload = frame.to_csv(index=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _synthetic_close_panel() -> pd.DataFrame:
    dates = pd.bdate_range("2020-01-01", periods=320)
    data = {}
    for idx in range(60):
        ticker = f"T{idx:03d}"
        base = 100.0 + idx
        trend = np.linspace(0, idx * 0.05, len(dates))
        data[ticker] = base + trend + np.arange(len(dates)) * (0.01 + idx * 0.001)
    return pd.DataFrame(data, index=dates)


def run_validation() -> dict[str, object]:
    model = CSM001MomentumModel(minimum_eligible_count=50)
    panel = _synthetic_close_panel()
    first = model.transform(panel).frame
    second = model.transform(panel).frame

    expected_columns = [
        "date",
        "ticker",
        "adjusted_close",
        "price_t_minus_21",
        "price_t_minus_252",
        "return_12_1",
        "csm001_rank",
        "csm001_eligible_count",
        "csm001_momentum_score",
        "csm001_top_decile_flag",
        "csm001_valid_observation",
    ]
    if list(first.columns) != expected_columns:
        raise AssertionError("CSM-001 output schema mismatch.")
    if _hash_frame(first) != _hash_frame(second):
        raise AssertionError("CSM-001 execution is not deterministic.")

    valid = first[first["csm001_valid_observation"]]
    if valid.empty:
        raise AssertionError("Synthetic validation produced no valid observations.")
    if not valid["csm001_momentum_score"].between(0, 1).all():
        raise AssertionError("Momentum score must be bounded between 0 and 1.")
    if valid["csm001_eligible_count"].min() < 50:
        raise AssertionError("Valid dates must satisfy minimum eligible count.")

    latest_date = valid["date"].max()
    latest = valid[valid["date"] == latest_date].sort_values("return_12_1")
    if latest.iloc[-1]["csm001_momentum_score"] != 1.0:
        raise AssertionError("Highest return security should receive percentile score 1.0.")
    if latest.iloc[0]["csm001_momentum_score"] != 0.0:
        raise AssertionError("Lowest return security should receive percentile score 0.0.")

    rejected = False
    try:
        CSM001MomentumModel(formation_anchor_trading_days=251).transform(panel)
    except ValueError:
        rejected = True
    if not rejected:
        raise AssertionError("Frozen parameter guard failed.")

    rejected_minimum_count = False
    try:
        CSM001MomentumModel(minimum_eligible_count=49).transform(panel)
    except ValueError:
        rejected_minimum_count = True
    if not rejected_minimum_count:
        raise AssertionError("Frozen minimum eligible count guard failed.")

    return {
        "rows": int(len(first)),
        "valid_rows": int(first["csm001_valid_observation"].sum()),
        "first_valid_date": str(valid["date"].min().date()),
        "last_valid_date": str(valid["date"].max().date()),
        "deterministic_hash": _hash_frame(first),
        "status": "PASSED",
    }


if __name__ == "__main__":
    report = run_validation()
    for key, value in report.items():
        print(f"{key}: {value}")
