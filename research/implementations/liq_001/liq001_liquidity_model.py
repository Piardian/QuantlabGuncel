from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from feature_pipeline import LiquidityFeaturePipeline


@dataclass(frozen=True, slots=True)
class LiquidityModelResult:
    frame: pd.DataFrame
    security_features: pd.DataFrame
    universe_size: int


@dataclass(frozen=True, slots=True)
class LIQ001LiquidityModel:
    """Frozen LIQ-001 aggregate daily illiquidity model."""

    smoothing_window: int = 20
    zscore_window: int = 252
    min_eligible_securities: int = 50

    def fit_transform(self, market_data: dict[str, pd.DataFrame]) -> LiquidityModelResult:
        if not market_data:
            raise ValueError("market_data cannot be empty.")

        pipeline = LiquidityFeaturePipeline(
            smoothing_window=self.smoothing_window,
            zscore_window=self.zscore_window,
            min_eligible_securities=self.min_eligible_securities,
        )
        security_frames = [
            pipeline.build_security_features(ticker=ticker, data=data)
            for ticker, data in sorted(market_data.items())
        ]
        security_features = pd.concat(security_frames, ignore_index=True)
        aggregate = pipeline.build_aggregate(security_features, universe_size=len(market_data))
        return LiquidityModelResult(
            frame=aggregate,
            security_features=security_features,
            universe_size=len(market_data),
        )


