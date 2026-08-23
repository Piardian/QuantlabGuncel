from __future__ import annotations

import math
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crd001_credit_stress import CRD001CreditStress  # noqa: E402


def _sample_fred_frame(periods: int = 320) -> pd.DataFrame:
    dates = pd.bdate_range("2020-01-01", periods=periods)
    values = [4.0 + index * 0.01 for index in range(periods)]
    return pd.DataFrame({"DATE": dates, "BAMLH0A0HYM2": values})


def test_model_builds_required_columns_from_fred_style_input():
    result = CRD001CreditStress().transform(_sample_fred_frame()).frame
    expected_columns = [
        "date",
        "crd001_hy_oas",
        "crd001_zscore_252d",
        "crd001_percentile_252d",
        "crd001_valid_observation_count_252d",
        "crd001_days_since_last_observation",
        "crd001_data_quality_flag",
    ]
    assert list(result.columns) == expected_columns
    assert result["crd001_hy_oas"].notna().sum() == 320
    assert result.iloc[0]["crd001_valid_observation_count_252d"] == 1
    assert result["crd001_zscore_252d"].notna().sum() > 0
    assert result["crd001_percentile_252d"].notna().sum() > 0


def test_normalization_uses_252_valid_observations():
    result = CRD001CreditStress().transform(_sample_fred_frame()).frame
    row = result.iloc[251]
    window = result["crd001_hy_oas"].iloc[:252]
    expected_z = (row["crd001_hy_oas"] - window.mean()) / window.std(ddof=0)
    assert row["crd001_valid_observation_count_252d"] == 252
    assert math.isclose(row["crd001_zscore_252d"], expected_z)
    assert math.isclose(row["crd001_percentile_252d"], 1.0)


def test_forward_fill_is_limited_to_five_calendar_days():
    data = pd.DataFrame(
        {
            "DATE": ["2020-01-01", "2020-01-02", "2020-01-10"],
            "BAMLH0A0HYM2": [4.0, 4.1, 4.2],
        }
    )
    result = CRD001CreditStress(normalization_window=2).transform(data).frame.set_index("date")
    assert not math.isnan(result.loc[pd.Timestamp("2020-01-07"), "crd001_hy_oas"])
    assert math.isnan(result.loc[pd.Timestamp("2020-01-08"), "crd001_hy_oas"])
    assert result.loc[pd.Timestamp("2020-01-08"), "crd001_data_quality_flag"] == "SOURCE_MISSING"


def test_model_is_deterministic_on_identical_input():
    data = _sample_fred_frame()
    model = CRD001CreditStress()
    first = model.transform(data).frame
    second = model.transform(data).frame
    pd.testing.assert_frame_equal(first, second)
