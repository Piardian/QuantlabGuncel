"""TCM-001: descriptive trend construct mapping for the frozen production RS gate.

This runner deliberately does not instantiate Backtrader, calculate trade outcomes,
or evaluate any performance statistic. It compares daily signal sets only.

All comparator definitions are preregistered and fixed before execution.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from data.yahoo_data import MarketDataRequest, YahooFinanceDataSource


STUDY_ID = "TCM-001"
PRODUCTION_RULE = "RS60 > 5% AND (RS20 > 0 OR RS120 > 10%), all relative to SPY"
REQUIRED_COLUMNS = ["Open", "High", "Low", "Close", "Volume"]


@dataclass(frozen=True, slots=True)
class Comparator:
    family: str
    name: str
    description: str
    score_builder: Callable[[pd.DataFrame, pd.DataFrame, pd.Series], pd.DataFrame]


def main() -> None:
    args = _args()
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    cache = Path(args.cache_dir) if args.cache_dir else output / "cache"
    cache.mkdir(parents=True, exist_ok=True)

    tickers = _load_universe(args.universe, args.benchmark)
    frames, completed, errors = _load_frames(tickers, args, cache)
    benchmark = _load_benchmark(args, cache)
    if len(frames) < 30:
        raise RuntimeError("TCM-001 requires at least 30 successfully downloaded securities.")

    closes, highs, lows, volumes = _align_market_data(frames)
    benchmark_close = pd.to_numeric(benchmark["Close"], errors="coerce").reindex(closes.index).ffill()

    production_frame = _production_frame(closes, benchmark_close)
    production_gate_wide = production_frame.pivot(index="date", columns="ticker", values="production_gate").sort_index()
    if production_frame.empty:
        raise RuntimeError("No dates had enough valid observations for TCM-001.")

    comparators = _comparators()
    comparator_rows = []
    agreement_rows = []
    distribution_rows = []

    for comparator in comparators:
        daily, selected_ranks, _ = _compare(
            closes=closes,
            highs=highs,
            lows=lows,
            volumes=volumes,
            benchmark=benchmark_close,
            production_gate_wide=production_gate_wide,
            comparator=comparator,
            start=args.start,
            end=args.end,
        )
        if daily.empty:
            continue
        comparator_rows.append(_comparator_matrix_row(comparator, daily, selected_ranks))
        agreement_rows.extend(_agreement_metrics(comparator, daily))
        distribution_rows.extend(_distribution_metrics(comparator, selected_ranks))

    if not comparator_rows:
        raise RuntimeError("TCM-001 produced no comparator results.")

    matrix = _family_matrix(comparator_rows)
    matrix.to_csv(output / "trend_construct_matrix.csv", index=False)
    pd.DataFrame(agreement_rows).to_csv(output / "agreement_metrics.csv", index=False)
    pd.DataFrame(distribution_rows).to_csv(output / "distribution_analysis.csv", index=False)
    family_comparison = _family_summary(matrix)
    _write_reports(output, args, tickers, completed, errors, matrix, family_comparison)
    pd.DataFrame({"ticker": completed}).to_csv(output / "completed_symbols.csv", index=False)
    pd.DataFrame(errors).to_csv(output / "download_errors.csv", index=False)


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run TCM-001 trend construct mapping without backtesting.")
    parser.add_argument("--universe", type=Path, default=ROOT / "sp500_current_universe.csv")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path, default=None)
    parser.add_argument("--benchmark", default="SPY")
    parser.add_argument("--warmup-start", default="2008-01-01")
    parser.add_argument("--start", default="2010-01-01")
    parser.add_argument("--end", default="2026-01-01")
    parser.add_argument("--resume", action="store_true", help="Reuse cached market files when present.")
    return parser.parse_args()


def _load_universe(path: Path, benchmark: str) -> list[str]:
    tickers = pd.read_csv(path).iloc[:, 0].dropna().astype(str).str.upper().tolist()
    return sorted({ticker for ticker in tickers if ticker != benchmark.upper()})


def _load_frames(tickers: list[str], args: argparse.Namespace, cache: Path) -> tuple[dict[str, pd.DataFrame], list[str], list[dict]]:
    source = YahooFinanceDataSource()
    frames: dict[str, pd.DataFrame] = {}
    completed, errors = [], []
    for number, ticker in enumerate(tickers, start=1):
        path = cache / f"{ticker}.csv"
        try:
            frame = _load_cached_frame(path, args.warmup_start, args.end, required_columns=REQUIRED_COLUMNS) if args.resume and path.exists() else None
            if frame is None:
                frame = source.fetch(MarketDataRequest(ticker, args.warmup_start, args.end, "1d"))
                frame.to_csv(path, index_label="Datetime")
            frames[ticker] = frame
            completed.append(ticker)
        except Exception as exc:
            errors.append({"ticker": ticker, "error": repr(exc)})
        if number % 50 == 0 or number == len(tickers):
            print(f"Downloaded or loaded {number}/{len(tickers)} symbols", flush=True)
    return frames, completed, errors


def _load_benchmark(args: argparse.Namespace, cache: Path) -> pd.DataFrame:
    path = cache / f"{args.benchmark.upper()}.csv"
    frame = _load_cached_frame(path, args.warmup_start, args.end, required_columns=["Close"]) if args.resume and path.exists() else None
    if frame is None:
        frame = YahooFinanceDataSource().fetch(MarketDataRequest(args.benchmark, args.warmup_start, args.end, "1d"))
        frame.to_csv(path, index_label="Datetime")
    return frame


def _load_cached_frame(path: Path, start: str, end: str, required_columns: list[str]) -> pd.DataFrame | None:
    cached = pd.read_csv(path, parse_dates=["Datetime"]).set_index("Datetime").sort_index()
    if _cache_covers(cached, start, end) and all(column in cached.columns for column in required_columns):
        return cached
    return None


def _cache_covers(frame: pd.DataFrame, start: str, end: str) -> bool:
    if frame.empty:
        return False
    index = pd.to_datetime(frame.index)
    return index.min() <= pd.Timestamp(start) and index.max() >= pd.Timestamp(end) - pd.Timedelta(days=7)


def _align_market_data(frames: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    closes = pd.DataFrame({ticker: pd.to_numeric(frame["Close"], errors="coerce") for ticker, frame in frames.items()}).sort_index()
    highs = pd.DataFrame({ticker: pd.to_numeric(frame["High"], errors="coerce") for ticker, frame in frames.items()}).sort_index()
    lows = pd.DataFrame({ticker: pd.to_numeric(frame["Low"], errors="coerce") for ticker, frame in frames.items()}).sort_index()
    volumes = pd.DataFrame({ticker: pd.to_numeric(frame["Volume"], errors="coerce") for ticker, frame in frames.items()}).sort_index()
    return closes, highs, lows, volumes


def _production_frame(closes: pd.DataFrame, benchmark: pd.Series) -> pd.DataFrame:
    benchmark_close = pd.to_numeric(benchmark, errors="coerce").reindex(closes.index).ffill()
    rs20 = closes.pct_change(20).sub(benchmark_close.pct_change(20), axis=0)
    rs60 = closes.pct_change(60).sub(benchmark_close.pct_change(60), axis=0)
    rs120 = closes.pct_change(120).sub(benchmark_close.pct_change(120), axis=0)
    frame = pd.DataFrame({"rs20": rs20.stack(), "rs60": rs60.stack(), "rs120": rs120.stack()}).reset_index()
    frame.columns = ["date", "ticker", "rs20", "rs60", "rs120"]
    frame["production_gate"] = (frame.rs60 > 0.05) & ((frame.rs20 > 0) | (frame.rs120 > 0.10))
    return frame


def _comparators() -> list[Comparator]:
    return [
        Comparator("Direction", "EMA50_GT_EMA200", "Binary signal: Close > EMA50 > EMA200", _ema50_gt_ema200),
        Comparator("Strength", "TREND_MAGNITUDE_60", "60-day trend magnitude based on log return", _trend_magnitude_60),
        Comparator("Persistence", "MULTI_HORIZON_AGREEMENT", "Agreement count across RS20, RS60, and RS120", _multi_horizon_agreement),
        Comparator("Smoothness", "TREND_EFFICIENCY_60", "60-day trend efficiency ratio", _trend_efficiency_60),
        Comparator("Composite", "COMPOSITE_TREND_SCORE", "Composite score across direction, strength, persistence, and smoothness", _composite_trend_score),
    ]


def _ema50_gt_ema200(closes: pd.DataFrame, highs: pd.DataFrame, lows: pd.DataFrame, volumes: pd.DataFrame, benchmark: pd.Series) -> pd.DataFrame:
    ema50 = closes.ewm(span=50, adjust=False, min_periods=50).mean()
    ema200 = closes.ewm(span=200, adjust=False, min_periods=200).mean()
    return ((closes > ema50) & (ema50 > ema200)).astype(float)


def _sma50_gt_sma200(closes: pd.DataFrame, highs: pd.DataFrame, lows: pd.DataFrame, volumes: pd.DataFrame, benchmark: pd.Series) -> pd.DataFrame:
    sma50 = closes.rolling(50, min_periods=50).mean()
    sma200 = closes.rolling(200, min_periods=200).mean()
    return ((closes > sma50) & (sma50 > sma200)).astype(float)


def _ema20_gt_ema50(closes: pd.DataFrame, highs: pd.DataFrame, lows: pd.DataFrame, volumes: pd.DataFrame, benchmark: pd.Series) -> pd.DataFrame:
    ema20 = closes.ewm(span=20, adjust=False, min_periods=20).mean()
    ema50 = closes.ewm(span=50, adjust=False, min_periods=50).mean()
    return ((closes > ema20) & (ema20 > ema50)).astype(float)


def _trend_magnitude_60(closes: pd.DataFrame, highs: pd.DataFrame, lows: pd.DataFrame, volumes: pd.DataFrame, benchmark: pd.Series) -> pd.DataFrame:
    return np.log(closes.div(closes.shift(60)))


def _multi_horizon_agreement(closes: pd.DataFrame, highs: pd.DataFrame, lows: pd.DataFrame, volumes: pd.DataFrame, benchmark: pd.Series) -> pd.DataFrame:
    r20 = closes.pct_change(20)
    r60 = closes.pct_change(60)
    r120 = closes.pct_change(120)
    return ((r20 > 0).astype(int) + (r60 > 0).astype(int) + (r120 > 0).astype(int)).astype(float)


def _consecutive_relative_outperformance(closes: pd.DataFrame, highs: pd.DataFrame, lows: pd.DataFrame, volumes: pd.DataFrame, benchmark: pd.Series) -> pd.DataFrame:
    rel = closes.pct_change().sub(benchmark.pct_change(), axis=0)
    rolling = rel.gt(0).rolling(20, min_periods=20).sum()
    return rolling.astype(float)


def _persistent_directional_agreement(closes: pd.DataFrame, highs: pd.DataFrame, lows: pd.DataFrame, volumes: pd.DataFrame, benchmark: pd.Series) -> pd.DataFrame:
    ema20 = closes.ewm(span=20, adjust=False, min_periods=20).mean()
    ema50 = closes.ewm(span=50, adjust=False, min_periods=50).mean()
    ema200 = closes.ewm(span=200, adjust=False, min_periods=200).mean()
    return ((closes > ema20).astype(int) + (ema20 > ema50).astype(int) + (ema50 > ema200).astype(int)).astype(float)


def _trend_efficiency_60(closes: pd.DataFrame, highs: pd.DataFrame, lows: pd.DataFrame, volumes: pd.DataFrame, benchmark: pd.Series) -> pd.DataFrame:
    net = closes.div(closes.shift(60)).sub(1.0).abs()
    path = closes.pct_change().abs().rolling(60, min_periods=60).sum()
    return net.div(path.replace(0, np.nan))


def _noise_adjusted_trend_60(closes: pd.DataFrame, highs: pd.DataFrame, lows: pd.DataFrame, volumes: pd.DataFrame, benchmark: pd.Series) -> pd.DataFrame:
    trend = _trend_magnitude_60(closes, highs, lows, volumes, benchmark)
    vol = closes.pct_change().rolling(60, min_periods=60).std()
    return trend.div(vol.replace(0, np.nan))


def _composite_trend_score(closes: pd.DataFrame, highs: pd.DataFrame, lows: pd.DataFrame, volumes: pd.DataFrame, benchmark: pd.Series) -> pd.DataFrame:
    direction = _ema50_gt_ema200(closes, highs, lows, volumes, benchmark)
    strength = _trend_magnitude_60(closes, highs, lows, volumes, benchmark)
    persistence = _multi_horizon_agreement(closes, highs, lows, volumes, benchmark)
    smoothness = _trend_efficiency_60(closes, highs, lows, volumes, benchmark)
    return _percentile_aggregate([direction, strength, persistence, smoothness])


def _weighted_trend_composite(closes: pd.DataFrame, highs: pd.DataFrame, lows: pd.DataFrame, volumes: pd.DataFrame, benchmark: pd.Series) -> pd.DataFrame:
    direction = _ema50_gt_ema200(closes, highs, lows, volumes, benchmark)
    strength = _noise_adjusted_trend_60(closes, highs, lows, volumes, benchmark)
    persistence = _consecutive_relative_outperformance(closes, highs, lows, volumes, benchmark)
    smoothness = _trend_efficiency_60(closes, highs, lows, volumes, benchmark)
    return direction.mul(0.25).add(_rank_frame(strength).mul(0.25)).add(_rank_frame(persistence).mul(0.25)).add(_rank_frame(smoothness).mul(0.25))


def _rank_frame(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.rank(axis=1, method="average", pct=True)


def _percentile_aggregate(frames: list[pd.DataFrame]) -> pd.DataFrame:
    ranks = [_rank_frame(frame) for frame in frames]
    return sum(ranks).div(len(ranks))


def _compare(
    closes: pd.DataFrame,
    highs: pd.DataFrame,
    lows: pd.DataFrame,
    volumes: pd.DataFrame,
    benchmark: pd.Series,
    production_gate_wide: pd.DataFrame,
    comparator: Comparator,
    start: str,
    end: str,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    scores = comparator.score_builder(closes, highs, lows, volumes, benchmark)
    if not isinstance(scores, pd.DataFrame):
        raise TypeError("Comparator score builder must return a DataFrame.")

    daily_rows = []
    selected_ranks = []
    benchmark_close = benchmark.reindex(closes.index).ffill()
    benchmark_return60 = benchmark_close.pct_change(60)
    dates = production_gate_wide.loc[start:end].index.intersection(scores.index)

    for date in dates:
        prod_row = production_gate_wide.loc[date]
        score_row = scores.loc[date]
        frame = pd.DataFrame({
            "ticker": score_row.index,
            "production_gate": prod_row.reindex(score_row.index),
            "score": score_row,
        }).dropna(subset=["production_gate", "score"])
        if len(frame) < 30:
            continue
        frame = frame.sort_values("ticker").reset_index(drop=True)
        frame["production_gate"] = frame["production_gate"].astype(bool)
        frame["comparator_percentile"] = frame["score"].rank(method="first", pct=True)
        frame["comparator_signal"] = frame["comparator_percentile"] > 0.90
        production_count = int(frame["production_gate"].sum())
        comparator_count = int(frame["comparator_signal"].sum())
        overlap = int((frame["production_gate"] & frame["comparator_signal"]).sum())
        union = production_count + comparator_count - overlap
        regime = "SPY_60D_POSITIVE" if benchmark_return60.loc[date] > 0 else "SPY_60D_NONPOSITIVE"
        spearman = _spearman(frame["production_gate"].astype(float), frame["score"])
        daily_rows.append({
            "date": date,
            "year": date.year,
            "market_regime": regime,
            "candidate_count": len(frame),
            "production_gate_count": production_count,
            "comparator_signal_count": comparator_count,
            "overlap_count": overlap,
            "union_count": union,
            "production_coverage_pct": production_count / len(frame) * 100,
            "comparator_coverage_pct": comparator_count / len(frame) * 100,
            "jaccard_similarity": overlap / union if union else np.nan,
            "precision_pct": overlap / production_count * 100 if production_count else np.nan,
            "recall_pct": overlap / comparator_count * 100 if comparator_count else np.nan,
            "mean_comparator_percentile_for_production_signals": frame.loc[frame.production_gate, "comparator_percentile"].mean(),
            "median_comparator_percentile_for_production_signals": frame.loc[frame.production_gate, "comparator_percentile"].median(),
            "share_of_production_signals_in_top_decile": (frame.loc[frame.production_gate, "comparator_percentile"] > 0.90).mean() * 100 if production_count else np.nan,
            "share_of_production_signals_below_median": (frame.loc[frame.production_gate, "comparator_percentile"] <= 0.50).mean() * 100 if production_count else np.nan,
            "production_vs_score_spearman": spearman,
        })
        for value in frame.loc[frame.production_gate, "comparator_percentile"]:
            selected_ranks.append({
                "date": date,
                "year": date.year,
                "market_regime": regime,
                "comparator_percentile": value,
            })

    return pd.DataFrame(daily_rows), pd.DataFrame(selected_ranks), pd.Series(dtype=float)


def _comparator_matrix_row(comparator: Comparator, daily: pd.DataFrame, selected_ranks: pd.DataFrame) -> dict:
    overall = _aggregate_daily(daily)
    values = selected_ranks["comparator_percentile"] if not selected_ranks.empty else pd.Series(dtype=float)
    return {
        "family": comparator.family,
        "comparator": comparator.name,
        "description": comparator.description,
        "date_count": int(overall["date_count"]),
        "candidate_observations": int(overall["candidate_observations"]),
        "production_signal_observations": int(overall["production_signal_observations"]),
        "comparator_signal_observations": int(overall["comparator_signal_observations"]),
        "overlap_observations": int(overall["overlap_observations"]),
        "union_observations": int(overall["union_observations"]),
        "jaccard_similarity": overall["jaccard_similarity"],
        "precision_pct": overall["precision_pct"],
        "recall_pct": overall["recall_pct"],
        "production_coverage_pct": overall["production_coverage_pct"],
        "comparator_coverage_pct": overall["comparator_coverage_pct"],
        "mean_daily_spearman": overall["mean_daily_spearman"],
        "median_daily_spearman": overall["median_daily_spearman"],
        "mean_selected_percentile": values.mean() if len(values) else np.nan,
        "median_selected_percentile": values.median() if len(values) else np.nan,
        "share_selected_in_top_decile_pct": (values > 0.90).mean() * 100 if len(values) else np.nan,
        "share_selected_below_median_pct": (values <= 0.50).mean() * 100 if len(values) else np.nan,
        "overlap_band": _overlap_band(overall["jaccard_similarity"]),
    }


def _aggregate_daily(daily: pd.DataFrame) -> dict:
    production = daily.production_gate_count.sum()
    comparator = daily.comparator_signal_count.sum()
    overlap = daily.overlap_count.sum()
    union = daily.union_count.sum()
    return {
        "date_count": len(daily),
        "candidate_observations": daily.candidate_count.sum(),
        "production_signal_observations": production,
        "comparator_signal_observations": comparator,
        "overlap_observations": overlap,
        "union_observations": union,
        "jaccard_similarity": overlap / union if union else np.nan,
        "precision_pct": overlap / production * 100 if production else np.nan,
        "recall_pct": overlap / comparator * 100 if comparator else np.nan,
        "production_coverage_pct": production / daily.candidate_count.sum() * 100 if daily.candidate_count.sum() else np.nan,
        "comparator_coverage_pct": comparator / daily.candidate_count.sum() * 100 if daily.candidate_count.sum() else np.nan,
        "mean_daily_spearman": daily.production_vs_score_spearman.mean(),
        "median_daily_spearman": daily.production_vs_score_spearman.median(),
    }


def _agreement_metrics(comparator: Comparator, daily: pd.DataFrame) -> list[dict]:
    rows = []
    groups = [("OVERALL", daily)]
    groups += [(f"YEAR:{year}", group) for year, group in daily.groupby("year")]
    groups += [(f"REGIME:{regime}", group) for regime, group in daily.groupby("market_regime")]
    for label, group in groups:
        if group.empty:
            continue
        production = group.production_gate_count.sum()
        comparator_signal = group.comparator_signal_count.sum()
        overlap = group.overlap_count.sum()
        union = group.union_count.sum()
        rows.append({
            "family": comparator.family,
            "comparator": comparator.name,
            "segment_type": "OVERALL" if label == "OVERALL" else ("YEAR" if label.startswith("YEAR:") else "REGIME"),
            "segment": label,
            "date_count": len(group),
            "candidate_observations": group.candidate_count.sum(),
            "production_signal_observations": production,
            "comparator_signal_observations": comparator_signal,
            "overlap_observations": overlap,
            "union_observations": union,
            "jaccard_similarity": overlap / union if union else np.nan,
            "precision_pct": overlap / production * 100 if production else np.nan,
            "recall_pct": overlap / comparator_signal * 100 if comparator_signal else np.nan,
            "mean_daily_spearman": group.production_vs_score_spearman.mean(),
            "median_daily_spearman": group.production_vs_score_spearman.median(),
            "overlap_band": _overlap_band(overlap / union if union else np.nan),
        })
    return rows


def _distribution_metrics(comparator: Comparator, selected_ranks: pd.DataFrame) -> list[dict]:
    if selected_ranks.empty:
        return []
    rows = []
    groups = [("OVERALL", selected_ranks)]
    groups += [(f"YEAR:{year}", group) for year, group in selected_ranks.groupby("year")]
    groups += [(f"REGIME:{regime}", group) for regime, group in selected_ranks.groupby("market_regime")]
    for label, group in groups:
        values = group.comparator_percentile
        rows.append({
            "family": comparator.family,
            "comparator": comparator.name,
            "segment": label,
            "observation_count": len(values),
            "mean_comparator_percentile": values.mean(),
            "median_comparator_percentile": values.median(),
            "p25_comparator_percentile": values.quantile(0.25),
            "p75_comparator_percentile": values.quantile(0.75),
            "share_in_top_decile_pct": (values > 0.90).mean() * 100,
            "share_below_median_pct": (values <= 0.50).mean() * 100,
        })
    return rows


def _family_matrix(comparator_rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(comparator_rows)
    rows = []
    for family, group in df.groupby("family"):
        best = group.sort_values(["jaccard_similarity", "precision_pct", "recall_pct"], ascending=False).iloc[0]
        rows.append({
            "row_type": "FAMILY",
            "family": family,
            "comparator": "FAMILY_AGGREGATE",
            "description": f"Aggregate across predefined {family} comparators",
            "comparator_count": len(group),
            "date_count": int(group.date_count.mean()),
            "candidate_observations": int(group.candidate_observations.mean()),
            "production_signal_observations": int(group.production_signal_observations.mean()),
            "comparator_signal_observations": int(group.comparator_signal_observations.mean()),
            "overlap_observations": int(group.overlap_observations.mean()),
            "union_observations": int(group.union_observations.mean()),
            "jaccard_similarity": group.jaccard_similarity.mean(),
            "precision_pct": group.precision_pct.mean(),
            "recall_pct": group.recall_pct.mean(),
            "production_coverage_pct": group.production_coverage_pct.mean(),
            "comparator_coverage_pct": group.comparator_coverage_pct.mean(),
            "mean_daily_spearman": group.mean_daily_spearman.mean(),
            "median_daily_spearman": group.median_daily_spearman.mean(),
            "mean_selected_percentile": group.mean_selected_percentile.mean(),
            "median_selected_percentile": group.median_selected_percentile.mean(),
            "share_selected_in_top_decile_pct": group.share_selected_in_top_decile_pct.mean(),
            "share_selected_below_median_pct": group.share_selected_below_median_pct.mean(),
            "overlap_band": _overlap_band(group.jaccard_similarity.mean()),
            "best_comparator": best.comparator,
            "best_comparator_jaccard": best.jaccard_similarity,
            "best_comparator_precision": best.precision_pct,
            "best_comparator_recall": best.recall_pct,
        })
    for _, row in df.iterrows():
        rows.append({"row_type": "COMPARATOR", **row.to_dict()})
    result = pd.DataFrame(rows)
    return result.sort_values(["row_type", "family", "jaccard_similarity"], ascending=[True, True, False]).reset_index(drop=True)


def _family_summary(family_matrix: pd.DataFrame) -> pd.DataFrame:
    families = family_matrix.loc[family_matrix.row_type == "FAMILY"].copy()
    families["rank_by_jaccard"] = families["jaccard_similarity"].rank(ascending=False, method="min").astype(int)
    families["rank_by_precision"] = families["precision_pct"].rank(ascending=False, method="min").astype(int)
    families["rank_by_recall"] = families["recall_pct"].rank(ascending=False, method="min").astype(int)
    families = families.sort_values(["rank_by_jaccard", "family"])
    return families[[
        "family", "comparator_count", "jaccard_similarity", "precision_pct", "recall_pct",
        "mean_daily_spearman", "mean_selected_percentile", "share_selected_in_top_decile_pct",
        "best_comparator", "best_comparator_jaccard", "best_comparator_precision", "best_comparator_recall",
        "rank_by_jaccard", "rank_by_precision", "rank_by_recall", "overlap_band",
    ]]


def _overlap_band(jaccard: float) -> str:
    if pd.isna(jaccard):
        return "UNAVAILABLE"
    if jaccard >= 0.50:
        return "HIGH_DESCRIPTIVE_OVERLAP"
    if jaccard >= 0.20:
        return "MODERATE_DESCRIPTIVE_OVERLAP"
    return "LOW_DESCRIPTIVE_OVERLAP"


def _spearman(left: pd.Series, right: pd.Series) -> float:
    ranked = pd.DataFrame({"left": left, "right": right}).rank(method="average")
    return ranked.left.corr(ranked.right)


def _write_reports(
    output: Path,
    args: argparse.Namespace,
    universe: list[str],
    completed: list[str],
    errors: list[dict],
    family_matrix: pd.DataFrame,
    family_summary: pd.DataFrame,
) -> None:
    top_family = family_summary.iloc[0]
    top_family_name = top_family.family
    top_construct = top_family.best_comparator
    lines = [
        f"# {STUDY_ID}: Trend Construct Mapping",
        "",
        "## Scope",
        "This is a descriptive trend-construct mapping study. No strategy was run, no trade outcomes were read, and no return, alpha, profitability, risk, or optimisation statistic was calculated.",
        "",
        "## Pre-specified trend constructs",
        "The comparator list was fixed before execution and grouped into Direction, Strength, Persistence, Smoothness, and Composite families.",
        "",
        "## Study design",
        f"- **Production gate:** `{PRODUCTION_RULE}`.",
        f"- **Analysis window:** {args.start} through {args.end}, with price warmup from {args.warmup_start}.",
        "- **Universe:** current S&P 500 constituent file fixed before execution; SPY is excluded from candidate ranking because production bypasses its own relative-strength check for the benchmark.",
        "- **Comparator policy:** all trend comparators were predefined before execution and evaluated under identical dates, securities, and preprocessing.",
        "",
        "## Family-level descriptive result",
        family_summary.to_string(index=False),
        "",
        "## Interpretation",
        f"The family with the highest mean Jaccard similarity is **{top_family_name}**. Within that family, the best-matching predefined comparator is **{top_construct}**.",
        "This is a descriptive construct-mapping result only. It does not compare trading performance, validate or invalidate the production strategy, establish economic value, or establish causality.",
        "",
        "## Data quality",
        f"- Candidate securities: {len(universe):,}",
        f"- Successfully downloaded: {len(completed):,}",
        f"- Failed: {len(errors):,}",
    ]
    (output / "tcm001_trend_mapping.md").write_text("\n".join(lines), encoding="utf-8")
    (output / "trend_family_comparison.md").write_text(
        "# Trend Family Comparison\n\n" +
        family_summary.to_string(index=False) +
        "\n\nThe ranking uses mean Jaccard similarity as the primary descriptive criterion, with precision and recall as tie-breakers for the best comparator inside each family.",
        encoding="utf-8",
    )
    (output / "construct_interpretation.md").write_text(
        f"# Construct Interpretation\n\nThe current production Relative Strength gate most closely resembles the {top_family_name} family in this fixed comparator set, and the best-matching comparator is {top_construct}. This is a descriptive mapping statement only and does not imply predictive or economic value.",
        encoding="utf-8",
    )
    (output / "limitations.md").write_text(
        f"""# Limitations

