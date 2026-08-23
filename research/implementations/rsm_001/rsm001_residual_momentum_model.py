from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from feature_pipeline import RSM001FeaturePipeline


@dataclass(frozen=True, slots=True)
class RSM001ResidualMomentumResult:
    frame: pd.DataFrame


@dataclass(frozen=True, slots=True)
class RSM001ResidualMomentumModel:
    """Frozen RSM-001 FF3 standardized 12-1 residual momentum model."""

    regression_window_months: int = 36
    minimum_observations: int = 24
    formation_start_lag_months: int = 12
    formation_end_lag_months: int = 2
    residual_vol_window_months: int = 36
    top_decile_threshold: float = 0.90
    bottom_decile_threshold: float = 0.10

    def transform(self, monthly_returns: pd.DataFrame, factor_returns: pd.DataFrame) -> RSM001ResidualMomentumResult:
        pipeline = RSM001FeaturePipeline(
            regression_window_months=self.regression_window_months,
            minimum_observations=self.minimum_observations,
            formation_start_lag_months=self.formation_start_lag_months,
            formation_end_lag_months=self.formation_end_lag_months,
            residual_vol_window_months=self.residual_vol_window_months,
            top_decile_threshold=self.top_decile_threshold,
            bottom_decile_threshold=self.bottom_decile_threshold,
        )
        return RSM001ResidualMomentumResult(frame=pipeline.build_features(monthly_returns, factor_returns))

