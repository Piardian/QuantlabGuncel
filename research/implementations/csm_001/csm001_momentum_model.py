from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from feature_pipeline import CSM001FeaturePipeline


@dataclass(frozen=True, slots=True)
class CSM001MomentumResult:
    frame: pd.DataFrame


@dataclass(frozen=True, slots=True)
class CSM001MomentumModel:
    """Frozen CSM-001 canonical 12-1 cross-sectional momentum model."""

    formation_anchor_trading_days: int = 252
    skip_period_trading_days: int = 21
    top_decile_threshold: float = 0.90
    minimum_eligible_count: int = 50

    def transform(self, close_panel: pd.DataFrame) -> CSM001MomentumResult:
        pipeline = CSM001FeaturePipeline(
            formation_anchor_trading_days=self.formation_anchor_trading_days,
            skip_period_trading_days=self.skip_period_trading_days,
            top_decile_threshold=self.top_decile_threshold,
            minimum_eligible_count=self.minimum_eligible_count,
        )
        return CSM001MomentumResult(frame=pipeline.build_features(close_panel))

