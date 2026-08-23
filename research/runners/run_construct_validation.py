"""CV-001: descriptive construct validation for the frozen production RS gate.

This runner deliberately does not instantiate Backtrader, calculate trade outcomes,
or evaluate any performance statistic.  It compares daily *signals* only.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from data.yahoo_data import MarketDataRequest, YahooFinanceDataSource


STUDY_ID = "CV-001"
PRODUCTION_RULE = "RS60 > 5% AND (RS20 > 0 OR RS120 > 10%), all relative to SPY"
CANONICAL_RULE = "12-1 cross-sectional momentum: rank Close[t-21]/Close[t-252]-1; top decile"


def main() -> None:
    args = _args()
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    cache = output / "close_cache"
    cache.mkdir(exist_ok=True)

    tickers = _load_universe(args.universe, args.benchmark)
    closes, completed, errors = _load_closes(tickers, args, cache)
    benchmark = _load_benchmark(args, cache)
    if len(closes) < 30:
        raise RuntimeError("CV-001 requires at least 30 successfully downloaded securities.")

    daily, selected_ranks = _compare(closes, benchmark, args.start, args.end)
    if daily.empty:
        raise RuntimeError("No dates had enough valid observations for CV-001.")

    daily.to_csv(output / "signal_overlap_analysis.csv", index=False)
    distribution = _distribution(selected_ranks)
    distribution.to_csv(output / "distribution_analysis.csv", index=False)
    agreement = _agreement_metrics(daily)
    agreement.to_csv(output / "agreement_metrics.csv", index=False)
    _write_reports(output, args, tickers, completed, errors, daily, distribution, agreement)
    pd.DataFrame({"ticker": completed}).to_csv(output / "completed_symbols.csv", index=False)
    pd.DataFrame(errors).to_csv(output / "download_errors.csv", index=False)


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run CV-001 construct validation without backtesting.")
    parser.add_argument("--universe", type=Path, default=ROOT / "sp500_current_universe.csv")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--benchmark", default="SPY")
    parser.add_argument("--warmup-start", default="2008-01-01")
    parser.add_argument("--start", default="2010-01-01")
    parser.add_argument("--end", default="2026-01-01")
    parser.add_argument("--resume", action="store_true", help="Reuse cached close files when present.")
    return parser.parse_args()


def _load_universe(path: Path, benchmark: str) -> list[str]:
    tickers = pd.read_csv(path).iloc[:, 0].dropna().astype(str).str.upper().tolist()
    # Production bypasses its own RS check for SPY, so it cannot be a comparable gate candidate.
    return sorted({ticker for ticker in tickers if ticker != benchmark.upper()})


def _load_closes(tickers: list[str], args: argparse.Namespace, cache: Path) -> tuple[pd.DataFrame, list[str], list[dict]]:
    source = YahooFinanceDataSource()
    columns: dict[str, pd.Series] = {}
    completed, errors = [], []
    for number, ticker in enumerate(tickers, start=1):
        path = cache / f"{ticker}.csv"
        try:
            if args.resume and path.exists():
                cached = pd.read_csv(path, parse_dates=["Datetime"]).set_index("Datetime")
                frame = cached if _cache_covers(cached, args.warmup_start, args.end) else None
            else:
                frame = None
            if frame is None:
                frame = source.fetch(MarketDataRequest(ticker, args.warmup_start, args.end, "1d"))
                frame[["Close"]].to_csv(path, index_label="Datetime")
            columns[ticker] = pd.to_numeric(frame["Close"], errors="coerce")
            completed.append(ticker)
        except Exception as exc:
            errors.append({"ticker": ticker, "error": repr(exc)})
        # Deliberately avoid per-symbol stdout: long research runs can outlive a UI output pipe.
        if number % 50 == 0 or number == len(tickers):
            print(f"Downloaded or loaded {number}/{len(tickers)} symbols", flush=True)
    return pd.DataFrame(columns).sort_index(), completed, errors


def _load_benchmark(args: argparse.Namespace, cache: Path) -> pd.Series:
    path = cache / f"{args.benchmark.upper()}.csv"
    if args.resume and path.exists():
        cached = pd.read_csv(path, parse_dates=["Datetime"]).set_index("Datetime")
        frame = cached if _cache_covers(cached, args.warmup_start, args.end) else None
    else:
        frame = None
    if frame is None:
        frame = YahooFinanceDataSource().fetch(MarketDataRequest(args.benchmark, args.warmup_start, args.end, "1d"))
        frame[["Close"]].to_csv(path, index_label="Datetime")
    return pd.to_numeric(frame["Close"], errors="coerce").sort_index()


def _cache_covers(frame: pd.DataFrame, start: str, end: str) -> bool:
    if frame.empty:
        return False
    index = pd.to_datetime(frame.index)
    return index.min() <= pd.Timestamp(start) and index.max() >= pd.Timestamp(end) - pd.Timedelta(days=7)


def _compare(closes: pd.DataFrame, benchmark: pd.Series, start: str, end: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    closes = closes.sort_index()
    benchmark = benchmark.reindex(closes.index).ffill()
    rs20 = closes.pct_change(20).sub(benchmark.pct_change(20), axis=0)
    rs60 = closes.pct_change(60).sub(benchmark.pct_change(60), axis=0)
    rs120 = closes.pct_change(120).sub(benchmark.pct_change(120), axis=0)
    momentum_12_1 = closes.shift(21).div(closes.shift(252)).sub(1.0)
    benchmark_return60 = benchmark.pct_change(60)

    rows, rank_rows = [], []
    for date in closes.loc[start:end].index:
        frame = pd.DataFrame({"rs20": rs20.loc[date], "rs60": rs60.loc[date], "rs120": rs120.loc[date], "momentum": momentum_12_1.loc[date]}).dropna()
        if len(frame) < 30:
            continue
        frame["momentum_percentile"] = frame["momentum"].rank(method="first", pct=True)
        frame["production_gate"] = (frame.rs60 > 0.05) & ((frame.rs20 > 0) | (frame.rs120 > 0.10))
        # Strictly greater than 0.90 makes an exact top-decile selection under method='first'.
        frame["canonical_top_decile"] = frame.momentum_percentile > 0.90
        production = int(frame.production_gate.sum())
        canonical = int(frame.canonical_top_decile.sum())
        overlap = int((frame.production_gate & frame.canonical_top_decile).sum())
        union = production + canonical - overlap
        regime = "SPY_60D_POSITIVE" if benchmark_return60.loc[date] > 0 else "SPY_60D_NONPOSITIVE"
        spearman = _spearman(frame.rs60, frame.momentum)
        rows.append({
            "date": date, "year": date.year, "market_regime": regime,
            "candidate_count": len(frame), "production_gate_count": production,
            "canonical_top_decile_count": canonical, "overlap_count": overlap, "union_count": union,
            "production_coverage_pct": production / len(frame) * 100,
            "canonical_coverage_pct": canonical / len(frame) * 100,
            "jaccard_similarity": overlap / union if union else np.nan,
            "precision_pct": overlap / production * 100 if production else np.nan,
            "recall_pct": overlap / canonical * 100 if canonical else np.nan,
            "rs60_momentum_spearman": spearman,
        })
        selected = frame.loc[frame.production_gate, "momentum_percentile"]
        for value in selected:
            rank_rows.append({"date": date, "year": date.year, "market_regime": regime, "momentum_percentile": value})
    return pd.DataFrame(rows), pd.DataFrame(rank_rows)


def _distribution(selected_ranks: pd.DataFrame) -> pd.DataFrame:
    groups = [("OVERALL", selected_ranks)]
    groups += [(f"YEAR:{year}", group) for year, group in selected_ranks.groupby("year")]
    groups += [(f"REGIME:{regime}", group) for regime, group in selected_ranks.groupby("market_regime")]
    rows = []
    for label, group in groups:
        values = group.momentum_percentile
        rows.append({
            "population": "PRODUCTION_GATE_PASSES", "segment": label, "observation_count": len(values),
            "mean_momentum_percentile": values.mean(), "median_momentum_percentile": values.median(),
            "p25_momentum_percentile": values.quantile(.25), "p75_momentum_percentile": values.quantile(.75),
            "share_in_canonical_top_decile_pct": (values > .90).mean() * 100,
            "share_below_median_pct": (values <= .50).mean() * 100,
        })
    return pd.DataFrame(rows)


def _spearman(left: pd.Series, right: pd.Series) -> float:
    """Spearman is Pearson correlation of within-date ranks; avoids SciPy dependency."""
    ranked = pd.DataFrame({"left": left, "right": right}).rank(method="average")
    return ranked.left.corr(ranked.right)


def _agreement_metrics(daily: pd.DataFrame) -> pd.DataFrame:
    groups = [("OVERALL", daily)]
    groups += [(f"YEAR:{year}", group) for year, group in daily.groupby("year")]
    groups += [(f"REGIME:{regime}", group) for regime, group in daily.groupby("market_regime")]
    rows = []
    for label, group in groups:
        production, canonical = group.production_gate_count.sum(), group.canonical_top_decile_count.sum()
        overlap, union = group.overlap_count.sum(), group.union_count.sum()
        jaccard = overlap / union if union else np.nan
        rows.append({
            "segment": label, "date_count": len(group), "candidate_observations": group.candidate_count.sum(),
            "production_signal_observations": production, "canonical_signal_observations": canonical,
            "overlap_observations": overlap, "union_observations": union,
            "production_coverage_pct": production / group.candidate_count.sum() * 100,
            "canonical_coverage_pct": canonical / group.candidate_count.sum() * 100,
            "jaccard_similarity": jaccard,
            "precision_pct": overlap / production * 100 if production else np.nan,
            "recall_pct": overlap / canonical * 100 if canonical else np.nan,
            "mean_daily_spearman_rs60_vs_12_1": group.rs60_momentum_spearman.mean(),
            "median_daily_spearman_rs60_vs_12_1": group.rs60_momentum_spearman.median(),
            "overlap_band": _overlap_band(jaccard),
            "sector_analysis": "NOT_EVALUATED_NO_HISTORICAL_SECTOR_CLASSIFICATION",
            "benchmark_sensitivity": "NOT_EVALUATED_PRODUCTION_GATE_DEFINED_RELATIVE_TO_SPY",
        })
    return pd.DataFrame(rows)


def _overlap_band(jaccard: float) -> str:
    if pd.isna(jaccard):
        return "UNAVAILABLE"
    if jaccard >= .50:
        return "HIGH_DESCRIPTIVE_OVERLAP"
    if jaccard >= .20:
        return "MODERATE_DESCRIPTIVE_OVERLAP"
    return "LOW_DESCRIPTIVE_OVERLAP"


def _write_reports(output: Path, args: argparse.Namespace, universe: list[str], completed: list[str], errors: list[dict], daily: pd.DataFrame, distribution: pd.DataFrame, agreement: pd.DataFrame) -> None:
    overall = agreement.loc[agreement.segment == "OVERALL"].iloc[0]
    band = overall.overlap_band
    construct = "The observed signal sets show " + band.lower().replace("_", " ") + "."
    if band == "LOW_DESCRIPTIVE_OVERLAP":
        construct += " Within this fixed dataset and definitions, the production gate does not appear to select the same daily security set as canonical 12-1 top-decile cross-sectional momentum."
    elif band == "MODERATE_DESCRIPTIVE_OVERLAP":
        construct += " Within this fixed dataset and definitions, the production gate has partial but not complete alignment with canonical 12-1 top-decile cross-sectional momentum."
    else:
        construct += " Within this fixed dataset and definitions, the production gate has substantial descriptive alignment with canonical 12-1 top-decile cross-sectional momentum."
    base = f"""# {STUDY_ID}: Production Relative Strength Gate vs Canonical Cross-Sectional Momentum\n\n## Scope\nThis is a descriptive construct-validation study. No strategy was run, no trade outcomes were read, and no return, alpha, profitability, risk, or optimisation statistic was calculated.\n\n## Pre-specified definitions\n- **Production gate:** `{PRODUCTION_RULE}`.\n- **Canonical comparator:** `{CANONICAL_RULE}`. Rankings are recalculated across the same valid securities on each date.\n- **Analysis window:** {args.start} through {args.end}, with price warmup from {args.warmup_start}.\n- **Universe:** current S&P 500 constituent file fixed before execution; SPY is excluded from candidate ranking because production bypasses its own relative-strength check for the benchmark.\n\n## Primary descriptive result\n- Valid daily comparison dates: {int(overall.date_count):,}\n- Candidate security-date observations: {int(overall.candidate_observations):,}\n- Production gate observations: {int(overall.production_signal_observations):,}\n- Canonical top-decile observations: {int(overall.canonical_signal_observations):,}\n- Shared observations: {int(overall.overlap_observations):,}\n- Jaccard similarity: {overall.jaccard_similarity:.4f}\n- Precision (production gate also canonical): {overall.precision_pct:.2f}%\n- Recall (canonical top decile also production gate): {overall.recall_pct:.2f}%\n- Mean daily Spearman correlation between RS60 and 12-1 momentum: {overall.mean_daily_spearman_rs60_vs_12_1:.4f}\n\n## Interpretation\n{construct}\n\nThis is observational construct evidence only. It does not compare trading performance, validate or invalidate the production strategy, establish economic value, or establish causality.\n"""
    (output / "cv001_construct_validation.md").write_text(base, encoding="utf-8")
    (output / "construct_interpretation.md").write_text(f"# Construct Interpretation\n\n{construct}\n\nThe conclusion is tied to the explicit definitions in CV-001: a fixed SPY-relative multi-horizon threshold gate versus a daily 12-1 cross-sectional top-decile rank. Different definitions can represent different operationalisations without either being economically superior.\n", encoding="utf-8")
    (output / "limitations.md").write_text(f"""# Limitations\n\n- The universe is the current S&P 500 constituent list, not a survivorship-free historical constituent universe.\n- {len(completed):,} of {len(universe):,} candidate securities downloaded successfully; {len(errors):,} did not.\n- Historical sector/industry classifications were not available in the project, so sector agreement was not evaluated rather than approximated using present-day labels.\n- The production gate is defined relative to SPY. Alternative benchmark definitions were not introduced because that would define a different gate rather than describe the frozen production one.\n- Yahoo Finance adjusted-data conventions, delistings, and ticker-history availability can affect the eligible daily cross-section.\n- Both definitions use the project's raw Yahoo `Close` series for like-for-like comparison with production. This is not a total-return implementation of academic momentum and limits direct comparability to studies that include dividends.\n- This study evaluates signal-set overlap only. It intentionally contains no performance, outcome, trade, or causal analysis.\n""", encoding="utf-8")
    (output / "executive_summary.md").write_text(f"""# CV-001 Executive Summary\n\nCV-001 compared the frozen production SPY-relative Relative Strength gate with a pre-specified canonical 12-1 cross-sectional momentum top-decile comparator on identical valid securities and dates. The observed Jaccard similarity was **{overall.jaccard_similarity:.4f}**, with production-to-canonical precision of **{overall.precision_pct:.2f}%** and canonical-to-production recall of **{overall.recall_pct:.2f}%**.\n\n**Descriptive classification:** {band}.\n\n{construct}\n\nNo returns, trading performance, optimisation, or production recommendation is included.\n""", encoding="utf-8")
    manifest = {"study_id": STUDY_ID, "production_rule": PRODUCTION_RULE, "canonical_rule": CANONICAL_RULE, "universe_file": str(args.universe), "analysis_start": args.start, "analysis_end": args.end, "warmup_start": args.warmup_start, "candidate_symbols": len(universe), "completed_symbols": len(completed), "failed_symbols": len(errors), "no_backtest_or_outcome_analysis": True}
    (output / "cv001_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
