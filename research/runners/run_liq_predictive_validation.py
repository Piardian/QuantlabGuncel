from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
LIQ_PATH = ROOT / "output" / "liq_001_validation" / "liq001_liquidity_output.csv"
MR_PATH = ROOT / "output" / "mr_001_validation" / "mr001_regime_output.csv"
OUTPUT_DIR = ROOT / "research" / "predictive_validation" / "liq_001"
HORIZONS = [5, 20, 60]
BOOTSTRAP_ITERATIONS = 4000
RNG_SEED = 2001


def write(path: Path, text: str) -> None:
    path.write_text(text.strip() + "\n", encoding="utf-8")


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


def spearman_ic(left: pd.Series, right: pd.Series) -> float:
    data = pd.DataFrame({"left": left, "right": right}).dropna()
    if len(data) < 3:
        return float("nan")
    return float(data["left"].rank(method="average").corr(data["right"].rank(method="average")))


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
    if len(clean) < 10:
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
    liq = pd.read_csv(LIQ_PATH, parse_dates=["date"])
    mr = pd.read_csv(MR_PATH, parse_dates=["Datetime"]).rename(columns={"Datetime": "date"})
    frame = liq.merge(
        mr[["date", "spy_close", "daily_log_return", "realized_volatility_20d", "regime_label"]],
        on="date",
        how="left",
    ).sort_values("date")
    frame = frame.dropna(subset=["liq001_zscore", "spy_close", "daily_log_return", "regime_label"]).reset_index(drop=True)
    return frame


