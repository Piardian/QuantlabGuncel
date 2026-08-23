from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


OUTPUT_COLUMNS = [
    "month",
    "ticker",
    "monthly_return",
    "rf",
    "mkt_rf",
    "smb",
    "hml",
    "excess_return",
    "residual_return",
    "residual_sum_12_1",
    "residual_vol_36m",
    "rsm_score",
    "rsm_rank",
    "rsm_eligible_count",
    "rsm_percentile",
    "rsm_state",
    "rsm_valid_observation",
]


@dataclass(frozen=True, slots=True)
class RSM001FeaturePipeline:
    """Deterministic feature builder for frozen RSM-001."""

    regression_window_months: int = 36
    minimum_observations: int = 24
    formation_start_lag_months: int = 12
    formation_end_lag_months: int = 2
    residual_vol_window_months: int = 36
    top_decile_threshold: float = 0.90
    bottom_decile_threshold: float = 0.10

    def build_features(self, monthly_returns: pd.DataFrame, factor_returns: pd.DataFrame) -> pd.DataFrame:
        self._validate_frozen_parameters()
        returns = self._prepare_return_panel(monthly_returns)
        factors = self._prepare_factor_frame(factor_returns)
        if returns.empty:
            raise ValueError("RSM-001 monthly return panel cannot be empty.")
        if factors.empty:
            raise ValueError("RSM-001 factor return frame cannot be empty.")

        aligned_returns, aligned_factors = self._align_inputs(returns, factors)
        excess_returns = aligned_returns.subtract(aligned_factors["rf"], axis=0)
        residuals = self._rolling_ff3_residuals(excess_returns, aligned_factors)

        residual_sum = self._formation_sum(residuals)
        residual_vol = residuals.shift(1).rolling(self.residual_vol_window_months, min_periods=self.minimum_observations).std(ddof=1)
        rsm_score = residual_sum / residual_vol
        rsm_score = rsm_score.where(np.isfinite(rsm_score))

        valid_score = rsm_score.notna()
        eligible_count = valid_score.sum(axis=1).astype(int)
        valid_date = eligible_count >= 1

        ranks = rsm_score.rank(axis=1, method="average", ascending=True, na_option="keep")
        percentile = (ranks - 1.0).divide((eligible_count - 1).replace(0, np.nan), axis=0)
        percentile = percentile.where(valid_date, np.nan)
        single_name_rows = valid_date & eligible_count.eq(1)
        percentile.loc[single_name_rows, :] = percentile.loc[single_name_rows, :].where(~valid_score.loc[single_name_rows, :], 1.0)

        state = pd.DataFrame("INVALID", index=rsm_score.index, columns=rsm_score.columns)
        state = state.mask(percentile.notna(), "MIDDLE")
        state = state.mask(percentile.ge(self.top_decile_threshold), "TOP_DECILE")
        state = state.mask(percentile.le(self.bottom_decile_threshold), "BOTTOM_DECILE")

        records = []
        for ticker in aligned_returns.columns:
            frame = pd.DataFrame(
                {
                    "month": aligned_returns.index,
                    "ticker": ticker,
                    "monthly_return": aligned_returns[ticker].to_numpy(dtype=float),
                    "rf": aligned_factors["rf"].to_numpy(dtype=float),
                    "mkt_rf": aligned_factors["mkt_rf"].to_numpy(dtype=float),
                    "smb": aligned_factors["smb"].to_numpy(dtype=float),
                    "hml": aligned_factors["hml"].to_numpy(dtype=float),
                    "excess_return": excess_returns[ticker].to_numpy(dtype=float),
                    "residual_return": residuals[ticker].to_numpy(dtype=float),
                    "residual_sum_12_1": residual_sum[ticker].to_numpy(dtype=float),
                    "residual_vol_36m": residual_vol[ticker].to_numpy(dtype=float),
                    "rsm_score": rsm_score[ticker].to_numpy(dtype=float),
                    "rsm_rank": ranks[ticker].to_numpy(dtype=float),
                    "rsm_eligible_count": eligible_count.to_numpy(dtype=int),
                    "rsm_percentile": percentile[ticker].to_numpy(dtype=float),
                    "rsm_state": state[ticker].to_numpy(dtype=str),
                    "rsm_valid_observation": valid_score[ticker].to_numpy(dtype=bool),
                }
            )
            records.append(frame)

        result = pd.concat(records, ignore_index=True)
        result = result.sort_values(["month", "ticker"]).reset_index(drop=True)
        return result[OUTPUT_COLUMNS]

    def _validate_frozen_parameters(self) -> None:
        if self.regression_window_months != 36:
            raise ValueError("RSM-001 CD-001 requires regression_window_months == 36.")
        if self.minimum_observations != 24:
            raise ValueError("RSM-001 CD-001 requires minimum_observations == 24.")
        if self.formation_start_lag_months != 12:
            raise ValueError("RSM-001 CD-001 requires formation_start_lag_months == 12.")
        if self.formation_end_lag_months != 2:
            raise ValueError("RSM-001 CD-001 requires formation_end_lag_months == 2.")
        if self.residual_vol_window_months != 36:
            raise ValueError("RSM-001 CD-001 requires residual_vol_window_months == 36.")
        if not np.isclose(self.top_decile_threshold, 0.90):
            raise ValueError("RSM-001 CD-001 requires top_decile_threshold == 0.90.")
        if not np.isclose(self.bottom_decile_threshold, 0.10):
            raise ValueError("RSM-001 CD-001 requires bottom_decile_threshold == 0.10.")

    def _prepare_return_panel(self, monthly_returns: pd.DataFrame) -> pd.DataFrame:
        frame = monthly_returns.copy()
        frame.index = pd.to_datetime(frame.index).tz_localize(None).to_period("M").to_timestamp("M")
        frame = frame.sort_index()
        frame = frame[~frame.index.duplicated(keep="first")]
        frame = frame.reindex(sorted(frame.columns), axis=1)
        return frame.apply(pd.to_numeric, errors="coerce")

    def _prepare_factor_frame(self, factor_returns: pd.DataFrame) -> pd.DataFrame:
        required = ["mkt_rf", "smb", "hml", "rf"]
        frame = factor_returns.copy()
        frame.columns = [str(column).lower() for column in frame.columns]
        missing = [column for column in required if column not in frame.columns]
        if missing:
            raise ValueError(f"RSM-001 factor frame missing required columns: {missing}")
        frame.index = pd.to_datetime(frame.index).tz_localize(None).to_period("M").to_timestamp("M")
        frame = frame.sort_index()
        frame = frame[~frame.index.duplicated(keep="first")]
        return frame[required].apply(pd.to_numeric, errors="coerce")

    def _align_inputs(self, returns: pd.DataFrame, factors: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        common_index = returns.index.intersection(factors.index).sort_values()
        if common_index.empty:
            raise ValueError("RSM-001 returns and factors have no overlapping months.")
        return returns.loc[common_index], factors.loc[common_index]

    def _rolling_ff3_residuals(self, excess_returns: pd.DataFrame, factors: pd.DataFrame) -> pd.DataFrame:
        x_factors = factors[["mkt_rf", "smb", "hml"]]
        residuals = pd.DataFrame(np.nan, index=excess_returns.index, columns=excess_returns.columns, dtype=float)
        for ticker in excess_returns.columns:
            y = excess_returns[ticker]
            for row_idx in range(len(excess_returns)):
                start_idx = max(0, row_idx - self.regression_window_months)
                if start_idx >= row_idx:
                    continue
                window_y = y.iloc[start_idx:row_idx]
                window_x = x_factors.iloc[start_idx:row_idx]
                valid = window_y.notna() & window_x.notna().all(axis=1)
                if int(valid.sum()) < self.minimum_observations:
                    continue
                x_matrix = np.column_stack([np.ones(int(valid.sum())), window_x.loc[valid].to_numpy(dtype=float)])
                y_vector = window_y.loc[valid].to_numpy(dtype=float)
                beta, *_ = np.linalg.lstsq(x_matrix, y_vector, rcond=None)
                current_x = x_factors.iloc[row_idx]
                current_y = y.iloc[row_idx]
                if pd.isna(current_y) or current_x.isna().any():
                    continue
                current_vector = np.array([1.0, current_x["mkt_rf"], current_x["smb"], current_x["hml"]], dtype=float)
                residuals.iat[row_idx, residuals.columns.get_loc(ticker)] = float(current_y - current_vector @ beta)
        return residuals

    def _formation_sum(self, residuals: pd.DataFrame) -> pd.DataFrame:
        total = pd.DataFrame(0.0, index=residuals.index, columns=residuals.columns)
        valid_count = pd.DataFrame(0, index=residuals.index, columns=residuals.columns)
        for lag in range(self.formation_end_lag_months, self.formation_start_lag_months + 1):
            shifted = residuals.shift(lag)
            total = total.add(shifted.fillna(0.0), fill_value=0.0)
            valid_count = valid_count.add(shifted.notna().astype(int), fill_value=0)
        return total.where(valid_count.eq(self.formation_start_lag_months - self.formation_end_lag_months + 1))

