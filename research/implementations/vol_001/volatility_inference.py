from __future__ import annotations

import time

import pandas as pd
import yfinance as yf

from vol001_volatility_model import VOL001VolatilityModel, VolatilityModelResult


def infer_volatility_from_market_data(
    data: pd.DataFrame,
    symbol: str = "SPY",
    vol_window: int = 20,
    normalization_window: int = 252,
    annualization_factor: int = 252,
) -> VolatilityModelResult:
    model = VOL001VolatilityModel(
        symbol=symbol,
        vol_window=vol_window,
        normalization_window=normalization_window,
        annualization_factor=annualization_factor,
    )
    return model.fit_transform(data)


def fetch_ohlc_with_adjustments(symbol: str, start: str, end: str, timeframe: str = "1d", attempts: int = 3) -> pd.DataFrame:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            data = yf.download(
                tickers=symbol,
                start=start,
                end=end,
                interval=timeframe,
                auto_adjust=False,
                progress=False,
                threads=False,
            )
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
            required = {"Open", "High", "Low", "Close"}
            missing = required - set(data.columns)
            if missing:
                raise ValueError(f"Missing required columns from Yahoo data: {sorted(missing)}")
            if data.empty:
                raise ValueError(f"No data returned for {symbol}.")
            data.index = pd.to_datetime(data.index)
            return data.sort_index()
        except Exception as exc:
            last_error = exc
            if attempt == attempts:
                break
            time.sleep(0.5)
    raise RuntimeError(f"Failed to fetch VOL-001 data for {symbol}: {last_error}") from last_error


def infer_volatility_from_yahoo(
    symbol: str = "SPY",
    start: str = "2010-01-01",
    end: str = "2026-01-01",
    timeframe: str = "1d",
    vol_window: int = 20,
    normalization_window: int = 252,
    annualization_factor: int = 252,
) -> VolatilityModelResult:
    data = fetch_ohlc_with_adjustments(symbol=symbol, start=start, end=end, timeframe=timeframe)
    return infer_volatility_from_market_data(
        data=data,
        symbol=symbol,
        vol_window=vol_window,
        normalization_window=normalization_window,
        annualization_factor=annualization_factor,
    )

