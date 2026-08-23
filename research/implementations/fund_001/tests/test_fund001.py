from __future__ import annotations

import math
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fund001_funding_stress_model import FUND001FundingStress  # noqa: E402


def _sample_frame(periods: int = 320) -> pd.DataFrame:
    dates = pd.bdate_range("2020-01-01", periods=periods)
    cp_values = [2.0 + index * 0.01 for index in range(periods)]
    tbill_values = [1.0 + index * 0.005 for index in range(periods)]
    return pd.DataFrame({"DATE": dates, "DCPF3M": cp_values, "DTB3": tbill_values})


def test_model_builds_required_columns_from_fred_style_input():
    result = FUND001FundingStress().transform(_sample_frame()).frame
    expected_columns = [
        "date",
        "fund001_cp_rate",
        "fund001_tbill_rate",
        "fund001_cp_tbill_spread",
        "fund001_zscore_252d",
        "fund001_percentile_252d",
        "fund001_valid_observation_count_252d",
        "fund001_data_quality_flag",
    ]
    assert list(result.columns) == expected_columns
    assert result["fund001_cp_tbill_spread"].notna().sum() == 320
    assert result.iloc[0]["fund001_valid_observation_count_252d"] == 1
    assert result["fund001_zscore_252d"].notna().sum() > 0
    assert result["fund001_percentile_252d"].notna().sum() > 0


def test_raw_spread_formula_is_cp_minus_tbill():
    result = FUND001FundingStress().transform(_sample_frame(5)).frame
    assert math.isclose(result.iloc[0]["fund001_cp_tbill_spread"], 1.0)
    assert math.isclose(result.iloc[4]["fund001_cp_tbill_spread"], 1.02)


def test_normalization_uses_252_valid_observations():
    result = FUND001FundingStress().transform(_sample_frame()).frame
    row = result.iloc[251]
    window = result["fund001_cp_tbill_spread"].iloc[:252]
    expected_z = (row["fund001_cp_tbill_spread"] - window.mean()) / window.std(ddof=0)
    assert row["fund001_valid_observation_count_252d"] == 252
    assert math.isclose(row["fund001_zscore_252d"], expected_z)
    assert math.isclose(row["fund001_percentile_252d"], 1.0)


def test_missing_inputs_are_not_forward_filled():
    data = pd.DataFrame(
        {
            "DATE": pd.bdate_range("2020-01-01", periods=4),
            "DCPF3M": [2.0, None, 2.2, 2.3],
            "DTB3": [1.0, 1.1, None, 1.2],
        }
    )
    result = FUND001FundingStress(normalization_window=2).transform(data).frame
    assert math.isnan(result.iloc[1]["fund001_cp_tbill_spread"])
    assert math.isnan(result.iloc[2]["fund001_cp_tbill_spread"])
    assert result.iloc[1]["fund001_data_quality_flag"] == "MISSING_INPUT"
    assert result.iloc[2]["fund001_data_quality_flag"] == "MISSING_INPUT"


def test_valid_observation_window_counts_valid_spreads_not_rows():
    data = _sample_frame(260)
    data.loc[10:20, "DCPF3M"] = None
    result = FUND001FundingStress().transform(data).frame
    assert result["fund001_zscore_252d"].notna().sum() == max(0, 249 - 251)
    assert result.iloc[-1]["fund001_valid_observation_count_252d"] == 249


def test_model_is_deterministic_on_identical_input():
    data = _sample_frame()
    model = FUND001FundingStress()
    first = model.transform(data).frame
    second = model.transform(data).frame
    pd.testing.assert_frame_equal(first, second)

