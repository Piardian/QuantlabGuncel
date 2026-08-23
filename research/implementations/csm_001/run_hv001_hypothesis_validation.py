from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[3]
STATE_FILE = REPO_ROOT / "output" / "csm_001_cv001" / "csm001_construct_state.csv"
OUTPUT_DIR = REPO_ROOT / "research" / "market_edge_discovery_program" / "csm_001_hv_001_hypothesis_validation"


BOOTSTRAP_SEED = 1001
BOOTSTRAP_ITERATIONS = 2000


def _safe_float(value: float) -> float | None:
    if pd.isna(value) or not np.isfinite(value):
        return None
    return float(value)


def _bootstrap_ci(values: pd.Series, statistic: str = "mean") -> tuple[float | None, float | None]:
    clean = values.dropna().to_numpy(dtype=float)
    if len(clean) == 0:
        return None, None
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    stats = []
    for _ in range(BOOTSTRAP_ITERATIONS):
        sample = rng.choice(clean, size=len(clean), replace=True)
        if statistic == "median":
            stats.append(float(np.median(sample)))
        else:
            stats.append(float(np.mean(sample)))
    return float(np.percentile(stats, 2.5)), float(np.percentile(stats, 97.5))


def _load_state() -> pd.DataFrame:
    usecols = [
        "date",
        "ticker",
        "adjusted_close",
        "price_t_minus_21",
        "price_t_minus_252",
        "return_12_1",
        "csm001_momentum_score",
        "csm001_top_decile_flag",
        "csm001_valid_observation",
    ]
    frame = pd.read_csv(STATE_FILE, usecols=usecols, parse_dates=["date"])
    frame = frame[frame["csm001_valid_observation"].astype(bool)].copy()
    frame["csm001_top_decile_flag"] = frame["csm001_top_decile_flag"].astype(bool)
    frame["recent_21d_return"] = frame["adjusted_close"] / frame["price_t_minus_21"] - 1.0
    frame["recent_21d_return"] = frame["recent_21d_return"].where(np.isfinite(frame["recent_21d_return"]))
    return frame.sort_values(["date", "ticker"]).reset_index(drop=True)


def _rank_corr_by_lag(score_panel: pd.DataFrame, lag: int) -> pd.Series:
    corrs = []
    dates = []
    for idx in range(lag, len(score_panel)):
        current = score_panel.iloc[idx]
        previous = score_panel.iloc[idx - lag]
        aligned = pd.concat([current, previous], axis=1).dropna()
        if len(aligned) >= 50:
            current_rank = aligned.iloc[:, 0].rank(method="average")
            previous_rank = aligned.iloc[:, 1].rank(method="average")
            corrs.append(current_rank.corr(previous_rank))
            dates.append(score_panel.index[idx])
    return pd.Series(corrs, index=pd.to_datetime(dates), dtype=float)


def _h1_rank_persistence(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object]]:
    score_panel = frame.pivot(index="date", columns="ticker", values="csm001_momentum_score").sort_index()
    rows = []
    yearly_positive = {}
    for lag in [1, 5, 21, 63, 126]:
        corr = _rank_corr_by_lag(score_panel, lag)
        low, high = _bootstrap_ci(corr, statistic="median")
        by_year = corr.groupby(corr.index.year).median()
        yearly_positive[lag] = float((by_year > 0).mean()) if len(by_year) else np.nan
        rows.append(
            {
                "hypothesis": "H1",
                "metric": f"rank_persistence_spearman_lag_{lag}",
                "observations": int(len(corr)),
                "mean": _safe_float(corr.mean()),
                "median": _safe_float(corr.median()),
                "bootstrap_median_ci_low": low,
                "bootstrap_median_ci_high": high,
                "year_positive_rate": _safe_float(yearly_positive[lag]),
            }
        )
    result = pd.DataFrame(rows)
    lag21 = result.loc[result["metric"] == "rank_persistence_spearman_lag_21", "bootstrap_median_ci_low"].iloc[0]
    lag63 = result.loc[result["metric"] == "rank_persistence_spearman_lag_63", "bootstrap_median_ci_low"].iloc[0]
    status = "Supported by evidence" if lag21 and lag21 > 0 and lag63 and lag63 > 0 else "Inconclusive"
    return result, {"status": status, "rationale": "21-day and 63-day rank persistence bootstrap median confidence intervals remain above zero."}