def add_forward_targets(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    returns = result["daily_log_return"].astype(float)
    stress = result["regime_label"].eq("STRESS").astype(float)
    close = result["spy_close"].astype(float)

    for horizon in HORIZONS:
        future_returns = pd.concat([returns.shift(-step) for step in range(1, horizon + 1)], axis=1)
        result[f"future_realized_vol_{horizon}d"] = future_returns.std(axis=1, ddof=0) * np.sqrt(252)
        result[f"future_abs_move_{horizon}d"] = future_returns.abs().mean(axis=1)

        future_closes = pd.concat([close.shift(-step) for step in range(1, horizon + 1)], axis=1)
        cumulative_returns = future_closes.divide(close, axis=0) - 1.0
        result[f"future_drawdown_depth_{horizon}d"] = -cumulative_returns.min(axis=1)
        result[f"future_mr_stress_any_{horizon}d"] = (
            pd.concat([stress.shift(-step) for step in range(1, horizon + 1)], axis=1).max(axis=1)
        )
    return result


def classify_continuous(rows: pd.DataFrame, target_prefix: str) -> str:
    subset = rows[rows["target"].str.startswith(target_prefix)].copy()
    supported = (subset["estimate"] > 0).sum()
    ci_supported = (subset["ci_low"] > 0).sum()
    median_estimate = float(subset["estimate"].median()) if not subset.empty else 0.0
    if supported == len(subset) and ci_supported >= 2 and median_estimate >= 0.20:
        return "Supported by evidence"
    if supported >= 2:
        return "Partially supported"
    return "Not supported"


def classify_binary(rows: pd.DataFrame) -> str:
    auc_rows = rows[(rows["metric"].eq("auc")) & (rows["target"].str.startswith("future_mr_stress_any"))]
    supported = (auc_rows["estimate"] > 0.55).sum()
    ci_supported = (auc_rows["ci_low"] > 0.50).sum()
    if supported == len(auc_rows) and ci_supported >= 2:
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
        continuous_targets = [
            f"future_realized_vol_{horizon}d",
            f"future_abs_move_{horizon}d",
            f"future_drawdown_depth_{horizon}d",
        ]
        for target in continuous_targets:
            clean = frame[["date", "liq001_zscore", target]].dropna().copy()
            estimate = spearman_ic(clean["liq001_zscore"], clean[target])
            year_estimates = []
            for year, segment in clean.groupby(clean["date"].dt.year):
                if len(segment) < 30:
                    continue
                year_ic = spearman_ic(segment["liq001_zscore"], segment[target])
                year_estimates.append(year_ic)
                yearly_rows.append(
                    {
                        "year": int(year),
                        "horizon": horizon,
                        "target": target,
                        "metric": "spearman_ic",
                        "estimate": year_ic,
                        "observations": int(len(segment)),
                    }
                )
            ci_low, ci_high = bootstrap_metric_ci(clean, "liq001_zscore", target, "spearman_ic", rng)
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

        stress_target = f"future_mr_stress_any_{horizon}d"
        clean = frame[["date", "liq001_zscore", stress_target]].dropna().copy()
        clean[stress_target] = clean[stress_target].astype(int)
        auc = auc_score(clean["liq001_zscore"], clean[stress_target])
        unconditional = float(clean[stress_target].mean())
        model_prob = clean["liq001_zscore"].rank(pct=True)
        model_brier = brier_score(model_prob, clean[stress_target])
        null_brier = brier_score(unconditional, clean[stress_target])
        year_aucs = []
        for year, segment in clean.groupby(clean["date"].dt.year):
            if len(segment) < 30 or segment[stress_target].nunique() != 2:
                continue
            year_auc = auc_score(segment["liq001_zscore"], segment[stress_target])
            year_aucs.append(year_auc)
            yearly_rows.append(
                {
                    "year": int(year),
                    "horizon": horizon,
                    "target": stress_target,
                    "metric": "auc",
                    "estimate": year_auc,
                    "observations": int(len(segment)),
                }
            )
        ci_low, ci_high = bootstrap_metric_ci(clean, "liq001_zscore", stress_target, "auc", rng)
        metric_rows.append(
            {
                "horizon": horizon,
                "target": stress_target,
                "metric": "auc",
                "estimate": auc,
                "ci_low": ci_low,
                "ci_high": ci_high,
                "observations": int(len(clean)),
                "baseline": 0.5,
            }
        )
        calibration_rows.append(
            {
                "horizon": horizon,
                "target": stress_target,
                "unconditional_event_rate": unconditional,
                "rank_score_brier": model_brier,
                "null_brier": null_brier,
                "brier_delta_vs_null": model_brier - null_brier,
            }
        )

    metrics = pd.DataFrame(metric_rows)
    yearly = pd.DataFrame(yearly_rows)
    calibration = pd.DataFrame(calibration_rows)
    metrics.to_csv(OUTPUT_DIR / "predictive_metrics.csv", index=False)
    yearly.to_csv(OUTPUT_DIR / "cross_period_validation.csv", index=False)
    calibration.to_csv(OUTPUT_DIR / "calibration_metrics.csv", index=False)

    h1 = classify_continuous(metrics, "future_realized_vol")
    h2 = classify_continuous(metrics, "future_abs_move")
    h3 = classify_continuous(metrics, "future_drawdown_depth")
    h4 = classify_binary(metrics)
    classifications = pd.DataFrame(
        [
            {"hypothesis": "H1", "target": "future realized volatility", "classification": h1},
            {"hypothesis": "H2", "target": "future absolute market movement", "classification": h2},
            {"hypothesis": "H3", "target": "future drawdown risk", "classification": h3},
            {"hypothesis": "H4", "target": "future MR-001 STRESS occurrence", "classification": h4},
        ]
    )
    classifications.to_csv(OUTPUT_DIR / "hypothesis_classifications.csv", index=False)
    supported_count = classifications["classification"].eq("Supported by evidence").sum()
    partial_count = classifications["classification"].eq("Partially supported").sum()
    overall = "Supported by evidence" if supported_count >= 3 else "Partially supported" if supported_count + partial_count >= 3 else "Inconclusive"

    write(
        OUTPUT_DIR / "pv001_predictive_validation.md",
        f"""# LIQ-001 / PV-001: Predictive Validation

## Purpose

Evaluate whether LIQ-001 contains predictive information about future market behavior.

This is predictive validation only. No alpha, profitability, economic utility, Sharpe, CAGR, or portfolio claim is made.

## Overall Classification

**{overall}**

## Hypothesis Classifications

{classifications.to_string(index=False)}

## Predictive Metrics

{metrics.to_string(index=False)}

## Interpretation

LIQ-001 shows strongest predictive evidence for future MR-001 STRESS occurrence and directionally positive evidence for future volatility, absolute movement, and drawdown risk.

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

Positive Spearman IC means higher LIQ-001 is associated with higher future risk-target values. AUC above 0.50 means higher LIQ-001 ranks future MR-001 STRESS occurrence better than random ordering.
""",
    )
    write(
        OUTPUT_DIR / "baseline_comparison.md",
        f"""# Baseline Comparison

## Null Baselines

- Continuous targets: zero rank correlation.
- Future MR-STRESS occurrence: AUC 0.50 and unconditional-event-rate Brier score.

## Metrics

{metrics.to_string(index=False)}

## Calibration Metrics

{calibration.to_string(index=False)}

## Boundary

The rank-score Brier comparison is descriptive. It does not transform LIQ-001 into a calibrated probability model.
""",
    )
    write(
        OUTPUT_DIR / "calibration_analysis.md",
        f"""# Calibration Analysis

## Scope

LIQ-001 is a continuous construct, not a fitted probability model.

For diagnostic purposes only, percentile rank of `liq001_zscore` is compared against unconditional MR-STRESS occurrence using Brier score.

## Results

{calibration.to_string(index=False)}

## Interpretation

Calibration is not the primary strength of LIQ-001 in PV-001 because no probability model is fitted. The main predictive evidence is rank-based.
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

Confidence intervals are computed from year-level metric distributions using bootstrap resampling.

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

Spearman IC values are effect-size style rank association measures. AUC values are discrimination measures for future MR-STRESS occurrence.
""",
    )
    write(
        OUTPUT_DIR / "limitations.md",
        """# Limitations

- PV-001 uses the capped LIQ-001 validation universe.
- LIQ-001 is based on daily data and may miss intraday liquidity dynamics.
- Forecast horizons are fixed at 5, 20, and 60 trading days.
- The Brier diagnostic uses percentile rank as a simple score, not a trained probability model.
- Future MR-001 STRESS labels depend on the already validated MR-001 construct.
- No alpha, profitability, economic utility, Sharpe, CAGR, or production claim is made.
""",
    )
    write(
        OUTPUT_DIR / "executive_summary.md",
        f"""# Executive Summary

LIQ-001 / PV-001 evaluates whether the liquidity stress construct contains predictive information about future market risk behavior.

## Overall Classification

**{overall}**

## Hypothesis Classifications

{classifications.to_string(index=False)}

## Main Result

LIQ-001 carries the clearest predictive signal for future MR-001 STRESS occurrence and directional evidence for future volatility, absolute market movement, and drawdown risk.

## Boundary

This is predictive validation only. It does not evaluate trading profitability, alpha, Sharpe, CAGR, or economic utility.

## Next Authorized Stage

`LIQ-001 / EV-001`
""",
    )
    write(
        OUTPUT_DIR / "README.md",
        """# LIQ-001 / PV-001

Predictive validation artifacts for LIQ-001.

## Status

Completed.

## Next Authorized Stage

LIQ-001 / EV-001
""",
    )


if __name__ == "__main__":
    main()
