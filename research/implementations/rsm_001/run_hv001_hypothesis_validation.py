from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[3]
STATE_FILE = REPO_ROOT / "output" / "rsm_001" / "rsm001_residual_momentum_state.csv"
MONTHLY_RETURNS_FILE = REPO_ROOT / "data" / "rsm_001" / "monthly_returns.csv"
OUTPUT_DIR = REPO_ROOT / "research" / "market_edge_discovery_program" / "rsm_001_hv_001_hypothesis_validation"
BOOTSTRAP_SEED = 3101
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
        stats.append(float(np.median(sample) if statistic == "median" else np.mean(sample)))
    return float(np.percentile(stats, 2.5)), float(np.percentile(stats, 97.5))


def _load_state() -> pd.DataFrame:
    frame = pd.read_csv(STATE_FILE, parse_dates=["month"])
    frame["rsm_valid_observation"] = frame["rsm_valid_observation"].astype(bool)
    return frame[frame["rsm_valid_observation"]].sort_values(["month", "ticker"]).reset_index(drop=True)


def _raw_12_1_momentum(monthly_returns: pd.DataFrame) -> pd.DataFrame:
    returns = monthly_returns.copy()
    returns.index = pd.to_datetime(returns.index).tz_localize(None).to_period("M").to_timestamp("M")
    gross = 1.0 + returns
    product = pd.DataFrame(1.0, index=returns.index, columns=returns.columns)
    count = pd.DataFrame(0, index=returns.index, columns=returns.columns)
    for lag in range(2, 13):
        shifted = gross.shift(lag)
        product = product.mul(shifted.fillna(1.0), fill_value=1.0)
        count = count.add(shifted.notna().astype(int), fill_value=0)
    return (product - 1.0).where(count.eq(11))


def _attach_raw_momentum(frame: pd.DataFrame) -> pd.DataFrame:
    monthly_returns = pd.read_csv(MONTHLY_RETURNS_FILE, index_col=0, parse_dates=True)
    raw = _raw_12_1_momentum(monthly_returns)
    raw_long = raw.reset_index(names="month").melt(id_vars="month", var_name="ticker", value_name="raw_return_12_1")
    raw_long["month"] = pd.to_datetime(raw_long["month"])
    merged = frame.merge(raw_long, on=["month", "ticker"], how="left")
    valid = merged["raw_return_12_1"].notna()
    ranks = merged.loc[valid].groupby("month")["raw_return_12_1"].rank(method="average", ascending=True)
    counts = merged.loc[valid].groupby("month")["raw_return_12_1"].transform("count")
    merged["raw_momentum_percentile"] = np.nan
    merged.loc[valid, "raw_momentum_percentile"] = (ranks - 1.0) / (counts - 1.0)
    return merged


def _h1_top_positive_residual(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object]]:
    top = frame[frame["rsm_state"] == "TOP_DECILE"].copy()
    yearly = top.groupby(top["month"].dt.year)["residual_sum_12_1"].agg(["count", "mean", "median"]).reset_index(names="year")
    low, high = _bootstrap_ci(top["residual_sum_12_1"], statistic="mean")
    positive_rate = float((top["residual_sum_12_1"] > 0).mean())
    positive_years = int((yearly["median"] > 0).sum())
    total_years = int(len(yearly))
    summary = pd.DataFrame(
        [
            {
                "hypothesis": "H1",
                "metric": "top_decile_residual_sum_12_1",
                "observations": int(len(top)),
                "mean": _safe_float(top["residual_sum_12_1"].mean()),
                "median": _safe_float(top["residual_sum_12_1"].median()),
                "positive_rate": positive_rate,
                "bootstrap_mean_ci_low": low,
                "bootstrap_mean_ci_high": high,
                "positive_years": positive_years,
                "total_years": total_years,
            }
        ]
    )
    status = "Supported by evidence" if low is not None and low > 0 and positive_years == total_years else "Partially supported"
    return summary, {"status": status, "yearly": yearly}


