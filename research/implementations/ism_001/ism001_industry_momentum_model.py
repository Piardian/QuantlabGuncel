from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from feature_pipeline import ISM001FeaturePipeline


@dataclass(frozen=True, slots=True)
class ISM001IndustryMomentumResult:
    frame: pd.DataFrame


@dataclass(frozen=True, slots=True)
class ISM001IndustryMomentumModel:
    """Frozen ISM-001 Ken French 49 Industry 12-1 momentum rank model."""

    formation_start_lag_months: int = 12
    formation_end_lag_months: int = 2
    minimum_valid_industries: int = 30
    top_decile_threshold: float = 0.90
    bottom_decile_threshold: float = 0.10

    def transform(self, industry_returns: pd.DataFrame) -> ISM001IndustryMomentumResult:
        pipeline = ISM001FeaturePipeline(
            formation_start_lag_months=self.formation_start_lag_months,
            formation_end_lag_months=self.formation_end_lag_months,
            minimum_valid_industries=self.minimum_valid_industries,
            top_decile_threshold=self.top_decile_threshold,
            bottom_decile_threshold=self.bottom_decile_threshold,
        )
        return ISM001IndustryMomentumResult(frame=pipeline.build_features(industry_returns))