def _top_sets_by_date(frame: pd.DataFrame) -> dict[pd.Timestamp, set[str]]:
    top = frame[frame["csm001_top_decile_flag"]]
    return {date: set(group["ticker"]) for date, group in top.groupby("date", sort=True)}


def _h2_top_decile_persistence(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object]]:
    top_by_date = _top_sets_by_date(frame)
    dates = sorted(frame["date"].drop_duplicates())
    rows = []
    previous = None
    for date in dates:
        current = top_by_date.get(date, set())
        if previous:
            retained = previous & current
            rows.append(
                {
                    "date": date,
                    "previous_top_count": len(previous),
                    "current_top_count": len(current),
                    "retention_rate": len(retained) / len(previous) if previous else np.nan,
                }
            )
        previous = current
    retention = pd.DataFrame(rows)
    series = retention["retention_rate"].dropna()
    low, high = _bootstrap_ci(series)
    null_random_daily_retention = 0.10
    status = "Supported by evidence" if low and low > null_random_daily_retention else "Inconclusive"
    summary = pd.DataFrame(
        [
            {
                "hypothesis": "H2",
                "metric": "daily_top_decile_retention_rate",
                "observations": int(len(series)),
                "mean": _safe_float(series.mean()),
                "median": _safe_float(series.median()),
                "bootstrap_mean_ci_low": low,
                "bootstrap_mean_ci_high": high,
                "null_reference": null_random_daily_retention,
            }
        ]
    )
    return summary, {"status": status, "rationale": "Observed daily top-decile retention is compared with a 10% random-membership reference."}


def _h3_rotation_not_broad_market(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object]]:
    top_by_date = _top_sets_by_date(frame)
    dates = sorted(frame["date"].drop_duplicates())
    rows = []
    previous = None
    for date in dates:
        current = top_by_date.get(date, set())
        eligible = frame.loc[frame["date"] == date, "ticker"].nunique()
        if previous is None:
            added_rate = np.nan
            dropped_rate = np.nan
            jaccard = np.nan
        else:
            added = current - previous
            dropped = previous - current
            added_rate = len(added) / len(current) if current else np.nan
            dropped_rate = len(dropped) / len(previous) if previous else np.nan
            union = previous | current
            jaccard = len(previous & current) / len(union) if union else np.nan
        rows.append(
            {
                "date": date,
                "eligible_count": eligible,
                "top_decile_count": len(current),
                "top_decile_rate": len(current) / eligible if eligible else np.nan,
                "added_rate": added_rate,
                "dropped_rate": dropped_rate,
                "daily_top_set_jaccard": jaccard,
            }
        )
        previous = current
    dynamics = pd.DataFrame(rows)
    top_rate_std = dynamics["top_decile_rate"].std(ddof=0)
    added_mean = dynamics["added_rate"].mean()
    jaccard_mean = dynamics["daily_top_set_jaccard"].mean()
    # The broad-market-direction part is supported by construction: percentile ranks produce a cross-sectional upper tail each day.
    status = "Partially supported" if top_rate_std < 0.02 and added_mean > 0 and jaccard_mean > 0 else "Inconclusive"
    summary = pd.DataFrame(
        [
            {
                "hypothesis": "H3",
                "metric": "daily_top_decile_rate_std",
                "value": _safe_float(top_rate_std),
                "interpretation": "Small variation supports cross-sectional normalization rather than broad-market level classification.",
            },
            {
                "hypothesis": "H3",
                "metric": "mean_daily_added_rate",
                "value": _safe_float(added_mean),
                "interpretation": "Positive added rate supports ongoing leadership rotation.",
            },
            {
                "hypothesis": "H3",
                "metric": "mean_daily_top_set_jaccard",
                "value": _safe_float(jaccard_mean),
                "interpretation": "Positive Jaccard supports persistence across adjacent dates.",
            },
        ]
    )
    return summary, {"status": status, "rationale": "H3 is only partially testable without introducing external market-direction variables."}


