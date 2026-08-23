from __future__ import annotations

import numpy as np
import pandas as pd

from feature_pipeline import MarketRegimeFeaturePipeline
from mr001_hmm_model import TwoStateGaussianHMM


def test_feature_pipeline_builds_expected_columns():
    data = pd.DataFrame(
        {"Close": [100.0, 101.0, 102.0, 101.5, 103.0, 104.0, 105.0, 104.0, 106.0, 107.0, 108.0, 109.0, 110.0, 111.0, 112.0, 113.0, 114.0, 115.0, 116.0, 117.0, 118.0]},
        index=pd.date_range("2020-01-01", periods=21, freq="B"),
    )
    features = MarketRegimeFeaturePipeline().build(data)
    assert list(features.columns) == ["spy_close", "daily_log_return", "realized_volatility_20d"]
    assert len(features) > 0


def test_hmm_produces_two_state_posteriors():
    x = np.column_stack([
        np.concatenate([np.full(30, -0.01), np.full(30, 0.01)]),
        np.concatenate([np.full(30, 0.30), np.full(30, 0.05)]),
    ])
    model = TwoStateGaussianHMM()
    result = model.fit(x)
    assert result.posterior.shape == (60, 2)
    assert np.allclose(result.posterior.sum(axis=1), 1.0, atol=1e-6)
    assert set(np.unique(result.states)).issubset({0, 1})

