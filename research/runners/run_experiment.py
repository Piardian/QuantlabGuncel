from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from config.settings import BacktestConfig, load_config
from data.yahoo_data import MarketDataRequest, YahooFinanceDataSource
from engine.backtest_engine import BacktestEngine
from main import build_strategy_params
from main import STRATEGY_REGISTRY
from research.component_registry import valid_toggle_names
from research.experiment_config import ResearchExperimentConfig


def main() -> None:
    args = _args()
    experiment = ResearchExperimentConfig.from_json(args.experiment)
    unknown = set(experiment.component_overrides).difference(valid_toggle_names())
    if unknown:
        raise ValueError(f"Unknown experiment component toggles: {sorted(unknown)}")
    config = load_config(args.config)
    config.strategy_name = experiment.strategy_version
    params = build_strategy_params(config)
    params.update(experiment.component_overrides)
    output_dir = args.output_root / experiment.experiment_id
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = experiment.to_manifest(
        dataset=args.dataset,
        universe=args.universe,
        time_range=args.time_range,
        python_version=platform.python_version(),
        strategy_parameters=params,
    )
    (output_dir / "experiment_manifest.json").write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    (output_dir / "resolved_strategy_params.json").write_text(json.dumps(params, indent=2, default=str), encoding="utf-8")
    if args.execute:
        _execute_experiment(args, config, params, output_dir)
    print(output_dir.resolve())


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a reproducible research experiment manifest.")
    parser.add_argument("--experiment", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--output-root", type=Path, default=Path("research/experiments"))
    parser.add_argument("--dataset", default="unspecified")
    parser.add_argument("--universe", default="unspecified")
    parser.add_argument("--time-range", default="unspecified")
    parser.add_argument("--execute", action="store_true", help="Run the configured experiment for one ticker.")
    parser.add_argument("--ticker", default="AAPL")
    parser.add_argument("--start", default="2020-01-01")
    parser.add_argument("--end", default="2025-01-01")
    return parser.parse_args()


def _execute_experiment(args: argparse.Namespace, config: BacktestConfig, params: dict, output_dir: Path) -> None:
    """Explicit execution path; omitted unless --execute is supplied."""
    source = YahooFinanceDataSource()
    stock = source.fetch(MarketDataRequest(args.ticker, args.start, args.end, config.timeframe))
    benchmark = source.fetch(MarketDataRequest(config.benchmark_ticker, args.start, args.end, config.timeframe))
    BacktestEngine(config.initial_capital, config.commission, config.slippage, output_dir / "backtest").run(
        dataframe=stock,
        strategy_class=STRATEGY_REGISTRY[config.strategy_name],
        strategy_params=params,
        extra_dataframes=[benchmark],
        plot_results=False,
        base_timeframe=config.timeframe,
    )


if __name__ == "__main__":
    main()