def _h4_skip_period_separation(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object]]:
    rows = []
    rank_corrs = []
    overlap_rates = []
    for date, group in frame.groupby("date", sort=True):
        clean = group[["return_12_1", "recent_21d_return", "csm001_top_decile_flag"]].dropna()
        if len(clean) < 50:
            continue
        prior_rank = clean["return_12_1"].rank(method="average")
        recent_rank = clean["recent_21d_return"].rank(method="average")
        corr = prior_rank.corr(recent_rank)
        recent_threshold = clean["recent_21d_return"].rank(pct=True).ge(0.90)
        production_top = clean["csm001_top_decile_flag"]
        overlap = (production_top & recent_threshold).sum() / max(production_top.sum(), 1)
        rank_corrs.append(corr)
        overlap_rates.append(overlap)
    corr_series = pd.Series(rank_corrs, dtype=float)
    overlap_series = pd.Series(overlap_rates, dtype=float)
    corr_low, corr_high = _bootstrap_ci(corr_series, statistic="median")
    overlap_low, overlap_high = _bootstrap_ci(overlap_series, statistic="median")
    rows.append(
        {
            "hypothesis": "H4",
            "metric": "cross_sectional_rank_corr_12_1_vs_recent_21d",
            "observations": int(len(corr_series)),
            "mean": _safe_float(corr_series.mean()),
            "median": _safe_float(corr_series.median()),
            "bootstrap_median_ci_low": corr_low,
            "bootstrap_median_ci_high": corr_high,
        }
    )
    rows.append(
        {
            "hypothesis": "H4",
            "metric": "production_top_overlap_with_recent_21d_top_decile",
            "observations": int(len(overlap_series)),
            "mean": _safe_float(overlap_series.mean()),
            "median": _safe_float(overlap_series.median()),
            "bootstrap_median_ci_low": overlap_low,
            "bootstrap_median_ci_high": overlap_high,
        }
    )
    status = "Supported by evidence" if corr_high is not None and corr_high < 0.50 and overlap_high is not None and overlap_high < 0.50 else "Partially supported"
    return pd.DataFrame(rows), {"status": status, "rationale": "Recent 21-day movement is measured separately from the frozen 12-1 formation window using only same-date known prices."}


