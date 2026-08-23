from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass(frozen=True, slots=True)
class MarketRegimeFeaturePipeline:
    """Deterministic feature builder for the frozen MR-001 construct."""

    realized_volatility_window: int = 20

    def build(self, data: pd.DataFrame) -> pd.DataFrame:
        required = {"Close"}
        missing = required - set(data.columns)
        if missing:
            raise ValueError(f"Missing required columns: {sorted(missing)}")

        frame = data.copy()
        frame.index = pd.to_datetime(frame.index)
        frame = frame.sort_index()
        frame = frame[~frame.index.duplicated(keep="first")]

        close = pd.to_numeric(frame["Close"], errors="coerce")
        frame["daily_log_return"] = np.log(close / close.shift(1))
        frame["realized_volatility_20d"] = frame["daily_log_return"].rolling(self.realized_volatility_window).std(ddof=0) * sqrt(252)
        frame = frame.dropna(subset=["daily_log_return", "realized_volatility_20d"])
        return frame[["Close", "daily_log_return", "realized_volatility_20d"]].rename(
            columns={"Close": "spy_close"}
        )

    @staticmethod
    def load_close_csv(path: Path | str) -> pd.DataFrame:
        frame = pd.read_csv(path, parse_dates=["Datetime"]).set_index("Datetime")
        if "Close" not in frame.columns:
            raise ValueError("CSV must contain a Close column.")
        return frame
