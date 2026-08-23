from __future__ import annotations

from pathlib import Path
import math
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
EMA_PERIOD = 50
BENCHMARK = "SPY"


def main() -> None:
    data_source = YahooFinanceDataSource()
    benchmark_data = _add_indicators(_fetch_with_retry(data_source=data_source, ticker=BENCHMARK))
    rows: list[dict[str, object]] = []

    for ticker in UNIVERSE:
        market_data = benchmark_data if ticker == BENCHMARK else _add_indicators(
            _fetch_with_retry(data_source=data_source, ticker=ticker)
        )
        trades_path = _resolve_trades_path(ticker)
        if trades_path is None:
            continue

        trades = pd.read_csv(trades_path, parse_dates=["entry_time", "exit_time"])
        for _, trade in trades.iterrows():
            row = _build_context_row(
                ticker=ticker,
                trade=trade,
                market_data=market_data,
                benchmark_data=benchmark_data,
            )
            if row is not None:
                rows.append(row)

    context = pd.DataFrame(rows)
    context_path = OUTPUT_DIR / "pre_expansion_context.csv"
    context.to_csv(context_path, index=False)

    summary = _build_summary(context)
    summary_path = OUTPUT_DIR / "pre_expansion_summary.csv"
    summary.to_csv(summary_path, index=False)

    print(context_path)
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


def _add_indicators(dataframe: pd.DataFrame) -> pd.DataFrame:
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
    data["EMA50"] = data["Close"].ewm(span=EMA_PERIOD, adjust=False).mean()
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


def _build_context_row(
    ticker: str,
    trade: pd.Series,
    market_data: pd.DataFrame,
    benchmark_data: pd.DataFrame,
) -> dict[str, object] | None:
    entry_time = pd.Timestamp(trade["entry_time"]).normalize()
    dates = market_data.index.normalize()
    matching_positions = [index for index, date in enumerate(dates) if date == entry_time]
    if not matching_positions:
        return None

    entry_position = matching_positions[0]
    breakout_position = entry_position - 1
    context_position = breakout_position - 1
    if context_position < 120:
        return None

    context_date = market_data.index[context_position]
    benchmark_position = _position_for_date(benchmark_data=benchmark_data, date=context_date)
    if benchmark_position is None or benchmark_position < 120:
        return None

    context_bar = market_data.iloc[context_position]
    close = float(context_bar["Close"])
    atr14 = float(context_bar["ATR14"])
    ema50 = float(context_bar["EMA50"])
    if close <= 0 or atr14 <= 0 or not math.isfinite(atr14):
        return None

    atr_20_ago = float(market_data.iloc[context_position - 20]["ATR14"])
    if atr_20_ago <= 0 or not math.isfinite(atr_20_ago):
        return None

    avg_volume_5 = float(market_data.iloc[context_position - 4 : context_position + 1]["Volume"].mean())
    avg_volume_20 = float(market_data.iloc[context_position - 19 : context_position + 1]["Volume"].mean())
    if avg_volume_20 <= 0:
        return None

    avg_atr_5 = float(market_data.iloc[context_position - 4 : context_position + 1]["ATR14"].mean())
    avg_atr_20 = float(market_data.iloc[context_position - 19 : context_position + 1]["ATR14"].mean())
    if avg_atr_20 <= 0:
        return None

    highest_high_10 = float(market_data.iloc[context_position - 9 : context_position + 1]["High"].max())
    lowest_low_10 = float(market_data.iloc[context_position - 9 : context_position + 1]["Low"].min())

    stock_return_20 = _return_at_position(market_data, context_position, 20)
    stock_return_60 = _return_at_position(market_data, context_position, 60)
    benchmark_return_20 = _return_at_position(benchmark_data, benchmark_position, 20)
    benchmark_return_60 = _return_at_position(benchmark_data, benchmark_position, 60)
    rs20 = stock_return_20 - benchmark_return_20
    rs60 = stock_return_60 - benchmark_return_60

    trade_r = float(trade["R_multiple"])
    trade_outcome = "flat"
    if trade_r > 0:
        trade_outcome = "win"
    elif trade_r < 0:
        trade_outcome = "loss"

    return {
        "ticker": ticker,
        "entry_time": trade["entry_time"],
        "breakout_time": market_data.index[breakout_position],
        "context_time": context_date,
        "consolidation_length": _consolidation_length(market_data, context_position),
        "compression_ratio": atr14 / atr_20_ago,
        "pre_expansion_volume_ratio": avg_volume_5 / avg_volume_20,
        "relative_strength_acceleration": rs20 - rs60,
        "ema50_distance": (close - ema50) / atr14,
        "base_tightness": (highest_high_10 - lowest_low_10) / atr14,
        "pre_breakout_volatility": avg_atr_5 / avg_atr_20,
        "trade_outcome": trade_outcome,
        "trade_R": trade_r,
    }


