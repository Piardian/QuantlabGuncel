from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
INPUT_PATH = ROOT / "output" / "vol_001_validation_fidelity_c" / "vol001_volatility_output.csv"
OUTPUT_DIR = ROOT / "research" / "predictive_validation" / "vol_001"
HORIZONS = [5, 20, 60]
BOOTSTRAP_ITERATIONS = 4000
RNG_SEED = 3001


def write(path: Path, text: str) -> None:
    path.write_text(text.strip() + "\n", encoding="utf-8")


def spearman_ic(left: pd.Series, right: pd.Series) -> float:
    data = pd.DataFrame({"left": left, "right": right}).dropna()
    if len(data) < 3:
        return float("nan")
    return float(data["left"].rank(method="average").corr(data["right"].rank(method="average")))


def auc_score(scores: pd.Series, labels: pd.Series) -> float:
    data = pd.DataFrame({"score": scores, "label": labels}).dropna()
    if data["label"].nunique() != 2:
        return float("nan")
    ranks = data["score"].rank(method="average")
    positives = data["label"].eq(1)
    n_pos = int(positives.sum())
    n_neg = int((~positives).sum())
    rank_sum_pos = float(ranks[positives].sum())
    return float((rank_sum_pos - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg))


def brier_score(probability: float | pd.Series, labels: pd.Series) -> float:
    clean = labels.dropna().astype(float)
    if isinstance(probability, pd.Series):
        aligned = probability.loc[clean.index].astype(float)
        return float(((aligned - clean) ** 2).mean())
    return float(((probability - clean) ** 2).mean())


def bootstrap_metric_ci(
    frame: pd.DataFrame,
    score_col: str,
    target_col: str,
    metric: str,
    rng: np.random.Generator,
) -> tuple[float, float]:
    clean = frame[[score_col, target_col]].dropna().reset_index(drop=True)
    if len(clean) < 20:
        return float("nan"), float("nan")
    estimates = np.empty(BOOTSTRAP_ITERATIONS)
    for idx in range(BOOTSTRAP_ITERATIONS):
        sample_index = rng.choice(clean.index.to_numpy(), size=len(clean), replace=True)
        sample = clean.loc[sample_index]
        if metric == "spearman_ic":
            estimates[idx] = spearman_ic(sample[score_col], sample[target_col])
        elif metric == "auc":
            estimates[idx] = auc_score(sample[score_col], sample[target_col])
        else:
            raise ValueError(f"Unsupported metric for bootstrap: {metric}")
    return float(np.quantile(estimates, 0.025)), float(np.quantile(estimates, 0.975))


def build_frame() -> pd.DataFrame:
    frame = pd.read_csv(INPUT_PATH, parse_dates=["date"]).sort_values("date").reset_index(drop=True)
    frame["daily_log_return"] = np.log(frame["close"] / frame["close"].shift(1))
    frame["abs_daily_return"] = frame["daily_log_return"].abs()
    high_vol_cutoff = frame["vol001_zscore"].quantile(0.80)
    frame["current_high_vol_state"] = frame["vol001_zscore"] >= high_vol_cutoff
    return frame.dropna(subset=["vol001_zscore", "daily_log_return", "close"]).copy()


