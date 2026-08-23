from __future__ import annotations

import math

import pandas as pd

from feature_pipeline import VolatilityFeaturePipeline
from vol001_volatility_model import VOL001VolatilityModel


def _sample_ohlc(periods: int = 320) -> pd.DataFrame:
    dates = pd.date_range("2020-01-01", periods=periods, freq="B")
    rows = []
    for index, _date in enumerate(dates):
        open_price = 100.0 + index * 0.15
        high = open_price * 1.012
        low = open_price * 0.991
        close = open_price * (1.002 if index % 2 == 0 else 0.998)
        rows.append({"Open": open_price, "High": high, "Low": low, "Close": close})
    return pd.DataFrame(rows, index=dates)


def test_feature_pipeline_follows_cd001_return_formula():
    data = pd.DataFrame(
        [
            {"Open": 100.0, "High": 103.0, "Low": 98.0, "Close": 101.0},
            {"Open": 102.0, "High": 105.0, "Low": 100.0, "Close": 104.0},
        ],
        index=pd.date_range("2020-01-01", periods=2, freq="B"),
    )
    features = VolatilityFeaturePipeline(vol_window=2, normalization_window=2).build_features(data)
    row = features.iloc[1]
    expected_overnight = math.log(102.0 / 101.0)
    expected_open_to_close = math.log(104.0 / 102.0)
    expected_rs = math.log(105.0 / 102.0) * math.log(105.0 / 104.0)
    expected_rs += math.log(100.0 / 102.0) * math.log(100.0 / 104.0)
    assert row["vol001_valid_observation"]
    assert math.isclose(row["overnight_return"], expected_overnight)
    assert math.isclose(row["open_to_close_return"], expected_open_to_close)
    assert math.isclose(row["rs_component"], expected_rs)


def test_model_builds_required_columns():
    result = VOL001VolatilityModel(vol_window=20, normalization_window=252).fit_transform(_sample_ohlc()).frame
    expected_columns = [
        "date",
        "open",
        "high",
        "low",
        "close",
        "overnight_return",
        "open_to_close_return",
        "rs_component",
        "vol001_yz_variance_20d",
        "vol001_yz_volatility_20d",
        "vol001_zscore",
        "vol001_percentile",
        "vol001_valid_observation",
    ]
    assert list(result.columns) == expected_columns
    assert result["vol001_yz_volatility_20d"].notna().sum() > 0
    assert result["vol001_zscore"].notna().sum() > 0


def test_model_is_deterministic_on_identical_input():
    data = _sample_ohlc()
    model = VOL001VolatilityModel(vol_window=20, normalization_window=252)
    first = model.fit_transform(data).frame
    second = model.fit_transform(data).frame
    pd.testing.assert_frame_equal(first, second)

