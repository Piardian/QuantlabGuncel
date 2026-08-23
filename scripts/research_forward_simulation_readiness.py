from __future__ import annotations

from dataclasses import dataclass
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
INITIAL_CAPITAL = 10_000.0
RISK_PER_TRADE = 0.01
MAX_POSITIONS = 3
EMA_TREND_PERIOD = 200
EMA_QUALITY_PERIOD = 50
ATR_PERIOD = 14
RS_LOOKBACK = 60
RS_THRESHOLD = 0.05
EXPANSION_ATR_MULTIPLE = 1.5
BREAKOUT_LOOKBACK = 20
INITIAL_STOP_ATR_MULTIPLE = 1.5
TRAILING_STOP_ATR_MULTIPLE = 2.0
MAX_HOLDING_BARS = 60


@dataclass(slots=True)
class Position:
    trade_id: int
    ticker: str
    entry_date: pd.Timestamp
    entry_price: float
    stop_price: float
    current_stop: float
    position_size: int
    entry_bar_index: int


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    data_source = YahooFinanceDataSource()
    universe = _load_validated_universe()
    benchmark_data = _add_indicators(_fetch_with_retry(data_source=data_source, ticker=BENCHMARK))
    market_data = {
        ticker: benchmark_data if ticker == BENCHMARK else _add_indicators(_fetch_with_retry(data_source=data_source, ticker=ticker))
        for ticker in universe
    }

    all_dates = _combined_dates(market_data)
    cash = INITIAL_CAPITAL
    realized_pnl = 0.0
    active_positions: list[Position] = []
    next_trade_id = 1
    signal_rows: list[dict[str, object]] = []
    timeline_rows: list[dict[str, object]] = []
    conflict_rows: list[dict[str, object]] = []

    for current_date in all_dates:
        cash, realized_pnl = _process_exits(
            current_date=current_date,
            market_data=market_data,
            active_positions=active_positions,
            cash=cash,
            realized_pnl=realized_pnl,
        )

        equity = cash + _market_value(active_positions=active_positions, market_data=market_data, current_date=current_date)
        raw_signals = _signals_for_date(
            current_date=current_date,
            universe=universe,
            market_data=market_data,
            benchmark_data=benchmark_data,
        )
        raw_signals.sort(key=lambda signal: signal["ticker"])

        executed_count = 0
        missed_count = 0
        available_slots_at_start = max(MAX_POSITIONS - len(active_positions), 0)
        for signal in raw_signals:
            entry_date = signal["entry_date"]
            entry_price = signal["entry_price"]
            atr_at_entry = signal["atr_at_entry"]
            stop_price = entry_price - (atr_at_entry * INITIAL_STOP_ATR_MULTIPLE)
            risk_per_share = max(entry_price - stop_price, 0.0)
            risk_dollars = equity * RISK_PER_TRADE
            raw_size = int(risk_dollars / risk_per_share) if risk_per_share > 0 else 0
            affordable_size = int(cash / max(entry_price, 0.01))
            position_size = max(min(raw_size, affordable_size), 0)
            cash_required = position_size * entry_price

            missed_reason = ""
            executed = False
            if len(active_positions) >= MAX_POSITIONS:
                missed_reason = "POSITION_LIMIT"
            elif position_size <= 0:
                missed_reason = "INSUFFICIENT_CASH_OR_RISK"
            else:
                executed = True
                executed_count += 1
                cash -= cash_required
                active_positions.append(
                    Position(
                        trade_id=next_trade_id,
                        ticker=signal["ticker"],
                        entry_date=entry_date,
                        entry_price=entry_price,
                        stop_price=stop_price,
                        current_stop=stop_price,
                        position_size=position_size,
                        entry_bar_index=signal["entry_bar_index"],
                    )
                )
                next_trade_id += 1

            if not executed:
                missed_count += 1

            signal_rows.append(
                {
                    "signal_date": current_date,
                    "entry_date": entry_date,
                    "ticker": signal["ticker"],
                    "entry_price": entry_price,
                    "stop_price": stop_price,
                    "position_size": position_size,
                    "risk_dollars": risk_dollars,
                    "cash_required": cash_required,
                    "executed": executed,
                    "missed_reason": missed_reason,
                    "active_positions_before_signal": len(active_positions) - (1 if executed else 0),
                }
            )

        cash_usage = _market_value(active_positions=active_positions, market_data=market_data, current_date=current_date)
        timeline_rows.append(
            {
                "date": current_date,
                "active_positions_per_day": len(active_positions),
                "cash_usage_per_day": cash_usage,
                "cash_usage_pct": cash_usage / max(equity, 0.01),
                "signals_generated": len(raw_signals),
                "signals_executed": executed_count,
                "signal_conflicts": max(len(raw_signals) - available_slots_at_start, 0),
                "missed_signals_due_to_position_limit": sum(
                    1
                    for row in signal_rows[-len(raw_signals) :]
                    if row["missed_reason"] == "POSITION_LIMIT"
                )
                if raw_signals
                else 0,
            }
        )

        if raw_signals and missed_count:
            conflict_rows.append(
                {
                    "date": current_date,
                    "signals_generated": len(raw_signals),
                    "signals_executed": executed_count,
                    "missed_signals": missed_count,
                    "missed_due_to_position_limit": sum(
                        1
                        for row in signal_rows[-len(raw_signals) :]
                        if row["missed_reason"] == "POSITION_LIMIT"
                    ),
                    "active_positions_end_of_day": len(active_positions),
                    "tickers": ", ".join(signal["ticker"] for signal in raw_signals),
                }
            )

    signal_report = pd.DataFrame(signal_rows)
    timeline = pd.DataFrame(timeline_rows)
    average_cash_usage = float(timeline["cash_usage_per_day"].mean()) if not timeline.empty else 0.0
    max_cash_usage = float(timeline["cash_usage_per_day"].max()) if not timeline.empty else 0.0
    timeline["average_cash_usage"] = average_cash_usage
    timeline["max_cash_usage"] = max_cash_usage

    signal_report.to_csv(OUTPUT_DIR / "forward_simulation_readiness.csv", index=False)
    timeline.to_csv(OUTPUT_DIR / "portfolio_capacity_report.csv", index=False)
    pd.DataFrame(conflict_rows).to_csv(OUTPUT_DIR / "signal_conflict_analysis.csv", index=False)

    print(OUTPUT_DIR / "forward_simulation_readiness.csv")
    print(OUTPUT_DIR / "portfolio_capacity_report.csv")
    print(OUTPUT_DIR / "signal_conflict_analysis.csv")


