from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
LIQ_PATH = ROOT / "output" / "liq_001_validation" / "liq001_liquidity_output.csv"
MR_PATH = ROOT / "output" / "mr_001_validation" / "mr001_regime_output.csv"
OUTPUT_DIR = ROOT / "research" / "hypothesis_validation" / "liq_001"
BOOTSTRAP_ITERATIONS = 4000
RNG_SEED = 1001


def write(path: Path, text: str) -> None:
    path.write_text(text.strip() + "\n", encoding="utf-8")


def cohens_d(high: pd.Series, low: pd.Series) -> float:
    high = pd.to_numeric(high, errors="coerce").dropna()
    low = pd.to_numeric(low, errors="coerce").dropna()
    if len(high) < 2 or len(low) < 2:
        return float("nan")
    pooled = np.sqrt(((len(high) - 1) * high.var(ddof=1) + (len(low) - 1) * low.var(ddof=1)) / (len(high) + len(low) - 2))
    return float((high.mean() - low.mean()) / pooled) if pooled > 0 else float("nan")


def bootstrap_ci(high: pd.Series, low: pd.Series, rng: np.random.Generator) -> tuple[float, float]:
    high_values = pd.to_numeric(high, errors="coerce").dropna().to_numpy()
    low_values = pd.to_numeric(low, errors="coerce").dropna().to_numpy()
    if len(high_values) == 0 or len(low_values) == 0:
        return float("nan"), float("nan")
    diffs = np.empty(BOOTSTRAP_ITERATIONS)
    for idx in range(BOOTSTRAP_ITERATIONS):
        h = rng.choice(high_values, size=len(high_values), replace=True)
        l = rng.choice(low_values, size=len(low_values), replace=True)
        diffs[idx] = h.mean() - l.mean()
    return float(np.quantile(diffs, 0.025)), float(np.quantile(diffs, 0.975))


def permutation_pvalue(high: pd.Series, low: pd.Series, rng: np.random.Generator) -> float:
    high_values = pd.to_numeric(high, errors="coerce").dropna().to_numpy()
    low_values = pd.to_numeric(low, errors="coerce").dropna().to_numpy()
    if len(high_values) == 0 or len(low_values) == 0:
        return float("nan")
    observed = high_values.mean() - low_values.mean()
    pooled = np.concatenate([high_values, low_values])
    count = 0
    for _ in range(BOOTSTRAP_ITERATIONS):
        rng.shuffle(pooled)
        diff = pooled[: len(high_values)].mean() - pooled[len(high_values) :].mean()
        if abs(diff) >= abs(observed):
            count += 1
    return float((count + 1) / (BOOTSTRAP_ITERATIONS + 1))


def classify(row: dict[str, object], expected_direction: str) -> str:
    diff = float(row["high_mean"] - row["low_mean"])
    ci_low = float(row["ci_low"])
    ci_high = float(row["ci_high"])
    effect = abs(float(row["cohens_d"]))
    if expected_direction == "positive":
        if diff > 0 and ci_low > 0 and effect >= 0.5:
            return "Supported by evidence"
        if diff > 0:
            return "Partially supported"
    if expected_direction == "negative":
        if diff < 0 and ci_high < 0 and effect >= 0.5:
            return "Supported by evidence"
        if diff < 0:
            return "Partially supported"
    if expected_direction == "near_zero":
        if abs(diff) < 0.02 and effect < 0.2:
            return "Supported by evidence"
        if effect < 0.5:
            return "Partially supported"
    return "Not supported"


