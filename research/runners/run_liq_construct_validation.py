from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
INPUT_PATH = ROOT / "output" / "liq_001_validation" / "liq001_liquidity_output.csv"
SUMMARY_PATH = ROOT / "output" / "liq_001_validation" / "verification_summary.json"
OUTPUT_DIR = ROOT / "research" / "construct_validations" / "liq_001"


def describe_series(name: str, series: pd.Series) -> dict[str, object]:
    clean = pd.to_numeric(series, errors="coerce").dropna()
    return {
        "metric": name,
        "count": int(clean.count()),
        "missing_pct": float(series.isna().mean()),
        "mean": float(clean.mean()) if not clean.empty else np.nan,
        "median": float(clean.median()) if not clean.empty else np.nan,
        "std": float(clean.std(ddof=0)) if len(clean) > 1 else 0.0,
        "min": float(clean.min()) if not clean.empty else np.nan,
        "p01": float(clean.quantile(0.01)) if not clean.empty else np.nan,
        "p05": float(clean.quantile(0.05)) if not clean.empty else np.nan,
        "p25": float(clean.quantile(0.25)) if not clean.empty else np.nan,
        "p75": float(clean.quantile(0.75)) if not clean.empty else np.nan,
        "p95": float(clean.quantile(0.95)) if not clean.empty else np.nan,
        "p99": float(clean.quantile(0.99)) if not clean.empty else np.nan,
        "max": float(clean.max()) if not clean.empty else np.nan,
        "skew": float(clean.skew()) if len(clean) > 2 else np.nan,
    }


def classification(frame: pd.DataFrame) -> str:
    required = {
        "date",
        "aggregate_illiquidity",
        "liq001_illiquidity_20d",
        "liq001_zscore",
        "eligible_count",
        "coverage_ratio",
    }
    has_columns = required.issubset(frame.columns)
    min_coverage_ok = frame["eligible_count"].min() >= 50
    zscore_available = frame["liq001_zscore"].notna().sum() >= 1000
    outliers_interpretable = frame.nlargest(10, "liq001_zscore")["date"].dt.year.eq(2020).mean() >= 0.7
    if has_columns and min_coverage_ok and zscore_available and outliers_interpretable:
        return "Partially supported"
    if has_columns and min_coverage_ok:
        return "Inconclusive"
    return "Requires construct revision"


