from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


OUTPUT_COLUMNS = [
    "date",
    "ticker",
    "adjusted_close",
    "price_t_minus_21",
    "price_t_minus_252",
    "return_12_1",
    "csm001_rank",
    "csm001_eligible_count",
    "csm001_momentum_score",
    "csm001_top_decile_flag",
    "csm001_valid_observation",
]


@dataclass(frozen=True, slots=True)
class CSM001FeaturePipeline:
    """Deterministic feature builder for frozen CSM-001."""

    formation_anchor_trading_days: int = 252
    skip_period_trading_days: int = 21
    top_decile_threshold: float = 0.90
    minimum_eligible_count: int = 50

    def build_features(self, close_panel: pd.DataFrame) -> pd.DataFrame:
        self._validate_frozen_parameters()
        closes = self._prepare_close_panel(close_panel)
        if closes.empty:
            raise ValueError("CSM-001 close panel cannot be empty.")

        price_t_minus_skip = closes.shift(self.skip_period_trading_days)
        price_t_minus_anchor = closes.shift(self.formation_anchor_trading_days)
        return_12_1 = (price_t_minus_skip / price_t_minus_anchor) - 1.0
        return_12_1 = return_12_1.where(np.isfinite(return_12_1))

        eligible = return_12_1.notna()
        eligible_count = eligible.sum(axis=1).astype(int)
        valid_date = eligible_count >= self.minimum_eligible_count

        ranks = return_12_1.rank(axis=1, method="average", ascending=True, na_option="keep")
        score = (ranks - 1.0).divide((eligible_count - 1).replace(0, np.nan), axis=0)
        score = score.where(valid_date, np.nan)
        top_decile = score.ge(self.top_decile_threshold) & score.notna()

        records = []
        for ticker in closes.columns:
            frame = pd.DataFrame(
                {
                    "date": closes.index,
                    "ticker": ticker,
                    "adjusted_close": closes[ticker].to_numpy(dtype=float),
                    "price_t_minus_21": price_t_minus_skip[ticker].to_numpy(dtype=float),
                    "price_t_minus_252": price_t_minus_anchor[ticker].to_numpy(dtype=float),
                    "return_12_1": return_12_1[ticker].to_numpy(dtype=float),
                    "csm001_rank": ranks[ticker].to_numpy(dtype=float),
                    "csm001_eligible_count": eligible_count.to_numpy(dtype=int),
                    "csm001_momentum_score": score[ticker].to_numpy(dtype=float),
                    "csm001_top_decile_flag": top_decile[ticker].to_numpy(dtype=bool),
                    "csm001_valid_observation": (valid_date & eligible[ticker]).to_numpy(dtype=bool),
                }
            )
            records.append(frame)

        result = pd.concat(records, ignore_index=True)
        result = result.sort_values(["date", "ticker"]).reset_index(drop=True)
        return result[OUTPUT_COLUMNS]

    def _validate_frozen_parameters(self) -> None:
        if self.formation_anchor_trading_days != 252:
            raise ValueError("CSM-001 CD-001 requires formation_anchor_trading_days == 252.")
        if self.skip_period_trading_days != 21:
            raise ValueError("CSM-001 CD-001 requires skip_period_trading_days == 21.")
        if not np.isclose(self.top_decile_threshold, 0.90):
            raise ValueError("CSM-001 CD-001 requires top_decile_threshold == 0.90.")
        if self.minimum_eligible_count != 50:
            raise ValueError("CSM-001 CD-001 requires minimum_eligible_count == 50.")

    def _prepare_close_panel(self, close_panel: pd.DataFrame) -> pd.DataFrame:
        frame = close_panel.copy()
        frame.index = pd.to_datetime(frame.index).tz_localize(None)
        frame = frame.sort_index()
        frame = frame[~frame.index.duplicated(keep="first")]
        frame = frame.reindex(sorted(frame.columns), axis=1)
        frame = frame.apply(pd.to_numeric, errors="coerce")
        return frame.where(frame > 0)
