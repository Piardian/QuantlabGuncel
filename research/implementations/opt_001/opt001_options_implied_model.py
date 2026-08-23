from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


DATA_QUALITY_OK = "OK"
DATA_QUALITY_MISSING_INPUT = "MISSING_INPUT"
DATA_QUALITY_INSUFFICIENT_LOOKBACK = "INSUFFICIENT_LOOKBACK"
DATA_QUALITY_ZERO_ROLLING_STD = "ZERO_ROLLING_STD"
DATA_QUALITY_INVALID_NON_POSITIVE = "INVALID_NON_POSITIVE"


@dataclass(frozen=True, slots=True)
class OptionsImpliedResult:
    frame: pd.DataFrame
    source_series: str


@dataclass(frozen=True, slots=True)
class OPT001OptionsImplied:
    """Frozen OPT-001 VIXCLS option-implied volatility state implementation."""

    source_series: str = "VIXCLS"
    normalization_window: int = 252

    def transform(self, data: pd.DataFrame) -> OptionsImpliedResult:
        if data.empty:
            raise ValueError("OPT-001 input data cannot be empty.")
        if self.normalization_window <= 1:
            raise ValueError("normalization_window must be greater than 1.")

        frame = self._standardize_input_frame(data)
        valid_vix = frame.loc[frame["opt001_vix_close"].notna(), "opt001_vix_close"]
        rolling = valid_vix.rolling(self.normalization_window, min_periods=self.normalization_window)
        rolling_mean = rolling.mean()
        rolling_std = rolling.std(ddof=0)
        valid_zscore = (valid_vix - rolling_mean) / rolling_std
        valid_zscore = valid_zscore.where(rolling_std.gt(0))
        valid_percentile = rolling.apply(_last_value_percentile_average_rank, raw=True)
        valid_percentile = valid_percentile.where(rolling_std.gt(0))

        frame["opt001_zscore_252d"] = np.nan
        frame.loc[valid_zscore.index, "opt001_zscore_252d"] = valid_zscore
        frame["opt001_percentile_252d"] = np.nan
        frame.loc[valid_percentile.index, "opt001_percentile_252d"] = valid_percentile

        cumulative_valid = frame["opt001_vix_close"].notna().cumsum().clip(upper=self.normalization_window)
        frame["opt001_valid_observation_count_252d"] = cumulative_valid.astype(int)
        frame["opt001_data_quality_flag"] = self._quality_flags(frame, rolling_std)

        output = frame.reset_index()
        output = output.rename(columns={output.columns[0]: "date"})
        output = output[
            [
                "date",
                "opt001_vix_close",
                "opt001_zscore_252d",
                "opt001_percentile_252d",
                "opt001_valid_observation_count_252d",
                "opt001_data_quality_flag",
            ]
        ]
        return OptionsImpliedResult(output, self.source_series)

    def _standardize_input_frame(self, data: pd.DataFrame) -> pd.DataFrame:
        frame = data.copy()
        if "date" in frame.columns:
            frame["date"] = pd.to_datetime(frame["date"])
            frame = frame.set_index("date")
        elif "DATE" in frame.columns:
            frame["DATE"] = pd.to_datetime(frame["DATE"])
            frame = frame.set_index("DATE")
        elif "observation_date" in frame.columns:
            frame["observation_date"] = pd.to_datetime(frame["observation_date"])
            frame = frame.set_index("observation_date")
        else:
            frame.index = pd.to_datetime(frame.index)

        value_column = self._find_column(frame)
        standardized = frame[[value_column]].rename(columns={value_column: "opt001_vix_close"})
        raw_values = pd.to_numeric(standardized["opt001_vix_close"], errors="coerce")
        standardized["opt001_raw_missing"] = raw_values.isna()
        standardized["opt001_raw_non_positive"] = raw_values.notna() & raw_values.le(0)
        standardized["opt001_vix_close"] = raw_values.where(raw_values.gt(0))
        standardized = standardized.sort_index()
        standardized = standardized[~standardized.index.duplicated(keep="first")]
        standardized = standardized[standardized.index.notna()]
        return standardized

    def _find_column(self, frame: pd.DataFrame) -> str:
        for candidate in [self.source_series, "value", "Value", "close", "Close", "opt001_vix_close"]:
            if candidate in frame.columns:
                return candidate
        numeric_columns = [column for column in frame.columns if pd.api.types.is_numeric_dtype(frame[column])]
        if len(numeric_columns) == 1:
            return numeric_columns[0]
        raise ValueError(
            "OPT-001 input must contain one value column named "
            f"{self.source_series}, value, Value, close, Close, or opt001_vix_close."
        )

    def _quality_flags(self, frame: pd.DataFrame, valid_rolling_std: pd.Series) -> pd.Series:
        raw_available = frame["opt001_vix_close"].notna()
        enough_history = frame["opt001_valid_observation_count_252d"].ge(self.normalization_window)
        zero_std_dates = valid_rolling_std.index[valid_rolling_std.eq(0)]

        flags = pd.Series(DATA_QUALITY_MISSING_INPUT, index=frame.index, dtype="object")
        flags.loc[frame["opt001_raw_non_positive"]] = DATA_QUALITY_INVALID_NON_POSITIVE
        flags.loc[raw_available & ~enough_history] = DATA_QUALITY_INSUFFICIENT_LOOKBACK
        flags.loc[raw_available & enough_history] = DATA_QUALITY_OK
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