def _load_validated_universe() -> list[str]:
    universe_path = OUTPUT_DIR / "walk_forward_universe.csv"
    if not universe_path.exists():
        raise RuntimeError("Missing walk_forward_universe.csv. Run walk-forward validation first.")
    return pd.read_csv(universe_path)["ticker"].dropna().astype(str).tolist()


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
    data["EMA200"] = data["Close"].ewm(span=EMA_TREND_PERIOD, adjust=False).mean()
    data["EMA50"] = data["Close"].ewm(span=EMA_QUALITY_PERIOD, adjust=False).mean()
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


def _combined_dates(market_data: dict[str, pd.DataFrame]) -> list[pd.Timestamp]:
    dates = sorted({date for dataframe in market_data.values() for date in dataframe.index})
    return [date for date in dates if pd.Timestamp(START) <= date < pd.Timestamp(END)]


def _process_exits(
    current_date: pd.Timestamp,
    market_data: dict[str, pd.DataFrame],
    active_positions: list[Position],
    cash: float,
    realized_pnl: float,
) -> tuple[float, float]:
    remaining_positions = []
    for position in active_positions:
        data = market_data[position.ticker]
        current_position = _position_for_date(dataframe=data, date=current_date)
        if current_position is None:
            remaining_positions.append(position)
            continue

        row = data.iloc[current_position]
        current_close = float(row["Close"])
        current_low = float(row["Low"])
        atr14 = float(row["ATR14"])
        ema50 = float(row["EMA50"])
        if atr14 > 0:
            trailing_stop = current_close - (atr14 * TRAILING_STOP_ATR_MULTIPLE)
            if trailing_stop > position.current_stop:
                position.current_stop = trailing_stop

        should_exit = False
        exit_price = current_close
        if current_low <= position.current_stop:
            should_exit = True
            exit_price = position.current_stop
        elif current_close < ema50:
            should_exit = True
            exit_price = current_close
        elif current_position - position.entry_bar_index >= MAX_HOLDING_BARS:
            should_exit = True
            exit_price = current_close

        if should_exit:
            proceeds = position.position_size * exit_price
            pnl = (exit_price - position.entry_price) * position.position_size
            cash += proceeds
            realized_pnl += pnl
        else:
            remaining_positions.append(position)

    active_positions[:] = remaining_positions
    return cash, realized_pnl