- The universe is the current S&P 500 constituent list, not a survivorship-free historical constituent universe.
- {len(completed):,} of {len(universe):,} candidate securities downloaded successfully; {len(errors):,} did not.
- Historical sector/industry classifications were not available in the project, so sector agreement was not evaluated.
- The production gate is defined relative to SPY. Alternative benchmark definitions were not introduced because that would define a different gate rather than describe the frozen production one.
- Yahoo Finance adjusted-data conventions, delistings, and ticker-history availability can affect the eligible daily cross-section.
- This study evaluates signal-set overlap only. It intentionally contains no performance, outcome, trade, or causal analysis.
""",
        encoding="utf-8",
    )
    (output / "executive_summary.md").write_text(
        f"""# TCM-001 Executive Summary

TCM-001 compared the frozen production SPY-relative Relative Strength gate against a fixed set of predefined Trend constructs on identical valid securities and dates. The study uses descriptive agreement metrics only.

**Best-matching family by mean Jaccard similarity:** {top_family_name}
**Best-matching comparator within that family:** {top_construct}

No returns, trading performance, optimisation, or production recommendation is included.
""",
        encoding="utf-8",
    )
    manifest = {
        "study_id": STUDY_ID,
        "production_rule": PRODUCTION_RULE,
        "universe_file": str(args.universe),
        "analysis_start": args.start,
        "analysis_end": args.end,
        "warmup_start": args.warmup_start,
        "candidate_symbols": len(universe),
        "completed_symbols": len(completed),
        "failed_symbols": len(errors),
        "comparators_pre_registered": True,
        "no_backtest_or_outcome_analysis": True,
    }
    (output / "tcm001_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