def _position_for_date(benchmark_data: pd.DataFrame, date: pd.Timestamp) -> int | None:
    normalized_date = pd.Timestamp(date).normalize()
    dates = benchmark_data.index.normalize()
    matches = [index for index, benchmark_date in enumerate(dates) if benchmark_date == normalized_date]
    if not matches:
        return None
    return matches[0]


def _return_at_position(dataframe: pd.DataFrame, position: int, lookback: int) -> float:
    current_close = float(dataframe.iloc[position]["Close"])
    previous_close = float(dataframe.iloc[position - lookback]["Close"])
    return (current_close / previous_close) - 1.0


def _consolidation_length(market_data: pd.DataFrame, context_position: int) -> int:
    length = 0
    for position in range(context_position, -1, -1):
        true_range = float(market_data.iloc[position]["TrueRange"])
        atr14 = float(market_data.iloc[position]["ATR14"])
        if atr14 <= 0 or not math.isfinite(atr14):
            break
        if true_range > atr14:
            break
        length += 1
    return length


def _build_summary(context: pd.DataFrame) -> pd.DataFrame:
    feature_names = [
        "consolidation_length",
        "compression_ratio",
        "pre_expansion_volume_ratio",
        "relative_strength_acceleration",
        "ema50_distance",
        "base_tightness",
        "pre_breakout_volatility",
    ]
    winners = context[context["trade_outcome"] == "win"]
    losers = context[context["trade_outcome"] == "loss"]

    rows = []
    for feature_name in feature_names:
        winner_values = winners[feature_name].astype(float).dropna()
        loser_values = losers[feature_name].astype(float).dropna()
        winner_mean = float(winner_values.mean()) if not winner_values.empty else 0.0
        loser_mean = float(loser_values.mean()) if not loser_values.empty else 0.0
        rows.append(
            {
                "feature_name": feature_name,
                "winner_mean": winner_mean,
                "loser_mean": loser_mean,
                "difference": winner_mean - loser_mean,
                "cohens_d": _cohens_d(winner_values, loser_values),
            }
        )
    return pd.DataFrame(rows)


def _cohens_d(winner_values: pd.Series, loser_values: pd.Series) -> float:
    winner_count = len(winner_values)
    loser_count = len(loser_values)
    if winner_count < 2 or loser_count < 2:
        return 0.0

    winner_var = float(winner_values.var(ddof=1))
    loser_var = float(loser_values.var(ddof=1))
    pooled_denominator = winner_count + loser_count - 2
    if pooled_denominator <= 0:
        return 0.0

    pooled_std = math.sqrt(((winner_count - 1) * winner_var + (loser_count - 1) * loser_var) / pooled_denominator)
    if pooled_std <= 0 or not math.isfinite(pooled_std):
        return 0.0
    return (float(winner_values.mean()) - float(loser_values.mean())) / pooled_std


if __name__ == "__main__":
    main()