def _signals_for_date(
    current_date: pd.Timestamp,
    universe: list[str],
    market_data: dict[str, pd.DataFrame],
    benchmark_data: pd.DataFrame,
) -> list[dict[str, object]]:
    signals = []
    for ticker in universe:
        data = market_data[ticker]
        position = _position_for_date(dataframe=data, date=current_date)
        if position is None or position + 1 >= len(data):
            continue
        if not _should_enter_long(data=data, benchmark_data=benchmark_data, position=position):
            continue
        entry_bar = data.iloc[position + 1]
        signals.append(
            {
                "ticker": ticker,
                "entry_date": data.index[position + 1],
                "entry_price": float(entry_bar["Open"]),
                "atr_at_entry": float(entry_bar["ATR14"]),
                "entry_bar_index": position + 1,
            }
        )
    return signals


def _should_enter_long(data: pd.DataFrame, benchmark_data: pd.DataFrame, position: int) -> bool:
    required = max(EMA_TREND_PERIOD + 1, EMA_QUALITY_PERIOD, ATR_PERIOD + 1, RS_LOOKBACK + 1, 121, BREAKOUT_LOOKBACK + 1)
    if position < required:
        return False

    row = data.iloc[position]
    previous_row = data.iloc[position - 1]
    close = float(row["Close"])
    ema200 = float(row["EMA200"])
    ema200_prev = float(previous_row["EMA200"])
    ema50 = float(row["EMA50"])
    atr14 = float(row["ATR14"])
    true_range = float(row["TrueRange"])
    if atr14 <= 0 or close <= ema200 or ema200 <= ema200_prev or close <= ema50:
        return False

    benchmark_position = _position_for_date(benchmark_data, data.index[position])
    if benchmark_position is None or benchmark_position < 120:
        return False

    stock_return_60 = _return_at_position(data, position, 60)
    benchmark_return_60 = _return_at_position(benchmark_data, benchmark_position, 60)
    rs60 = stock_return_60 - benchmark_return_60
    if stock_return_60 <= benchmark_return_60 or rs60 <= RS_THRESHOLD:
        return False

    rs20 = _return_at_position(data, position, 20) - _return_at_position(benchmark_data, benchmark_position, 20)
    rs120 = _return_at_position(data, position, 120) - _return_at_position(benchmark_data, benchmark_position, 120)
    if not (rs20 > 0.0 or rs120 > 0.10):
        return False

    if true_range <= EXPANSION_ATR_MULTIPLE * atr14:
        return False

    highest_close = data.iloc[position - BREAKOUT_LOOKBACK : position]["Close"].max()
    return close > float(highest_close)


def _position_for_date(dataframe: pd.DataFrame, date: pd.Timestamp) -> int | None:
    normalized_date = date.normalize()
    matches = [index for index, item in enumerate(dataframe.index.normalize()) if item == normalized_date]
    if not matches:
        return None
    return matches[0]


def _return_at_position(dataframe: pd.DataFrame, position: int, lookback: int) -> float:
    return (float(dataframe.iloc[position]["Close"]) / float(dataframe.iloc[position - lookback]["Close"])) - 1.0


def _market_value(active_positions: list[Position], market_data: dict[str, pd.DataFrame], current_date: pd.Timestamp) -> float:
    value = 0.0
    for position in active_positions:
        data = market_data[position.ticker]
        current_position = _position_for_date(dataframe=data, date=current_date)
        if current_position is None:
            value += position.position_size * position.entry_price
        else:
            value += position.position_size * float(data.iloc[current_position]["Close"])
    return value


if __name__ == "__main__":
    main()
