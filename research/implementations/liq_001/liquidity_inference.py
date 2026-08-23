from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from data.yahoo_data import MarketDataRequest, YahooFinanceDataSource  # noqa: E402
from liq001_liquidity_model import LIQ001LiquidityModel, LiquidityModelResult  # noqa: E402


def infer_liquidity_from_market_data(
    market_data: dict[str, pd.DataFrame],
    smoothing_window: int = 20,
    zscore_window: int = 252,
    min_eligible_securities: int = 50,
) -> LiquidityModelResult:
    model = LIQ001LiquidityModel(
        smoothing_window=smoothing_window,
        zscore_window=zscore_window,
        min_eligible_securities=min_eligible_securities,
    )
    return model.fit_transform(market_data)


def infer_liquidity_from_yahoo(
    tickers: list[str],
    start: str,
    end: str,
    timeframe: str = "1d",
    smoothing_window: int = 20,
    zscore_window: int = 252,
    min_eligible_securities: int = 50,
) -> LiquidityModelResult:
    source = YahooFinanceDataSource()
    market_data: dict[str, pd.DataFrame] = {}
    for ticker in tickers:
        market_data[ticker] = source.fetch(
            MarketDataRequest(ticker=ticker, start=start, end=end, timeframe=timeframe)
        )
    return infer_liquidity_from_market_data(
        market_data=market_data,
        smoothing_window=smoothing_window,
        zscore_window=zscore_window,
        min_eligible_securities=min_eligible_securities,
    )


