"""RC-A1 controlled EMA trend architecture ablation; no strategy changes."""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from dataclasses import asdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from config.settings import load_config
from data.yahoo_data import MarketDataRequest, YahooFinanceDataSource
from engine.backtest_engine import BacktestEngine
from main import STRATEGY_REGISTRY, build_strategy_params


EXPERIMENTS = {
    "RC-A1-E0_BASELINE": {},
    "RC-A1-E1_NO_EMA200_PRICE": {"enable_ema200_filter": False},
    "RC-A1-E2_NO_EMA200_SLOPE": {"enable_ema200_slope_filter": False},
    "RC-A1-E3_NO_EMA200_ARCHITECTURE": {"enable_ema200_filter": False, "enable_ema200_slope_filter": False},
}


def main() -> None:
    global EXPERIMENTS
    args = _args()
    if args.experiment_spec is not None:
        EXPERIMENTS = json.loads(args.experiment_spec.read_text(encoding="utf-8"))
    _require_baseline_pass(args.baseline_report)
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    config = load_config(args.config)
    config.strategy_name = "leadership_expansion_v1"
    config.start_date, config.end_date, config.timeframe, config.plot = args.start, args.end, "1d", False
    universe = pd.read_csv(args.universe).iloc[:, 0].dropna().astype(str).str.upper().tolist()
    (out / "experiment_manifest.json").write_text(
        json.dumps(
            {
                "experiment_id": args.experiment_id,
                "title": args.experiment_title,
                "strategy": config.strategy_name,
                "universe_file": str(args.universe),
                "universe_symbol_count": len(universe),
                "warmup_start": args.warmup_start,
                "research_start": args.start,
                "research_end_exclusive": args.end,
                "experiments": EXPERIMENTS,
                "portfolio_model": "independent_single_symbol_runs",
                "portfolio_metric_policy": "not_aggregated",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    source = YahooFinanceDataSource()
    benchmark = source.fetch(MarketDataRequest(config.benchmark_ticker, args.warmup_start, args.end, "1d"))
    all_trades: dict[str, list[pd.DataFrame]] = {name: [] for name in EXPERIMENTS}
    symbol_rows: dict[str, list[dict]] = {name: [] for name in EXPERIMENTS}
    errors: list[dict] = []

    for index, ticker in enumerate(universe, start=1):
        if args.resume and _ticker_complete(out, ticker):
            print(f"{index}/{len(universe)} {ticker} (resume: already complete)")
            continue
        try:
            market = source.fetch(MarketDataRequest(ticker, args.warmup_start, args.end, "1d"))
        except Exception as exc:
            errors.append({"ticker": ticker, "stage": "fetch", "error": repr(exc)})
            continue
        for experiment, overrides in EXPERIMENTS.items():
            try:
                params = build_strategy_params(config)
                params.update(overrides)
                params["skip_relative_strength_filter"] = ticker == config.benchmark_ticker
                symbol_dir = out / "runs" / experiment / ticker
                result = BacktestEngine(config.initial_capital, config.commission, config.slippage, symbol_dir).run(
                    dataframe=market, strategy_class=STRATEGY_REGISTRY[config.strategy_name], strategy_params=params,
                    extra_dataframes=[benchmark], plot_results=False, base_timeframe="1d",
                )
                trades = pd.read_csv(symbol_dir / "trades.csv")
                if not trades.empty:
                    entry = pd.to_datetime(trades["entry_time"], errors="coerce")
                    trades = trades.loc[entry >= pd.Timestamp(args.start)].copy()
                    trades.insert(0, "ticker", ticker)
                    all_trades[experiment].append(trades)
                symbol_rows[experiment].append({"ticker": ticker, **asdict(result.metrics), "final_portfolio_value": result.final_portfolio_value})
            except Exception as exc:
                errors.append({"ticker": ticker, "stage": experiment, "error": repr(exc)})
        print(f"{index}/{len(universe)} {ticker}")

    combined = {}
    for experiment in EXPERIMENTS:
        trades = _load_completed_trades(out, experiment, args.start)
        combined[experiment] = trades
        trades.to_csv(out / f"{experiment}_trades.csv", index=False)
        pd.DataFrame(symbol_rows[experiment]).to_csv(out / f"{experiment}_symbol_metrics.csv", index=False)
    pd.DataFrame(errors).to_csv(out / "ablation_errors.csv", index=False)

    metrics = pd.DataFrame([_aggregate_metrics(name, combined[name]) for name in EXPERIMENTS])
    baseline = metrics.iloc[0]
    delta = metrics.copy()
    for field in ["trade_count", "profit_factor", "expectancy", "avg_R", "median_R", "win_rate", "average_holding_days", "largest_winner", "largest_loser"]:
        delta[f"delta_{field}"] = delta[field] - baseline[field]
    for field in ["sharpe", "sortino", "maximum_drawdown", "cagr", "exposure", "recovery_factor"]:
        delta[f"delta_{field}"] = None
    metrics.to_csv(out / "ema_trend_summary.csv", index=False)
    delta.to_csv(out / "ema_trend_delta.csv", index=False)
    yearly = _stability(combined, "year")
    symbols = _stability(combined, "ticker")
    yearly.to_csv(out / "ema_trend_yearly.csv", index=False)
    symbols.to_csv(out / "ema_trend_symbol.csv", index=False)
    verdict = _verdict(metrics, yearly, symbols)
    (out / "ema_trend_verdict.json").write_text(json.dumps(verdict, indent=2), encoding="utf-8")
    _report(out / "ema_trend_ablation.md", args, metrics, delta, verdict, errors)
    print(out.resolve())


def _args():
    p = argparse.ArgumentParser()
    p.add_argument("--universe", type=Path, required=True)
    p.add_argument("--warmup-start", default="2009-01-01")
    p.add_argument("--start", default="2010-01-01")
    p.add_argument("--end", default="2026-01-01")
    p.add_argument("--config", type=Path, default=None)
    p.add_argument("--baseline-report", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--resume", action="store_true", help="Skip tickers with all four completed run outputs.")
    p.add_argument("--experiment-id", default="RC-A1")
    p.add_argument("--experiment-title", default="EMA Trend Architecture Ablation")
    p.add_argument("--experiment-spec", type=Path, help="JSON mapping of four experiment names to parameter overrides.")
    return p.parse_args()


def _require_baseline_pass(path: Path) -> None:
    if not path.exists() or "Trade records identical: True" not in path.read_text(encoding="utf-8"):
        raise RuntimeError("Baseline validation missing or failed; aborting RC-A1.")


def _ticker_complete(output_dir: Path, ticker: str) -> bool:
    return all((output_dir / "runs" / experiment / ticker / "trades.csv").exists() for experiment in EXPERIMENTS)


def _load_completed_trades(output_dir: Path, experiment: str, research_start: str) -> pd.DataFrame:
    frames = []
    for path in (output_dir / "runs" / experiment).glob("*/trades.csv"):
        trades = pd.read_csv(path)
        if trades.empty:
            continue
        entry = pd.to_datetime(trades["entry_time"], errors="coerce")
        trades = trades.loc[entry >= pd.Timestamp(research_start)].copy()
        if "ticker" not in trades.columns:
            trades.insert(0, "ticker", path.parent.name)
        frames.append(trades)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def _aggregate_metrics(experiment: str, trades: pd.DataFrame) -> dict:
    if trades.empty:
        return {"experiment": experiment, "trade_count": 0}
    r = pd.to_numeric(trades["R_multiple"], errors="coerce").dropna()
    pnl = pd.to_numeric(trades["pnl_dollars"], errors="coerce").dropna()
    wins, losses = r[r > 0], r[r < 0]
    pf = float(wins.sum() / abs(losses.sum())) if len(losses) else math.inf
    return {
        "experiment": experiment, "trade_count": len(r), "win_rate": float((r > 0).mean()*100),
        "profit_factor": pf, "expectancy": float(r.mean()), "avg_R": float(r.mean()), "median_R": float(r.median()),
        "average_holding_days": float(pd.to_numeric(trades["holding_days"], errors="coerce").mean()),
        "largest_winner": float(r.max()), "largest_loser": float(r.min()),
        "sharpe": None, "sortino": None, "maximum_drawdown": None, "cagr": None, "mar": None,
        "exposure": None, "recovery_factor": None,
        "portfolio_metric_limitation": "N/A: UNAVAILABLE_WITH_INDEPENDENT_SINGLE_SYMBOL_RUNS",
    }


def _stability(combined: dict[str, pd.DataFrame], dimension: str) -> pd.DataFrame:
    rows = []
    for experiment, trades in combined.items():
        if trades.empty:
            continue
        if dimension == "year":
            keys = pd.to_datetime(trades["entry_time"], errors="coerce").dt.year
        else:
            keys = trades["ticker"]
        for segment, group in trades.groupby(keys, dropna=True):
            r = pd.to_numeric(group["R_multiple"], errors="coerce").dropna()
            rows.append({"experiment": experiment, dimension: segment, "trade_count": len(r), "avg_R": r.mean() if len(r) else None, "median_R": r.median() if len(r) else None, "win_rate": (r > 0).mean()*100 if len(r) else None})
    return pd.DataFrame(rows)


def _verdict(metrics: pd.DataFrame, yearly: pd.DataFrame, symbols: pd.DataFrame) -> dict:
    baseline_experiment = metrics.experiment.iloc[0]
    baseline = metrics.iloc[0]
    tests = {}
    for experiment in metrics.experiment.iloc[1:]:
        row = metrics.loc[metrics.experiment == experiment].iloc[0]
        delta = float(row.avg_R - baseline.avg_R)
        y_base = yearly[yearly.experiment == baseline_experiment].set_index("year")["avg_R"]
        y_test = yearly[yearly.experiment == experiment].set_index("year")["avg_R"]
        aligned = pd.concat([y_base, y_test], axis=1).dropna()
        deterioration_years = float((aligned.iloc[:, 1] < aligned.iloc[:, 0]).mean()) if len(aligned) else None
        s_base = symbols[symbols.experiment == baseline_experiment].set_index("ticker")["avg_R"]
        s_test = symbols[symbols.experiment == experiment].set_index("ticker")["avg_R"]
        symbol_aligned = pd.concat([s_base, s_test], axis=1).dropna()
        deterioration_symbols = float((symbol_aligned.iloc[:, 1] < symbol_aligned.iloc[:, 0]).mean()) if len(symbol_aligned) else None
        tests[experiment] = {
            "delta_avg_R": delta,
            "deterioration_year_fraction": deterioration_years,
            "deterioration_ticker_fraction": deterioration_symbols,
        }
    first, second, both = (tests[experiment] for experiment in metrics.experiment.iloc[1:])
    def classify(test):
        if (test["delta_avg_R"] <= -0.10 and (test["deterioration_year_fraction"] or 0) >= .60
                and (test["deterioration_ticker_fraction"] or 0) >= .60):
            return "Important"
        if test["delta_avg_R"] < 0:
            return "Marginal"
        return "Redundant"
    return {"first_filter": {**first, "classification": classify(first)}, "second_filter": {**second, "classification": classify(second)}, "both_filters": {**both, "classification": classify(both)}, "summary": {"first_filter": classify(first), "second_filter": classify(second), "combined_filters": classify(both), "criterion": "Preregistered: Avg R deterioration >=0.10 plus >=60% deterioration across both years and tickers for Important."}}


def _report(path, args, metrics, delta, verdict, errors):
    lines = ["# RC-A1 EMA Trend Architecture Ablation", "", "Baseline validation passed before execution.", "", "## Experiment Metrics", "", metrics.to_string(index=False), "", "## Delta vs Baseline", "", delta.to_string(index=False), "", "## Verdict", "", json.dumps(verdict, indent=2), "", "## Limitations", "", "- Runs are per-symbol independent; shared-account portfolio metrics (Sharpe, Sortino, maximum drawdown, CAGR, exposure, recovery factor) are N/A rather than fabricated.", "- This is controlled attribution, not causality or an optimization result.", "- No exit, sizing, or non-EMA entry component was changed.", f"- Errors recorded: {len(errors)}"]
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
