from __future__ import annotations

from pathlib import Path
import csv
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
START = "2018-01-01"
END = "2024-01-01"
TIMEFRAME = "1d"
BENCHMARK = "SPY"
UNIVERSE = [
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
    benchmark_data = _fetch_with_retry(data_source=data_source, ticker=BENCHMARK)
    rows = []

    for ticker in UNIVERSE:
        print(f"Running {ticker}...")
        try:
            market_data = benchmark_data if ticker == BENCHMARK else _fetch_with_retry(
                data_source=data_source,
                ticker=ticker,
            )
            run_dir = OUTPUT_DIR / f"universe_expansion_validation_{ticker}"
            run_dir.mkdir(exist_ok=True)
            config = BacktestConfig(
                ticker=ticker,
                start_date=START,
                end_date=END,
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
            engine.run(
                dataframe=market_data,
                strategy_class=LeadershipExpansionV1Strategy,
                strategy_params=build_strategy_params(config),
                extra_dataframes=[benchmark_data],
                plot_results=False,
                base_timeframe=TIMEFRAME,
                resample_rules=[],
            )
            row = {"ticker": ticker, **_summarize_trades(run_dir / "trades.csv")}
        except Exception as exc:
            row = {
                "ticker": ticker,
                "trade_count": 0,
                "avg_R": 0.0,
                "expectancy": 0.0,
                "profit_factor": 0.0,
                "net_pnl": 0.0,
                "winrate": 0.0,
                "error": str(exc),
            }
        rows.append(row)
        print(row)

    validation = pd.DataFrame(rows)
    validation_path = OUTPUT_DIR / "universe_expansion_validation.csv"
    validation.to_csv(validation_path, index=False)

    aggregate = _aggregate_validation(validation)
    aggregate_path = OUTPUT_DIR / "aggregate_validation.csv"
    aggregate.to_csv(aggregate_path, index=False)

    distribution = _distribution_analysis(validation)
    distribution_path = OUTPUT_DIR / "distribution_analysis.csv"
    distribution.to_csv(distribution_path, index=False)

    print(validation_path)
    print(aggregate_path)
    print(distribution_path)


def _fetch_with_retry(data_source: YahooFinanceDataSource, ticker: str) -> pd.DataFrame:
    last_error: Exception | None = None
    for _ in range(3):
        try:
            return data_source.fetch(MarketDataRequest(ticker=ticker, start=START, end=END, timeframe=TIMEFRAME))
        except Exception as exc:
            last_error = exc
            time.sleep(1)
    raise RuntimeError(f"Could not fetch data for {ticker}: {last_error}") from last_error


def _summarize_trades(trades_path: Path) -> dict[str, float | int]:
    trades = pd.read_csv(trades_path) if trades_path.exists() else pd.DataFrame()
    if trades.empty:
        return {
            "trade_count": 0,
            "avg_R": 0.0,
            "expectancy": 0.0,
            "profit_factor": 0.0,
            "net_pnl": 0.0,
            "winrate": 0.0,
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
    }


def _aggregate_validation(validation: pd.DataFrame) -> pd.DataFrame:
    all_trades = _load_all_trades(validation["ticker"].tolist())
    summary = _summarize_dataframe(all_trades)
    return pd.DataFrame(
        [
            {
                "overall_trade_count": summary["trade_count"],
                "overall_avg_R": summary["avg_R"],
                "overall_expectancy": summary["expectancy"],
                "overall_profit_factor": summary["profit_factor"],
                "overall_net_pnl": summary["net_pnl"],
            }
        ]
    )


def _load_all_trades(tickers: list[str]) -> pd.DataFrame:
    frames = []
    for ticker in tickers:
        path = OUTPUT_DIR / f"universe_expansion_validation_{ticker}" / "trades.csv"
        if not path.exists():
            continue
        trades = pd.read_csv(path)
        if trades.empty:
            continue
        trades["ticker"] = ticker
        frames.append(trades)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def _summarize_dataframe(trades: pd.DataFrame) -> dict[str, float | int]:
    if trades.empty:
        return {
            "trade_count": 0,
            "avg_R": 0.0,
            "expectancy": 0.0,
            "profit_factor": 0.0,
            "net_pnl": 0.0,
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
    }


def _distribution_analysis(validation: pd.DataFrame) -> pd.DataFrame:
    avg_r = pd.to_numeric(validation["avg_R"], errors="coerce").fillna(0.0)
    sorted_validation = validation.sort_values("avg_R", ascending=False)
    return pd.DataFrame(
        [
            {
                "count_positive_avgR": int((avg_r > 0).sum()),
                "count_negative_avgR": int((avg_r < 0).sum()),
                "median_avgR": float(avg_r.median()),
                "mean_avgR": float(avg_r.mean()),
                "top_10": ", ".join(sorted_validation.head(10)["ticker"].tolist()),
                "bottom_10": ", ".join(sorted_validation.tail(10)["ticker"].tolist()),
            }
        ]
    )


if __name__ == "__main__":
    main()
