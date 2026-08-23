from __future__ import annotations

from pathlib import Path
import sys
import time

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from data.yahoo_data import MarketDataRequest, YahooFinanceDataSource

OUTPUT_DIR = ROOT / "output"
UNIVERSE = ["AAPL", "MSFT", "NVDA", "META", "AMZN", "GOOGL", "TSLA", "SPY", "QQQ"]
START = "2018-01-01"
END = "2024-01-01"
TIMEFRAME = "1d"
ATR_PERIOD = 14


def main() -> None:
    data_source = YahooFinanceDataSource()
    rows: list[dict[str, object]] = []

    for ticker in UNIVERSE:
        market_data = _fetch_with_retry(data_source=data_source, ticker=ticker)
        enriched_data = _add_atr(market_data)
        trades_path = _resolve_trades_path(ticker)
        if trades_path is None:
            continue

        trades = pd.read_csv(trades_path, parse_dates=["entry_time", "exit_time"])
        for _, trade in trades.iterrows():
            feature_row = _build_feature_row(ticker=ticker, trade=trade, market_data=enriched_data)
            if feature_row is not None:
                rows.append(feature_row)

    features = pd.DataFrame(rows)
    features_path = OUTPUT_DIR / "trade_features.csv"
    features.to_csv(features_path, index=False)

    summary = _build_summary(features)
    summary_path = OUTPUT_DIR / "expansion_feature_summary.csv"
    summary.to_csv(summary_path, index=False)

    print(features_path)
    print(summary_path)


def _fetch_with_retry(data_source: YahooFinanceDataSource, ticker: str) -> pd.DataFrame:
    last_error: Exception | None = None
    for _ in range(3):
        try:
            return data_source.fetch(MarketDataRequest(ticker=ticker, start=START, end=END, timeframe=TIMEFRAME))
        except Exception as exc:
            last_error = exc
            time.sleep(1)
    raise RuntimeError(f"Could not fetch data for {ticker}: {last_error}") from last_error


def _resolve_trades_path(ticker: str) -> Path | None:
    candidates = [
        OUTPUT_DIR / f"leadership_quality_FULL_SYSTEM_{ticker}" / "trades.csv",
        OUTPUT_DIR / f"leadership_expansion_v1_{ticker}" / "trades.csv",
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def _add_atr(dataframe: pd.DataFrame) -> pd.DataFrame:
    data = dataframe.copy()
    previous_close = data["Close"].shift(1)
    true_range = pd.concat(
        [
            data["High"] - data["Low"],
            (data["High"] - previous_close).abs(),
            (data["Low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    data["TrueRange"] = true_range
    data["ATR14"] = _wilder_average(true_range, ATR_PERIOD)
    return data


def _wilder_average(series: pd.Series, period: int) -> pd.Series:
    values = series.astype(float)
    averages = pd.Series(index=values.index, dtype=float)
    if len(values) < period:
        return averages

    averages.iloc[period - 1] = values.iloc[:period].mean()
    for index in range(period, len(values)):
        averages.iloc[index] = ((averages.iloc[index - 1] * (period - 1)) + values.iloc[index]) / period
    return averages


def _build_feature_row(ticker: str, trade: pd.Series, market_data: pd.DataFrame) -> dict[str, object] | None:
    entry_time = pd.Timestamp(trade["entry_time"]).normalize()
    dates = market_data.index.normalize()
    matching_positions = [index for index, date in enumerate(dates) if date == entry_time]
    if not matching_positions:
        return None

    entry_position = matching_positions[0]
    signal_position = entry_position - 1
    next_position = signal_position + 1
    previous_position = signal_position - 1
    if signal_position < 1 or next_position >= len(market_data):
        return None

    signal_bar = market_data.iloc[signal_position]
    previous_bar = market_data.iloc[previous_position]
    next_bar = market_data.iloc[next_position]

    high = float(signal_bar["High"])
    low = float(signal_bar["Low"])
    open_price = float(signal_bar["Open"])
    close = float(signal_bar["Close"])
    true_range = float(signal_bar["TrueRange"])
    atr14 = float(signal_bar["ATR14"])
    previous_close = float(previous_bar["Close"])
    previous_high = float(previous_bar["High"])

    if high <= low or true_range <= 0 or previous_close <= 0 or atr14 <= 0:
        return None

    trade_r = float(trade["R_multiple"])
    trade_outcome = "flat"
    if trade_r > 0:
        trade_outcome = "win"
    elif trade_r < 0:
        trade_outcome = "loss"

    return {
        "ticker": ticker,
        "entry_time": trade["entry_time"],
        "signal_time": market_data.index[signal_position],
        "close_location": (close - low) / (high - low),
        "body_pct": abs(close - open_price) / true_range,
        "upper_wick_pct": (high - max(open_price, close)) / true_range,
        "gap_pct": (open_price - previous_close) / previous_close,
        "close_vs_prev_high": close > previous_high,
        "range_expansion_ratio": true_range / atr14,
        "followthrough_next_day": float(next_bar["Close"]) > close,
        "trade_outcome": trade_outcome,
        "trade_R": trade_r,
    }


def _build_summary(features: pd.DataFrame) -> pd.DataFrame:
    numeric_features = [
        "close_location",
        "body_pct",
        "upper_wick_pct",
        "gap_pct",
        "range_expansion_ratio",
        "close_vs_prev_high",
        "followthrough_next_day",
    ]
    winners = features[features["trade_outcome"] == "win"]
    losers = features[features["trade_outcome"] == "loss"]

    rows = []
    for feature_name in numeric_features:
        winner_mean = float(winners[feature_name].mean()) if not winners.empty else 0.0
        loser_mean = float(losers[feature_name].mean()) if not losers.empty else 0.0
        rows.append(
            {
                "feature_name": feature_name,
                "winner_mean": winner_mean,
                "loser_mean": loser_mean,
                "difference": winner_mean - loser_mean,
            }
        )
    return pd.DataFrame(rows)


if __name__ == "__main__":
    main()