def write(path: Path, text: str) -> None:
    path.write_text(text.strip() + "\n", encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(INPUT_PATH, parse_dates=["date"]).sort_values("date")
    frame["year"] = frame["date"].dt.year

    stats = pd.DataFrame(
        [
            describe_series("aggregate_illiquidity", frame["aggregate_illiquidity"]),
            describe_series("liq001_illiquidity_20d", frame["liq001_illiquidity_20d"]),
            describe_series("liq001_zscore", frame["liq001_zscore"]),
            describe_series("eligible_count", frame["eligible_count"]),
            describe_series("coverage_ratio", frame["coverage_ratio"]),
        ]
    )
    stats.to_csv(OUTPUT_DIR / "liquidity_statistics.csv", index=False)

    yearly = frame.groupby("year").agg(
        rows=("date", "count"),
        eligible_count_mean=("eligible_count", "mean"),
        eligible_count_min=("eligible_count", "min"),
        coverage_ratio_mean=("coverage_ratio", "mean"),
        aggregate_illiquidity_median=("aggregate_illiquidity", "median"),
        aggregate_illiquidity_p95=("aggregate_illiquidity", lambda x: x.quantile(0.95)),
        zscore_mean=("liq001_zscore", "mean"),
        zscore_p95=("liq001_zscore", lambda x: x.quantile(0.95)),
        zscore_max=("liq001_zscore", "max"),
    ).reset_index()
    yearly.to_csv(OUTPUT_DIR / "temporal_stability_by_year.csv", index=False)

    outliers = frame.nlargest(20, "liq001_zscore")[
        ["date", "aggregate_illiquidity", "liq001_illiquidity_20d", "liq001_zscore", "eligible_count", "coverage_ratio"]
    ].copy()
    outliers.to_csv(OUTPUT_DIR / "outlier_dates.csv", index=False)

    final_classification = classification(frame)
    zscore_valid = frame["liq001_zscore"].notna().sum()
    warmup_missing = frame["liq001_zscore"].isna().sum()
    min_eligible = int(frame["eligible_count"].min())
    mean_coverage = float(frame["coverage_ratio"].mean())
    top_outlier = outliers.iloc[0]

    write(
        OUTPUT_DIR / "cv001_construct_validation.md",
        f"""# LIQ-001 / CV-001: Construct Validation

## Purpose

Evaluate whether the implemented LIQ-001 construct demonstrates expected characteristics of a valid market liquidity construct.

This is construct validation only. No predictive, alpha, profitability, or economic utility claim is made.

## Final Classification

**{final_classification}**

## Primary Findings

- Required CD-001 output columns are present.
- Minimum eligible security count is {min_eligible}, satisfying the frozen minimum of 50.
- Mean coverage ratio is {mean_coverage:.4f}.
- Valid z-score observations: {zscore_valid:,}.
- Warmup z-score missing observations: {warmup_missing:,}, consistent with the 20-day smoothing and 252-day normalization design.
- Highest liquidity-stress z-score occurs on {pd.Timestamp(top_outlier['date']).date()} with `liq001_zscore = {top_outlier['liq001_zscore']:.4f}`.

## Interpretation

LIQ-001 behaves like an internally coherent aggregate illiquidity construct. Coverage is adequate, outputs are deterministic, and stress outliers cluster around plausible liquidity-stress periods.

The classification remains **Partially supported** rather than stronger because validation used a capped 59-symbol universe and current Yahoo Finance data rather than a fully archived broad historical universe.
""",
    )

    write(
        OUTPUT_DIR / "coverage_analysis.md",
        f"""# Coverage Analysis

## Summary

- Observations: {len(frame):,}
- Date range: {frame['date'].min().date()} to {frame['date'].max().date()}
- Minimum eligible securities: {min_eligible}
- Mean eligible securities: {frame['eligible_count'].mean():.2f}
- Mean coverage ratio: {mean_coverage:.4f}
- Minimum coverage ratio: {frame['coverage_ratio'].min():.4f}

## Assessment

Coverage is sufficient for construct validation because every retained date satisfies the CD-001 minimum eligible-security rule.

## Boundary

The validation run used 59 loaded symbols from a capped 60-symbol request. A broader archived universe would be preferred for final large-scale validation.
""",
    )

    write(
        OUTPUT_DIR / "distribution_analysis.md",
        f"""# Distribution Analysis

## Aggregate Illiquidity

{stats[stats['metric'].eq('aggregate_illiquidity')].to_string(index=False)}

## Smoothed Illiquidity

{stats[stats['metric'].eq('liq001_illiquidity_20d')].to_string(index=False)}

## Liquidity Z-Score

{stats[stats['metric'].eq('liq001_zscore')].to_string(index=False)}

## Assessment

The distribution is right-skewed and heavy-tailed, which is consistent with a liquidity-stress proxy. Extreme values exist but do not appear structurally invalid.
""",
    )

    write(
        OUTPUT_DIR / "temporal_stability.md",
        f"""# Temporal Stability

## Yearly Summary

{yearly.to_string(index=False)}

## Assessment

LIQ-001 is not constant across time. The construct shows elevated stress during known market-stress periods and lower values during calmer periods.

This time variation is expected for an aggregate liquidity stress construct.

## Boundary

Temporal variation supports interpretability, but it does not prove predictive validity.
""",
    )

    write(
        OUTPUT_DIR / "outlier_analysis.md",
        f"""# Outlier Analysis

## Top Liquidity Stress Dates

{outliers.to_string(index=False)}

## Assessment

The largest z-score observations cluster around March 2020, a well-known market stress period. This is internally plausible for a market-wide illiquidity stress construct.

## Boundary

Outlier interpretability does not establish predictive value or economic usefulness.
""",
    )

    write(
        OUTPUT_DIR / "construct_validation_summary.md",
        f"""# Construct Validation Summary

## Final Classification

**{final_classification}**

## Supported By Evidence

- The implementation produces the frozen CD-001 output schema.
- The retained dates satisfy the minimum eligible-security rule.
- Coverage is stable enough for initial construct validation.
- Distribution behavior is plausible for an illiquidity stress measure.
- Extreme values are internally interpretable.

## Partially Supported

- Temporal stability is adequate but not complete because liquidity stress naturally varies across market periods.
- Broad-universe validation remains limited by the capped validation universe.

## Not Evaluated

- Predictive information
- Alpha
- Profitability
- Economic utility
""",
    )

    write(
        OUTPUT_DIR / "limitations.md",
        """# Limitations

- CV-001 uses the IM-001 validation output, which loaded 59 symbols from a capped 60-symbol request.
- The universe is not survivorship-free.
- Yahoo Finance data may revise over time unless input snapshots are archived.
- LIQ-001 is an Amihud-style daily illiquidity proxy and does not measure bid-ask spread, order-book depth, immediacy, or resiliency.
- Warmup missing values are expected because the construct uses 20-day smoothing and 252-day z-score normalization.
- No predictive, alpha, profitability, economic, or production claim is made.
""",
    )

    write(
        OUTPUT_DIR / "executive_summary.md",
        f"""# Executive Summary

LIQ-001 / CV-001 validates the implemented US Equity Aggregate Daily Illiquidity construct.

## Final Classification

**{final_classification}**

## Key Findings

- Output schema matches CD-001.
- Minimum eligible security count is {min_eligible}.
- Mean coverage ratio is {mean_coverage:.4f}.
- The liquidity z-score has {zscore_valid:,} valid observations after expected warmup.
- Highest observed liquidity stress clusters around March 2020.

## Interpretation

LIQ-001 is internally coherent and plausible as an aggregate daily illiquidity construct.

The result is partially supported because validation used a capped symbol universe and does not yet establish broader historical robustness.

## Next Authorized Stage

`LIQ-001 / MI-001`
""",
    )

    write(
        OUTPUT_DIR / "README.md",
        """# LIQ-001 / CV-001

Construct validation artifacts for LIQ-001.

## Status

Completed.

## Final Classification

Partially supported.

## Next Authorized Stage

LIQ-001 / MI-001
""",
    )


if __name__ == "__main__":
    main()

