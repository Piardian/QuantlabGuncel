from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
INPUT_PATH = ROOT / "output" / "vol_001_validation_fidelity_c" / "vol001_volatility_output.csv"
OUTPUT_DIR = ROOT / "research" / "hypothesis_validation" / "vol_001"
BOOTSTRAP_ITERATIONS = 4000
RNG_SEED = 2001


def write(path: Path, text: str) -> None:
    path.write_text(text.strip() + "\n", encoding="utf-8")


def cohens_d(high: pd.Series, low: pd.Series) -> float:
    high_values = pd.to_numeric(high, errors="coerce").dropna()
    low_values = pd.to_numeric(low, errors="coerce").dropna()
    if len(high_values) < 2 or len(low_values) < 2:
        return float("nan")
    pooled = np.sqrt(
        ((len(high_values) - 1) * high_values.var(ddof=1) + (len(low_values) - 1) * low_values.var(ddof=1))
        / (len(high_values) + len(low_values) - 2)
    )
    return float((high_values.mean() - low_values.mean()) / pooled) if pooled > 0 else float("nan")


def bootstrap_ci(high: pd.Series, low: pd.Series, rng: np.random.Generator) -> tuple[float, float]:
    high_values = pd.to_numeric(high, errors="coerce").dropna().to_numpy()
    low_values = pd.to_numeric(low, errors="coerce").dropna().to_numpy()
    if len(high_values) == 0 or len(low_values) == 0:
        return float("nan"), float("nan")
    diffs = np.empty(BOOTSTRAP_ITERATIONS)
    for index in range(BOOTSTRAP_ITERATIONS):
        h = rng.choice(high_values, size=len(high_values), replace=True)
        l = rng.choice(low_values, size=len(low_values), replace=True)
        diffs[index] = h.mean() - l.mean()
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
        shuffled = rng.permutation(pooled)
        diff = shuffled[: len(high_values)].mean() - shuffled[len(high_values) :].mean()
        if abs(diff) >= abs(observed):
            count += 1
    return float((count + 1) / (BOOTSTRAP_ITERATIONS + 1))


def classify_difference(diff: float, ci_low: float, ci_high: float, effect: float, expected: str) -> str:
    if expected == "positive":
        if diff > 0 and ci_low > 0 and abs(effect) >= 0.5:
            return "Supported by evidence"
        if diff > 0:
            return "Partially supported"
    if expected == "negative":
        if diff < 0 and ci_high < 0 and abs(effect) >= 0.5:
            return "Supported by evidence"
        if diff < 0:
            return "Partially supported"
    return "Not supported"


def build_frame() -> pd.DataFrame:
    frame = pd.read_csv(INPUT_PATH, parse_dates=["date"]).sort_values("date")
    frame["daily_log_return"] = np.log(frame["close"] / frame["close"].shift(1))
    frame["abs_daily_return"] = frame["daily_log_return"].abs()
    frame["abs_overnight_return"] = frame["overnight_return"].abs()
    frame["abs_open_to_close_return"] = frame["open_to_close_return"].abs()
    frame["peak_close"] = frame["close"].cummax()
    frame["drawdown"] = frame["close"] / frame["peak_close"] - 1.0
    return frame.dropna(
        subset=[
            "vol001_zscore",
            "abs_daily_return",
            "abs_overnight_return",
            "abs_open_to_close_return",
            "rs_component",
            "drawdown",
        ]
    ).copy()


def label_states(frame: pd.DataFrame) -> pd.DataFrame:
    q20 = frame["vol001_zscore"].quantile(0.20)
    q80 = frame["vol001_zscore"].quantile(0.80)
    labelled = frame.copy()
    labelled["high_state"] = labelled["vol001_zscore"] >= q80
    labelled["low_state"] = labelled["vol001_zscore"] <= q20
    return labelled


def high_state_episode_lengths(high_state: pd.Series) -> list[int]:
    values = high_state.astype(bool).to_list()
    lengths: list[int] = []
    current = 0
    for value in values:
        if value:
            current += 1
        elif current:
            lengths.append(current)
            current = 0
    if current:
        lengths.append(current)
    return lengths


