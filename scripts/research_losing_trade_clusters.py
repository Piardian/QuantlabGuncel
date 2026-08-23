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
BENCHMARK = "SPY"
START = "2018-01-01"
END = "2025-01-01"
TIMEFRAME = "1d"
ATR_PERIOD = 14
EMA50_PERIOD = 50
EMA200_PERIOD = 200
VOL_PERIOD = 20
WINDOWS = [
    ("W1_2021", "2021-01-01", "2022-01-01"),
    ("W2_2022", "2022-01-01", "2023-01-01"),
    ("W3_2023", "2023-01-01", "2024-01-01"),
    ("W4_2024", "2024-01-01", "2025-01-01"),
]


def main() -> None:
    data_source = YahooFinanceDataSource()
    benchmark_data = _add_indicators(_fetch_with_retry(data_source=data_source, ticker=BENCHMARK))
    universe = _load_walk_forward_universe()
    market_cache = {BENCHMARK: benchmark_data}
    for ticker in universe:
        if ticker == BENCHMARK:
            continue
        market_cache[ticker] = _add_indicators(_fetch_with_retry(data_source=data_source, ticker=ticker))

    trades = _load_walk_forward_trades(universe=universe)
    enriched = _enrich_trades(trades=trades, market_cache=market_cache, benchmark_data=benchmark_data)
    cluster_path = OUTPUT_DIR / "losing_trade_cluster_analysis.csv"
    enriched.to_csv(cluster_path, index=False)

    summary = _build_group_summary(enriched)
    summary_path = OUTPUT_DIR / "winning_vs_losing_summary.csv"
    summary.to_csv(summary_path, index=False)

    failure_2022 = _build_2022_failure_analysis(enriched)
    failure_path = OUTPUT_DIR / "2022_failure_analysis.csv"
    failure_2022.to_csv(failure_path, index=False)

    print(cluster_path)
    print(summary_path)
    print(failure_path)


def _fetch_with_retry(data_source: YahooFinanceDataSource, ticker: str) -> pd.DataFrame:
    last_error: Exception | None = None
    for _ in range(3):
        try:
            return data_source.fetch(MarketDataRequest(ticker=ticker, start=START, end=END, timeframe=TIMEFRAME))
        except Exception as exc:
            last_error = exc
            time.sleep(1)
    raise RuntimeError(f"Could not fetch data for {ticker}: {last_error}") from last_error


def _load_walk_forward_universe() -> list[str]:
    universe_path = OUTPUT_DIR / "walk_forward_universe.csv"
    if not universe_path.exists():
        raise RuntimeError("Missing walk_forward_universe.csv. Run walk-forward validation first.")
    return pd.read_csv(universe_path)["ticker"].dropna().astype(str).tolist()


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
    data["EMA50"] = data["Close"].ewm(span=EMA50_PERIOD, adjust=False).mean()
    data["EMA200"] = data["Close"].ewm(span=EMA200_PERIOD, adjust=False).mean()
    data["DailyReturn"] = data["Close"].pct_change()
    data["RealizedVol20"] = data["DailyReturn"].rolling(VOL_PERIOD).std() * math.sqrt(252)
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


def _load_walk_forward_trades(universe: list[str]) -> pd.DataFrame:
    frames = []
    for window_name, test_start, test_end in WINDOWS:
        for ticker in universe:
            trades_path = OUTPUT_DIR / f"walk_forward_{window_name}_{ticker}" / "trades.csv"
            if not trades_path.exists():
                continue
            trades = pd.read_csv(trades_path, parse_dates=["entry_time", "exit_time"])
            if trades.empty:
                continue
            test_trades = trades[
                (trades["entry_time"] >= pd.Timestamp(test_start))
                & (trades["entry_time"] < pd.Timestamp(test_end))
            ].copy()
            if test_trades.empty:
                continue
            test_trades["window"] = window_name
            test_trades["ticker"] = ticker
            frames.append(test_trades)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def _enrich_trades(
    trades: pd.DataFrame,
    market_cache: dict[str, pd.DataFrame],
    benchmark_data: pd.DataFrame,
) -> pd.DataFrame:
    rows = []
    for trade_id, trade in trades.reset_index(drop=True).iterrows():
        ticker = str(trade["ticker"])
        market_data = market_cache[ticker]
        entry_position = _position_for_date(market_data, pd.Timestamp(trade["entry_time"]))
        benchmark_position = _position_for_date(benchmark_data, pd.Timestamp(trade["entry_time"]))
        if entry_position is None or benchmark_position is None or entry_position < 60 or benchmark_position < 60:
            continue

        row = market_data.iloc[entry_position]
        close = float(row["Close"])
        atr14 = float(row["ATR14"])
        ema50 = float(row["EMA50"])
        ema200 = float(row["EMA200"])
        if close <= 0 or atr14 <= 0 or ema50 <= 0 or ema200 <= 0:
            continue

        stock_return_60 = _return_at_position(market_data, entry_position, 60)
        benchmark_return_60 = _return_at_position(benchmark_data, benchmark_position, 60)
        trade_r = float(trade["R_multiple"])
        outcome = "WIN" if trade_r > 0 else "LOSS" if trade_r < 0 else "FLAT"

        rows.append(
            {
                "trade_id": trade_id + 1,
                "window": trade["window"],
                "ticker": ticker,
                "entry_time": trade["entry_time"],
                "exit_time": trade["exit_time"],
                "trade_R": trade_r,
                "trade_outcome": outcome,
                "trade_duration_bars": int(trade["trade_duration_bars"]),
                "exit_reason": trade["exit_reason"],
                "RS60": stock_return_60 - benchmark_return_60,
                "ATR_percent": atr14 / close,
                "volatility": float(row["RealizedVol20"]),
                "distance_from_EMA50": (close - ema50) / atr14,
                "distance_from_EMA200": (close - ema200) / atr14,
            }
        )
    return pd.DataFrame(rows)


