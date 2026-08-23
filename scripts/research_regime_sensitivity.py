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
EMA_PERIOD = 200
VOL_PERIOD = 20
HIGH_LOOKBACK = 252
WINDOWS = [
    ("W1_2021", "2021-01-01", "2022-01-01"),
    ("W2_2022", "2022-01-01", "2023-01-01"),
    ("W3_2023", "2023-01-01", "2024-01-01"),
    ("W4_2024", "2024-01-01", "2025-01-01"),
]


def main() -> None:
    data_source = YahooFinanceDataSource()
    spy_data = _add_regime_features(_fetch_with_retry(data_source=data_source, ticker=BENCHMARK))
    trades = _load_walk_forward_trades()
    if trades.empty:
        raise RuntimeError("No walk-forward trades found for regime sensitivity research.")

    rows = []
    for trade_id, trade in trades.reset_index(drop=True).iterrows():
        regime = _regime_for_entry(spy_data=spy_data, entry_time=pd.Timestamp(trade["entry_time"]))
        if regime is None:
            continue
        trade_r = float(trade["R_multiple"])
        rows.append(
            {
                "trade_id": trade_id + 1,
                "entry_time": trade["entry_time"],
                "ticker": trade["ticker"],
                "window": trade["window"],
                "trade_R": trade_r,
                **regime,
            }
        )

    sensitivity = pd.DataFrame(rows)
    sensitivity_path = OUTPUT_DIR / "regime_sensitivity.csv"
    sensitivity.to_csv(sensitivity_path, index=False)

    summary = _build_regime_summary(sensitivity)
    summary_path = OUTPUT_DIR / "regime_summary.csv"
    summary.to_csv(summary_path, index=False)

    correlations = _build_feature_correlations(sensitivity)
    correlations_path = OUTPUT_DIR / "regime_feature_correlation.csv"
    correlations.to_csv(correlations_path, index=False)

    print(sensitivity_path)
    print(summary_path)
    print(correlations_path)


def _fetch_with_retry(data_source: YahooFinanceDataSource, ticker: str) -> pd.DataFrame:
    last_error: Exception | None = None
    for _ in range(3):
        try:
            return data_source.fetch(MarketDataRequest(ticker=ticker, start=START, end=END, timeframe=TIMEFRAME))
        except Exception as exc:
            last_error = exc
            time.sleep(1)
    raise RuntimeError(f"Could not fetch data for {ticker}: {last_error}") from last_error


def _add_regime_features(dataframe: pd.DataFrame) -> pd.DataFrame:
    data = dataframe.copy()
    data["EMA200"] = data["Close"].ewm(span=EMA_PERIOD, adjust=False).mean()
    data["EMA200Prev"] = data["EMA200"].shift(1)
    data["SPYAboveEMA200"] = data["Close"] > data["EMA200"]
    data["SPYEMA200SlopePositive"] = data["EMA200"] > data["EMA200Prev"]
    data["SPYDistanceFromEMA200"] = (data["Close"] - data["EMA200"]) / data["EMA200"]
    data["SPYReturn60"] = data["Close"].pct_change(60)
    data["SPYRealizedVol20"] = data["Close"].pct_change().rolling(VOL_PERIOD).std() * math.sqrt(252)
    data["SPY52WeekHigh"] = data["High"].rolling(HIGH_LOOKBACK).max()
    data["SPYDrawdownFrom52WeekHigh"] = (data["Close"] / data["SPY52WeekHigh"]) - 1.0
    return data


def _load_walk_forward_trades() -> pd.DataFrame:
    universe_path = OUTPUT_DIR / "walk_forward_universe.csv"
    if not universe_path.exists():
        raise RuntimeError("Missing walk_forward_universe.csv. Run walk-forward validation first.")

    tickers = pd.read_csv(universe_path)["ticker"].dropna().astype(str).tolist()
    frames = []
    for window_name, test_start, test_end in WINDOWS:
        for ticker in tickers:
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


