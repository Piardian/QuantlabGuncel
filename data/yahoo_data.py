from __future__ import annotations

from dataclasses import dataclass
import time

import pandas as pd
import yfinance as yf


REQUIRED_COLUMNS = ["Open", "High", "Low", "Close", "Volume"]


@dataclass(slots=True)
class MarketDataRequest:
    ticker: str
    start: str
    end: str
    timeframe: str = "1d"


class YahooFinanceDataSource:
    """Fetches and normalizes OHLCV market data from Yahoo Finance."""

    def fetch(self, request: MarketDataRequest) -> pd.DataFrame:
        dataframe = self._download_with_retry(request)

        if dataframe.empty:
            raise ValueError(
                f"No market data returned for {request.ticker} "
                f"between {request.start} and {request.end} at {request.timeframe}."
            )

        dataframe = self._normalize_columns(dataframe)
        dataframe = self._clean_missing_data(dataframe)

        if dataframe.empty:
            raise ValueError(
                f"Market data for {request.ticker} became empty after cleaning. "
                "Check the symbol, dates, or timeframe."
            )

        return dataframe

    @staticmethod
    def _normalize_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
        dataframe = dataframe.copy()

        if isinstance(dataframe.columns, pd.MultiIndex):
            dataframe.columns = dataframe.columns.get_level_values(0)

        missing = [column for column in REQUIRED_COLUMNS if column not in dataframe.columns]
        if missing:
            raise ValueError(f"Missing required market data columns: {missing}")

        dataframe = dataframe[REQUIRED_COLUMNS]
        dataframe.index = pd.to_datetime(dataframe.index)
        dataframe.index.name = "Datetime"
        dataframe = dataframe.sort_index()
        dataframe = dataframe[~dataframe.index.duplicated(keep="first")]

        return dataframe

    @staticmethod
    def _clean_missing_data(dataframe: pd.DataFrame) -> pd.DataFrame:
        cleaned = dataframe.copy()

        cleaned["Volume"] = cleaned["Volume"].fillna(0)
        cleaned[["Open", "High", "Low", "Close"]] = cleaned[
            ["Open", "High", "Low", "Close"]
        ].ffill()

        cleaned = cleaned.dropna(subset=["Open", "High", "Low", "Close"])
        cleaned = cleaned[(cleaned["High"] >= cleaned["Low"]) & (cleaned["Volume"] >= 0)]

        return cleaned

    @staticmethod
    def _download_with_retry(request: MarketDataRequest, attempts: int = 3, delay_seconds: float = 1.5) -> pd.DataFrame:
        last_error: Exception | None = None

        for attempt in range(1, attempts + 1):
            try:
                return yf.download(
                    tickers=request.ticker,
                    start=request.start,
                    end=request.end,
                    interval=request.timeframe,
                    auto_adjust=False,
                    progress=False,
                    threads=False,
                )
            except Exception as exc:
                last_error = exc
                if "database is locked" not in str(exc).lower() or attempt == attempts:
                    break
                time.sleep(delay_seconds)

        if last_error is not None:
            raise RuntimeError(f"Yahoo Finance download failed: {last_error}") from last_error

        raise RuntimeError("Yahoo Finance download failed for an unknown reason.")