def _position_for_date(dataframe: pd.DataFrame, date: pd.Timestamp) -> int | None:
    normalized_date = date.normalize()
    matches = [index for index, item in enumerate(dataframe.index.normalize()) if item == normalized_date]
    if not matches:
        return None
    return matches[0]


def _return_at_position(dataframe: pd.DataFrame, position: int, lookback: int) -> float:
    current_close = float(dataframe.iloc[position]["Close"])
    previous_close = float(dataframe.iloc[position - lookback]["Close"])
    return (current_close / previous_close) - 1.0


def _build_group_summary(enriched: pd.DataFrame) -> pd.DataFrame:
    groups = {
        "ALL_WINNING_TRADES": enriched[enriched["trade_outcome"] == "WIN"],
        "ALL_LOSING_TRADES": enriched[enriched["trade_outcome"] == "LOSS"],
        "LOSING_TRADES_2022": enriched[
            (enriched["trade_outcome"] == "LOSS")
            & (pd.to_datetime(enriched["entry_time"]) >= pd.Timestamp("2022-01-01"))
            & (pd.to_datetime(enriched["entry_time"]) < pd.Timestamp("2023-01-01"))
        ],
    }
    return pd.DataFrame([{"group": group_name, **_summarize_group(group)} for group_name, group in groups.items()])


def _summarize_group(group: pd.DataFrame) -> dict[str, float | int]:
    if group.empty:
        return {
            "trade_count": 0,
            "avg_R": 0.0,
            "avg_duration": 0.0,
            "median_duration": 0.0,
            "avg_RS60": 0.0,
            "avg_ATR_percent": 0.0,
            "avg_volatility": 0.0,
            "avg_distance_from_EMA50": 0.0,
            "avg_distance_from_EMA200": 0.0,
            "STOP_pct": 0.0,
            "ATR_TRAIL_pct": 0.0,
            "EMA_EXIT_pct": 0.0,
            "TIME_EXIT_pct": 0.0,
        }

    exit_counts = group["exit_reason"].value_counts(normalize=True) * 100.0
    return {
        "trade_count": int(len(group)),
        "avg_R": float(group["trade_R"].mean()),
        "avg_duration": float(group["trade_duration_bars"].mean()),
        "median_duration": float(group["trade_duration_bars"].median()),
        "avg_RS60": float(group["RS60"].mean()),
        "avg_ATR_percent": float(group["ATR_percent"].mean()),
        "avg_volatility": float(group["volatility"].mean()),
        "avg_distance_from_EMA50": float(group["distance_from_EMA50"].mean()),
        "avg_distance_from_EMA200": float(group["distance_from_EMA200"].mean()),
        "STOP_pct": float(exit_counts.get("STOP", 0.0)),
        "ATR_TRAIL_pct": float(exit_counts.get("ATR_TRAIL", 0.0)),
        "EMA_EXIT_pct": float(exit_counts.get("EMA_EXIT", 0.0)),
        "TIME_EXIT_pct": float(exit_counts.get("TIME_EXIT", 0.0)),
    }


def _build_2022_failure_analysis(enriched: pd.DataFrame) -> pd.DataFrame:
    losing_2022 = enriched[
        (enriched["trade_outcome"] == "LOSS")
        & (pd.to_datetime(enriched["entry_time"]) >= pd.Timestamp("2022-01-01"))
        & (pd.to_datetime(enriched["entry_time"]) < pd.Timestamp("2023-01-01"))
    ]
    rows = [{"section": "GROUP_SUMMARY", "label": "2022_LOSING_TRADES", **_summarize_group(losing_2022)}]

    for ticker, group in losing_2022.groupby("ticker"):
        rows.append(
            {
                "section": "TOP_LOSING_TICKERS_2022",
                "label": ticker,
                "trade_count": int(len(group)),
                "avg_R": float(group["trade_R"].mean()),
                "net_R": float(group["trade_R"].sum()),
            }
        )

    top_winners = (
        enriched[enriched["trade_outcome"] == "WIN"]
        .groupby("ticker")["trade_R"]
        .agg(["count", "sum", "mean"])
        .sort_values("sum", ascending=False)
        .head(10)
    )
    for ticker, row in top_winners.iterrows():
        rows.append(
            {
                "section": "TOP_WINNING_TICKERS_ALL",
                "label": ticker,
                "trade_count": int(row["count"]),
                "avg_R": float(row["mean"]),
                "net_R": float(row["sum"]),
            }
        )

    top_losers = (
        enriched[enriched["trade_outcome"] == "LOSS"]
        .groupby("ticker")["trade_R"]
        .agg(["count", "sum", "mean"])
        .sort_values("sum", ascending=True)
        .head(10)
    )
    for ticker, row in top_losers.iterrows():
        rows.append(
            {
                "section": "TOP_LOSING_TICKERS_ALL",
                "label": ticker,
                "trade_count": int(row["count"]),
                "avg_R": float(row["mean"]),
                "net_R": float(row["sum"]),
            }
        )

    return pd.DataFrame(rows)


if __name__ == "__main__":
    main()
