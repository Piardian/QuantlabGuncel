"""PV-001: predictive validation for the identified trend-related construct.

This study is descriptive and preregistered. It does not run a backtest,
does not tune thresholds, and does not search for a better trading rule.

Input:
    A merged trade journal containing entry-time trend features and realized
    trade outcomes.

Output:
    A set of reproducibility-oriented predictive validation reports.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "research_runs" / "2026-07-20_SP500_CURRENT_DAILY_LEADERSHIP_V1_CORRECT" / "merged_trades.csv"
DEFAULT_OUTPUT_DIR = ROOT / "research" / "program_reports" / "pv_001"

ANALYSIS_START = pd.Timestamp("2010-01-01")
ANALYSIS_END = pd.Timestamp("2026-01-01")
MIN_TRAIN_TRADES = 100
BOOTSTRAP_ITERATIONS = 300
PERMUTATION_ITERATIONS = 300
SEED = 20260728

PRIMARY_COMPONENTS = [
    "ema50_slope",
    "ema200_slope",
    "distance_above_ema50",
    "distance_above_ema200",
    "rs20",
    "rs60",
    "rs120",
    "atr_percent",
    "daily_range_percent",
]

SECONDARY_COMPONENTS = [
    "rs20",
    "rs60",
    "rs120",
]


@dataclass(frozen=True)
class FoldResult:
    year: int
    score_variant: str
    trade_count: int
    win_rate_pct: float
    avg_R: float
    median_R: float
    auc: float
    ic: float
    top_decile_trade_count: int
    top_decile_win_rate_pct: float
    top_decile_avg_R: float
    bottom_decile_trade_count: int
    bottom_decile_win_rate_pct: float
    bottom_decile_avg_R: float
    lift_avg_R: float
    calibration_slope: float
    calibration_monotonicity: float


def main() -> None:
    args = _parse_args()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    trades = _load_trades(args.trades)
    trade_predictions, fold_summaries, protocol_summary = _run_walk_forward(trades)

    predictive_metrics = _build_predictive_metrics(fold_summaries)
    predictive_metrics.to_csv(output_dir / "predictive_metrics.csv", index=False)

    ci = _build_confidence_intervals(trade_predictions)
    ci.to_csv(output_dir / "confidence_intervals.csv", index=False)

    stat_report = _build_statistical_tests(trade_predictions)
    (output_dir / "statistical_tests.md").write_text(stat_report, encoding="utf-8")

    effect_report = _build_effect_size_report(trade_predictions)
    (output_dir / "effect_size_analysis.md").write_text(effect_report, encoding="utf-8")

    protocol_report = _build_protocol_report(protocol_summary, trades)
    (output_dir / "evaluation_protocol.md").write_text(protocol_report, encoding="utf-8")

    limitation_report = _build_limitations_report(trades, trade_predictions)
    (output_dir / "limitations.md").write_text(limitation_report, encoding="utf-8")

    summary = _build_executive_summary(trade_predictions, ci)
    (output_dir / "executive_summary.md").write_text(summary, encoding="utf-8")

    main_report = _build_main_report(trade_predictions, ci)
    (output_dir / "pv001_predictive_validation.md").write_text(main_report, encoding="utf-8")

    _write_supporting_csvs(output_dir, trade_predictions)
    print(output_dir / "pv001_predictive_validation.md")
    print(output_dir / "evaluation_protocol.md")
    print(output_dir / "statistical_tests.md")
    print(output_dir / "predictive_metrics.csv")
    print(output_dir / "confidence_intervals.csv")
    print(output_dir / "effect_size_analysis.md")
    print(output_dir / "limitations.md")
    print(output_dir / "executive_summary.md")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PV-001 predictive validation")
    parser.add_argument("--trades", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def _load_trades(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame["entry_time"] = pd.to_datetime(frame["entry_time"], errors="coerce")
    frame["exit_time"] = pd.to_datetime(frame["exit_time"], errors="coerce")
    numeric_columns = [
        "entry_price",
        "exit_price",
        "stop_loss",
        "take_profit",
        "position_size",
        "pnl_dollars",
        "pnl_percent",
        "R_multiple",
        "trade_duration_bars",
        "ema50_slope",
        "ema200_slope",
        "distance_above_ema50",
        "distance_above_ema200",
        "rs20",
        "rs60",
        "rs120",
        "atr14",
        "atr_percent",
        "daily_range_percent",
        "true_range",
        "breakout_distance",
        "previous_20_bar_high",
        "days_since_last_breakout",
        "volume",
        "average_volume20",
        "relative_volume",
        "spy_return60",
        "entry_atr",
        "initial_risk",
        "holding_days",
        "mae",
        "mfe",
    ]
    for column in numeric_columns:
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.loc[(frame["entry_time"] >= ANALYSIS_START) & (frame["entry_time"] < ANALYSIS_END)].copy()
    frame["entry_year"] = frame["entry_time"].dt.year
    frame["binary_win"] = (frame["R_multiple"] > 0).astype(int)
    frame["stock_return60"] = frame["rs60"] + frame["spy_return60"]
    return frame.reset_index(drop=True)


def _run_walk_forward(trades: pd.DataFrame) -> tuple[pd.DataFrame, list[dict[str, object]], dict[str, object]]:
    years = sorted(int(year) for year in trades["entry_year"].dropna().unique())
    predictions: list[pd.DataFrame] = []
    fold_summaries: list[dict[str, object]] = []

    for year in years:
        train = trades[trades["entry_year"] < year].copy()
        test = trades[trades["entry_year"] == year].copy()
        if len(train) < MIN_TRAIN_TRADES or test.empty:
            continue

        train = _prepare_model_frame(train)
        test = _prepare_model_frame(test)

        primary, primary_rows = _score_fold(train, test, PRIMARY_COMPONENTS, score_name="COMPOSITE_TREND_PROXY")
        secondary, secondary_rows = _score_fold(train, test, SECONDARY_COMPONENTS, score_name="TREND_STRENGTH_PROXY")
        predictions.append(primary)
        predictions.append(secondary)

        for score_name, rows in [
            ("COMPOSITE_TREND_PROXY", primary_rows),
            ("TREND_STRENGTH_PROXY", secondary_rows),
        ]:
            if rows:
                summary_row = dict(rows[-1])
                summary_row.update(
                    {
                        "year": year,
                        "score_variant": score_name,
                        "train_trade_count": int(len(train)),
                        "test_trade_count": int(len(test)),
                        "train_year_span": f"{int(train['entry_year'].min())}-{year - 1}",
                    }
                )
                fold_summaries.append(summary_row)

    if not predictions:
        raise RuntimeError("PV-001 produced no predictive folds. Check the trade dataset and minimum training threshold.")

    combined = pd.concat(predictions, ignore_index=True)
    summary = {
        "years_evaluated": sorted({row["year"] for row in fold_summaries}),
        "folds": fold_summaries,
        "trade_count": int(len(combined)),
        "analysis_years": years,
    }
    return combined, fold_summaries, summary


def _prepare_model_frame(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    required = [
        "ema50_slope",
        "ema200_slope",
        "distance_above_ema50",
        "distance_above_ema200",
        "rs20",
        "rs60",
        "rs120",
        "atr_percent",
        "daily_range_percent",
        "stock_return60",
        "R_multiple",
    ]
    result = result.dropna(subset=required).copy()
    return result


def _score_fold(train: pd.DataFrame, test: pd.DataFrame, components: list[str], score_name: str) -> tuple[pd.DataFrame, list[dict[str, object]]]:
    stats = _fit_statistics(train, components + ["stock_return60"])
    scored = test.copy()
    for component in components:
        scored[f"{component}__z"] = _zscore(scored[component], stats[component]["mean"], stats[component]["std"])
    scored["stock_return60__z"] = _zscore(scored["stock_return60"], stats["stock_return60"]["mean"], stats["stock_return60"]["std"])

    if score_name == "COMPOSITE_TREND_PROXY":
        scored["direction_score"] = scored[[f"{c}__z" for c in ["ema50_slope", "ema200_slope", "distance_above_ema50", "distance_above_ema200"]]].mean(axis=1)
        scored["strength_score"] = scored["stock_return60__z"]
        scored["persistence_score"] = scored[[f"{c}__z" for c in ["rs20", "rs60", "rs120"]]].mean(axis=1)
        scored["smoothness_score"] = scored[[f"{c}__z" for c in ["atr_percent", "daily_range_percent"]]].mean(axis=1) * -1.0
        scored["score"] = scored[["direction_score", "strength_score", "persistence_score", "smoothness_score"]].mean(axis=1)
    elif score_name == "TREND_STRENGTH_PROXY":
        scored["score"] = scored[[f"{c}__z" for c in ["rs20", "rs60", "rs120"]]].mean(axis=1)
    else:
        raise ValueError(f"Unknown score variant: {score_name}")

    scored["score_variant"] = score_name
    scored["segment_type"] = "YEAR"
    scored["segment"] = scored["entry_year"].astype(int).map(lambda year: f"YEAR_{year}")
    scored["predicted_rank"] = scored["score"].rank(method="average", pct=True)
    scored["predicted_bucket"] = pd.cut(
        scored["predicted_rank"],
        bins=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
        labels=["LOWEST_20", "20_40", "40_60", "60_80", "TOP_20"],
        include_lowest=True,
        right=True,
    )

    rows = []
    for _, group in scored.groupby("entry_year", sort=True):
        rows.append(_summarize_segment(group, score_name, f"YEAR_{int(group['entry_year'].iloc[0])}", "YEAR"))
    overall = _summarize_segment(scored, score_name, "OVERALL_OOS", "OVERALL")
    rows.append(overall)
    scored = scored.assign(score_variant=score_name)
    scored["segment_summary"] = scored["entry_year"].map(lambda y: f"YEAR_{int(y)}")
    scored["overall_segment"] = "OVERALL_OOS"
    return scored, rows


def _fit_statistics(frame: pd.DataFrame, columns: list[str]) -> dict[str, dict[str, float]]:
    stats: dict[str, dict[str, float]] = {}
    for column in columns:
        series = pd.to_numeric(frame[column], errors="coerce")
        std = float(series.std(ddof=1))
        if not np.isfinite(std) or std == 0:
            std = 1.0
        stats[column] = {"mean": float(series.mean()), "std": std}
    return stats


def _zscore(values: pd.Series, mean: float, std: float) -> pd.Series:
    std = 1.0 if std == 0 or not np.isfinite(std) else std
    return (pd.to_numeric(values, errors="coerce") - mean) / std


def _summarize_segment(frame: pd.DataFrame, score_variant: str, segment: str, segment_type: str) -> dict[str, object]:
    r = pd.to_numeric(frame["R_multiple"], errors="coerce").dropna()
    score = pd.to_numeric(frame["score"], errors="coerce").dropna()
    binary = pd.to_numeric(frame["binary_win"], errors="coerce").dropna()
    top = _top_bottom_slice(frame, high=True, pct=0.10)
    bottom = _top_bottom_slice(frame, high=False, pct=0.10)
    bucket_means = _bucket_profile(frame)
    auc = _auc(binary, score)
    ic = _spearman(score, r)
    return {
        "score_variant": score_variant,
        "segment_type": segment_type,
        "segment": segment,
        "trade_count": int(len(frame)),
        "win_rate_pct": float(binary.mean() * 100.0) if len(binary) else np.nan,
        "avg_R": float(r.mean()) if len(r) else np.nan,
        "median_R": float(r.median()) if len(r) else np.nan,
        "auc": auc,
        "ic": ic,
        "top_decile_trade_count": int(len(top)),
        "top_decile_win_rate_pct": float((top["binary_win"] > 0).mean() * 100.0) if len(top) else np.nan,
        "top_decile_avg_R": float(pd.to_numeric(top["R_multiple"], errors="coerce").mean()) if len(top) else np.nan,
        "bottom_decile_trade_count": int(len(bottom)),
        "bottom_decile_win_rate_pct": float((bottom["binary_win"] > 0).mean() * 100.0) if len(bottom) else np.nan,
        "bottom_decile_avg_R": float(pd.to_numeric(bottom["R_multiple"], errors="coerce").mean()) if len(bottom) else np.nan,
        "lift_avg_R": float(pd.to_numeric(top["R_multiple"], errors="coerce").mean() - pd.to_numeric(bottom["R_multiple"], errors="coerce").mean()) if len(top) and len(bottom) else np.nan,
        "calibration_slope": bucket_means["calibration_slope"],
        "calibration_monotonicity": bucket_means["calibration_monotonicity"],
    }


def _bucket_profile(frame: pd.DataFrame) -> dict[str, float]:
    if frame.empty:
        return {"calibration_slope": np.nan, "calibration_monotonicity": np.nan}
    temp = frame.copy()
    temp["bucket"] = pd.qcut(temp["predicted_rank"], q=5, labels=False, duplicates="drop")
    grouped = temp.groupby("bucket", observed=True)["binary_win"].mean().sort_index()
    if len(grouped) < 2:
        return {"calibration_slope": np.nan, "calibration_monotonicity": np.nan}
    x = np.arange(len(grouped), dtype=float)
    y = grouped.to_numpy(dtype=float)
    slope = float(np.polyfit(x, y, deg=1)[0])
    monotonic = float((np.diff(y) > -1e-12).mean())
    return {"calibration_slope": slope, "calibration_monotonicity": monotonic}


def _top_bottom_slice(frame: pd.DataFrame, high: bool, pct: float) -> pd.DataFrame:
    if frame.empty:
        return frame.iloc[0:0].copy()
    ranked = frame.sort_values("score", ascending=not high)
    n = max(1, int(math.ceil(len(ranked) * pct)))
    return ranked.head(n).copy()


def _auc(y: pd.Series, score: pd.Series) -> float:
    values = pd.DataFrame({"y": y, "score": score}).dropna()
    if values.empty:
        return np.nan
    positives = int(values["y"].sum())
    negatives = len(values) - positives
    if positives == 0 or negatives == 0:
        return np.nan
    ranks = values["score"].rank(method="average")
    u = ranks[values["y"] == 1].sum() - positives * (positives + 1) / 2.0
    return float(u / (positives * negatives))


def _spearman(left: pd.Series, right: pd.Series) -> float:
    values = pd.DataFrame({"left": left, "right": right}).dropna()
    if len(values) < 3:
        return np.nan
    ranked = values.rank(method="average")
    return float(ranked["left"].corr(ranked["right"]))


def _build_predictive_metrics(rows: list[dict[str, object]]) -> pd.DataFrame:
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    frame = frame.sort_values(["score_variant", "segment_type", "segment"]).reset_index(drop=True)
    return frame


def _build_confidence_intervals(trades: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for score_variant in trades["score_variant"].unique():
        subset = trades[trades["score_variant"] == score_variant].copy()
        overall = _summarize_segment(subset, score_variant, "OVERALL_OOS", "OVERALL")
        years = sorted(subset["entry_year"].dropna().astype(int).unique())
        year_groups = [subset[subset["entry_year"] == year].copy() for year in years]
        rows.extend(_bootstrap_rows(score_variant, overall, year_groups))
    return pd.DataFrame(rows)


def _bootstrap_rows(score_variant: str, observed: dict[str, object], year_groups: list[pd.DataFrame]) -> list[dict[str, object]]:
    rng = np.random.default_rng(SEED)
    metrics = ["auc", "ic", "lift_avg_R", "calibration_slope", "top_decile_avg_R", "bottom_decile_avg_R"]
    samples = {metric: [] for metric in metrics}
    if not year_groups:
        return []

    for _ in range(BOOTSTRAP_ITERATIONS):
        sampled = [year_groups[idx] for idx in rng.integers(0, len(year_groups), size=len(year_groups))]
        boot = pd.concat(sampled, ignore_index=True)
        summary = _summarize_segment(boot, score_variant, "BOOTSTRAP", "BOOTSTRAP")
        for metric in metrics:
            samples[metric].append(float(summary[metric]))

    for metric in metrics:
        values = np.asarray(samples[metric], dtype=float)
        rows = {
            "score_variant": score_variant,
            "metric": metric,
            "estimate": float(observed[metric]),
            "ci_low": float(np.nanquantile(values, 0.025)),
            "ci_high": float(np.nanquantile(values, 0.975)),
            "bootstrap_method": "year_cluster",
            "iterations": BOOTSTRAP_ITERATIONS,
        }
        yield rows


def _build_statistical_tests(trades: pd.DataFrame) -> str:
    lines = [
        "# Statistical Tests",
        "",
        "This section reports preregistered, descriptive predictive-validation tests only.",
        "No threshold tuning or model selection was performed.",
        "",
    ]
    for score_variant in trades["score_variant"].unique():
        subset = trades[trades["score_variant"] == score_variant].copy()
        observed = _summarize_segment(subset, score_variant, "OVERALL_OOS", "OVERALL")
        years = sorted(subset["entry_year"].dropna().astype(int).unique())
        year_groups = [subset[subset["entry_year"] == year].copy() for year in years]
        perm = _permutation_test(year_groups, score_variant)
        positive_years = int((subset.groupby("entry_year").apply(lambda g: _spearman(g["score"], g["R_multiple"]) > 0)).sum())
        total_years = int(subset["entry_year"].nunique())
        lines.extend([
            f"## {score_variant}",
            "",
            f"- Overall OOS AUC: {observed['auc']:.4f}",
            f"- Overall OOS rank IC: {observed['ic']:.4f}",
            f"- Overall OOS lift in mean R (top decile minus bottom decile): {observed['lift_avg_R']:.4f}",
            f"- Permutation p-value for AUC > 0.5: {perm['auc_p_value']:.6f}",
            f"- Permutation p-value for rank IC > 0: {perm['ic_p_value']:.6f}",
            f"- Positive year-fold ICs: {positive_years}/{total_years}",
            f"- Sign-test p-value for yearly IC > 0: {perm['year_sign_p_value']:.6f}",
            "",
        ])
    return "\n".join(lines)


def _permutation_test(year_groups: list[pd.DataFrame], score_variant: str) -> dict[str, float]:
    rng = np.random.default_rng(SEED + 7)
    observed_auc = []
    observed_ic = []
    for group in year_groups:
        observed = _summarize_segment(group, score_variant, "PERMUTE_BASELINE", "PERMUTE_BASELINE")
        observed_auc.append(float(observed["auc"]))
        observed_ic.append(float(observed["ic"]))
    observed_auc_value = float(np.nanmean(observed_auc))
    observed_ic_value = float(np.nanmean(observed_ic))

    perm_auc = []
    perm_ic = []
    for _ in range(PERMUTATION_ITERATIONS):
        auc_parts = []
        ic_parts = []
        for group in year_groups:
            shuffled = group.copy()
            shuffled["score"] = rng.permutation(shuffled["score"].to_numpy())
            auc_parts.append(_auc(shuffled["binary_win"], shuffled["score"]))
            ic_parts.append(_spearman(shuffled["score"], shuffled["R_multiple"]))
        perm_auc.append(float(np.nanmean(auc_parts)))
        perm_ic.append(float(np.nanmean(ic_parts)))

    auc_p = (np.sum(np.asarray(perm_auc) >= observed_auc_value) + 1.0) / (len(perm_auc) + 1.0)
    ic_p = (np.sum(np.asarray(perm_ic) >= observed_ic_value) + 1.0) / (len(perm_ic) + 1.0)
    signs = np.array([1 if _spearman(group["score"], group["R_multiple"]) > 0 else 0 for group in year_groups if len(group) >= 3], dtype=int)
    year_sign_p = _binomial_one_sided_pvalue(int(signs.sum()), int(len(signs)))
    return {
        "auc_p_value": float(auc_p),
        "ic_p_value": float(ic_p),
        "year_sign_p_value": float(year_sign_p),
    }


def _binomial_one_sided_pvalue(k: int, n: int) -> float:
    if n == 0:
        return np.nan
    # One-sided p-value for observing at least k positives under p=0.5.
    total = 0.0
    for i in range(k, n + 1):
        total += math.comb(n, i) * (0.5 ** n)
    return float(total)


def _build_effect_size_report(trades: pd.DataFrame) -> str:
    lines = [
        "# Effect Size Analysis",
        "",
        "Effect sizes compare the top and bottom deciles of the preregistered OOS score distribution.",
        "",
    ]
    for score_variant in trades["score_variant"].unique():
        subset = trades[trades["score_variant"] == score_variant].copy()
        top = _top_bottom_slice(subset, high=True, pct=0.10)
        bottom = _top_bottom_slice(subset, high=False, pct=0.10)
        d = _cohens_d(top["R_multiple"], bottom["R_multiple"]) if len(top) and len(bottom) else np.nan
        delta = _cliffs_delta(top["R_multiple"], bottom["R_multiple"]) if len(top) and len(bottom) else np.nan
        rb = 2 * d / math.sqrt(d * d + 4) if pd.notna(d) else np.nan
        lines.extend([
            f"## {score_variant}",
            "",
            f"- Cohen's d (top decile R vs bottom decile R): {d:.4f}",
            f"- Cliff's delta: {delta:.4f}",
            f"- Rank-biserial correlation (approx.): {rb:.4f}",
            "",
        ])
    return "\n".join(lines)


def _cohens_d(left: pd.Series, right: pd.Series) -> float:
    left = pd.to_numeric(left, errors="coerce").dropna()
    right = pd.to_numeric(right, errors="coerce").dropna()
    if len(left) < 2 or len(right) < 2:
        return np.nan
    pooled = math.sqrt(((len(left) - 1) * left.var(ddof=1) + (len(right) - 1) * right.var(ddof=1)) / (len(left) + len(right) - 2))
    return float((left.mean() - right.mean()) / pooled) if pooled > 0 else 0.0


def _cliffs_delta(left: pd.Series, right: pd.Series) -> float:
    left = pd.to_numeric(left, errors="coerce").dropna().to_numpy()
    right = pd.to_numeric(right, errors="coerce").dropna().to_numpy()
    if len(left) == 0 or len(right) == 0:
        return np.nan
    more = sum((l > r) for l in left for r in right)
    less = sum((l < r) for l in left for r in right)
    return float((more - less) / (len(left) * len(right)))


def _build_protocol_report(summary: dict[str, object], trades: pd.DataFrame) -> str:
    return "\n".join(
        [
            "# Evaluation Protocol",
            "",
            "## Study Design",
            "- Objective: predictive validation of the identified trend-related construct.",
            "- No backtests were run and no parameters were tuned.",
            "- The study uses executed trades only, from the frozen production architecture.",
            "- Analysis window: 2010-01-01 through 2026-01-01.",
            "- OOS protocol: expanding-window, year-by-year walk-forward validation.",
            f"- Initial training requirement: at least {MIN_TRAIN_TRADES} trades before a year can be evaluated.",
            "",
            "## Construct Proxy",
            "Primary score: COMPOSITE_TREND_PROXY",
            "Components:",
            "- ema50_slope",
            "- ema200_slope",
            "- distance_above_ema50",
            "- distance_above_ema200",
            "- rs20",
            "- rs60",
            "- rs120",
            "- atr_percent (inverse smoothness contribution)",
            "- daily_range_percent (inverse smoothness contribution)",
            "",
            "Secondary sensitivity score: TREND_STRENGTH_PROXY (rs20/rs60/rs120 only).",
            "",
            "## Outcomes",
            "- Binary: R_multiple > 0",
            "- Continuous: R_multiple",
            "",
            "## Primary Predictive Metrics",
            "- ROC-AUC",
            "- Rank IC (Spearman)",
            "- Top-decile vs bottom-decile mean R lift",
            "- Calibration slope across quintiles",
            "- Year-by-year stability of sign and magnitude",
            "",
            "## Statistical Tests",
            "- Cluster bootstrap confidence intervals by year",
            "- Within-year permutation test for AUC and rank IC",
            "- One-sided sign test on yearly IC direction",
            "",
            "## Data Scope",
            f"- Trades analyzed: {len(trades):,}",
            f"- Symbols represented: {trades['ticker'].nunique():,}",
            f"- Entry years represented: {int(trades['entry_year'].min())} to {int(trades['entry_year'].max())}",
            "",
            "This protocol is fixed and was not altered after inspecting outcomes.",
        ]
    )


def _build_limitations_report(trades: pd.DataFrame, predictions: pd.DataFrame) -> str:
    return "\n".join(
        [
            "# Limitations",
            "",
            "- The study uses executed trades only, so it is still conditioned on prior selection by the production system.",
            "- The universe is the current research universe, not a fully survivorship-free historical constituent set.",
            "- The composite score is an observable proxy built from available entry-time fields; it is not the hidden internal comparator formula from TCM-001.",
            "- Year-level walk-forward reduces leakage, but trade outcomes remain serially dependent within symbols and market regimes.",
            "- No paper-trading or live-trading validation has been performed.",
            "- This study evaluates predictive validity only; it does not establish economic value or deployment readiness.",
            f"- Completed OOS predictions: {len(predictions):,} across {predictions['entry_year'].nunique():,} test years.",
            f"- Symbols represented in the merged journal: {trades['ticker'].nunique():,}.",
        ]
    )


def _build_executive_summary(trades: pd.DataFrame, ci: pd.DataFrame) -> str:
    primary = trades[trades["score_variant"] == "COMPOSITE_TREND_PROXY"].copy()
    overall = _summarize_segment(primary, "COMPOSITE_TREND_PROXY", "OVERALL_OOS", "OVERALL")
    auc_ci = ci[(ci["score_variant"] == "COMPOSITE_TREND_PROXY") & (ci["metric"] == "auc")].iloc[0]
    ic_ci = ci[(ci["score_variant"] == "COMPOSITE_TREND_PROXY") & (ci["metric"] == "ic")].iloc[0]
    return "\n".join(
        [
            "# PV-001 Executive Summary",
            "",
            "PV-001 tested whether the identified trend-related construct has reproducible predictive validity under a preregistered walk-forward protocol.",
            "",
            f"- OOS trade count: {len(primary):,}",
            f"- OOS AUC: {overall['auc']:.4f} (95% CI {auc_ci['ci_low']:.4f} to {auc_ci['ci_high']:.4f})",
            f"- OOS rank IC: {overall['ic']:.4f} (95% CI {ic_ci['ci_low']:.4f} to {ic_ci['ci_high']:.4f})",
            f"- OOS mean R lift top decile vs bottom decile: {overall['lift_avg_R']:.4f}",
            "",
            "Interpretation is limited to predictive validity. No economic or deployment conclusion is implied.",
        ]
    )


def _build_main_report(trades: pd.DataFrame, ci: pd.DataFrame) -> str:
    primary = trades[trades["score_variant"] == "COMPOSITE_TREND_PROXY"].copy()
    secondary = trades[trades["score_variant"] == "TREND_STRENGTH_PROXY"].copy()
    primary_overall = _summarize_segment(primary, "COMPOSITE_TREND_PROXY", "OVERALL_OOS", "OVERALL")
    secondary_overall = _summarize_segment(secondary, "TREND_STRENGTH_PROXY", "OVERALL_OOS", "OVERALL")
    return "\n".join(
        [
            "# PV-001 Predictive Validation",
            "",
            "## Question",
            "Does the identified trend-related construct demonstrate statistically credible predictive validity under the preregistered evaluation protocol?",
            "",
            "## Primary result",
            f"- Composite trend proxy OOS AUC: {primary_overall['auc']:.4f}",
            f"- Composite trend proxy OOS rank IC: {primary_overall['ic']:.4f}",
            f"- Composite trend proxy top-decile minus bottom-decile mean R: {primary_overall['lift_avg_R']:.4f}",
            f"- Composite trend proxy calibration slope: {primary_overall['calibration_slope']:.4f}",
            "",
            "## Sensitivity check",
            f"- Trend strength proxy OOS AUC: {secondary_overall['auc']:.4f}",
            f"- Trend strength proxy OOS rank IC: {secondary_overall['ic']:.4f}",
            f"- Trend strength proxy top-decile minus bottom-decile mean R: {secondary_overall['lift_avg_R']:.4f}",
            "",
            "## Confidence intervals",
            ci.to_string(index=False),
            "",
            "## Interpretation standard",
            "- Supported by evidence: the metric remains positive and stable OOS with non-trivial separation.",
            "- Not supported by evidence: the metric is near-null, unstable, or does not survive OOS.",
            "- Inconclusive: evidence is directionally positive but too small or too unstable for a firm conclusion.",
            "- Speculation: any statement beyond the observed OOS metrics and their uncertainty.",
            "",
            "## Current conclusion",
            _conclusion_text(primary_overall, secondary_overall),
        ]
    )


def _conclusion_text(primary: dict[str, object], secondary: dict[str, object]) -> str:
    primary_auc = float(primary["auc"])
    primary_ic = float(primary["ic"])
    primary_lift = float(primary["lift_avg_R"])
    years = int(pd.Series(primary["segment"]).str.startswith("YEAR_").sum()) if "segment" in primary else 0
    if primary_auc > 0.55 and primary_ic > 0.05 and primary_lift > 0:
        return (
            "Predictive validity is supported by evidence for the composite trend proxy, "
            "with a positive OOS ranking relationship and positive top-vs-bottom decile lift."
        )
    if primary_auc < 0.52 and primary_ic < 0.02:
        return (
            "Predictive validity is not supported by evidence for the composite trend proxy; "
            "the OOS separation is too weak to distinguish it from the null."
        )
    return (
        "Evidence is inconclusive: the composite trend proxy shows some OOS separation, "
        "but not enough stability or magnitude to justify a stronger claim."
    )


def _write_supporting_csvs(output_dir: Path, trades: pd.DataFrame) -> None:
    meta = {
        "study_id": "PV-001",
        "analysis_start": str(ANALYSIS_START.date()),
        "analysis_end": str(ANALYSIS_END.date()),
        "minimum_train_trades": MIN_TRAIN_TRADES,
        "bootstrap_iterations": BOOTSTRAP_ITERATIONS,
        "permutation_iterations": PERMUTATION_ITERATIONS,
        "input_trades": str(DEFAULT_INPUT),
        "oos_trade_rows": int(len(trades)),
    }
    (output_dir / "pv001_manifest.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
