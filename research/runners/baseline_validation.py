from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

import pandas as pd
from pandas.testing import assert_frame_equal

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from config.settings import BacktestConfig, load_config
from data.yahoo_data import MarketDataRequest, YahooFinanceDataSource
from engine.backtest_engine import BacktestEngine
from main import STRATEGY_REGISTRY, build_strategy_params
from research.component_registry import valid_toggle_names


CORE_TRADE_COLUMNS = [
    "entry_time", "exit_time", "direction", "entry_price", "exit_price", "stop_loss",
    "take_profit", "position_size", "pnl_dollars", "pnl_percent", "R_multiple",
    "trade_duration_bars", "exit_reason",
]


def main() -> None:
    args = _args()
    config = load_config(args.config)
    config.strategy_name = "leadership_expansion_v1"
    config.ticker = args.ticker
    config.start_date = args.start
    config.end_date = args.end
    config.plot = False
    output = args.output_dir
    source = YahooFinanceDataSource()
    stock = source.fetch(MarketDataRequest(args.ticker, args.start, args.end, config.timeframe))
    benchmark = source.fetch(MarketDataRequest(config.benchmark_ticker, args.start, args.end, config.timeframe))
    strategy = STRATEGY_REGISTRY[config.strategy_name]
    research_params = build_strategy_params(config)
    production_params = {key: value for key, value in research_params.items() if key not in valid_toggle_names()}
    production = _run(stock, benchmark, strategy, production_params, config, output / "production")
    framework = _run(stock, benchmark, strategy, research_params, config, output / "framework_defaults")
    production_trades = pd.read_csv(output / "production" / "trades.csv")[CORE_TRADE_COLUMNS]
    framework_trades = pd.read_csv(output / "framework_defaults" / "trades.csv")[CORE_TRADE_COLUMNS]
    identical = True
    error = ""
    try:
        assert_frame_equal(production_trades, framework_trades, check_dtype=False, rtol=1e-12, atol=1e-12)
        if asdict(production.metrics) != asdict(framework.metrics) or production.final_portfolio_value != framework.final_portfolio_value:
            raise AssertionError("Portfolio metrics differ")
    except AssertionError as exc:
        identical = False
        error = str(exc)
    report = [
        "# Baseline Validation Report", "",
        f"Ticker: `{args.ticker}`", f"Range: {args.start} -> {args.end}",
        f"Trade records identical: {identical}",
        f"Production trades: {len(production_trades)}", f"Framework-default trades: {len(framework_trades)}",
        f"Production final value: {production.final_portfolio_value}", f"Framework final value: {framework.final_portfolio_value}",
        "", "The framework passes only when trade records and portfolio metrics are identical.",
    ]
    if error:
        report.extend(["", "## Difference", "", error])
    output.mkdir(parents=True, exist_ok=True)
    (output / "baseline_validation_report.md").write_text("\n".join(report), encoding="utf-8")
    if not identical:
        raise SystemExit("Baseline validation failed")
    print(output / "baseline_validation_report.md")


def _run(stock, benchmark, strategy, params, config, output):
    return BacktestEngine(config.initial_capital, config.commission, config.slippage, output).run(
        dataframe=stock, strategy_class=strategy, strategy_params=params,
        extra_dataframes=[benchmark], plot_results=False, base_timeframe=config.timeframe,
    )


def _args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", default="AAPL")
    parser.add_argument("--start", default="2020-01-01")
    parser.add_argument("--end", default="2025-01-01")
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=Path("research/baseline_validation"))
    return parser.parse_args()


if __name__ == "__main__":
    main()