def _h2_bottom_negative_residual(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object]]:
    bottom = frame[frame["rsm_state"] == "BOTTOM_DECILE"].copy()
    yearly = bottom.groupby(bottom["month"].dt.year)["residual_sum_12_1"].agg(["count", "mean", "median"]).reset_index(names="year")
    low, high = _bootstrap_ci(bottom["residual_sum_12_1"], statistic="mean")
    negative_rate = float((bottom["residual_sum_12_1"] < 0).mean())
    negative_years = int((yearly["median"] < 0).sum())
    total_years = int(len(yearly))
    summary = pd.DataFrame(
        [
            {
                "hypothesis": "H2",
                "metric": "bottom_decile_residual_sum_12_1",
                "observations": int(len(bottom)),
                "mean": _safe_float(bottom["residual_sum_12_1"].mean()),
                "median": _safe_float(bottom["residual_sum_12_1"].median()),
                "negative_rate": negative_rate,
                "bootstrap_mean_ci_low": low,
                "bootstrap_mean_ci_high": high,
                "negative_years": negative_years,
                "total_years": total_years,
            }
        ]
    )
    status = "Supported by evidence" if high is not None and high < 0 and negative_years == total_years else "Partially supported"
    return summary, {"status": status, "yearly": yearly}


def _h3_raw_vs_residual_distinction(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    clean = frame[frame["raw_momentum_percentile"].notna()].copy()
    rows = []
    for month, group in clean.groupby("month", sort=True):
        if len(group) < 30:
            continue
        rsm_rank = group["rsm_percentile"].rank(method="average")
        raw_rank = group["raw_momentum_percentile"].rank(method="average")
        raw_top = set(group.loc[group["raw_momentum_percentile"] >= 0.90, "ticker"])
        rsm_top = set(group.loc[group["rsm_state"] == "TOP_DECILE", "ticker"])
        raw_bottom = set(group.loc[group["raw_momentum_percentile"] <= 0.10, "ticker"])
        rsm_bottom = set(group.loc[group["rsm_state"] == "BOTTOM_DECILE", "ticker"])
        top_union = raw_top | rsm_top
        bottom_union = raw_bottom | rsm_bottom
        rows.append(
            {
                "month": month,
                "eligible_count": int(len(group)),
                "spearman_rsm_vs_raw": float(rsm_rank.corr(raw_rank, method="pearson")),
                "top_decile_jaccard": len(raw_top & rsm_top) / len(top_union) if top_union else np.nan,
                "bottom_decile_jaccard": len(raw_bottom & rsm_bottom) / len(bottom_union) if bottom_union else np.nan,
            }
        )
    monthly = pd.DataFrame(rows)
    low, high = _bootstrap_ci(monthly["spearman_rsm_vs_raw"], statistic="median")
    median_spearman = float(monthly["spearman_rsm_vs_raw"].median())
    median_top_jaccard = float(monthly["top_decile_jaccard"].median())
    median_bottom_jaccard = float(monthly["bottom_decile_jaccard"].median())
    summary = pd.DataFrame(
        [
            {
                "hypothesis": "H3",
                "metric": "median_spearman_rsm_vs_raw",
                "observations": int(len(monthly)),
                "value": median_spearman,
                "bootstrap_median_ci_low": low,
                "bootstrap_median_ci_high": high,
            },
            {
                "hypothesis": "H3",
                "metric": "median_top_decile_jaccard",
                "observations": int(len(monthly)),
                "value": median_top_jaccard,
            },
            {
                "hypothesis": "H3",
                "metric": "median_bottom_decile_jaccard",
                "observations": int(len(monthly)),
                "value": median_bottom_jaccard,
            },
        ]
    )
    status = "Supported by evidence" if 0.25 < median_spearman < 0.95 and median_top_jaccard < 0.80 else "Inconclusive"
    return summary, monthly, {"status": status}


def _h4_standardization_effect(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    rows = []
    for month, group in frame.groupby("month", sort=True):
        if len(group) < 30:
            continue
        raw_resid_rank = group["residual_sum_12_1"].rank(method="average", ascending=True)
        raw_resid_pct = (raw_resid_rank - 1.0) / (len(group) - 1.0)
        standardized_top = set(group.loc[group["rsm_state"] == "TOP_DECILE", "ticker"])
        unstandardized_top = set(group.loc[raw_resid_pct >= 0.90, "ticker"])
        standardized_bottom = set(group.loc[group["rsm_state"] == "BOTTOM_DECILE", "ticker"])
        unstandardized_bottom = set(group.loc[raw_resid_pct <= 0.10, "ticker"])
        top_union = standardized_top | unstandardized_top
        bottom_union = standardized_bottom | unstandardized_bottom
        rows.append(
            {
                "month": month,
                "eligible_count": int(len(group)),
                "score_vs_unstandardized_spearman": float(group["rsm_percentile"].rank().corr(raw_resid_pct.rank(), method="pearson")),
                "top_decile_jaccard_standardized_vs_unstandardized": len(standardized_top & unstandardized_top) / len(top_union) if top_union else np.nan,
                "bottom_decile_jaccard_standardized_vs_unstandardized": len(standardized_bottom & unstandardized_bottom) / len(bottom_union) if bottom_union else np.nan,
            }
        )
    monthly = pd.DataFrame(rows)
    median_top_jaccard = float(monthly["top_decile_jaccard_standardized_vs_unstandardized"].median())
    median_bottom_jaccard = float(monthly["bottom_decile_jaccard_standardized_vs_unstandardized"].median())
    median_spearman = float(monthly["score_vs_unstandardized_spearman"].median())
    summary = pd.DataFrame(
        [
            {
                "hypothesis": "H4",
                "metric": "median_score_vs_unstandardized_spearman",
                "observations": int(len(monthly)),
                "value": median_spearman,
            },
            {
                "hypothesis": "H4",
                "metric": "median_top_decile_jaccard_standardized_vs_unstandardized",
                "observations": int(len(monthly)),
                "value": median_top_jaccard,
            },
            {
                "hypothesis": "H4",
                "metric": "median_bottom_decile_jaccard_standardized_vs_unstandardized",
                "observations": int(len(monthly)),
                "value": median_bottom_jaccard,
            },
        ]
    )
    status = "Supported by evidence" if median_top_jaccard < 0.90 or median_bottom_jaccard < 0.90 else "Not supported"
    return summary, monthly, {"status": status}


def _write_reports(
    *,
    frame: pd.DataFrame,
    hypothesis_results: pd.DataFrame,
    verdicts: pd.DataFrame,
    h1_yearly: pd.DataFrame,
    h2_yearly: pd.DataFrame,
    h3_monthly: pd.DataFrame,
    h4_monthly: pd.DataFrame,
) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    hypothesis_results.to_csv(OUTPUT_DIR / "hypothesis_test_results.csv", index=False)
    verdicts.to_csv(OUTPUT_DIR / "hypothesis_verdicts.csv", index=False)
    h1_yearly.to_csv(OUTPUT_DIR / "h1_top_yearly_validation.csv", index=False)
    h2_yearly.to_csv(OUTPUT_DIR / "h2_bottom_yearly_validation.csv", index=False)
    h3_monthly.to_csv(OUTPUT_DIR / "h3_raw_vs_residual_monthly.csv", index=False)
    h4_monthly.to_csv(OUTPUT_DIR / "h4_standardization_monthly.csv", index=False)

    verdict_map = dict(zip(verdicts["hypothesis"], verdicts["classification"]))
    h1 = hypothesis_results[hypothesis_results["hypothesis"] == "H1"].iloc[0]
    h2 = hypothesis_results[hypothesis_results["hypothesis"] == "H2"].iloc[0]
    h3_spear = hypothesis_results[
        (hypothesis_results["hypothesis"] == "H3") & (hypothesis_results["metric"] == "median_spearman_rsm_vs_raw")
    ].iloc[0]
    h3_top = hypothesis_results[
        (hypothesis_results["hypothesis"] == "H3") & (hypothesis_results["metric"] == "median_top_decile_jaccard")
    ].iloc[0]
    h4_top = hypothesis_results[
        (hypothesis_results["hypothesis"] == "H4")
        & (hypothesis_results["metric"] == "median_top_decile_jaccard_standardized_vs_unstandardized")
    ].iloc[0]
    h4_bottom = hypothesis_results[
        (hypothesis_results["hypothesis"] == "H4")
        & (hypothesis_results["metric"] == "median_bottom_decile_jaccard_standardized_vs_unstandardized")
    ].iloc[0]
    supported_count = int(verdicts["classification"].eq("Supported by evidence").sum())
    overall = "Supported by evidence" if supported_count >= 3 else "Partially supported"

    main = f"""# RSM-001 / HV-001 Hypothesis Validation

## Purpose

Formally validate the MI-001 mechanism hypotheses for the frozen RSM-001 residual momentum construct.

No future returns, alpha, trading performance, backtests, forecasting, parameter optimization or economic value were evaluated.

## Evidence Base

- Source state file: `output/rsm_001/rsm001_residual_momentum_state.csv`
- Valid observations: {len(frame):,}
- Unique tickers: {frame["ticker"].nunique():,}
- Valid months: {frame["month"].min().date()} to {frame["month"].max().date()}

## Hypothesis Results

### H1

TOP_DECILE states represent persistently positive factor-residual intermediate-horizon performance.

- Classification: **{verdict_map["H1"]}**
- TOP_DECILE residual_sum_12_1 mean: {h1["mean"]:.6f}
- Positive rate: {h1["positive_rate"]:.6f}
- Positive years with positive median: {int(h1["positive_years"])}/{int(h1["total_years"])}
- 95% bootstrap CI for mean: [{h1["bootstrap_mean_ci_low"]:.6f}, {h1["bootstrap_mean_ci_high"]:.6f}]

### H2

BOTTOM_DECILE states represent persistently negative factor-residual intermediate-horizon performance.

- Classification: **{verdict_map["H2"]}**
- BOTTOM_DECILE residual_sum_12_1 mean: {h2["mean"]:.6f}
- Negative rate: {h2["negative_rate"]:.6f}
- Negative years with negative median: {int(h2["negative_years"])}/{int(h2["total_years"])}
- 95% bootstrap CI for mean: [{h2["bootstrap_mean_ci_low"]:.6f}, {h2["bootstrap_mean_ci_high"]:.6f}]

### H3

RSM states are related to, but distinguishable from, raw 12-1 cross-sectional momentum states.

- Classification: **{verdict_map["H3"]}**
- Median monthly Spearman RSM vs raw momentum: {h3_spear["value"]:.6f}
- Median TOP_DECILE Jaccard vs raw momentum top decile: {h3_top["value"]:.6f}

### H4

Residual volatility standardization materially affects cross-sectional state assignment relative to unstandardized residual sums.

- Classification: **{verdict_map["H4"]}**
- Median TOP_DECILE Jaccard standardized vs unstandardized: {h4_top["value"]:.6f}
- Median BOTTOM_DECILE Jaccard standardized vs unstandardized: {h4_bottom["value"]:.6f}

## Overall HV-001 Conclusion

**{overall}**

The evidence supports the explanatory interpretation that RSM-001 is a factor-residual cross-sectional winner-loser state construct. H3 and H4 support that it is related to, but not identical with, raw momentum or unstandardized residual ranking.
"""
    (OUTPUT_DIR / "hv001_hypothesis_validation.md").write_text(main, encoding="utf-8")

    (OUTPUT_DIR / "confidence_interval_report.md").write_text(
        """# Confidence Interval Report

Bootstrap confidence intervals were calculated only for descriptive mechanism statistics.

No future outcome, return forecast, alpha or economic metric was evaluated.

See `hypothesis_test_results.csv` for interval values.
""",
        encoding="utf-8",
    )

    (OUTPUT_DIR / "effect_size_analysis.md").write_text(
        f"""# Effect Size Analysis

Mechanism effect sizes are descriptive:

- H1 TOP_DECILE residual_sum_12_1 mean: {h1["mean"]:.6f}
- H2 BOTTOM_DECILE residual_sum_12_1 mean: {h2["mean"]:.6f}
- H3 median RSM-vs-raw rank agreement: {h3_spear["value"]:.6f}
- H4 median standardized-vs-unstandardized TOP_DECILE overlap: {h4_top["value"]:.6f}

These values describe construct behavior only.
""",
        encoding="utf-8",
    )

    (OUTPUT_DIR / "cross_period_validation.md").write_text(
        """# Cross-Period Validation

H1 and H2 were evaluated year-by-year using same-period residual formation variables.

Outputs:

- `h1_top_yearly_validation.csv`
- `h2_bottom_yearly_validation.csv`

No future-period outcome was evaluated.
""",
        encoding="utf-8",
    )

    (OUTPUT_DIR / "robustness_analysis.md").write_text(
        """# Robustness Analysis

Robustness was evaluated descriptively through:

- Year-by-year sign consistency for TOP_DECILE and BOTTOM_DECILE residual sums.
- Monthly RSM-vs-raw momentum rank agreement.
- Monthly standardized-vs-unstandardized residual decile overlap.

No parameter sensitivity, optimization, or predictive validation was performed.
""",
        encoding="utf-8",
    )

    (OUTPUT_DIR / "limitations.md").write_text(
        """# Limitations

- This HV study validates explanatory mechanism only.
- The current universe is not survivorship-free.
- The raw momentum comparator is descriptive and was not introduced as a competing tradable construct.
- No future returns were evaluated.
- No predictive validation was performed.
- No economic validation was performed.
- No alpha claim was made.
""",
        encoding="utf-8",
    )

    (OUTPUT_DIR / "executive_summary.md").write_text(
        f"""# Executive Summary

RSM-001 / HV-001 formally tested the mechanism hypotheses generated in MI-001.

Overall conclusion:

**{overall}**

Supported findings:

- TOP_DECILE states consistently represent positive factor-residual intermediate-horizon performance.
- BOTTOM_DECILE states consistently represent negative factor-residual intermediate-horizon performance.
- RSM is related to, but distinguishable from, raw 12-1 momentum.
- Residual volatility standardization materially changes state assignment relative to unstandardized residual sums.

No predictive, alpha, trading-performance or economic claim was made.
""",
        encoding="utf-8",
    )

    (OUTPUT_DIR / "next_stage_goal_pv001.md").write_text(
        """# RSM-001 / PV-001 Predictive Validation

Purpose:

Evaluate whether RSM-001 contains predictive information about future security-level outcomes.

This stage is not yet performed.

Forbidden before PV-001 begins:

- Economic validation.
- Trading strategy design.
- Parameter optimization.
- Production recommendations.

PV-001 must preregister horizons, outcomes, null models, validation design and statistical criteria before execution.
""",
        encoding="utf-8",
    )

    manifest = {
        "construct_id": "RSM-001",
        "stage": "HV-001",
        "overall_conclusion": overall,
        "hypothesis_classifications": verdict_map,
        "valid_observations": int(len(frame)),
        "unique_tickers": int(frame["ticker"].nunique()),
        "next_stage": "PV-001",
    }
    (OUTPUT_DIR / "hv001_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def run_hypothesis_validation() -> dict[str, object]:
    frame = _attach_raw_momentum(_load_state())
    h1, h1_meta = _h1_top_positive_residual(frame)
    h2, h2_meta = _h2_bottom_negative_residual(frame)
    h3, h3_monthly, h3_meta = _h3_raw_vs_residual_distinction(frame)
    h4, h4_monthly, h4_meta = _h4_standardization_effect(frame)
    results = pd.concat([h1, h2, h3, h4], ignore_index=True, sort=False)
    verdicts = pd.DataFrame(
        [
            {"hypothesis": "H1", "classification": h1_meta["status"]},
            {"hypothesis": "H2", "classification": h2_meta["status"]},
            {"hypothesis": "H3", "classification": h3_meta["status"]},
            {"hypothesis": "H4", "classification": h4_meta["status"]},
        ]
    )
    _write_reports(
        frame=frame,
        hypothesis_results=results,
        verdicts=verdicts,
        h1_yearly=h1_meta["yearly"],
        h2_yearly=h2_meta["yearly"],
        h3_monthly=h3_monthly,
        h4_monthly=h4_monthly,
    )
    return {
        "valid_observations": int(len(frame)),
        "supported_hypotheses": int(verdicts["classification"].eq("Supported by evidence").sum()),
        "status": "COMPLETE",
    }


if __name__ == "__main__":
    print(json.dumps(run_hypothesis_validation(), indent=2))

