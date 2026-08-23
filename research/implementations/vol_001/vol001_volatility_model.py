from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from feature_pipeline import VolatilityFeaturePipeline


@dataclass(frozen=True, slots=True)
class VolatilityModelResult:
    frame: pd.DataFrame
    symbol: str


@dataclass(frozen=True, slots=True)
class VOL001VolatilityModel:
    """Frozen VOL-001 daily Yang-Zhang volatility-state model."""

    symbol: str = "SPY"
    vol_window: int = 20
    normalization_window: int = 252
    annualization_factor: int = 252

    def fit_transform(self, data: pd.DataFrame) -> VolatilityModelResult:
        if data.empty:
            raise ValueError("VOL-001 input data cannot be empty.")
        pipeline = VolatilityFeaturePipeline(
            vol_window=self.vol_window,
            normalization_window=self.normalization_window,
            annualization_factor=self.annualization_factor,
        )
        return VolatilityModelResult(frame=pipeline.build_features(data), symbol=self.symbol)

