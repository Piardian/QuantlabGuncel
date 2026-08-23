from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from feature_pipeline import TSM001FeaturePipeline


@dataclass(frozen=True, slots=True)
class TSM001MomentumResult:
    frame: pd.DataFrame


@dataclass(frozen=True, slots=True)
class TSM001MomentumModel:
    """Frozen TSM-001 raw 12-1 time-series momentum model."""

    formation_anchor_trading_days: int = 252
    skip_period_trading_days: int = 21
    direction_threshold: float = 0.0
    volatility_scaling: str = "excluded"

    def transform(self, close_panel: pd.DataFrame) -> TSM001MomentumResult:
        pipeline = TSM001FeaturePipeline(
            formation_anchor_trading_days=self.formation_anchor_trading_days,
            skip_period_trading_days=self.skip_period_trading_days,
            direction_threshold=self.direction_threshold,
            volatility_scaling=self.volatility_scaling,
        )
        return TSM001MomentumResult(frame=pipeline.build_features(close_panel))
