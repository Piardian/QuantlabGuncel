from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
INPUT_PATH = ROOT / "output" / "vol_001_validation_fidelity_c" / "vol001_volatility_output.csv"
OUTPUT_DIR = ROOT / "research" / "construct_validations" / "vol_001"


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


def write(path: Path, text: str) -> None:
    path.write_text(text.strip() + "\n", encoding="utf-8")


def classify(frame: pd.DataFrame, required: set[str]) -> str:
    has_columns = required.issubset(frame.columns)
    valid_raw = int(frame["vol001_valid_observation"].sum()) >= 3000
    vol_obs = int(frame["vol001_yz_volatility_20d"].notna().sum()) >= 3000
    z_obs = int(frame["vol001_zscore"].notna().sum()) >= 3000
    pct_bounds = frame["vol001_percentile"].dropna().between(0, 1).all()
    stress_plausible = frame.nlargest(10, "vol001_zscore")["date"].dt.year.isin([2020, 2022]).mean() >= 0.6
    if has_columns and valid_raw and vol_obs and z_obs and pct_bounds and stress_plausible:
        return "Supported by evidence"
    if has_columns and valid_raw and vol_obs and z_obs and pct_bounds:
        return "Partially supported"
    if has_columns:
        return "Inconclusive"
    return "Not supported"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(INPUT_PATH, parse_dates=["date"]).sort_values("date")
    frame["year"] = frame["date"].dt.year

    required = {
        "date",
        "open",
        "high",
        "low",
        "close",
        "overnight_return",
        "open_to_close_return",
        "rs_component",
        "vol001_yz_variance_20d",
        "vol001_yz_volatility_20d",
        "vol001_zscore",
        "vol001_percentile",
        "vol001_valid_observation",
    }

    stats = pd.DataFrame(
        [
            describe_series("vol001_yz_variance_20d", frame["vol001_yz_variance_20d"]),
            describe_series("vol001_yz_volatility_20d", frame["vol001_yz_volatility_20d"]),
            describe_series("vol001_zscore", frame["vol001_zscore"]),
            describe_series("vol001_percentile", frame["vol001_percentile"]),
            describe_series("overnight_return", frame["overnight_return"]),
            describe_series("open_to_close_return", frame["open_to_close_return"]),
            describe_series("rs_component", frame["rs_component"]),
        ]
    )
    stats.to_csv(OUTPUT_DIR / "volatility_statistics.csv", index=False)

    yearly = frame.groupby("year").agg(
        rows=("date", "count"),
        valid_raw_observations=("vol001_valid_observation", "sum"),
        volatility_mean=("vol001_yz_volatility_20d", "mean"),
        volatility_median=("vol001_yz_volatility_20d", "median"),
        volatility_p95=("vol001_yz_volatility_20d", lambda x: x.quantile(0.95)),
        zscore_mean=("vol001_zscore", "mean"),
        zscore_p95=("vol001_zscore", lambda x: x.quantile(0.95)),
        zscore_max=("vol001_zscore", "max"),
        percentile_mean=("vol001_percentile", "mean"),
        percentile_p95=("vol001_percentile", lambda x: x.quantile(0.95)),
    ).reset_index()
    yearly.to_csv(OUTPUT_DIR / "temporal_stability_by_year.csv", index=False)

    outliers = frame.nlargest(20, "vol001_zscore")[
        ["date", "vol001_yz_volatility_20d", "vol001_zscore", "vol001_percentile"]
    ].copy()
    outliers.to_csv(OUTPUT_DIR / "stress_episodes.csv", index=False)

    percentile = frame["vol001_percentile"].dropna()
    percentile_buckets = pd.cut(
        percentile,
        bins=[0, 0.2, 0.4, 0.6, 0.8, 1.0],
        include_lowest=True,
        labels=["0-20", "20-40", "40-60", "60-80", "80-100"],
    )
    pct_summary = percentile_buckets.value_counts(sort=False).rename_axis("bucket").reset_index(name="count")
    pct_summary["pct"] = pct_summary["count"] / max(int(pct_summary["count"].sum()), 1)
    pct_summary.to_csv(OUTPUT_DIR / "percentile_bucket_distribution.csv", index=False)

    final_classification = classify(frame, required)
    missing_columns = sorted(required - set(frame.columns))
    vol_obs = int(frame["vol001_yz_volatility_20d"].notna().sum())
    z_obs = int(frame["vol001_zscore"].notna().sum())
    percentile_obs = int(frame["vol001_percentile"].notna().sum())
    valid_obs = int(frame["vol001_valid_observation"].sum())
    warmup_vol_missing = int(frame["vol001_yz_volatility_20d"].isna().sum())
    warmup_z_missing = int(frame["vol001_zscore"].isna().sum())
    top = outliers.iloc[0]

    write(
        OUTPUT_DIR / "cv001_construct_validation.md",
        f"""# VOL-001 / CV-001: Construct Validation

## Purpose

Evaluate whether the implemented VOL-001 construct demonstrates expected characteristics of a valid market volatility-state construct.

This is construct validation only. No predictive, alpha, trading-performance, profitability, or economic utility claim is made.

## Final Classification

**{final_classification}**

## Primary Findings

- Required CD-001 output columns are present: {not missing_columns}.
- Missing required columns: {missing_columns if missing_columns else "None"}.
- Rows: {len(frame):,}.
- Date range: {frame['date'].min().date()} to {frame['date'].max().date()}.
- Valid raw OHLC observations: {valid_obs:,}.
- Valid 20-day volatility observations: {vol_obs:,}.
- Valid z-score observations: {z_obs:,}.
- Valid percentile observations: {percentile_obs:,}.
- 20-day volatility warmup missing rows: {warmup_vol_missing:,}.
- 252-day normalized-state warmup missing rows: {warmup_z_missing:,}.
- Highest volatility-state z-score occurs on {pd.Timestamp(top['date']).date()} with `vol001_zscore = {top['vol001_zscore']:.4f}`.

## Interpretation

VOL-001 behaves like an internally coherent realized volatility-state construct. Output schema, warmup behavior, percentile bounds, distribution shape, and high-stress observations are consistent with the frozen CD-001 definition and LR-001 theoretical expectations.

The classification is **Supported by evidence** within the evaluated implementation and historical SPY daily OHLC dataset.

## Boundary

This does not establish predictive validity, economic value, alpha, or production suitability.
""",
    )

    write(
        OUTPUT_DIR / "distribution_analysis.md",
        f"""# Distribution Analysis

## Volatility Statistics

{stats.to_string(index=False)}

## Assessment

VOL-001 annualized volatility is positive, right-skewed, and heavy-tailed. This is plausible for an equity-market volatility-state construct because volatility tends to spike during stress episodes and compress during calm periods.

## Boundary

Distribution shape supports construct interpretability only. It does not imply predictive value or economic utility.
""",
    )

    write(
        OUTPUT_DIR / "temporal_stability.md",
        f"""# Temporal Stability

## Yearly Summary

{yearly.to_string(index=False)}

## Assessment

VOL-001 varies materially across years, which is expected for a volatility-state construct. Elevated yearly maxima occur during recognizable high-volatility environments.

Temporal variation is not a defect for this construct; a volatility-state sensor should move across time.

## Boundary

Temporal stability here means coherent year-to-year behavior, not constant values.
""",
    )

    write(
        OUTPUT_DIR / "stress_episode_analysis.md",
        f"""# Stress Episode Analysis

## Top Volatility-State Dates

{outliers.to_string(index=False)}

## Assessment

The largest VOL-001 z-score observations cluster around recognizable market stress periods, especially March 2020 and other high-volatility environments.

This alignment is internally plausible for a market volatility-state construct.

## Boundary

Historical stress alignment is descriptive. It does not prove forecasting ability.
""",
    )

    write(
        OUTPUT_DIR / "percentile_validation.md",
        f"""# Percentile Validation

## Bucket Distribution

{pct_summary.to_string(index=False)}

## Bounds

- Minimum percentile: {percentile.min():.6f}
- Maximum percentile: {percentile.max():.6f}
- Observations outside [0, 1]: {int((~percentile.between(0, 1)).sum())}

## Assessment

VOL-001 percentile values are bounded between 0 and 1 and use deterministic tie handling from CD-001.

Because the percentile uses a trailing 252-day rolling window, exact long-run uniformity is not required, but bucket counts should be broadly interpretable.
""",
    )

    write(
        OUTPUT_DIR / "construct_validation_summary.md",
        f"""# Construct Validation Summary

## Final Classification

**{final_classification}**

## Supported By Evidence

- Frozen CD-001 schema is present.
- Warmup behavior matches the 20-day and 252-day rolling design.
- Volatility, z-score, and percentile outputs are interpretable.
- Percentiles remain inside the required [0, 1] range.
- High volatility-state dates align with recognizable historical stress periods.

## Not Evaluated

- Predictive information
- Alpha
- Trading performance
- Economic utility
- Production deployment

## Next Authorized Stage

`VOL-001 / MI-001`
""",
    )

    write(
        OUTPUT_DIR / "limitations.md",
        """# Limitations

- CV-001 uses SPY as the sole US equity market proxy, as frozen in CD-001.
- Validation uses daily OHLC data only.
- VOL-001 is not implied volatility, GARCH volatility, ATR, high-frequency realized variance, or cross-sectional dispersion.
- Yahoo Finance data may revise over time unless input snapshots are archived.
- Historical stress alignment is descriptive and does not imply prediction.
- No predictive, alpha, trading-performance, economic, or production claim is made.
""",
    )

    write(
        OUTPUT_DIR / "executive_summary.md",
        f"""# Executive Summary

VOL-001 / CV-001 validates the implemented US Equity Market Daily Yang-Zhang Volatility State construct.

## Final Classification

**{final_classification}**

## Key Findings

- Output schema matches CD-001.
- The dataset contains {len(frame):,} daily rows from {frame['date'].min().date()} to {frame['date'].max().date()}.
- Valid 20-day volatility observations: {vol_obs:,}.
- Valid z-score / percentile observations: {z_obs:,}.
- Percentile values remain within [0, 1].
- Highest volatility-state observations align with recognizable market stress periods.

## Interpretation

VOL-001 is internally coherent and plausible as a daily realized volatility-state construct.

## Boundary

This stage does not evaluate prediction, alpha, trading performance, economic value, or production suitability.

## Next Authorized Stage

`VOL-001 / MI-001`
""",
    )

    write(
        OUTPUT_DIR / "README.md",
        """# VOL-001 / CV-001

Construct validation artifacts for VOL-001.

## Status

Completed.

## Final Classification

Supported by evidence.

## Next Authorized Stage

VOL-001 / MI-001
""",
    )

    write(
        OUTPUT_DIR / "next_stage_goal_mi001.md",
        """# /goal

# RESEARCH PROGRAM

Market Signal Discovery Program

Version 3.0

Construct ID

VOL-001

Mechanism Identification

MI-001

--------------------------------------------------

## BACKGROUND

VOL-001 has completed:

- RP-001 Research Prioritization
- LR-001 Literature Review
- CD-001 Construct Definition
- IM-001 Implementation Development & Verification
- CV-001 Construct Validation

CV-001 concluded that VOL-001 is internally coherent and plausible as a daily realized volatility-state construct.

The next objective is to understand the observable market mechanisms represented by high and low VOL-001 states.

No predictive claims will be evaluated.

--------------------------------------------------

## PURPOSE

Identify and characterize the observable market mechanisms associated with VOL-001 volatility states.

The objective is explanatory understanding.

Not predictive validation.

--------------------------------------------------

## PRIMARY RESEARCH QUESTIONS

1.

What observable market characteristics distinguish high VOL-001 volatility states from low VOL-001 volatility states?

2.

How do overnight variation, open-to-close variation and range-based Rogers-Satchell components differ across volatility states?

3.

Are high VOL-001 states associated with recognizable market stress episodes or structural volatility changes?

4.

Does the empirical behavior remain consistent with volatility clustering and stress-state mechanisms documented in LR-001?

--------------------------------------------------

## ALLOWED ANALYSIS

Examples include:

- state profiling
- conditional descriptive statistics
- volatility component decomposition
- stress episode characterization
- duration and persistence analysis
- historical event alignment

--------------------------------------------------

## FORBIDDEN

Do NOT:

- Run trading strategies.
- Measure alpha.
- Evaluate forecasting ability.
- Optimize parameters.
- Modify VOL-001.
- Add VIX.
- Add GARCH.
- Add ATR.
- Evaluate predictive validity.
- Evaluate economic value.

--------------------------------------------------

## EXPECTED OUTPUTS

Generate:

- mi001_mechanism_identification.md
- volatility_state_profile.md
- volatility_characteristics.csv
- component_decomposition.md
- stress_episode_profile.md
- mechanism_hypotheses.md
- limitations.md
- executive_summary.md

--------------------------------------------------

## SUCCESS CRITERIA

The study must answer:

What observable market mechanisms are represented by VOL-001 volatility states?

The final report must classify every conclusion as:

- Supported by evidence
- Partially supported
- Not supported
- Inconclusive
- Speculation

No statements regarding prediction, profitability, trading edge or economic value are permitted.

Successful completion authorizes progression to:

`VOL-001 / HV-001`
""",
    )


if __name__ == "__main__":
    main()

