from __future__ import annotations

import math

import pandas as pd

from feature_pipeline import LiquidityFeaturePipeline
from liq001_liquidity_model import LIQ001LiquidityModel


def _sample_data(base: float) -> pd.DataFrame:
    dates = pd.date_range("2020-01-01", periods=280, freq="B")
    closes = [base + i * 0.1 for i in range(len(dates))]
    volumes = [1_000_000 + i for i in range(len(dates))]
    return pd.DataFrame({"Close": closes, "Volume": volumes}, index=dates)


def test_security_features_follow_cd001_formula():
    data = pd.DataFrame(
        {"Close": [100.0, 102.0], "Volume": [1_000_000, 2_000_000]},
        index=pd.date_range("2020-01-01", periods=2, freq="B"),
    )
    features = LiquidityFeaturePipeline(min_eligible_securities=1).build_security_features("AAA", data)
    expected_return = math.log(102.0 / 100.0)
    expected_dollar_volume = 102.0 * 2_000_000
    expected_illiquidity = abs(expected_return) / expected_dollar_volume
    row = features.iloc[1]
    assert row["eligible"]
    assert math.isclose(row["log_return"], expected_return)
    assert math.isclose(row["dollar_volume"], expected_dollar_volume)
    assert math.isclose(row["security_illiquidity"], expected_illiquidity)


def test_aggregate_builds_required_columns():
    market_data = {f"T{i:03d}": _sample_data(100.0 + i) for i in range(55)}
    result = LIQ001LiquidityModel(min_eligible_securities=50).fit_transform(market_data)
    expected_columns = [
        "date",
        "aggregate_illiquidity",
        "liq001_illiquidity_20d",
        "liq001_zscore",
        "eligible_count",
        "coverage_ratio",
    ]
    assert list(result.frame.columns) == expected_columns
    assert not result.frame.empty
    assert result.frame["eligible_count"].min() >= 50


def test_model_is_deterministic_on_identical_input():
    market_data = {f"T{i:03d}": _sample_data(100.0 + i) for i in range(55)}
    model = LIQ001LiquidityModel(min_eligible_securities=50)
    first = model.fit_transform(market_data).frame
    second = model.fit_transform(market_data).frame
    pd.testing.assert_frame_equal(first, second)

