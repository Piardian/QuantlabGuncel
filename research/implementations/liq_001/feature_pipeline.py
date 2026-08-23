from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True, slots=True)
class LiquidityFeaturePipeline:
    """Deterministic feature builder for the frozen LIQ-001 construct."""

    smoothing_window: int = 20
    zscore_window: int = 252
    min_eligible_securities: int = 50

    def build_security_features(self, ticker: str, data: pd.DataFrame) -> pd.DataFrame:
        required = {"Close", "Volume"}
        missing = required - set(data.columns)
        if missing:
            raise ValueError(f"Missing required columns for {ticker}: {sorted(missing)}")

        frame = data.copy()
        frame.index = pd.to_datetime(frame.index)
        frame = frame.sort_index()
        frame = frame[~frame.index.duplicated(keep="first")]

        close = pd.to_numeric(frame["Close"], errors="coerce")
        volume = pd.to_numeric(frame["Volume"], errors="coerce")
        previous_close = close.shift(1)
        log_return = np.log(close / previous_close)
        dollar_volume = close * volume

        result = pd.DataFrame(
            {
                "date": frame.index,
                "ticker": ticker,
                "close": close.to_numpy(),
                "volume": volume.to_numpy(),
                "log_return": log_return.to_numpy(),
                "dollar_volume": dollar_volume.to_numpy(),
            }
        )
        result["eligible"] = (
            result["close"].gt(0)
            & result["volume"].gt(0)
            & result["dollar_volume"].gt(0)
            & np.isfinite(result["log_return"])
        )
        result["security_illiquidity"] = np.where(
            result["eligible"],
            result["log_return"].abs() / result["dollar_volume"],
            np.nan,
        )
        return result

    def build_aggregate(self, security_features: pd.DataFrame, universe_size: int) -> pd.DataFrame:
        required = {"date", "security_illiquidity", "eligible"}
        missing = required - set(security_features.columns)
        if missing:
            raise ValueError(f"Missing required security feature columns: {sorted(missing)}")
        if universe_size <= 0:
            raise ValueError("universe_size must be positive.")

        eligible = security_features[security_features["eligible"]].copy()
        grouped = eligible.groupby("date", sort=True)
        aggregate = grouped["security_illiquidity"].median().rename("aggregate_illiquidity").to_frame()
        aggregate["eligible_count"] = grouped["security_illiquidity"].count().astype(int)
        aggregate["coverage_ratio"] = aggregate["eligible_count"] / float(universe_size)
        aggregate = aggregate[aggregate["eligible_count"] >= self.min_eligible_securities]
        aggregate = aggregate.sort_index()
        aggregate["liq001_illiquidity_20d"] = (
            aggregate["aggregate_illiquidity"].rolling(self.smoothing_window, min_periods=self.smoothing_window).mean()
        )
        rolling_mean = aggregate["liq001_illiquidity_20d"].rolling(self.zscore_window, min_periods=self.zscore_window).mean()
        rolling_std = aggregate["liq001_illiquidity_20d"].rolling(self.zscore_window, min_periods=self.zscore_window).std(ddof=0)
        aggregate["liq001_zscore"] = (aggregate["liq001_illiquidity_20d"] - rolling_mean) / rolling_std
        aggregate = aggregate.reset_index().rename(columns={"index": "date"})
        return aggregate[
            [
                "date",
                "aggregate_illiquidity",
                "liq001_illiquidity_20d",
                "liq001_zscore",
                "eligible_count",
                "coverage_ratio",
            ]
        ]