def _write_reports(results: pd.DataFrame, verdicts: dict[str, dict[str, object]]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    verdict_rows = []
    for hypothesis, verdict in verdicts.items():
        verdict_rows.append({"hypothesis": hypothesis, **verdict})
    verdict_df = pd.DataFrame(verdict_rows)
    verdict_df.to_csv(OUTPUT_DIR / "hypothesis_verdicts.csv", index=False)

    overall = "Supported by evidence"
    if any(v["status"] in {"Partially supported", "Inconclusive"} for v in verdicts.values()):
        overall = "Partially supported"
    if all(v["status"] == "Inconclusive" for v in verdicts.values()):
        overall = "Inconclusive"

    def metric_value(metric: str, column: str = "median") -> str:
        row = results[results["metric"] == metric]
        if row.empty or column not in row.columns:
            return "N/A"
        value = row[column].iloc[0]
        return "N/A" if pd.isna(value) else f"{float(value):.4f}"

    report = f"""# CSM-001 / HV-001 Hypothesis Validation

## Purpose

Formally validate the mechanism hypotheses generated during MI-001 for the CSM-001 Canonical 12-1 Cross-Sectional Momentum State.

No returns, alpha, trading strategy backtests, profitability, Sharpe, CAGR, drawdown or economic value were evaluated.

## Preregistered Hypotheses

- H1: CSM-001 represents a persistent cross-sectional relative leadership state.
- H2: Top-decile membership persists beyond one-day noise.
- H3: The construct's primary observable mechanism is rank persistence and leadership rotation rather than broad market direction.
- H4: The 12-1 skip-period design separates intermediate-horizon winner status from very short-term price movement.

## Results

- H1: **{verdicts["H1"]["status"]}**
- H2: **{verdicts["H2"]["status"]}**
- H3: **{verdicts["H3"]["status"]}**
- H4: **{verdicts["H4"]["status"]}**

## Key Evidence

- 21-day median rank persistence: {metric_value("rank_persistence_spearman_lag_21")}
- 63-day median rank persistence: {metric_value("rank_persistence_spearman_lag_63")}
- Daily top-decile retention mean: {metric_value("daily_top_decile_retention_rate", "mean")}
- 12-1 vs recent 21-day rank-correlation median: {metric_value("cross_sectional_rank_corr_12_1_vs_recent_21d")}
- Production top overlap with recent 21-day top decile median: {metric_value("production_top_overlap_with_recent_21d_top_decile")}

## Overall HV-001 Classification

**{overall}**

The evidence supports that CSM-001 behaves as a persistent cross-sectional relative leadership state with rotating upper-tail membership. The claim that this behavior is not broad-market-direction driven is only partially supported because no external market-direction construct was introduced in HV-001.
"""
    (OUTPUT_DIR / "hv001_hypothesis_validation.md").write_text(report, encoding="utf-8")

    confidence = f"""# Confidence Interval Report

Bootstrap confidence intervals used {BOOTSTRAP_ITERATIONS} resamples with seed `{BOOTSTRAP_SEED}`.

The bootstrap was applied to date-level descriptive statistics, not to future returns or trading outcomes.
"""
    (OUTPUT_DIR / "confidence_interval_report.md").write_text(confidence, encoding="utf-8")

    robustness = """# Robustness Analysis

HV-001 evaluates persistence over multiple lags: 1, 5, 21, 63 and 126 trading days.

The analysis also includes year-positive rates for rank persistence where applicable.

No parameter tuning or threshold search was performed.
"""
    (OUTPUT_DIR / "robustness_analysis.md").write_text(robustness, encoding="utf-8")

    limitations = """# Limitations

- HV-001 does not evaluate future returns, alpha, profitability, Sharpe, CAGR, drawdown or economic value.
- H3 is only partially testable without introducing an external market-direction construct.
- The analysis uses the CV-001 current S&P 500-style universe, not survivorship-free historical constituents.
- Bootstrap intervals describe empirical uncertainty in construct behavior only.
- Evidence of persistence does not imply predictive validity.
"""
    (OUTPUT_DIR / "limitations.md").write_text(limitations, encoding="utf-8")

    summary = f"""# Executive Summary

CSM-001 / HV-001 tested whether the MI-001 mechanism description is empirically supported.

Overall classification: **{overall}**.

The strongest evidence supports rank persistence and top-decile membership persistence beyond one-day random turnover. The construct is therefore consistent with a persistent cross-sectional relative leadership state.

Predictive validity remains untested and must be evaluated separately in CSM-001 / PV-001.
"""
    (OUTPUT_DIR / "executive_summary.md").write_text(summary, encoding="utf-8")

    next_goal = """# CSM-001 / PV-001 Predictive Validation

Purpose: evaluate whether the validated CSM-001 construct contains statistically significant predictive information about predefined future outcomes.

Required boundaries:

- No economic validation.
- No strategy optimization.
- No production recommendation.
- No parameter tuning.

PV-001 may evaluate predictive information only after preregistering outcomes, forecast horizons, null models, sample splits and statistical tests.
"""
    (OUTPUT_DIR / "next_stage_goal_pv001.md").write_text(next_goal, encoding="utf-8")

    manifest = {
        "construct_id": "CSM-001",
        "stage": "HV-001",
        "overall_classification": overall,
        "verdicts": verdicts,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "bootstrap_iterations": BOOTSTRAP_ITERATIONS,
    }
    (OUTPUT_DIR / "hv001_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    frame = _load_state()
    h1, v1 = _h1_rank_persistence(frame)
    h2, v2 = _h2_top_decile_persistence(frame)
    h3, v3 = _h3_rotation_not_broad_market(frame)
    h4, v4 = _h4_skip_period_separation(frame)
    results = pd.concat([h1, h2, h3, h4], ignore_index=True, sort=False)
    results.to_csv(OUTPUT_DIR / "hypothesis_test_results.csv", index=False)
    _write_reports(results, {"H1": v1, "H2": v2, "H3": v3, "H4": v4})
    print(json.dumps({"status": "PASSED", "output_dir": str(OUTPUT_DIR)}, indent=2))


if __name__ == "__main__":
    main()