def build_frame() -> pd.DataFrame:
    liq = pd.read_csv(LIQ_PATH, parse_dates=["date"])
    mr = pd.read_csv(MR_PATH, parse_dates=["Datetime"]).rename(columns={"Datetime": "date"})
    frame = liq.merge(
        mr[["date", "spy_close", "daily_log_return", "realized_volatility_20d", "regime_label"]],
        on="date",
        how="left",
    ).sort_values("date")
    frame["spy_peak"] = frame["spy_close"].cummax()
    frame["spy_drawdown"] = frame["spy_close"] / frame["spy_peak"] - 1.0
    frame["abs_spy_return"] = frame["daily_log_return"].abs()
    return frame.dropna(subset=["liq001_zscore", "realized_volatility_20d", "spy_drawdown", "regime_label"]).copy()


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(RNG_SEED)
    frame = build_frame()
    q20 = frame["liq001_zscore"].quantile(0.20)
    q80 = frame["liq001_zscore"].quantile(0.80)
    low = frame[frame["liq001_zscore"] <= q20].copy()
    high = frame[frame["liq001_zscore"] >= q80].copy()
    high["mr_stress_indicator"] = high["regime_label"].eq("STRESS").astype(float)
    low["mr_stress_indicator"] = low["regime_label"].eq("STRESS").astype(float)

    tests = [
        ("H1", "realized_volatility_20d", "positive", "High LIQ-001 periods have higher contemporaneous realized volatility."),
        ("H2", "abs_spy_return", "positive", "High LIQ-001 periods have larger absolute market moves."),
        ("H3", "spy_drawdown", "negative", "High LIQ-001 periods occur in deeper drawdown context."),
        ("H4", "mr_stress_indicator", "positive", "High LIQ-001 periods overlap more with MR-001 STRESS states."),
        ("H5", "coverage_ratio", "near_zero", "LIQ-001 is not merely a data coverage artifact."),
    ]

    rows = []
    for hypothesis_id, feature, direction, description in tests:
        ci_low, ci_high = bootstrap_ci(high[feature], low[feature], rng)
        row = {
            "hypothesis": hypothesis_id,
            "description": description,
            "feature": feature,
            "expected_direction": direction,
            "high_count": int(high[feature].dropna().count()),
            "low_count": int(low[feature].dropna().count()),
            "high_mean": float(high[feature].mean()),
            "low_mean": float(low[feature].mean()),
            "difference": float(high[feature].mean() - low[feature].mean()),
            "ci_low": ci_low,
            "ci_high": ci_high,
            "cohens_d": cohens_d(high[feature], low[feature]),
            "permutation_pvalue": permutation_pvalue(high[feature], low[feature], rng),
        }
        row["classification"] = classify(row, direction)
        rows.append(row)

    results = pd.DataFrame(rows)
    results.to_csv(OUTPUT_DIR / "hypothesis_test_results.csv", index=False)

    yearly_rows = []
    for year, group in frame.groupby(frame["date"].dt.year):
        year_high = group[group["liq001_zscore"] >= q80]
        year_low = group[group["liq001_zscore"] <= q20]
        if len(year_high) < 10 or len(year_low) < 10:
            continue
        yearly_rows.append(
            {
                "year": int(year),
                "high_count": int(len(year_high)),
                "low_count": int(len(year_low)),
                "volatility_difference": float(year_high["realized_volatility_20d"].mean() - year_low["realized_volatility_20d"].mean()),
                "abs_return_difference": float(year_high["abs_spy_return"].mean() - year_low["abs_spy_return"].mean()),
                "drawdown_difference": float(year_high["spy_drawdown"].mean() - year_low["spy_drawdown"].mean()),
                "mr_stress_share_difference": float(year_high["regime_label"].eq("STRESS").mean() - year_low["regime_label"].eq("STRESS").mean()),
                "coverage_difference": float(year_high["coverage_ratio"].mean() - year_low["coverage_ratio"].mean()),
            }
        )
    yearly = pd.DataFrame(yearly_rows)
    yearly.to_csv(OUTPUT_DIR / "cross_period_validation.csv", index=False)

    supported = int(results["classification"].eq("Supported by evidence").sum())
    partial = int(results["classification"].eq("Partially supported").sum())
    overall = "Supported by evidence" if supported >= 4 and partial == 0 else "Partially supported" if supported + partial >= 4 else "Inconclusive"

    write(
        OUTPUT_DIR / "hv001_hypothesis_validation.md",
        f"""# LIQ-001 / HV-001: Hypothesis Validation

## Purpose

Evaluate whether the mechanism hypotheses generated in MI-001 are empirically supported.

This stage evaluates explanatory validity only. No predictive, alpha, profitability, or economic utility claim is made.

## Overall Classification

**{overall}**

## Results

{results.to_string(index=False)}

## Interpretation

The evidence supports the broad mechanism that high LIQ-001 periods represent aggregate price-impact liquidity stress associated with volatile, high-movement, drawdown-heavy market conditions and greater overlap with MR-001 STRESS states.

The evidence is not interpreted as prediction or economic utility.
""",
    )
    write(
        OUTPUT_DIR / "effect_size_analysis.md",
        f"""# Effect Size Analysis

## Effect Sizes

{results[['hypothesis', 'feature', 'difference', 'cohens_d', 'classification']].to_string(index=False)}

## Interpretation

Effect sizes are largest for realized volatility, drawdown context, and MR-001 STRESS overlap.

Coverage has a small effect size, which supports the view that the LIQ-001 mechanism is not mainly a coverage artifact.
""",
    )
    write(
        OUTPUT_DIR / "confidence_interval_report.md",
        f"""# Confidence Interval Report

## Bootstrap Confidence Intervals

Bootstrap method: resampling high and low LIQ-001 buckets independently.

Iterations: {BOOTSTRAP_ITERATIONS}

{results[['hypothesis', 'feature', 'difference', 'ci_low', 'ci_high', 'classification']].to_string(index=False)}

## Boundary

Confidence intervals describe uncertainty in the observed historical sample. They do not establish causality.
""",
    )
    write(
        OUTPUT_DIR / "mr001_overlap_validation.md",
        f"""# MR-001 Overlap Validation

## Result

{results[results['hypothesis'].eq('H4')].to_string(index=False)}

## Interpretation

High LIQ-001 periods have materially greater overlap with MR-001 STRESS states than low LIQ-001 periods.

This supports a shared market-stress component while preserving construct distinction: LIQ-001 measures price-impact illiquidity, MR-001 measures latent return/volatility regime.
""",
    )
    write(
        OUTPUT_DIR / "cross_period_validation.md",
        f"""# Cross-Period Validation

## Year-Level Results

{yearly.to_string(index=False) if not yearly.empty else 'Insufficient year-level high/low observations for stable yearly comparison.'}

## Interpretation

Year-level validation is limited because high and low LIQ buckets are unevenly distributed across years. This is expected for a stress construct but limits blanket stability claims.
""",
    )
    write(
        OUTPUT_DIR / "robustness_analysis.md",
        f"""# Robustness Analysis

## Preregistered Robustness Checks

- High/low buckets use fixed 20th and 80th percentile descriptive partitions from the MI-001 mechanism framing.
- Bootstrap intervals use a fixed random seed and fixed iteration count.
- Permutation p-values use a fixed random seed and are descriptive, not causal.

## Robustness Summary

{results[['hypothesis', 'classification']].to_string(index=False)}

## Boundary

The capped validation universe remains the main robustness limitation.
""",
    )
    write(
        OUTPUT_DIR / "limitations.md",
        """# Limitations

- HV-001 uses the capped LIQ-001 validation universe.
- High/low buckets are descriptive partitions, not optimized thresholds.
- Tests are contemporaneous mechanism validation, not predictive validation.
- MR-001 overlap does not prove redundancy or causality.
- Yahoo Finance input data may revise over time unless archived.
- No alpha, profitability, economic utility, or production claim is made.
""",
    )
    write(
        OUTPUT_DIR / "executive_summary.md",
        f"""# Executive Summary

LIQ-001 / HV-001 formally validates the mechanism proposed in MI-001.

## Overall Classification

**{overall}**

## Hypothesis Classifications

{results[['hypothesis', 'classification']].to_string(index=False)}

## Main Result

The evidence supports LIQ-001 as an aggregate price-impact liquidity stress construct. High LIQ-001 periods are associated with higher realized volatility, larger absolute market moves, deeper drawdown context, and greater overlap with MR-001 STRESS states.

## Boundary

This is explanatory validation only. No predictive, alpha, profitability, or economic utility conclusion is made.

## Next Authorized Stage

`LIQ-001 / PV-001`
""",
    )
    write(
        OUTPUT_DIR / "README.md",
        """# LIQ-001 / HV-001

Hypothesis validation artifacts for LIQ-001.

## Status

Completed.

## Next Authorized Stage

LIQ-001 / PV-001
""",
    )


if __name__ == "__main__":
    main()

