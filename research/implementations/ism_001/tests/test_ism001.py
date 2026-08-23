from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

IMPLEMENTATION_DIR = Path(__file__).resolve().parents[1]
if str(IMPLEMENTATION_DIR) not in sys.path:
    sys.path.insert(0, str(IMPLEMENTATION_DIR))

from ism001_industry_momentum_model import ISM001IndustryMomentumModel


def synthetic_returns() -> pd.DataFrame:
    months = pd.date_range("2018-01-31", periods=36, freq="ME")
    return pd.DataFrame(
        {f"IND{idx:02d}": np.linspace(-0.01, 0.02, len(months)) + idx * 0.0002 for idx in range(49)},
        index=months,
    )


def test_schema_and_valid_states() -> None:
    result = ISM001IndustryMomentumModel().transform(synthetic_returns()).frame
    assert list(result.columns) == [
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
    valid = result[result["ism_valid_observation"]]
    assert len(valid) > 0
    assert valid["ism_score"].between(0, 1).all()
    assert set(valid["ism_state"].unique()).issubset({"TOP_DECILE", "BOTTOM_DECILE", "MIDDLE"})


def test_frozen_parameter_guard() -> None:
    try:
        ISM001IndustryMomentumModel(minimum_valid_industries=29).transform(synthetic_returns())
    except ValueError:
        return
    raise AssertionError("Expected frozen parameter guard to reject modified minimum_valid_industries.")
