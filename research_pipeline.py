"""Reproducible large-scale research orchestrator.

The pipeline does not alter strategy logic. It runs the existing engine per
symbol, merges completed journals, then delegates analysis to the existing
research scripts.

Example:
    python research_pipeline.py --universe research_universe.csv \
        --start 2018-01-01 --end 2024-01-01 --warmup-start 2017-01-01 \
        --output-root research_runs
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import platform
import subprocess
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from importlib.metadata import distributions
from pathlib import Path
from typing import Any

import pandas as pd

from config.settings import BacktestConfig, load_config
from data.yahoo_data import MarketDataRequest, YahooFinanceDataSource
from engine.backtest_engine import BacktestEngine
from main import STRATEGY_REGISTRY, build_strategy_params


def main() -> None:
    args = _parse_args()
    symbols = _load_universe(args.universe)
    config = load_config(args.config)
    config = _apply_overrides(config, args)
    research_id = args.research_id or _research_id(args, symbols, config)
    run_dir = Path(args.output_root) / research_id
    run_dir.mkdir(parents=True, exist_ok=True)
    log_path = run_dir / "research_log.txt"
    _configure_logging(log_path)
    logger = logging.getLogger("research_pipeline")
    started = time.time()

    manifest = _build_manifest(research_id, args, config, symbols, run_dir)
    (run_dir / "research_manifest.json").write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    logger.info("Research run started: %s", research_id)

    source = YahooFinanceDataSource()
    strategy_class = STRATEGY_REGISTRY.get(config.strategy_name)
    if strategy_class is None:
        raise ValueError(f"Unsupported strategy: {config.strategy_name}")

    completed: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []
    all_trades: list[pd.DataFrame] = []
    all_summaries: list[dict[str, Any]] = []
    benchmark_data: pd.DataFrame | None = None

    if config.strategy_name == "leadership_expansion_v1":
        benchmark_data = _fetch_with_retry(source, config.benchmark_ticker, args.data_start, args.end, args.retries, logger)

    for symbol in symbols:
        symbol_dir = run_dir / "symbols" / symbol
        symbol_dir.mkdir(parents=True, exist_ok=True)
        try:
            market_data = _fetch_with_retry(source, symbol, args.data_start, args.end, args.retries, logger, config.timeframe)
            extra = [benchmark_data] if benchmark_data is not None else None
            params = build_strategy_params(config)
            if config.strategy_name == "leadership_expansion_v1":
                params["skip_relative_strength_filter"] = symbol.upper() == config.benchmark_ticker.upper()
            result = BacktestEngine(
                initial_capital=config.initial_capital,
                commission=config.commission,
                slippage_perc=config.slippage,
                output_dir=symbol_dir,
            ).run(
                dataframe=market_data,
                strategy_class=strategy_class,
                strategy_params=params,
                extra_dataframes=extra,
                plot_results=False,
                base_timeframe=config.timeframe,
            )
            trades_path = symbol_dir / "trades.csv"
            trades = pd.read_csv(trades_path) if trades_path.exists() else pd.DataFrame()
            if not trades.empty and "entry_time" in trades:
                entry_times = pd.to_datetime(trades["entry_time"], errors="coerce")
                trades = trades.loc[entry_times >= pd.Timestamp(config.start_date)].copy()
                trades.insert(0, "ticker", symbol)
                all_trades.append(trades)
            metrics = asdict(result.metrics)
            metrics.update({"ticker": symbol, "final_portfolio_value": result.final_portfolio_value})
            all_summaries.append(metrics)
            completed.append({"ticker": symbol, "trade_count": len(trades), "status": "completed"})
            logger.info("Completed %s: %s trades", symbol, len(trades))
        except Exception as exc:
            item = {"ticker": symbol, "status": "failed", "error": repr(exc)}
            failed.append(item)
            logger.exception("Failed %s", symbol)

    merged_trades = pd.concat(all_trades, ignore_index=True) if all_trades else pd.DataFrame()
    merged_trades.to_csv(run_dir / "merged_trades.csv", index=False)
    pd.DataFrame(all_summaries).to_csv(run_dir / "symbol_summary.csv", index=False)
    pd.DataFrame(failed).to_csv(run_dir / "error_report.csv", index=False)

    feature_dir = run_dir / "feature_research"
    hypothesis_dir = run_dir / "hypothesis_discovery"
    feature_ok = _run_analysis("scripts/research_feature_engine.py", run_dir / "merged_trades.csv", feature_dir, logger)
    hypothesis_input = feature_dir / "feature_research_trades.csv"
    hypothesis_ok = hypothesis_input.exists() and _run_analysis(
        "scripts/hypothesis_discovery_engine.py", hypothesis_input, hypothesis_dir, logger
    )
    _copy_analysis_outputs(feature_dir, hypothesis_dir, run_dir)
    _write_report(run_dir / "research_run_report.md", manifest, completed, failed, merged_trades, all_summaries, feature_ok, hypothesis_ok, time.time() - started)
    logger.info("Research run finished: %s", research_id)
    print(run_dir.resolve())


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Large-scale reproducible research pipeline")
    parser.add_argument("--universe", type=Path, required=True, help="CSV, JSON, or text symbol list")
    parser.add_argument("--start", dest="start_date", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--warmup-start", dest="data_start", required=True)
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--output-root", type=Path, default=Path("research_runs"))
    parser.add_argument("--research-id")
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--strategy", default=None)
    parser.add_argument("--timeframe", default=None)
    return parser.parse_args()


def _load_universe(path: Path) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(path)
    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        values = payload.get("symbols", payload) if isinstance(payload, dict) else payload
    elif path.suffix.lower() == ".csv":
        frame = pd.read_csv(path)
        column = next((name for name in frame.columns if name.lower() in {"ticker", "symbol"}), frame.columns[0])
        values = frame[column].tolist()
    else:
        values = path.read_text(encoding="utf-8").replace(",", "\n").splitlines()
    symbols = sorted({str(value).strip().upper() for value in values if str(value).strip()})
    if not symbols:
        raise ValueError(f"Universe is empty: {path}")
    return symbols


def _apply_overrides(config: BacktestConfig, args: argparse.Namespace) -> BacktestConfig:
    values = asdict(config)
    values["start_date"] = args.start_date
    values["end_date"] = args.end
    if args.strategy:
        values["strategy_name"] = args.strategy
    if args.timeframe:
        values["timeframe"] = args.timeframe
    return BacktestConfig(**values)


def _fetch_with_retry(source: YahooFinanceDataSource, ticker: str, start: str, end: str, retries: int, logger: logging.Logger, timeframe: str = "1d") -> pd.DataFrame:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            return source.fetch(MarketDataRequest(ticker=ticker, start=start, end=end, timeframe=timeframe))
        except Exception as exc:
            last_error = exc
            logger.warning("Fetch failed %s attempt %s/%s: %s", ticker, attempt, retries, exc)
            if attempt < retries:
                time.sleep(min(attempt, 5))
    raise RuntimeError(f"Could not fetch {ticker}: {last_error}") from last_error


def _run_analysis(script: str, trades_path: Path, output_dir: Path, logger: logging.Logger) -> bool:
    command = [sys.executable, script, "--trades", str(trades_path), "--output-dir", str(output_dir)]
    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.returncode:
        logger.error("Analysis failed %s: %s", script, completed.stderr.strip())
        return False
    logger.info("Analysis completed %s", script)
    return True


def _copy_analysis_outputs(feature_dir: Path, hypothesis_dir: Path, run_dir: Path) -> None:
    feature_source = feature_dir / "feature_research_trades.csv"
    hypothesis_source = hypothesis_dir / "hypothesis_candidates.csv"
    if feature_source.exists():
        feature_source.replace(run_dir / "merged_feature_research.csv")
    if hypothesis_source.exists():
        hypothesis_source.replace(run_dir / "merged_hypotheses.csv")


def _research_id(args: argparse.Namespace, symbols: list[str], config: BacktestConfig) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"{stamp}_{args.universe.stem}_{config.timeframe}_{config.strategy_name}"


def _build_manifest(research_id: str, args: argparse.Namespace, config: BacktestConfig, symbols: list[str], run_dir: Path) -> dict[str, Any]:
    packages = {}
    for distribution in distributions():
        if distribution.metadata.get("Name") in {"backtrader", "pandas", "yfinance", "matplotlib", "numpy"}:
            packages[distribution.metadata["Name"]] = distribution.version
    return {
        "research_id": research_id,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "project_path": str(Path.cwd().resolve()),
        "strategy_version": config.strategy_name,
        "strategy_parameters": {key: value for key, value in asdict(config).items() if key not in {"output_dir", "plot"}},
        "timeframe": config.timeframe,
        "data_start_warmup": args.data_start,
        "research_start": args.start_date,
        "research_end": args.end,
        "universe_file": str(args.universe.resolve()),
        "universe_symbols": symbols,
        "commission": config.commission,
        "slippage": config.slippage,
        "risk_per_trade": config.risk_per_trade,
        "max_positions": config.max_positions,
        "seed": None,
        "python_version": platform.python_version(),
        "packages": packages,
        "output_directory": str(run_dir.resolve()),
    }


def _configure_logging(path: Path) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", handlers=[logging.FileHandler(path, encoding="utf-8"), logging.StreamHandler()])


def _write_report(path: Path, manifest: dict[str, Any], completed: list[dict[str, Any]], failed: list[dict[str, Any]], trades: pd.DataFrame, summaries: list[dict[str, Any]], feature_ok: bool, hypothesis_ok: bool, elapsed: float) -> None:
    symbol_summary = pd.DataFrame(summaries)
    best = symbol_summary.sort_values("net_profit", ascending=False).head(5)[["ticker", "net_profit", "total_trades"]].to_dict("records") if not symbol_summary.empty else []
    worst = symbol_summary.sort_values("net_profit").head(5)[["ticker", "net_profit", "total_trades"]].to_dict("records") if not symbol_summary.empty else []
    lines = [
        "# Research Run Report", "", f"Research ID: `{manifest['research_id']}`", f"Strategy: `{manifest['strategy_version']}`",
        f"Period: {manifest['research_start']} -> {manifest['research_end']}", f"Universe symbols: {len(manifest['universe_symbols'])}",
        f"Symbols completed: {len(completed)}", f"Symbols failed: {len(failed)}", f"Merged completed trades: {len(trades)}", f"Elapsed seconds: {elapsed:.2f}",
        "", "## Portfolio/Run Metrics", "", "The per-symbol runs use the existing BacktestEngine. This merged result is not a substitute for a single shared-account portfolio simulation.", "",
        f"Feature analysis completed: {feature_ok}", f"Hypothesis analysis completed: {hypothesis_ok}", "", "## Best Symbols", "", str(best), "", "## Worst Symbols", "", str(worst), "",
        "## Research Quality Warnings", "", "- Failed symbols are listed in `error_report.csv` and are not silently treated as zero trades.", "- Warmup data is used for indicator initialization; only entries on or after the research start are merged.", "- The pipeline runs symbols independently; max_positions and cash competition require a separate shared-portfolio validation.", "- Hypotheses are descriptive candidates and require out-of-sample validation.", "",
        "## Recommendations", "", "Use the merged journal for attribution first. Do not change parameters or filters based on this report alone.",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