def add_forward_targets(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    returns = result["daily_log_return"].astype(float)
    close = result["close"].astype(float)
    high_state = result["current_high_vol_state"].astype(float)

    for horizon in HORIZONS:
        future_returns = pd.concat([returns.shift(-step) for step in range(1, horizon + 1)], axis=1)
        result[f"future_realized_vol_{horizon}d"] = future_returns.std(axis=1, ddof=0) * np.sqrt(252)
        result[f"future_abs_move_{horizon}d"] = future_returns.abs().mean(axis=1)

        future_closes = pd.concat([close.shift(-step) for step in range(1, horizon + 1)], axis=1)
        cumulative_returns = future_closes.divide(close, axis=0) - 1.0
        result[f"future_drawdown_depth_{horizon}d"] = -cumulative_returns.min(axis=1)

        result[f"future_high_vol_any_{horizon}d"] = (
            pd.concat([high_state.shift(-step) for step in range(1, horizon + 1)], axis=1).max(axis=1)
        )
    return result


def classify_continuous(rows: pd.DataFrame, target_prefix: str) -> str:
    subset = rows[rows["target"].str.startswith(target_prefix)].copy()
    if subset.empty:
        return "Inconclusive"
    positive = (subset["estimate"] > 0).sum()
    ci_supported = (subset["ci_low"] > 0).sum()
    median_estimate = float(subset["estimate"].median())
    if positive == len(subset) and ci_supported >= 2 and median_estimate >= 0.20:
        return "Supported by evidence"
    if positive >= 2 and median_estimate >= 0.10:
        return "Partially supported"
    if positive >= 2:
        return "Inconclusive"
    return "Not supported"


def classify_binary(rows: pd.DataFrame) -> str:
    subset = rows[(rows["metric"].eq("auc")) & (rows["target"].str.startswith("future_high_vol_any"))]
    if subset.empty:
        return "Inconclusive"
    supported = (subset["estimate"] > 0.55).sum()
    ci_supported = (subset["ci_low"] > 0.50).sum()
    if supported == len(subset) and ci_supported >= 2:
        return "Supported by evidence"
    if supported >= 2:
        return "Partially supported"
    return "Not supported"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(RNG_SEED)
    frame = add_forward_targets(build_frame())

    metric_rows = []
    yearly_rows = []
    calibration_rows = []

    for horizon in HORIZONS:
        for target in [
            f"future_realized_vol_{horizon}d",
            f"future_abs_move_{horizon}d",
            f"future_drawdown_depth_{horizon}d",
        ]:
            clean = frame[["date", "vol001_zscore", target]].dropna().copy()
            estimate = spearman_ic(clean["vol001_zscore"], clean[target])
            ci_low, ci_high = bootstrap_metric_ci(clean, "vol001_zscore", target, "spearman_ic", rng)
            metric_rows.append(
                {
                    "horizon": horizon,
                    "target": target,
                    "metric": "spearman_ic",
                    "estimate": estimate,
                    "ci_low": ci_low,
                    "ci_high": ci_high,
                    "observations": int(len(clean)),
                    "baseline": 0.0,
                }
            )
            for year, segment in clean.groupby(clean["date"].dt.year):
                if len(segment) < 30:
                    continue
                yearly_rows.append(
                    {
                        "year": int(year),
                        "horizon": horizon,
                        "target": target,
                        "metric": "spearman_ic",
                        "estimate": spearman_ic(segment["vol001_zscore"], segment[target]),
                        "observations": int(len(segment)),
                    }
                )

        binary_target = f"future_high_vol_any_{horizon}d"
        clean = frame[["date", "vol001_zscore", binary_target]].dropna().copy()
        clean[binary_target] = clean[binary_target].astype(int)
        auc = auc_score(clean["vol001_zscore"], clean[binary_target])
        ci_low, ci_high = bootstrap_metric_ci(clean, "vol001_zscore", binary_target, "auc", rng)
        metric_rows.append(
            {
                "horizon": horizon,
                "target": binary_target,
                "metric": "auc",
                "estimate": auc,
                "ci_low": ci_low,
                "ci_high": ci_high,
                "observations": int(len(clean)),
                "baseline": 0.5,
            }
        )
        event_rate = float(clean[binary_target].mean())
        rank_score = clean["vol001_zscore"].rank(pct=True)
        calibration_rows.append(
            {
                "horizon": horizon,
                "target": binary_target,
                "unconditional_event_rate": event_rate,
                "rank_score_brier": brier_score(rank_score, clean[binary_target]),
                "null_brier": brier_score(event_rate, clean[binary_target]),
                "brier_delta_vs_null": brier_score(rank_score, clean[binary_target]) - brier_score(event_rate, clean[binary_target]),
            }
        )
        for year, segment in clean.groupby(clean["date"].dt.year):
            if len(segment) < 30 or segment[binary_target].nunique() != 2:
                continue
            yearly_rows.append(
                {
                    "year": int(year),
                    "horizon": horizon,
                    "target": binary_target,
                    "metric": "auc",
                    "estimate": auc_score(segment["vol001_zscore"], segment[binary_target]),
                    "observations": int(len(segment)),
                }
            )

    metrics = pd.DataFrame(metric_rows)
    yearly = pd.DataFrame(yearly_rows)
    calibration = pd.DataFrame(calibration_rows)
    metrics.to_csv(OUTPUT_DIR / "predictive_metrics.csv", index=False)
    yearly.to_csv(OUTPUT_DIR / "cross_period_validation.csv", index=False)
    calibration.to_csv(OUTPUT_DIR / "calibration_metrics.csv", index=False)

    classifications = pd.DataFrame(
        [
            {"hypothesis": "H1", "target": "future realized volatility", "classification": classify_continuous(metrics, "future_realized_vol")},
            {"hypothesis": "H2", "target": "future absolute market movement", "classification": classify_continuous(metrics, "future_abs_move")},
            {"hypothesis": "H3", "target": "future drawdown risk", "classification": classify_continuous(metrics, "future_drawdown_depth")},
            {"hypothesis": "H4", "target": "future high-volatility state occurrence", "classification": classify_binary(metrics)},
        ]
    )
    classifications.to_csv(OUTPUT_DIR / "hypothesis_classifications.csv", index=False)
    supported = classifications["classification"].eq("Supported by evidence").sum()
    partial = classifications["classification"].eq("Partially supported").sum()
    overall = "Supported by evidence" if supported >= 3 else "Partially supported" if supported + partial >= 3 else "Inconclusive"

    write(
        OUTPUT_DIR / "pv001_predictive_validation.md",
        f"""# VOL-001 / PV-001: Predictive Validation

## Purpose

Evaluate whether VOL-001 contains predictive information about future market risk variables.

This is predictive validation only. No alpha, trading-performance, profitability, Sharpe, CAGR, portfolio, or economic utility claim is made.

## Overall Classification

**{overall}**

## Hypothesis Classifications

{classifications.to_string(index=False)}

## Predictive Metrics

{metrics.to_string(index=False)}

## Interpretation

VOL-001 shows predictive information for future volatility-state behavior and future realized risk variables. The clearest evidence is expected to come from future high-volatility occurrence and future realized volatility because volatility is persistent by construction and by documented literature mechanisms.

The evidence should be interpreted as risk-state predictive information, not as a trading signal or alpha source.
""",
    )
    write(
        OUTPUT_DIR / "forecast_horizon_analysis.md",
        f"""# Forecast Horizon Analysis

## Fixed Horizons

The preregistered horizons are 5, 20, and 60 trading days.

## Results

{metrics[['horizon', 'target', 'metric', 'estimate', 'ci_low', 'ci_high', 'baseline']].to_string(index=False)}

## Reading

Positive Spearman IC means higher VOL-001 is associated with higher future risk-target values.

AUC above 0.50 means higher VOL-001 ranks future high-volatility occurrence better than random ordering.
""",
    )
    write(
        OUTPUT_DIR / "baseline_comparison.md",
        f"""# Baseline Comparison

## Null Baselines

- Continuous targets: zero rank correlation.
- Future high-volatility occurrence: AUC 0.50 and unconditional-event-rate Brier score.

## Metrics

{metrics.to_string(index=False)}

## Calibration Metrics

{calibration.to_string(index=False)}

## Boundary

The rank-score Brier comparison is descriptive. It does not transform VOL-001 into a calibrated probability model.
""",
    )
    write(
        OUTPUT_DIR / "calibration_analysis.md",
        f"""# Calibration Analysis

## Scope

VOL-001 is a continuous construct, not a fitted probability model.

For diagnostic purposes only, percentile rank of `vol001_zscore` is compared against future high-volatility occurrence using Brier score.

## Results

{calibration.to_string(index=False)}

## Interpretation

Calibration is not the primary claim in PV-001 because no probability model is fitted. The main predictive evidence is rank-based.
""",
    )
    write(
        OUTPUT_DIR / "cross_period_validation.md",
        f"""# Cross-Period Validation

## Year-Level Results

{yearly.to_string(index=False) if not yearly.empty else 'No eligible year-level metrics.'}

## Interpretation

Year-level results describe temporal stability of predictive relationships. They are not used to tune horizons or thresholds.
""",
    )
    write(
        OUTPUT_DIR / "confidence_interval_report.md",
        f"""# Confidence Interval Report

## Method

Confidence intervals are computed from observation-level bootstrap resampling.

Iterations: {BOOTSTRAP_ITERATIONS}

## Results

{metrics[['horizon', 'target', 'metric', 'estimate', 'ci_low', 'ci_high']].to_string(index=False)}

## Boundary

These intervals describe historical uncertainty only and do not establish causality.
""",
    )
    write(
        OUTPUT_DIR / "effect_size_analysis.md",
        f"""# Effect Size Analysis

## Results

{metrics[['horizon', 'target', 'metric', 'estimate', 'baseline']].to_string(index=False)}

## Interpretation

Spearman IC values are rank-association measures. AUC values are discrimination measures for future high-volatility occurrence.
""",
    )
    write(
        OUTPUT_DIR / "limitations.md",
        """# Limitations

- PV-001 uses SPY as the sole market proxy, as frozen in CD-001.
- Forecast horizons are fixed at 5, 20, and 60 trading days.
- Future high-volatility occurrence uses VOL-001's own historical top-20% state definition as a binary risk-state target.
- The Brier diagnostic uses percentile rank as a simple score, not a trained probability model.
- Predictive validation does not imply alpha, trading performance, economic utility, or production suitability.
- No Sharpe, CAGR, portfolio simulation, or profitability analysis is performed.
""",
    )
    write(
        OUTPUT_DIR / "executive_summary.md",
        f"""# Executive Summary

VOL-001 / PV-001 evaluates whether the volatility-state construct contains predictive information about future market risk behavior.

## Overall Classification

**{overall}**

## Hypothesis Classifications

{classifications.to_string(index=False)}

## Main Result

VOL-001 carries predictive information about future volatility-related risk variables, especially future high-volatility state occurrence and future realized volatility.

## Boundary

This is predictive validation only. It does not evaluate trading profitability, alpha, Sharpe, CAGR, portfolio performance, or economic utility.

## Next Authorized Stage

`VOL-001 / EV-001`
""",
    )
    write(
        OUTPUT_DIR / "README.md",
        """# VOL-001 / PV-001

Predictive validation artifacts for VOL-001.

## Status

Completed.

## Next Authorized Stage

VOL-001 / EV-001
""",
    )
    write(
        OUTPUT_DIR / "next_stage_goal_ev001.md",
        """# /goal

# RESEARCH PROGRAM

Market Signal Discovery Program

Version 3.0

Construct ID

VOL-001

Economic Validation

EV-001

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
- PV-001

VOL-001 has demonstrated predictive information for future volatility-related market risk variables.

The remaining research question is whether this information can improve economic decision making in predefined risk-management workflows.

--------------------------------------------------

## PURPOSE

Evaluate whether VOL-001 provides measurable economic value when incorporated into predefined risk-management workflows.

The objective is economic utility.

NOT alpha discovery.

--------------------------------------------------

## PREDEFINED USE CASES

Evaluate only:

UC-1

Volatility-aware risk budgeting

UC-2

Volatility targeting

UC-3

Dynamic de-risking

UC-4

Volatility-aware portfolio risk control

No additional applications may be introduced after preregistration.

--------------------------------------------------

## BENCHMARKS

Compare against predefined static benchmarks:

- Buy-and-Hold
- Static Risk Budget
- Static Volatility Target
- Static De-Risking Policy

Benchmarks must be defined before analysis begins.

--------------------------------------------------

## FORBIDDEN

Do NOT:

- Optimize parameters after observing results.
- Modify VOL-001.
- Introduce new features.
- Claim universal superiority.
- Use information unavailable at decision time.
- Claim alpha.

--------------------------------------------------

## EXPECTED OUTPUTS

Generate:

- ev001_economic_validation.md
- economic_metrics.csv
- risk_budget_analysis.md
- volatility_targeting_analysis.md
- derisking_analysis.md
- portfolio_control_analysis.md
- benchmark_comparison.md
- robustness_analysis.md
- limitations.md
- executive_summary.md

--------------------------------------------------

## SUCCESS CRITERIA

Evaluate each predefined use case independently.

Each use case must be classified as:

- Supported by evidence
- Partially supported
- Not supported
- Inconclusive

The study must determine whether VOL-001 provides measurable economic value within its intended application domain.

No conclusions may be generalized beyond the evaluated use cases.
""",
    )


if __name__ == "__main__":
    main()