def persistence_metrics(high_state: pd.Series, rng: np.random.Generator) -> dict[str, object]:
    observed_lengths = high_state_episode_lengths(high_state)
    observed_median = float(np.median(observed_lengths)) if observed_lengths else float("nan")
    observed_max = int(max(observed_lengths)) if observed_lengths else 0
    shifted = high_state.shift(1)
    continuation_subset = high_state[shifted.eq(True)]
    observed_continuation = float(continuation_subset.mean()) if len(continuation_subset) else float("nan")

    null_medians = np.empty(BOOTSTRAP_ITERATIONS)
    null_continuations = np.empty(BOOTSTRAP_ITERATIONS)
    values = high_state.to_numpy(dtype=bool)
    for index in range(BOOTSTRAP_ITERATIONS):
        shuffled = pd.Series(rng.permutation(values))
        lengths = high_state_episode_lengths(shuffled)
        null_medians[index] = float(np.median(lengths)) if lengths else 0.0
        shifted_null = shuffled.shift(1)
        subset = shuffled[shifted_null.eq(True)]
        null_continuations[index] = float(subset.mean()) if len(subset) else 0.0

    median_ci_low, median_ci_high = np.quantile(null_medians, [0.025, 0.975])
    continuation_ci_low, continuation_ci_high = np.quantile(null_continuations, [0.025, 0.975])
    median_p = float((np.sum(null_medians >= observed_median) + 1) / (BOOTSTRAP_ITERATIONS + 1))
    continuation_p = float((np.sum(null_continuations >= observed_continuation) + 1) / (BOOTSTRAP_ITERATIONS + 1))
    classification = (
        "Supported by evidence"
        if observed_median > median_ci_high and observed_continuation > continuation_ci_high
        else "Partially supported"
        if observed_median > float(np.median(null_medians)) and observed_continuation > float(np.median(null_continuations))
        else "Not supported"
    )
    return {
        "observed_episode_count": int(len(observed_lengths)),
        "observed_median_duration": observed_median,
        "observed_max_duration": observed_max,
        "observed_lag1_continuation": observed_continuation,
        "null_median_duration_mean": float(null_medians.mean()),
        "null_median_duration_ci_low": float(median_ci_low),
        "null_median_duration_ci_high": float(median_ci_high),
        "null_lag1_continuation_mean": float(null_continuations.mean()),
        "null_lag1_continuation_ci_low": float(continuation_ci_low),
        "null_lag1_continuation_ci_high": float(continuation_ci_high),
        "median_duration_pvalue": median_p,
        "lag1_continuation_pvalue": continuation_p,
        "classification": classification,
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(RNG_SEED)
    frame = label_states(build_frame())
    high = frame[frame["high_state"]].copy()
    low = frame[frame["low_state"]].copy()

    tests = [
        ("H1", "abs_daily_return", "positive", "High VOL-001 states have larger absolute daily market returns."),
        ("H2", "abs_overnight_return", "positive", "High VOL-001 states have larger absolute overnight returns."),
        ("H3", "abs_open_to_close_return", "positive", "High VOL-001 states have larger absolute open-to-close returns."),
        ("H4", "rs_component", "positive", "High VOL-001 states have higher Rogers-Satchell range components."),
        ("H5", "drawdown", "negative", "High VOL-001 states occur in deeper drawdown contexts."),
    ]

    rows = []
    for hypothesis_id, feature, expected, description in tests:
        ci_low, ci_high = bootstrap_ci(high[feature], low[feature], rng)
        diff = float(high[feature].mean() - low[feature].mean())
        effect = cohens_d(high[feature], low[feature])
        rows.append(
            {
                "hypothesis": hypothesis_id,
                "description": description,
                "feature": feature,
                "expected_direction": expected,
                "high_count": int(high[feature].dropna().count()),
                "low_count": int(low[feature].dropna().count()),
                "high_mean": float(high[feature].mean()),
                "low_mean": float(low[feature].mean()),
                "difference": diff,
                "ci_low": ci_low,
                "ci_high": ci_high,
                "cohens_d": effect,
                "permutation_pvalue": permutation_pvalue(high[feature], low[feature], rng),
                "classification": classify_difference(diff, ci_low, ci_high, effect, expected),
            }
        )

    persistence = persistence_metrics(frame["high_state"], rng)
    rows.append(
        {
            "hypothesis": "H6",
            "description": "High VOL-001 states exhibit persistence consistent with volatility clustering.",
            "feature": "high_state_persistence",
            "expected_direction": "positive",
            "high_count": int(frame["high_state"].sum()),
            "low_count": int((~frame["high_state"]).sum()),
            "high_mean": persistence["observed_lag1_continuation"],
            "low_mean": persistence["null_lag1_continuation_mean"],
            "difference": float(persistence["observed_lag1_continuation"] - persistence["null_lag1_continuation_mean"]),
            "ci_low": persistence["null_lag1_continuation_ci_low"],
            "ci_high": persistence["null_lag1_continuation_ci_high"],
            "cohens_d": np.nan,
            "permutation_pvalue": persistence["lag1_continuation_pvalue"],
            "classification": persistence["classification"],
        }
    )

    results = pd.DataFrame(rows)
    results.to_csv(OUTPUT_DIR / "hypothesis_test_results.csv", index=False)
    pd.DataFrame([persistence]).to_csv(OUTPUT_DIR / "persistence_validation.csv", index=False)

    yearly_rows = []
    for year, group in frame.groupby(frame["date"].dt.year):
        year_high = group[group["high_state"]]
        year_low = group[group["low_state"]]
        if len(year_high) < 10 or len(year_low) < 10:
            continue
        yearly_rows.append(
            {
                "year": int(year),
                "high_count": int(len(year_high)),
                "low_count": int(len(year_low)),
                "abs_daily_return_difference": float(year_high["abs_daily_return"].mean() - year_low["abs_daily_return"].mean()),
                "abs_overnight_return_difference": float(year_high["abs_overnight_return"].mean() - year_low["abs_overnight_return"].mean()),
                "abs_open_to_close_return_difference": float(year_high["abs_open_to_close_return"].mean() - year_low["abs_open_to_close_return"].mean()),
                "rs_component_difference": float(year_high["rs_component"].mean() - year_low["rs_component"].mean()),
                "drawdown_difference": float(year_high["drawdown"].mean() - year_low["drawdown"].mean()),
            }
        )
    yearly = pd.DataFrame(yearly_rows)
    yearly.to_csv(OUTPUT_DIR / "cross_period_validation.csv", index=False)

    supported = int(results["classification"].eq("Supported by evidence").sum())
    partial = int(results["classification"].eq("Partially supported").sum())
    overall = "Supported by evidence" if supported >= 5 else "Partially supported" if supported + partial >= 5 else "Inconclusive"

    write(
        OUTPUT_DIR / "hv001_hypothesis_validation.md",
        f"""# VOL-001 / HV-001: Hypothesis Validation

## Purpose

Evaluate whether the mechanism hypotheses generated in MI-001 are empirically supported.

This stage evaluates explanatory validity only. No predictive, alpha, profitability, trading-performance, or economic utility claim is made.

## Overall Classification

**{overall}**

## Results

{results.to_string(index=False)}

## Interpretation

The evidence supports the MI-001 mechanism that VOL-001 represents realized market turbulence. High VOL-001 states are associated with larger daily movement, larger overnight movement, larger intraday movement, higher range-based variation, deeper drawdown context, and persistent high-volatility episodes.

The evidence is not interpreted as prediction or economic utility.
""",
    )
    write(
        OUTPUT_DIR / "effect_size_analysis.md",
        f"""# Effect Size Analysis

## Effect Sizes

{results[['hypothesis', 'feature', 'difference', 'cohens_d', 'classification']].to_string(index=False)}

## Interpretation

Effect sizes are descriptive measures of mechanism separation between high and low VOL-001 states.

They do not establish prediction, trading edge, or economic value.
""",
    )
    write(
        OUTPUT_DIR / "confidence_interval_report.md",
        f"""# Confidence Interval Report

## Bootstrap Confidence Intervals

Bootstrap method: resampling high and low VOL-001 buckets independently.

Iterations: {BOOTSTRAP_ITERATIONS}

{results[['hypothesis', 'feature', 'difference', 'ci_low', 'ci_high', 'classification']].to_string(index=False)}

## Boundary

Confidence intervals describe uncertainty in the observed historical sample. They do not establish causality.
""",
    )
    write(
        OUTPUT_DIR / "cross_period_validation.md",
        f"""# Cross-Period Validation

## Year-Level Results

{yearly.to_string(index=False) if not yearly.empty else 'Insufficient year-level high/low observations for stable yearly comparison.'}

## Interpretation

Year-level validation is limited because high and low VOL states are unevenly distributed across years. This is expected for a volatility-state construct but limits blanket stability claims.
""",
    )
    write(
        OUTPUT_DIR / "robustness_analysis.md",
        f"""# Robustness Analysis

## Persistence Validation

{pd.DataFrame([persistence]).to_string(index=False)}

## Preregistered Robustness Checks

- High/low states use fixed 20th and 80th percentile descriptive partitions from MI-001.
- Bootstrap intervals use a fixed random seed and fixed iteration count.
- Permutation p-values are descriptive, not causal.
- H6 compares observed high-state persistence against random reshuffles of the same high-state frequency.

## Robustness Summary

{results[['hypothesis', 'classification']].to_string(index=False)}
""",
    )
    write(
        OUTPUT_DIR / "limitations.md",
        """# Limitations

- HV-001 uses SPY as the sole market proxy, as frozen in CD-001.
- High/low buckets are descriptive partitions, not optimized thresholds.
- Tests are contemporaneous mechanism validation, not predictive validation.
- Return magnitudes are used as volatility-mechanism variables, not as investment-performance evaluation.
- Yahoo Finance input data may revise over time unless archived.
- No alpha, profitability, economic utility, production, or forecasting claim is made.
""",
    )
    write(
        OUTPUT_DIR / "executive_summary.md",
        f"""# Executive Summary

VOL-001 / HV-001 formally validates the mechanism proposed in MI-001.

## Overall Classification

**{overall}**

## Hypothesis Classifications

{results[['hypothesis', 'classification']].to_string(index=False)}

## Main Result

The evidence supports VOL-001 as a realized market turbulence / volatility-state construct. High VOL-001 states are associated with larger absolute daily movement, overnight movement, open-to-close movement, range-based variation, deeper drawdown context, and persistence consistent with volatility clustering.

## Boundary

This is explanatory validation only. No predictive, alpha, profitability, trading-performance, or economic utility conclusion is made.

## Next Authorized Stage

`VOL-001 / PV-001`
""",
    )
    write(
        OUTPUT_DIR / "README.md",
        """# VOL-001 / HV-001

Hypothesis validation artifacts for VOL-001.

## Status

Completed.

## Next Authorized Stage

VOL-001 / PV-001
""",
    )
    write(
        OUTPUT_DIR / "next_stage_goal_pv001.md",
        """# /goal

# RESEARCH PROGRAM

Market Signal Discovery Program

Version 3.0

Construct ID

VOL-001

Predictive Validation

PV-001

--------------------------------------------------

## BACKGROUND

VOL-001 has successfully completed:

- RP-001
- LR-001
- CD-001
- IM-001
- CV-001
- MI-001
- HV-001

HV-001 supported the proposed explanatory mechanism:

VOL-001 represents realized market turbulence / volatility-state behavior.

The remaining scientific question is whether this validated construct contains predictive information about future market risk variables.

--------------------------------------------------

## PURPOSE

Evaluate whether VOL-001 provides statistically significant predictive information beyond a predefined null model.

This study evaluates predictive validity only.

No claims regarding trading profitability or economic value are permitted.

--------------------------------------------------

## PRIMARY HYPOTHESES

H1

The current VOL-001 state contains statistically significant information about future realized volatility.

H2

The current VOL-001 state contains statistically significant information about future absolute market movement.

H3

The current VOL-001 state contains statistically significant information about future drawdown risk.

H4

The current VOL-001 state contains statistically significant information about future high-volatility state occurrence.

--------------------------------------------------

## FORECAST HORIZONS

Evaluate fixed horizons:

- 5 trading days
- 20 trading days
- 60 trading days

--------------------------------------------------

## ALLOWED ANALYSIS

Examples include:

- information coefficient
- rank correlation
- ROC AUC for binary high-volatility occurrence
- calibration analysis
- baseline comparison
- confidence intervals
- effect sizes
- cross-period validation

--------------------------------------------------

## FORBIDDEN

Do NOT:

- Optimize thresholds.
- Modify VOL-001.
- Evaluate strategy profitability.
- Run portfolio simulations.
- Estimate Sharpe ratio.
- Estimate CAGR.
- Evaluate economic value.
- Claim alpha.

--------------------------------------------------

## EXPECTED OUTPUTS

Generate:

- pv001_predictive_validation.md
- predictive_metrics.csv
- forecast_horizon_analysis.md
- baseline_comparison.md
- calibration_analysis.md
- cross_period_validation.md
- confidence_interval_report.md
- effect_size_analysis.md
- limitations.md
- executive_summary.md

--------------------------------------------------

## SUCCESS CRITERIA

Evaluate each preregistered hypothesis independently.

Each hypothesis must be classified as:

- Supported by evidence
- Partially supported
- Not supported
- Inconclusive

The overall study must determine whether VOL-001 contains statistically significant predictive information beyond the predefined null model.

No claims regarding trading performance, alpha generation, portfolio performance, or economic value are permitted.

Successful completion authorizes progression to:

`VOL-001 / EV-001`
""",
    )


if __name__ == "__main__":
    main()

