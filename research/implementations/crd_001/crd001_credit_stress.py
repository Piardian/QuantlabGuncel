from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


DATA_QUALITY_VALID = "VALID"
DATA_QUALITY_RAW_ONLY = "RAW_ONLY"
DATA_QUALITY_NORMALIZED_INVALID = "NORMALIZED_INVALID"
DATA_QUALITY_SOURCE_MISSING = "SOURCE_MISSING"


@dataclass(frozen=True, slots=True)
class CreditStressResult:
    frame: pd.DataFrame
    source_series: str


@dataclass(frozen=True, slots=True)
class CRD001CreditStress:
    """Frozen CRD-001 high-yield credit spread stress implementation."""

    source_series: str = "BAMLH0A0HYM2"
    normalization_window: int = 252
    max_forward_fill_calendar_days: int = 5

    def transform(self, data: pd.DataFrame) -> CreditStressResult:
        if data.empty:
            raise ValueError("CRD-001 input data cannot be empty.")
        if self.normalization_window <= 1:
            raise ValueError("normalization_window must be greater than 1.")
        if self.max_forward_fill_calendar_days < 0:
            raise ValueError("max_forward_fill_calendar_days cannot be negative.")

        source = self._standardize_source_frame(data)
        business_index = pd.bdate_range(source.index.min(), source.index.max())
        source = source.reindex(business_index)

        last_valid_date = pd.Series(source.index.where(source["source_value"].notna()), index=source.index).ffill()
        days_since = (pd.Series(source.index, index=source.index) - last_valid_date).dt.days
        filled = source["source_value"].ffill()
        fill_allowed = days_since.le(self.max_forward_fill_calendar_days) & filled.notna()
        raw = filled.where(fill_allowed)

        frame = pd.DataFrame(
            {
                "date": source.index,
                "crd001_hy_oas": raw.astype(float),
                "crd001_days_since_last_observation": days_since,
            }
        )
        frame.loc[frame["crd001_hy_oas"].isna(), "crd001_days_since_last_observation"] = np.nan

        raw_series = frame["crd001_hy_oas"]
        rolling = raw_series.rolling(self.normalization_window, min_periods=self.normalization_window)
        diagnostic_count = raw_series.rolling(self.normalization_window, min_periods=1).count()
        rolling_mean = rolling.mean()
        rolling_std = rolling.std(ddof=0)
        zscore = (raw_series - rolling_mean) / rolling_std
        zscore = zscore.where(rolling_std.gt(0))
        percentile = rolling.apply(_last_value_percentile, raw=True)
        percentile = percentile.where(rolling_std.gt(0))

        frame["crd001_zscore_252d"] = zscore
        frame["crd001_percentile_252d"] = percentile
        frame["crd001_valid_observation_count_252d"] = diagnostic_count.fillna(0).astype(int)
        frame["crd001_data_quality_flag"] = self._quality_flags(frame, rolling_std)

        return CreditStressResult(
            frame=frame[
                [
                    "date",
                    "crd001_hy_oas",
                    "crd001_zscore_252d",
                    "crd001_percentile_252d",
                    "crd001_valid_observation_count_252d",
                    "crd001_days_since_last_observation",
                    "crd001_data_quality_flag",
                ]
            ],
            source_series=self.source_series,
        )

    def _standardize_source_frame(self, data: pd.DataFrame) -> pd.DataFrame:
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

        value_column = self._find_value_column(frame)
        frame = frame[[value_column]].rename(columns={value_column: "source_value"})
        frame["source_value"] = pd.to_numeric(frame["source_value"], errors="coerce")
        frame = frame.sort_index()
        frame = frame[~frame.index.duplicated(keep="first")]
        frame = frame[frame.index.notna()]
        return frame

    def _find_value_column(self, frame: pd.DataFrame) -> str:
        candidates = [self.source_series, "value", "Value", "close", "Close", "source_value"]
        for candidate in candidates:
            if candidate in frame.columns:
                return candidate
        numeric_columns = [column for column in frame.columns if pd.api.types.is_numeric_dtype(frame[column])]
        if len(numeric_columns) == 1:
            return numeric_columns[0]
        raise ValueError(
            "CRD-001 input must contain one value column named "
            f"{self.source_series}, value, Value, close, Close, or source_value."
        )

    def _quality_flags(self, frame: pd.DataFrame, rolling_std: pd.Series) -> pd.Series:
        raw_available = frame["crd001_hy_oas"].notna()
        enough_history = frame["crd001_valid_observation_count_252d"].ge(self.normalization_window)
        normalized_available = (
            frame["crd001_zscore_252d"].notna()
            & frame["crd001_percentile_252d"].notna()
            & rolling_std.gt(0).to_numpy()
        )
        flags = pd.Series(DATA_QUALITY_SOURCE_MISSING, index=frame.index, dtype="object")
        flags.loc[raw_available & ~enough_history] = DATA_QUALITY_RAW_ONLY
        flags.loc[raw_available & enough_history & ~normalized_available] = DATA_QUALITY_NORMALIZED_INVALID
        flags.loc[raw_available & normalized_available] = DATA_QUALITY_VALID
        return flags


def _last_value_percentile(values: np.ndarray) -> float:
    if len(values) == 0 or np.isnan(values[-1]):
        return np.nan
    valid_values = values[~np.isnan(values)]
    if len(valid_values) == 0:
        return np.nan
    return float(np.sum(valid_values <= values[-1]) / len(valid_values))


def load_fred_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def fetch_fred_series_csv(series_id: str) -> pd.DataFrame:
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    return pd.read_csv(url)
