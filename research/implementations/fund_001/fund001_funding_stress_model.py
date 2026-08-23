from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


DATA_QUALITY_OK = "OK"
DATA_QUALITY_MISSING_INPUT = "MISSING_INPUT"
DATA_QUALITY_INSUFFICIENT_LOOKBACK = "INSUFFICIENT_LOOKBACK"
DATA_QUALITY_ZERO_ROLLING_STD = "ZERO_ROLLING_STD"


@dataclass(frozen=True, slots=True)
class FundingStressResult:
    frame: pd.DataFrame
    cp_series: str
    tbill_series: str


@dataclass(frozen=True, slots=True)
class FUND001FundingStress:
    """Frozen FUND-001 funding stress implementation."""

    cp_series: str = "DCPF3M"
    tbill_series: str = "DTB3"
    normalization_window: int = 252

    def transform(self, data: pd.DataFrame) -> FundingStressResult:
        if data.empty:
            raise ValueError("FUND-001 input data cannot be empty.")
        if self.normalization_window <= 1:
            raise ValueError("normalization_window must be greater than 1.")

        frame = self._standardize_input_frame(data)
        frame["fund001_cp_tbill_spread"] = frame["fund001_cp_rate"] - frame["fund001_tbill_rate"]

        valid_spread = frame.loc[frame["fund001_cp_tbill_spread"].notna(), "fund001_cp_tbill_spread"]
        rolling = valid_spread.rolling(self.normalization_window, min_periods=self.normalization_window)
        rolling_mean = rolling.mean()
        rolling_std = rolling.std(ddof=0)
        valid_zscore = (valid_spread - rolling_mean) / rolling_std
        valid_zscore = valid_zscore.where(rolling_std.gt(0))
        valid_percentile = rolling.apply(_last_value_percentile_average_rank, raw=True)
        valid_percentile = valid_percentile.where(rolling_std.gt(0))

        frame["fund001_zscore_252d"] = np.nan
        frame.loc[valid_zscore.index, "fund001_zscore_252d"] = valid_zscore
        frame["fund001_percentile_252d"] = np.nan
        frame.loc[valid_percentile.index, "fund001_percentile_252d"] = valid_percentile

        cumulative_valid = frame["fund001_cp_tbill_spread"].notna().cumsum().clip(upper=self.normalization_window)
        frame["fund001_valid_observation_count_252d"] = cumulative_valid.astype(int)
        frame["fund001_data_quality_flag"] = self._quality_flags(frame, rolling_std)

        output = frame.reset_index()
        output = output.rename(columns={output.columns[0]: "date"})
        output = output[
            [
                "date",
                "fund001_cp_rate",
                "fund001_tbill_rate",
                "fund001_cp_tbill_spread",
                "fund001_zscore_252d",
                "fund001_percentile_252d",
                "fund001_valid_observation_count_252d",
                "fund001_data_quality_flag",
            ]
        ]
        return FundingStressResult(output, self.cp_series, self.tbill_series)

    def _standardize_input_frame(self, data: pd.DataFrame) -> pd.DataFrame:
        frame = data.copy()
        if "date" in frame.columns:
            frame["date"] = pd.to_datetime(frame["date"])
            frame = frame.set_index("date")
        elif "DATE" in frame.columns:
            frame["DATE"] = pd.to_datetime(frame["DATE"])
            frame = frame.set_index("DATE")
        else:
            frame.index = pd.to_datetime(frame.index)

        cp_column = self._find_column(frame, self.cp_series, ["cp_rate", "fund001_cp_rate"])
        tbill_column = self._find_column(frame, self.tbill_series, ["tbill_rate", "fund001_tbill_rate"])
        standardized = frame[[cp_column, tbill_column]].rename(
            columns={cp_column: "fund001_cp_rate", tbill_column: "fund001_tbill_rate"}
        )
        standardized["fund001_cp_rate"] = pd.to_numeric(standardized["fund001_cp_rate"], errors="coerce")
        standardized["fund001_tbill_rate"] = pd.to_numeric(standardized["fund001_tbill_rate"], errors="coerce")
        standardized = standardized.sort_index()
        standardized = standardized[~standardized.index.duplicated(keep="first")]
        standardized = standardized[standardized.index.notna()]
        return standardized

    def _find_column(self, frame: pd.DataFrame, series_id: str, aliases: list[str]) -> str:
        for candidate in [series_id, *aliases]:
            if candidate in frame.columns:
                return candidate
        raise ValueError(f"FUND-001 input must contain a column named {series_id} or one of {aliases}.")

    def _quality_flags(self, frame: pd.DataFrame, valid_rolling_std: pd.Series) -> pd.Series:
        spread_available = frame["fund001_cp_tbill_spread"].notna()
        enough_history = frame["fund001_valid_observation_count_252d"].ge(self.normalization_window)
        zero_std_dates = valid_rolling_std.index[valid_rolling_std.eq(0)]

        flags = pd.Series(DATA_QUALITY_MISSING_INPUT, index=frame.index, dtype="object")
        flags.loc[spread_available & ~enough_history] = DATA_QUALITY_INSUFFICIENT_LOOKBACK
        flags.loc[spread_available & enough_history] = DATA_QUALITY_OK
        flags.loc[zero_std_dates] = DATA_QUALITY_ZERO_ROLLING_STD
        return flags


def _last_value_percentile_average_rank(values: np.ndarray) -> float:
    if len(values) == 0 or np.isnan(values[-1]):
        return np.nan
    valid_values = values[~np.isnan(values)]
    if len(valid_values) == 0:
        return np.nan
    ranks = pd.Series(valid_values).rank(method="average")
    return float(ranks.iloc[-1] / len(valid_values))


def load_fred_csv(path: Path, value_name: str) -> pd.DataFrame:
    frame = pd.read_csv(path)
    if "DATE" in frame.columns:
        date_column = "DATE"
    elif "observation_date" in frame.columns:
        date_column = "observation_date"
    else:
        raise ValueError(f"{path} must contain a DATE or observation_date column.")
    value_columns = [column for column in frame.columns if column != date_column]
    if len(value_columns) != 1:
        raise ValueError(f"{path} must contain exactly one value column besides the date column.")
    return frame.rename(columns={date_column: "DATE", value_columns[0]: value_name})


def fetch_fred_series_csv(series_id: str) -> pd.DataFrame:
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    return pd.read_csv(url)
