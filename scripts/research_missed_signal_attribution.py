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
FORWARD_SIGNALS_PATH = OUTPUT_DIR / "forward_simulation_readiness.csv"
BENCHMARK = "SPY"
START = "2018-01-01"
END = "2025-01-01"
TIMEFRAME = "1d"
ATR_PERIOD = 14
EMA50_PERIOD = 50
EMA200_PERIOD = 200
TRAILING_STOP_ATR_MULTIPLE = 2.0
MAX_HOLDING_BARS = 60


def main() -> None:
    if not FORWARD_SIGNALS_PATH.exists():
        raise RuntimeError("Missing forward_simulation_readiness.csv. Run forward simulation readiness first.")

    signals = pd.read_csv(FORWARD_SIGNALS_PATH, parse_dates=["signal_date", "entry_date"])
    data_source = YahooFinanceDataSource()
    benchmark_data = _add_indicators(_fetch_with_retry(data_source=data_source, ticker=BENCHMARK))
    tickers = sorted(signals["ticker"].dropna().astype(str).unique().tolist())
    market_cache = {
        ticker: benchmark_data if ticker == BENCHMARK else _add_indicators(_fetch_with_retry(data_source=data_source, ticker=ticker))
        for ticker in tickers
    }

    conflict_dates = set(signals.groupby("signal_date").size()[lambda item: item > 1].index)
    rows = []
    for signal_id, signal in signals.reset_index(drop=True).iterrows():
        row = _analyze_signal(
            signal_id=signal_id + 1,
            signal=signal,
            market_data=market_cache[str(signal["ticker"])],
            benchmark_data=benchmark_data,
            is_conflict_day=signal["signal_date"] in conflict_dates,
        )
        if row is not None:
            rows.append(row)

    analysis = pd.DataFrame(rows)
    analysis_path = OUTPUT_DIR / "missed_signal_analysis.csv"
    analysis.to_csv(analysis_path, index=False)

    summary = _build_executed_vs_missed_summary(analysis)
    summary_path = OUTPUT_DIR / "executed_vs_missed_summary.csv"
    summary.to_csv(summary_path, index=False)

    capture = _build_top_winner_capture_rate(analysis)
    capture_path = OUTPUT_DIR / "top_winner_capture_rate.csv"
    capture.to_csv(capture_path, index=False)

    conflict_summary = _build_conflict_feature_summary(analysis)
    conflict_summary_path = OUTPUT_DIR / "signal_conflict_feature_summary.csv"
    conflict_summary.to_csv(conflict_summary_path, index=False)

    print(analysis_path)
    print(summary_path)
    print(capture_path)
    print(conflict_summary_path)


def _fetch_with_retry(data_source: YahooFinanceDataSource, ticker: str) -> pd.DataFrame:
    last_error: Exception | None = None
    for _ in range(3):
        try:
            return data_source.fetch(MarketDataRequest(ticker=ticker, start=START, end=END, timeframe=TIMEFRAME))
        except Exception as exc:
            last_error = exc
            time.sleep(1)
    raise RuntimeError(f"Could not fetch data for {ticker}: {last_error}") from last_error


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
    data["Return60"] = data["Close"].pct_change(60)
    data["RealizedVol20"] = data["Close"].pct_change().rolling(20).std() * math.sqrt(252)
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


def _analyze_signal(
    signal_id: int,
    signal: pd.Series,
    market_data: pd.DataFrame,
    benchmark_data: pd.DataFrame,
    is_conflict_day: bool,
) -> dict[str, object] | None:
    ticker = str(signal["ticker"])
    signal_position = _position_for_date(market_data, pd.Timestamp(signal["signal_date"]))
    entry_position = _position_for_date(market_data, pd.Timestamp(signal["entry_date"]))
    benchmark_position = _position_for_date(benchmark_data, pd.Timestamp(signal["signal_date"]))
    if signal_position is None or entry_position is None or benchmark_position is None:
        return None
    if signal_position < 60 or benchmark_position < 60:
        return None

    entry_price = float(signal["entry_price"])
    stop_price = float(signal["stop_price"])
    initial_risk = entry_price - stop_price
    if entry_price <= 0 or initial_risk <= 0:
        return None

    outcome = _simulate_signal_outcome(
        market_data=market_data,
        entry_position=entry_position,
        entry_price=entry_price,
        stop_price=stop_price,
    )
    if outcome is None:
        return None

    signal_bar = market_data.iloc[signal_position]
    benchmark_return_60 = _return_at_position(benchmark_data, benchmark_position, 60)
    stock_return_60 = _return_at_position(market_data, signal_position, 60)
    rs60 = stock_return_60 - benchmark_return_60
    close = float(signal_bar["Close"])
    atr14 = float(signal_bar["ATR14"])

    return {
        "signal_id": signal_id,
        "signal_date": signal["signal_date"],
        "entry_date": signal["entry_date"],
        "ticker": ticker,
        "executed": bool(signal["executed"]),
        "missed_reason": signal.get("missed_reason", ""),
        "is_conflict_day": is_conflict_day,
        "entry_price": entry_price,
        "stop_price": stop_price,
        "hypothetical_exit_date": outcome["exit_date"],
        "hypothetical_exit_price": outcome["exit_price"],
        "hypothetical_exit_reason": outcome["exit_reason"],
        "R_multiple": outcome["R_multiple"],
        "trade_outcome": "WIN" if outcome["R_multiple"] > 0 else "LOSS" if outcome["R_multiple"] < 0 else "FLAT",
        "RS60": rs60,
        "ATR_percent": atr14 / close if close > 0 else 0.0,
        "volatility": float(signal_bar["RealizedVol20"]),
        "momentum": stock_return_60,
    }