def _regime_for_entry(spy_data: pd.DataFrame, entry_time: pd.Timestamp) -> dict[str, object] | None:
    entry_date = entry_time.normalize()
    dates = spy_data.index.normalize()
    matches = [index for index, date in enumerate(dates) if date == entry_date]
    if not matches:
        return None

    row = spy_data.iloc[matches[0]]
    required_columns = [
        "EMA200",
        "EMA200Prev",
        "SPYDistanceFromEMA200",
        "SPYReturn60",
        "SPYRealizedVol20",
        "SPYDrawdownFrom52WeekHigh",
    ]
    if row[required_columns].isna().any():
        return None

    spy_above_ema200 = bool(row["SPYAboveEMA200"])
    spy_ema200_slope_positive = bool(row["SPYEMA200SlopePositive"])
    spy_distance = float(row["SPYDistanceFromEMA200"])
    spy_return_60 = float(row["SPYReturn60"])
    spy_realized_vol_20 = float(row["SPYRealizedVol20"])
    spy_drawdown = float(row["SPYDrawdownFrom52WeekHigh"])
    return {
        "spy_above_ema200": spy_above_ema200,
        "spy_ema200_slope_positive": spy_ema200_slope_positive,
        "spy_distance_from_ema200": spy_distance,
        "spy_60d_return": spy_return_60,
        "spy_realized_volatility_20d": spy_realized_vol_20,
        "spy_drawdown_from_52w_high": spy_drawdown,
        "regime_bucket": _classify_regime(
            spy_above_ema200=spy_above_ema200,
            spy_ema200_slope_positive=spy_ema200_slope_positive,
            spy_return_60=spy_return_60,
        ),
    }


def _classify_regime(
    spy_above_ema200: bool,
    spy_ema200_slope_positive: bool,
    spy_return_60: float,
) -> str:
    if spy_above_ema200 and spy_ema200_slope_positive and spy_return_60 > 0:
        return "BULL"
    if not spy_above_ema200 and not spy_ema200_slope_positive and spy_return_60 < 0:
        return "BEAR"
    return "NEUTRAL"


def _build_regime_summary(sensitivity: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for regime_bucket in ["BULL", "NEUTRAL", "BEAR"]:
        trades = sensitivity[sensitivity["regime_bucket"] == regime_bucket]
        rows.append({"regime_bucket": regime_bucket, **_summarize_trades(trades)})
    return pd.DataFrame(rows)


def _summarize_trades(trades: pd.DataFrame) -> dict[str, float | int]:
    if trades.empty:
        return {
            "trade_count": 0,
            "avg_R": 0.0,
            "expectancy": 0.0,
            "profit_factor": 0.0,
            "winrate": 0.0,
        }

    r_values = pd.to_numeric(trades["trade_R"], errors="coerce").dropna()
    wins = r_values[r_values > 0]
    losses = r_values[r_values < 0]
    win_rate_dec = float((r_values > 0).mean())
    loss_rate_dec = float((r_values < 0).mean())
    avg_win = float(wins.mean()) if not wins.empty else 0.0
    avg_loss_abs = float(abs(losses.mean())) if not losses.empty else 0.0
    gross_profit = float(wins.sum()) if not wins.empty else 0.0
    gross_loss = float(abs(losses.sum())) if not losses.empty else 0.0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else (math.inf if gross_profit > 0 else 0.0)
    return {
        "trade_count": int(len(r_values)),
        "avg_R": float(r_values.mean()) if not r_values.empty else 0.0,
        "expectancy": (win_rate_dec * avg_win) - (loss_rate_dec * avg_loss_abs),
        "profit_factor": profit_factor,
        "winrate": win_rate_dec * 100.0,
    }


def _build_feature_correlations(sensitivity: pd.DataFrame) -> pd.DataFrame:
    feature_columns = [
        "spy_above_ema200",
        "spy_ema200_slope_positive",
        "spy_distance_from_ema200",
        "spy_60d_return",
        "spy_realized_volatility_20d",
        "spy_drawdown_from_52w_high",
    ]
    rows = []
    for feature_name in feature_columns:
        values = sensitivity[feature_name].astype(float)
        rows.append(
            {
                "feature_name": feature_name,
                "correlation_with_trade_R": float(values.corr(sensitivity["trade_R"].astype(float))),
            }
        )
    return pd.DataFrame(rows)


if __name__ == "__main__":
    main()
