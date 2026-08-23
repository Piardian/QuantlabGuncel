from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True, slots=True)
class VolatilityFeaturePipeline:
    """Deterministic feature builder for the frozen VOL-001 construct."""

    vol_window: int = 20
    normalization_window: int = 252
    annualization_factor: int = 252

    def build_features(self, data: pd.DataFrame) -> pd.DataFrame:
        frame = self._prepare_ohlc(data)

        previous_close = frame["close"].shift(1)
        overnight_return = np.log(frame["open"] / previous_close)
        open_to_close_return = np.log(frame["close"] / frame["open"])
        high_open_return = np.log(frame["high"] / frame["open"])
        high_close_return = np.log(frame["high"] / frame["close"])
        low_open_return = np.log(frame["low"] / frame["open"])
        low_close_return = np.log(frame["low"] / frame["close"])
        rs_component = (high_open_return * high_close_return) + (low_open_return * low_close_return)

        result = pd.DataFrame(
            {
                "date": frame.index,
                "open": frame["open"].to_numpy(),
                "high": frame["high"].to_numpy(),
                "low": frame["low"].to_numpy(),
                "close": frame["close"].to_numpy(),
                "overnight_return": overnight_return.to_numpy(),
                "open_to_close_return": open_to_close_return.to_numpy(),
                "rs_component": rs_component.to_numpy(),
            }
        )
        result["vol001_valid_observation"] = (
            result["open"].gt(0)
            & result["high"].gt(0)
            & result["low"].gt(0)
            & result["close"].gt(0)
            & result["high"].ge(result[["open", "close"]].max(axis=1))
            & result["low"].le(result[["open", "close"]].min(axis=1))
            & np.isfinite(result["overnight_return"])
            & np.isfinite(result["open_to_close_return"])
            & np.isfinite(result["rs_component"])
        )

        result.loc[~result["vol001_valid_observation"], ["overnight_return", "open_to_close_return", "rs_component"]] = np.nan
        result["vol001_yz_variance_20d"] = self._yang_zhang_variance(result)
        result["vol001_yz_volatility_20d"] = np.sqrt(
            np.maximum(result["vol001_yz_variance_20d"], 0) * float(self.annualization_factor)
        )
        result["vol001_zscore"] = self._rolling_zscore(result["vol001_yz_volatility_20d"])
        result["vol001_percentile"] = self._rolling_percentile(result["vol001_yz_volatility_20d"])
        return result[
            [
                "date",
                "open",
                "high",
                "low",
                "close",
                "overnight_return",
                "open_to_close_return",
                "rs_component",
                "vol001_yz_variance_20d",
                "vol001_yz_volatility_20d",
                "vol001_zscore",
                "vol001_percentile",
                "vol001_valid_observation",
            ]
        ]

    def _prepare_ohlc(self, data: pd.DataFrame) -> pd.DataFrame:
        required = {"Open", "High", "Low", "Close"}
        missing = required - set(data.columns)
        if missing:
            raise ValueError(f"Missing required VOL-001 OHLC columns: {sorted(missing)}")

        frame = data.copy()
        frame.index = pd.to_datetime(frame.index)
        frame = frame.sort_index()
        frame = frame[~frame.index.duplicated(keep="first")]

        ohlc = pd.DataFrame(index=frame.index)
        for source, target in [("Open", "open"), ("High", "high"), ("Low", "low"), ("Close", "close")]:
            ohlc[target] = pd.to_numeric(frame[source], errors="coerce")

        if "Adj Close" in frame.columns:
            adj_close = pd.to_numeric(frame["Adj Close"], errors="coerce")
            raw_close = pd.to_numeric(frame["Close"], errors="coerce")
            factor = adj_close / raw_close
            valid_factor = np.isfinite(factor) & factor.gt(0)
            for column in ["open", "high", "low", "close"]:
                ohlc[column] = np.where(valid_factor, ohlc[column] * factor, ohlc[column])

        return ohlc.dropna(subset=["open", "high", "low", "close"])

    def _yang_zhang_variance(self, frame: pd.DataFrame) -> pd.Series:
        k = 0.34 / (1.34 + (self.vol_window + 1) / (self.vol_window - 1))
        sigma_o2 = frame["overnight_return"].rolling(self.vol_window, min_periods=self.vol_window).var(ddof=1)
        sigma_c2 = frame["open_to_close_return"].rolling(self.vol_window, min_periods=self.vol_window).var(ddof=1)
        sigma_rs = frame["rs_component"].rolling(self.vol_window, min_periods=self.vol_window).mean()
        return sigma_o2 + (k * sigma_c2) + ((1 - k) * sigma_rs)

    def _rolling_zscore(self, series: pd.Series) -> pd.Series:
        rolling_mean = series.rolling(self.normalization_window, min_periods=self.normalization_window).mean()
        rolling_std = series.rolling(self.normalization_window, min_periods=self.normalization_window).std(ddof=0)
        return (series - rolling_mean) / rolling_std

    def _rolling_percentile(self, series: pd.Series) -> pd.Series:
        def percentile(values: np.ndarray) -> float:
            current = values[-1]
            if not np.isfinite(current) or np.isnan(values).any():
                return np.nan
            return float(np.sum(values <= current) / self.normalization_window)

        return series.rolling(self.normalization_window, min_periods=self.normalization_window).apply(percentile, raw=True)

