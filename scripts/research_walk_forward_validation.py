from __future__ import annotations

from pathlib import Path
import math
import sys
import time

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config.settings import BacktestConfig
from data.yahoo_data import MarketDataRequest, YahooFinanceDataSource
from engine.backtest_engine import BacktestEngine
from main import build_strategy_params
from strategies.leadership_expansion_v1 import LeadershipExpansionV1Strategy


OUTPUT_DIR = ROOT / "output"
TIMEFRAME = "1d"
BENCHMARK = "SPY"
DATA_START = "2018-01-01"
DATA_END = "2025-01-01"
FULL_HISTORY_CUTOFF = pd.Timestamp("2018-02-01")
WINDOWS = [
    ("W1_2021", "2018-01-01", "2021-01-01", "2022-01-01"),
    ("W2_2022", "2018-01-01", "2022-01-01", "2023-01-01"),
    ("W3_2023", "2018-01-01", "2023-01-01", "2024-01-01"),
    ("W4_2024", "2018-01-01", "2024-01-01", "2025-01-01"),
]
FALLBACK_UNIVERSE = [
    "AAPL",
    "NVDA",
    "META",
    "TSLA",
    "AMD",
    "NFLX",
    "PLTR",
    "CRWD",
    "PANW",
    "SMCI",
    "ARM",
    "AVGO",
    "DDOG",
    "NET",
    "MDB",
    "SHOP",
    "SNOW",
    "ZS",
    "TTD",
    "CELH",
    "COIN",
    "ROKU",
    "UPST",
    "MSTR",
    "APP",
    "HIMS",
    "RKLB",
    "DUOL",
    "CAVA",
    "IOT",
]


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    data_source = YahooFinanceDataSource()
    candidate_universe = _load_candidate_universe()
    benchmark_data = _fetch_with_retry(data_source=data_source, ticker=BENCHMARK)
    market_cache = {BENCHMARK: benchmark_data}

    validated_universe = []
    for ticker in candidate_universe:
        try:
            market_data = benchmark_data if ticker == BENCHMARK else _fetch_with_retry(data_source=data_source, ticker=ticker)
        except Exception:
            continue
        if market_data.index.min() <= FULL_HISTORY_CUTOFF:
            market_cache[ticker] = market_data
            validated_universe.append(ticker)

    rows = []
    for window_name, train_start, test_start, test_end in WINDOWS:
        print(f"Running {window_name}...")
        window_trades = []
        for ticker in validated_universe:
            run_dir = OUTPUT_DIR / f"walk_forward_{window_name}_{ticker}"
            run_dir.mkdir(exist_ok=True)
            market_data = market_cache[ticker].loc[
                (market_cache[ticker].index >= pd.Timestamp(train_start))
                & (market_cache[ticker].index < pd.Timestamp(test_end))
            ]
            benchmark_slice = benchmark_data.loc[
                (benchmark_data.index >= pd.Timestamp(train_start))
                & (benchmark_data.index < pd.Timestamp(test_end))
            ]
            if market_data.empty or benchmark_slice.empty:
                continue

            config = BacktestConfig(
                ticker=ticker,
                start_date=train_start,
                end_date=test_end,
                timeframe=TIMEFRAME,
                strategy_name="leadership_expansion_v1",
                output_dir=str(run_dir),
                plot=False,
            )
            config.skip_relative_strength_filter = ticker.upper() == BENCHMARK
            engine = BacktestEngine(
                initial_capital=config.initial_capital,
                commission=config.commission,
                slippage_perc=config.slippage,
                output_dir=run_dir,
            )
            try:
                engine.run(
                    dataframe=market_data,
                    strategy_class=LeadershipExpansionV1Strategy,
                    strategy_params=build_strategy_params(config),
                    extra_dataframes=[benchmark_slice],
                    plot_results=False,
                    base_timeframe=TIMEFRAME,
                    resample_rules=[],
                )
            except Exception as exc:
                print(f"Skipped {ticker} {window_name}: {exc}")
                continue

            trades_path = run_dir / "trades.csv"
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
            test_trades["ticker"] = ticker
            window_trades.append(test_trades)

        trades_dataframe = pd.concat(window_trades, ignore_index=True) if window_trades else pd.DataFrame()
        rows.append({"window": window_name, **_summarize_trades(trades_dataframe)})

    validation = pd.DataFrame(rows)
    validation_path = OUTPUT_DIR / "walk_forward_validation.csv"
    validation.to_csv(validation_path, index=False)

    summary = _build_summary(validation)
    summary_path = OUTPUT_DIR / "walk_forward_summary.csv"
    summary.to_csv(summary_path, index=False)

    universe_path = OUTPUT_DIR / "walk_forward_universe.csv"
    pd.DataFrame({"ticker": validated_universe}).to_csv(universe_path, index=False)

    print(validation_path)
    print(summary_path)
    print(universe_path)


