from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


OUTPUT_COLUMNS = [
    "month",
    "industry_id",
    "industry_name",
    "industry_return",
    "industry_return_12_1",
    "ism_rank",
    "ism_eligible_count",
    "ism_score",
    "ism_state",
    "ism_valid_observation",
]


@dataclass(frozen=True, slots=True)
class ISM001FeaturePipeline:
    """Deterministic feature builder for frozen ISM-001."""

    formation_start_lag_months: int = 12
    formation_end_lag_months: int = 2
    minimum_valid_industries: int = 30
    top_decile_threshold: float = 0.90
    bottom_decile_threshold: float = 0.10

    def build_features(self, industry_returns: pd.DataFrame) -> pd.DataFrame:
        self._validate_frozen_parameters()
        returns = self._prepare_return_panel(industry_returns)
        if returns.empty:
            raise ValueError("ISM-001 industry return panel cannot be empty.")

        return_12_1 = self._formation_compounded_return(returns)
        valid_signal = return_12_1.notna()
        eligible_count = valid_signal.sum(axis=1).astype(int)
        valid_month = eligible_count >= self.minimum_valid_industries

        ranks = return_12_1.rank(axis=1, method="average", ascending=True, na_option="keep")
        score = (ranks - 1.0).divide((eligible_count - 1).replace(0, np.nan), axis=0)
        score = score.where(valid_month, np.nan)
        valid_month_frame = pd.DataFrame(
            np.repeat(valid_month.to_numpy(dtype=bool)[:, None], len(returns.columns), axis=1),
            index=returns.index,
            columns=returns.columns,
        )
        valid_observation = valid_signal & valid_month_frame

        state = pd.DataFrame("INVALID", index=returns.index, columns=returns.columns)
        state = state.mask(score.notna(), "MIDDLE")
        state = state.mask(score.ge(self.top_decile_threshold), "TOP_DECILE")
        state = state.mask(score.le(self.bottom_decile_threshold), "BOTTOM_DECILE")

        records = []
        for industry_id in returns.columns:
            frame = pd.DataFrame(
                {
                    "month": returns.index,
                    "industry_id": industry_id,
                    "industry_name": industry_id,
                    "industry_return": returns[industry_id].to_numpy(dtype=float),
                    "industry_return_12_1": return_12_1[industry_id].to_numpy(dtype=float),
                    "ism_rank": ranks[industry_id].to_numpy(dtype=float),
                    "ism_eligible_count": eligible_count.to_numpy(dtype=int),
                    "ism_score": score[industry_id].to_numpy(dtype=float),
                    "ism_state": state[industry_id].to_numpy(dtype=str),
                    "ism_valid_observation": valid_observation[industry_id].to_numpy(dtype=bool),
                }
            )
            records.append(frame)

        result = pd.concat(records, ignore_index=True)
        result = result.sort_values(["month", "industry_id"]).reset_index(drop=True)
        return result[OUTPUT_COLUMNS]

    def _validate_frozen_parameters(self) -> None:
        if self.formation_start_lag_months != 12:
            raise ValueError("ISM-001 CD-001 requires formation_start_lag_months == 12.")
        if self.formation_end_lag_months != 2:
            raise ValueError("ISM-001 CD-001 requires formation_end_lag_months == 2.")
        if self.minimum_valid_industries != 30:
            raise ValueError("ISM-001 CD-001 requires minimum_valid_industries == 30.")
        if not np.isclose(self.top_decile_threshold, 0.90):
            raise ValueError("ISM-001 CD-001 requires top_decile_threshold == 0.90.")
        if not np.isclose(self.bottom_decile_threshold, 0.10):
            raise ValueError("ISM-001 CD-001 requires bottom_decile_threshold == 0.10.")

    def _prepare_return_panel(self, industry_returns: pd.DataFrame) -> pd.DataFrame:
        frame = industry_returns.copy()
        frame.index = pd.to_datetime(frame.index).tz_localize(None).to_period("M").to_timestamp("M")
        frame = frame.sort_index()
        frame = frame[~frame.index.duplicated(keep="first")]
        frame = frame.reindex(sorted(frame.columns), axis=1)
        frame = frame.apply(pd.to_numeric, errors="coerce")
        return frame.where(np.isfinite(frame))

    def _formation_compounded_return(self, returns: pd.DataFrame) -> pd.DataFrame:
        compounded = pd.DataFrame(1.0, index=returns.index, columns=returns.columns)
        valid_count = pd.DataFrame(0, index=returns.index, columns=returns.columns)
        required_months = self.formation_start_lag_months - self.formation_end_lag_months + 1
        for lag in range(self.formation_end_lag_months, self.formation_start_lag_months + 1):
            shifted = returns.shift(lag)
            compounded = compounded.mul(1.0 + shifted.fillna(0.0), fill_value=1.0)
            valid_count = valid_count.add(shifted.notna().astype(int), fill_value=0)
        return (compounded - 1.0).where(valid_count.eq(required_months))
