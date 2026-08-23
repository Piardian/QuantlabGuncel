from __future__ import annotations

import math
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from opt001_options_implied_model import OPT001OptionsImplied  # noqa: E402


def _sample_frame(periods: int = 320) -> pd.DataFrame:
    dates = pd.bdate_range("2020-01-01", periods=periods)
    values = [10.0 + index * 0.05 for index in range(periods)]
    return pd.DataFrame({"DATE": dates, "VIXCLS": values})


def test_model_builds_required_columns_from_fred_style_input():
    result = OPT001OptionsImplied().transform(_sample_frame()).frame
    expected_columns = [
        "date",
        "opt001_vix_close",
        "opt001_zscore_252d",
        "opt001_percentile_252d",
        "opt001_valid_observation_count_252d",
        "opt001_data_quality_flag",
    ]
    assert list(result.columns) == expected_columns
    assert result["opt001_vix_close"].notna().sum() == 320
    assert result.iloc[0]["opt001_valid_observation_count_252d"] == 1
    assert result["opt001_zscore_252d"].notna().sum() > 0
    assert result["opt001_percentile_252d"].notna().sum() > 0


def test_normalization_uses_252_valid_observations():
    result = OPT001OptionsImplied().transform(_sample_frame()).frame
    row = result.iloc[251]
    window = result["opt001_vix_close"].iloc[:252]
    expected_z = (row["opt001_vix_close"] - window.mean()) / window.std(ddof=0)
    assert row["opt001_valid_observation_count_252d"] == 252
    assert math.isclose(row["opt001_zscore_252d"], expected_z)
    assert math.isclose(row["opt001_percentile_252d"], 1.0)


def test_missing_inputs_are_not_forward_filled():
    data = pd.DataFrame({"DATE": pd.bdate_range("2020-01-01", periods=3), "VIXCLS": [12.0, None, 14.0]})
    result = OPT001OptionsImplied(normalization_window=2).transform(data).frame
    assert math.isnan(result.iloc[1]["opt001_vix_close"])
    assert result.iloc[1]["opt001_data_quality_flag"] == "MISSING_INPUT"


def test_non_positive_inputs_are_invalid():
    data = pd.DataFrame({"DATE": pd.bdate_range("2020-01-01", periods=4), "VIXCLS": [12.0, 0.0, -1.0, 13.0]})
    result = OPT001OptionsImplied(normalization_window=2).transform(data).frame
    assert math.isnan(result.iloc[1]["opt001_vix_close"])
    assert math.isnan(result.iloc[2]["opt001_vix_close"])
    assert result.iloc[1]["opt001_data_quality_flag"] == "INVALID_NON_POSITIVE"
    assert result.iloc[2]["opt001_data_quality_flag"] == "INVALID_NON_POSITIVE"


def test_model_accepts_observation_date_column():
    data = _sample_frame().rename(columns={"DATE": "observation_date"})
    result = OPT001OptionsImplied().transform(data).frame
    assert result["opt001_vix_close"].notna().sum() == 320


def test_model_is_deterministic_on_identical_input():
    data = _sample_frame()
    model = OPT001OptionsImplied()
    first = model.transform(data).frame
    second = model.transform(data).frame
    pd.testing.assert_frame_equal(first, second)

