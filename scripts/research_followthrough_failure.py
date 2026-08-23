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
START = "2018-01-01"
END = "2025-01-01"
TIMEFRAME = "1d"
WINDOWS = [
    ("W1_2021", "2021-01-01", "2022-01-01"),
    ("W2_2022", "2022-01-01", "2023-01-01"),
    ("W3_2023", "2023-01-01", "2024-01-01"),
    ("W4_2024", "2024-01-01", "2025-01-01"),
]


def main() -> None:
    data_source = YahooFinanceDataSource()
    universe = _load_walk_forward_universe()
    market_cache = {
        ticker: _fetch_with_retry(data_source=data_source, ticker=ticker)
        for ticker in universe
    }
    trades = _load_walk_forward_trades(universe=universe)

    rows = []
    for trade_id, trade in trades.reset_index(drop=True).iterrows():
        row = _build_followthrough_row(
            trade_id=trade_id + 1,
            trade=trade,
            market_data=market_cache[str(trade["ticker"])],
        )
        if row is not None:
            rows.append(row)

    followthrough = pd.DataFrame(rows)
    followthrough_path = OUTPUT_DIR / "followthrough_research.csv"
    followthrough.to_csv(followthrough_path, index=False)

    summary = _build_summary(followthrough)
    summary_path = OUTPUT_DIR / "followthrough_summary.csv"
    summary.to_csv(summary_path, index=False)

    false_expansion = _build_false_expansion_profile(followthrough)
    false_expansion_path = OUTPUT_DIR / "false_expansion_profile.csv"
    false_expansion.to_csv(false_expansion_path, index=False)

    print(followthrough_path)
    print(summary_path)
    print(false_expansion_path)


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


def _build_followthrough_row(
    trade_id: int,
    trade: pd.Series,
    market_data: pd.DataFrame,
) -> dict[str, object] | None:
    entry_position = _position_for_date(market_data, pd.Timestamp(trade["entry_time"]))
    if entry_position is None or entry_position + 3 >= len(market_data):
        return None

    entry_bar = market_data.iloc[entry_position]
    day1 = market_data.iloc[entry_position + 1]
    day2 = market_data.iloc[entry_position + 2]
    day3 = market_data.iloc[entry_position + 3]

    entry_close = float(entry_bar["Close"])
    entry_price = float(trade["entry_price"])
    if entry_close <= 0 or entry_price <= 0:
        return None

    first_3 = market_data.iloc[entry_position + 1 : entry_position + 4]
    high_3d = float(first_3["High"].max())
    low_3d = float(first_3["Low"].min())
    trade_r = float(trade["R_multiple"])

    return {
        "trade_id": trade_id,
        "window": trade["window"],
        "ticker": trade["ticker"],
        "entry_time": trade["entry_time"],
        "trade_R": trade_r,
        "trade_outcome": "WIN" if trade_r > 0 else "LOSS" if trade_r < 0 else "FLAT",
        "exit_reason": trade["exit_reason"],
        "trade_duration_bars": int(trade["trade_duration_bars"]),
        "max_favorable_excursion_3d": (high_3d - entry_price) / entry_price,
        "max_adverse_excursion_3d": (low_3d - entry_price) / entry_price,
        "close_change_day1": (float(day1["Close"]) - entry_close) / entry_close,
        "close_change_day2": (float(day2["Close"]) - entry_close) / entry_close,
        "close_change_day3": (float(day3["Close"]) - entry_close) / entry_close,
        "distance_from_entry_to_day3_high": (high_3d - entry_price) / entry_price,
        "distance_from_entry_to_day3_low": (low_3d - entry_price) / entry_price,
        "day1_followthrough": float(day1["Close"]) > entry_close,
        "day3_followthrough": float(day3["Close"]) > entry_close,
    }


def _position_for_date(dataframe: pd.DataFrame, date: pd.Timestamp) -> int | None:
    normalized_date = date.normalize()
    matches = [index for index, item in enumerate(dataframe.index.normalize()) if item == normalized_date]
    if not matches:
        return None
    return matches[0]


def _build_summary(followthrough: pd.DataFrame) -> pd.DataFrame:
    features = [
        "max_favorable_excursion_3d",
        "max_adverse_excursion_3d",
        "close_change_day1",
        "close_change_day2",
        "close_change_day3",
        "distance_from_entry_to_day3_high",
        "distance_from_entry_to_day3_low",
        "day1_followthrough",
        "day3_followthrough",
    ]
    winners = followthrough[followthrough["trade_outcome"] == "WIN"]
    losers = followthrough[followthrough["trade_outcome"] == "LOSS"]
    rows = []
    for feature_name in features:
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


def _build_false_expansion_profile(followthrough: pd.DataFrame) -> pd.DataFrame:
    losers = followthrough[followthrough["trade_outcome"] == "LOSS"]
    if losers.empty:
        return pd.DataFrame()

    return pd.DataFrame(
        [
            {
                "group": "LOSING_TRADES",
                "trade_count": int(len(losers)),
                "avg_trade_R": float(losers["trade_R"].mean()),
                "avg_max_favorable_excursion_3d": float(losers["max_favorable_excursion_3d"].mean()),
                "avg_max_adverse_excursion_3d": float(losers["max_adverse_excursion_3d"].mean()),
                "avg_close_change_day1": float(losers["close_change_day1"].mean()),
                "avg_close_change_day2": float(losers["close_change_day2"].mean()),
                "avg_close_change_day3": float(losers["close_change_day3"].mean()),
                "day1_followthrough_pct": float(losers["day1_followthrough"].mean() * 100.0),
                "day3_followthrough_pct": float(losers["day3_followthrough"].mean() * 100.0),
                "STOP_pct": float((losers["exit_reason"] == "STOP").mean() * 100.0),
                "ATR_TRAIL_pct": float((losers["exit_reason"] == "ATR_TRAIL").mean() * 100.0),
            }
        ]
    )


if __name__ == "__main__":
    main()