def _simulate_signal_outcome(
    market_data: pd.DataFrame,
    entry_position: int,
    entry_price: float,
    stop_price: float,
) -> dict[str, object] | None:
    current_stop = stop_price
    initial_risk = entry_price - stop_price
    final_position = min(entry_position + MAX_HOLDING_BARS, len(market_data) - 1)

    for position in range(entry_position, final_position + 1):
        row = market_data.iloc[position]
        current_close = float(row["Close"])
        current_low = float(row["Low"])
        atr14 = float(row["ATR14"])
        ema50 = float(row["EMA50"])
        if atr14 > 0:
            trailing_stop = current_close - (atr14 * TRAILING_STOP_ATR_MULTIPLE)
            if trailing_stop > current_stop:
                current_stop = trailing_stop

        exit_reason = None
        exit_price = current_close
        if current_low <= current_stop:
            exit_reason = "ATR_TRAIL" if current_stop > stop_price + 1e-8 else "STOP"
            exit_price = current_stop
        elif current_close < ema50:
            exit_reason = "EMA_EXIT"
            exit_price = current_close
        elif position - entry_position >= MAX_HOLDING_BARS:
            exit_reason = "TIME_EXIT"
            exit_price = current_close

        if exit_reason is not None:
            return {
                "exit_date": market_data.index[position],
                "exit_price": exit_price,
                "exit_reason": exit_reason,
                "R_multiple": (exit_price - entry_price) / initial_risk,
            }
    return None


def _position_for_date(dataframe: pd.DataFrame, date: pd.Timestamp) -> int | None:
    normalized_date = date.normalize()
    matches = [index for index, item in enumerate(dataframe.index.normalize()) if item == normalized_date]
    if not matches:
        return None
    return matches[0]


def _return_at_position(dataframe: pd.DataFrame, position: int, lookback: int) -> float:
    return (float(dataframe.iloc[position]["Close"]) / float(dataframe.iloc[position - lookback]["Close"])) - 1.0


def _build_executed_vs_missed_summary(analysis: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for label, group in {
        "EXECUTED": analysis[analysis["executed"]],
        "MISSED": analysis[~analysis["executed"]],
    }.items():
        rows.append({"group": label, **_summarize_r(group["R_multiple"])})
    return pd.DataFrame(rows)


def _summarize_r(r_values: pd.Series) -> dict[str, float | int]:
    r = pd.to_numeric(r_values, errors="coerce").dropna()
    if r.empty:
        return {"trade_count": 0, "avg_R": 0.0, "expectancy": 0.0, "profit_factor": 0.0, "winrate": 0.0}
    wins = r[r > 0]
    losses = r[r < 0]
    win_rate_dec = float((r > 0).mean())
    loss_rate_dec = float((r < 0).mean())
    avg_win = float(wins.mean()) if not wins.empty else 0.0
    avg_loss_abs = float(abs(losses.mean())) if not losses.empty else 0.0
    gross_profit = float(wins.sum()) if not wins.empty else 0.0
    gross_loss = float(abs(losses.sum())) if not losses.empty else 0.0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else (math.inf if gross_profit > 0 else 0.0)
    return {
        "trade_count": int(len(r)),
        "avg_R": float(r.mean()),
        "expectancy": (win_rate_dec * avg_win) - (loss_rate_dec * avg_loss_abs),
        "profit_factor": profit_factor,
        "winrate": win_rate_dec * 100.0,
    }


def _build_top_winner_capture_rate(analysis: pd.DataFrame) -> pd.DataFrame:
    sorted_trades = analysis.sort_values("R_multiple", ascending=False)
    rows = []
    for top_n in [10, 20, 50]:
        group = sorted_trades.head(top_n)
        executed_count = int(group["executed"].sum())
        missed_count = int((~group["executed"]).sum())
        rows.append(
            {
                "top_n": top_n,
                "executed_count": executed_count,
                "missed_count": missed_count,
                "capture_rate": executed_count / top_n if top_n else 0.0,
                "avg_R": float(group["R_multiple"].mean()) if not group.empty else 0.0,
            }
        )
    return pd.DataFrame(rows)


def _build_conflict_feature_summary(analysis: pd.DataFrame) -> pd.DataFrame:
    conflict = analysis[analysis["is_conflict_day"]]
    groups = {
        "CONFLICT_WINNERS": conflict[conflict["R_multiple"] > 0],
        "CONFLICT_LOSERS": conflict[conflict["R_multiple"] < 0],
    }
    rows = []
    for group_name, group in groups.items():
        rows.append(
            {
                "group": group_name,
                "trade_count": int(len(group)),
                "avg_R": float(group["R_multiple"].mean()) if not group.empty else 0.0,
                "avg_RS60": float(group["RS60"].mean()) if not group.empty else 0.0,
                "avg_ATR_percent": float(group["ATR_percent"].mean()) if not group.empty else 0.0,
                "avg_volatility": float(group["volatility"].mean()) if not group.empty else 0.0,
                "avg_momentum": float(group["momentum"].mean()) if not group.empty else 0.0,
                "executed_pct": float(group["executed"].mean() * 100.0) if not group.empty else 0.0,
            }
        )
    return pd.DataFrame(rows)


if __name__ == "__main__":
    main()
