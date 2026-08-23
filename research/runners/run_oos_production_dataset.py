"""Generate a strictly post-RC-C1 production-trade dataset with indicator-only warmup."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from config.settings import load_config
from data.yahoo_data import MarketDataRequest, YahooFinanceDataSource
from engine.backtest_engine import BacktestEngine
from main import build_strategy_params
from research.audit_strategies import LeadershipExpansionOOSWarmupStrategy


def main() -> None:
    args = _args()
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    config = load_config(args.config)
    config.strategy_name, config.timeframe, config.plot = "leadership_expansion_v1", "1d", False
    params = build_strategy_params(config)
    params["entry_start_date"] = args.oos_start
    universe = pd.read_csv(args.universe).iloc[:, 0].dropna().astype(str).str.upper().tolist()
    source = YahooFinanceDataSource()
    benchmark = source.fetch(MarketDataRequest(config.benchmark_ticker, args.warmup_start, args.end, "1d"))
    completed, errors, frames = [], [], []
    for index, ticker in enumerate(universe, start=1):
        try:
            stock = source.fetch(MarketDataRequest(ticker, args.warmup_start, args.end, "1d"))
            ticker_params = dict(params)
            ticker_params["skip_relative_strength_filter"] = ticker == config.benchmark_ticker
            result_dir = output / "runs" / ticker
            BacktestEngine(config.initial_capital, config.commission, config.slippage, result_dir).run(
                dataframe=stock, strategy_class=LeadershipExpansionOOSWarmupStrategy, strategy_params=ticker_params,
                extra_dataframes=[benchmark], plot_results=False, base_timeframe="1d",
            )
            trades = pd.read_csv(result_dir / "trades.csv")
            if not trades.empty:
                trades["entry_time"] = pd.to_datetime(trades["entry_time"])
                trades = trades.loc[trades.entry_time >= pd.Timestamp(args.oos_start)].copy()
                trades.insert(0, "ticker", ticker)
                frames.append(trades)
            completed.append(ticker)
        except Exception as exc:
            errors.append({"ticker": ticker, "error": repr(exc)})
        print(f"{index}/{len(universe)} {ticker}")
    merged = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    merged.to_csv(output / "merged_oos_trades.csv", index=False)
    pd.DataFrame({"ticker": completed}).to_csv(output / "completed_symbols.csv", index=False)
    pd.DataFrame(errors).to_csv(output / "oos_errors.csv", index=False)


def _args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--universe", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--warmup-start", default="2025-01-01")
    parser.add_argument("--oos-start", default="2026-01-01")
    parser.add_argument("--end", default="2026-07-25")
    parser.add_argument("--config", type=Path, default=None)
    return parser.parse_args()


if __name__ == "__main__":
    main()