def _load_candidate_universe() -> list[str]:
    validation_path = OUTPUT_DIR / "universe_expansion_validation.csv"
    if not validation_path.exists():
        return FALLBACK_UNIVERSE

    validation = pd.read_csv(validation_path)
    if "error" in validation.columns:
        validation = validation[validation["error"].isna()]
    validation = validation[validation["trade_count"] > 0]
    return validation["ticker"].tolist()


def _fetch_with_retry(data_source: YahooFinanceDataSource, ticker: str) -> pd.DataFrame:
    last_error: Exception | None = None
    for _ in range(3):
        try:
            return data_source.fetch(MarketDataRequest(ticker=ticker, start=DATA_START, end=DATA_END, timeframe=TIMEFRAME))
        except Exception as exc:
            last_error = exc
            time.sleep(1)
    raise RuntimeError(f"Could not fetch data for {ticker}: {last_error}") from last_error


def _summarize_trades(trades: pd.DataFrame) -> dict[str, float | int]:
    if trades.empty:
        return {
            "trade_count": 0,
            "avg_R": 0.0,
            "expectancy": 0.0,
            "profit_factor": 0.0,
            "net_pnl": 0.0,
            "winrate": 0.0,
            "max_drawdown": 0.0,
        }

    pnl = pd.to_numeric(trades["pnl_dollars"], errors="coerce").fillna(0.0)
    r_values = pd.to_numeric(trades["R_multiple"], errors="coerce").dropna()
    wins = pnl[pnl > 0]
    losses = pnl[pnl < 0]
    win_rate_dec = float((pnl > 0).mean())
    loss_rate_dec = float((pnl < 0).mean())
    avg_win = float(wins.mean()) if not wins.empty else 0.0
    avg_loss_abs = float(abs(losses.mean())) if not losses.empty else 0.0
    gross_profit = float(wins.sum()) if not wins.empty else 0.0
    gross_loss = float(abs(losses.sum())) if not losses.empty else 0.0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else (math.inf if gross_profit > 0 else 0.0)

    return {
        "trade_count": int(len(trades)),
        "avg_R": float(r_values.mean()) if not r_values.empty else 0.0,
        "expectancy": (win_rate_dec * avg_win) - (loss_rate_dec * avg_loss_abs),
        "profit_factor": profit_factor,
        "net_pnl": float(pnl.sum()),
        "winrate": win_rate_dec * 100.0,
        "max_drawdown": _trade_level_max_drawdown(pnl),
    }


def _trade_level_max_drawdown(pnl: pd.Series) -> float:
    cumulative = pnl.cumsum()
    running_peak = cumulative.cummax()
    drawdown = cumulative - running_peak
    return float(drawdown.min()) if not drawdown.empty else 0.0


def _build_summary(validation: pd.DataFrame) -> pd.DataFrame:
    if validation.empty:
        return pd.DataFrame(
            [
                {
                    "average_avg_R": 0.0,
                    "median_avg_R": 0.0,
                    "average_profit_factor": 0.0,
                    "worst_window": "",
                    "best_window": "",
                    "positive_windows": 0,
                    "negative_windows": 0,
                }
            ]
        )

    avg_r = pd.to_numeric(validation["avg_R"], errors="coerce").fillna(0.0)
    profit_factor = pd.to_numeric(validation["profit_factor"], errors="coerce").replace([math.inf, -math.inf], pd.NA).dropna()
    worst_index = avg_r.idxmin()
    best_index = avg_r.idxmax()
    return pd.DataFrame(
        [
            {
                "average_avg_R": float(avg_r.mean()),
                "median_avg_R": float(avg_r.median()),
                "average_profit_factor": float(profit_factor.mean()) if not profit_factor.empty else 0.0,
                "worst_window": validation.loc[worst_index, "window"],
                "best_window": validation.loc[best_index, "window"],
                "positive_windows": int((avg_r > 0).sum()),
                "negative_windows": int((avg_r < 0).sum()),
            }
        ]
    )


if __name__ == "__main__":
    main()
