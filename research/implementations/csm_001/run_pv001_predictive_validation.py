from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[3]
STATE_FILE = REPO_ROOT / "output" / "csm_001_cv001" / "csm001_construct_state.csv"
OUTPUT_DIR = REPO_ROOT / "research" / "market_edge_discovery_program" / "csm_001_pv_001_predictive_validation"

HORIZONS = [21, 63, 126]
BOOTSTRAP_SEED = 2001
BOOTSTRAP_ITERATIONS = 2000


def _safe_float(value: float) -> float | None:
    if pd.isna(value) or not np.isfinite(value):
        return None
    return float(value)


def _bootstrap_ci(values: pd.Series) -> tuple[float | None, float | None]:
    clean = values.dropna().to_numpy(dtype=float)
    if len(clean) == 0:
        return None, None
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    stats = []
    for _ in range(BOOTSTRAP_ITERATIONS):
        sample = rng.choice(clean, size=len(clean), replace=True)
        stats.append(float(np.mean(sample)))
    return float(np.percentile(stats, 2.5)), float(np.percentile(stats, 97.5))


def _spearman_no_scipy(x: pd.Series, y: pd.Series) -> float:
    aligned = pd.concat([x, y], axis=1).dropna()
    if len(aligned) < 50:
        return np.nan
    return float(aligned.iloc[:, 0].rank(method="average").corr(aligned.iloc[:, 1].rank(method="average")))


def _load_state() -> pd.DataFrame:
    usecols = [
        "date",
        "ticker",
        "adjusted_close",
        "return_12_1",
        "csm001_momentum_score",
        "csm001_top_decile_flag",
        "csm001_valid_observation",
    ]
    frame = pd.read_csv(STATE_FILE, usecols=usecols, parse_dates=["date"])
    frame = frame[frame["csm001_valid_observation"].astype(bool)].copy()
    frame["csm001_top_decile_flag"] = frame["csm001_top_decile_flag"].astype(bool)
    score_decile = np.floor(frame["csm001_momentum_score"] * 10).astype(int) + 1
    frame["score_decile"] = np.clip(score_decile, 1, 10)
    return frame.sort_values(["date", "ticker"]).reset_index(drop=True)


def _add_future_outcomes(frame: pd.DataFrame) -> pd.DataFrame:
    close_panel = frame.pivot(index="date", columns="ticker", values="adjusted_close").sort_index()
    enriched = frame.copy()
    for horizon in HORIZONS:
        future_return = close_panel.shift(-horizon) / close_panel - 1.0
        stacked = future_return.stack(future_stack=True).rename(f"future_return_{horizon}d").reset_index()
        enriched = enriched.merge(stacked, on=["date", "ticker"], how="left")
    return enriched


def _information_coefficient(enriched: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for horizon in HORIZONS:
        target = f"future_return_{horizon}d"
        daily = []
        for date, group in enriched.groupby("date", sort=True):
            corr = _spearman_no_scipy(group["csm001_momentum_score"], group[target])
            if pd.notna(corr):
                daily.append({"date": date, "ic": corr})
        daily_df = pd.DataFrame(daily)
        low, high = _bootstrap_ci(daily_df["ic"])
        rows.append(
            {
                "horizon_days": horizon,
                "metric": "daily_spearman_ic",
                "observations": int(len(daily_df)),
                "mean": _safe_float(daily_df["ic"].mean()),
                "median": _safe_float(daily_df["ic"].median()),
                "bootstrap_mean_ci_low": low,
                "bootstrap_mean_ci_high": high,
                "positive_day_rate": _safe_float((daily_df["ic"] > 0).mean()),
            }
        )
    return pd.DataFrame(rows)


def _decile_analysis(enriched: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for horizon in HORIZONS:
        target = f"future_return_{horizon}d"
        for decile, group in enriched.groupby("score_decile", sort=True):
            target_series = group[target].dropna()
            rows.append(
                {
                    "horizon_days": horizon,
                    "score_decile": int(decile),
                    "observations": int(len(target_series)),
                    "mean_future_return": _safe_float(target_series.mean()),
                    "median_future_return": _safe_float(target_series.median()),
                    "positive_future_return_rate": _safe_float((target_series > 0).mean()),
                }
            )
    return pd.DataFrame(rows)


def _top_vs_rest(enriched: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for horizon in HORIZONS:
        target = f"future_return_{horizon}d"
        daily = []
        for date, group in enriched.groupby("date", sort=True):
            top = group.loc[group["csm001_top_decile_flag"], target].dropna()
            rest = group.loc[~group["csm001_top_decile_flag"], target].dropna()
            if len(top) >= 5 and len(rest) >= 50:
                daily.append(
                    {
                        "date": date,
                        "top_mean": top.mean(),
                        "rest_mean": rest.mean(),
                        "top_minus_rest": top.mean() - rest.mean(),
                    }
                )
        daily_df = pd.DataFrame(daily)
        low, high = _bootstrap_ci(daily_df["top_minus_rest"])
        rows.append(
            {
                "horizon_days": horizon,
                "metric": "top_decile_minus_rest_future_return",
                "observations": int(len(daily_df)),
                "mean": _safe_float(daily_df["top_minus_rest"].mean()),
                "median": _safe_float(daily_df["top_minus_rest"].median()),
                "bootstrap_mean_ci_low": low,
                "bootstrap_mean_ci_high": high,
                "positive_day_rate": _safe_float((daily_df["top_minus_rest"] > 0).mean()),
            }
        )
    return pd.DataFrame(rows)


def _yearly_validation(enriched: pd.DataFrame) -> pd.DataFrame:
    rows = []
    enriched = enriched.copy()
    enriched["year"] = enriched["date"].dt.year
    for horizon in HORIZONS:
        target = f"future_return_{horizon}d"
        for year, year_frame in enriched.groupby("year", sort=True):
            daily_ics = []
            daily_top_diff = []
            for date, group in year_frame.groupby("date", sort=True):
                ic = _spearman_no_scipy(group["csm001_momentum_score"], group[target])
                if pd.notna(ic):
                    daily_ics.append(ic)
                top = group.loc[group["csm001_top_decile_flag"], target].dropna()
                rest = group.loc[~group["csm001_top_decile_flag"], target].dropna()
                if len(top) >= 5 and len(rest) >= 50:
                    daily_top_diff.append(top.mean() - rest.mean())
            rows.append(
                {
                    "year": int(year),
                    "horizon_days": horizon,
                    "daily_ic_observations": int(len(daily_ics)),
                    "mean_daily_ic": _safe_float(pd.Series(daily_ics, dtype=float).mean()),
                    "mean_top_minus_rest": _safe_float(pd.Series(daily_top_diff, dtype=float).mean()),
                    "ic_positive": bool(pd.Series(daily_ics, dtype=float).mean() > 0) if daily_ics else False,
                    "top_minus_rest_positive": bool(pd.Series(daily_top_diff, dtype=float).mean() > 0) if daily_top_diff else False,
                }
            )
    return pd.DataFrame(rows)


def _horizon_summary(ic: pd.DataFrame, top_rest: pd.DataFrame, yearly: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str]]:
    rows = []
    verdicts = {}
    for horizon in HORIZONS:
        ic_row = ic[ic["horizon_days"] == horizon].iloc[0]
        spread_row = top_rest[top_rest["horizon_days"] == horizon].iloc[0]
        year_rows = yearly[yearly["horizon_days"] == horizon]
        ic_supported = ic_row["bootstrap_mean_ci_low"] > 0
        spread_supported = spread_row["bootstrap_mean_ci_low"] > 0
        year_stability = float(year_rows["ic_positive"].mean()) if len(year_rows) else np.nan
        if ic_supported and spread_supported and year_stability >= 0.60:
            verdict = "Supported by evidence"
        elif (ic_supported or spread_supported) and year_stability >= 0.50:
            verdict = "Partially supported"
        elif pd.notna(year_stability):
            verdict = "Not supported"
        else:
            verdict = "Inconclusive"
        verdicts[str(horizon)] = verdict
        rows.append(
            {
                "horizon_days": horizon,
                "ic_mean": ic_row["mean"],
                "ic_ci_low": ic_row["bootstrap_mean_ci_low"],
                "ic_ci_high": ic_row["bootstrap_mean_ci_high"],
                "top_minus_rest_mean": spread_row["mean"],
                "top_minus_rest_ci_low": spread_row["bootstrap_mean_ci_low"],
                "top_minus_rest_ci_high": spread_row["bootstrap_mean_ci_high"],
                "ic_positive_year_rate": year_stability,
                "classification": verdict,
            }
        )
    return pd.DataFrame(rows), verdicts


def _write_reports(
    ic: pd.DataFrame,
    deciles: pd.DataFrame,
    top_rest: pd.DataFrame,
    yearly: pd.DataFrame,
    horizon_summary: pd.DataFrame,
    verdicts: dict[str, str],
) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    supported_count = sum(v == "Supported by evidence" for v in verdicts.values())
    partial_count = sum(v == "Partially supported" for v in verdicts.values())
    if supported_count >= 2:
        overall = "Supported by evidence"
    elif supported_count + partial_count >= 2:
        overall = "Partially supported"
    else:
        overall = "Not supported"

    def val(horizon: int, col: str) -> str:
        row = horizon_summary[horizon_summary["horizon_days"] == horizon]
        if row.empty:
            return "N/A"
        value = row[col].iloc[0]
        return "N/A" if pd.isna(value) else f"{float(value):.6f}"

    report = f"""# CSM-001 / PV-001 Predictive Validation

## Purpose

Evaluate whether the validated CSM-001 construct contains statistical predictive information about predefined future outcomes.

This is predictive validation only. It is not economic validation, not a trading strategy backtest, and not a production recommendation.

## Preregistered Forecast Horizons

- 21 trading days
- 63 trading days
- 126 trading days

## Preregistered Outcomes

- Future adjusted-close return over each horizon
- Cross-sectional information coefficient between CSM-001 score and future return
- Top-decile future return difference versus the rest of the eligible universe

## Results By Horizon

- 21d: **{verdicts["21"]}**, mean IC {val(21, "ic_mean")}, mean top-minus-rest {val(21, "top_minus_rest_mean")}
- 63d: **{verdicts["63"]}**, mean IC {val(63, "ic_mean")}, mean top-minus-rest {val(63, "top_minus_rest_mean")}
- 126d: **{verdicts["126"]}**, mean IC {val(126, "ic_mean")}, mean top-minus-rest {val(126, "top_minus_rest_mean")}

## Overall PV-001 Classification

**{overall}**

The conclusion is limited to statistical predictive information in the evaluated current-constituent universe and predefined horizons. No economic utility or trade profitability is inferred.
"""
    (OUTPUT_DIR / "pv001_predictive_validation.md").write_text(report, encoding="utf-8")

    forecast = "# Forecast Horizon Analysis\n\n" + horizon_summary.to_csv(index=False) + "\n"
    (OUTPUT_DIR / "forecast_horizon_analysis.md").write_text(forecast, encoding="utf-8")

    baseline = """# Baseline Comparison

The predefined null comparisons are:

- Mean daily information coefficient equal to zero.
- Mean top-decile minus rest future-return difference equal to zero.

Bootstrap confidence intervals are computed on date-level statistics. No portfolio benchmark, Sharpe ratio, CAGR, drawdown or economic value benchmark is used in PV-001.
"""
    (OUTPUT_DIR / "baseline_comparison.md").write_text(baseline, encoding="utf-8")

    calibration = """# Calibration Analysis

Calibration is evaluated descriptively through score-decile future outcome ordering.

The accompanying `decile_predictive_analysis.csv` file reports mean and median future return by score decile and forecast horizon.

This does not define a trading rule and does not optimize thresholds.
"""
    (OUTPUT_DIR / "calibration_analysis.md").write_text(calibration, encoding="utf-8")

    yearly_summary = yearly.groupby("horizon_days").agg(
        years=("year", "count"),
        ic_positive_year_rate=("ic_positive", "mean"),
        top_minus_rest_positive_year_rate=("top_minus_rest_positive", "mean"),
    ).reset_index()
    cross_period = "# Cross-Period Validation\n\n" + yearly_summary.to_csv(index=False) + "\n"
    (OUTPUT_DIR / "cross_period_validation.md").write_text(cross_period, encoding="utf-8")

    confidence = f"""# Confidence Interval Report

Bootstrap confidence intervals used {BOOTSTRAP_ITERATIONS} date-level resamples with seed `{BOOTSTRAP_SEED}`.

Confidence intervals were calculated for:

- Mean daily Spearman IC
- Mean daily top-decile minus rest future-return difference

These intervals describe predictive-statistical uncertainty only, not economic uncertainty.
"""
    (OUTPUT_DIR / "confidence_interval_report.md").write_text(confidence, encoding="utf-8")

    effect = """# Effect Size Analysis

Effect size is represented by:

- Mean daily Spearman information coefficient.
- Mean top-decile minus rest future-return difference.
- Positive-year rate for cross-period stability.

No Sharpe, CAGR, alpha or portfolio-level economic metric is calculated.
"""
    (OUTPUT_DIR / "effect_size_analysis.md").write_text(effect, encoding="utf-8")

    limitations = """# Limitations

- The universe is current S&P 500-style membership, not survivorship-free historical constituents.
- Future adjusted-close returns are used only as predictive validation outcomes, not as trading strategy returns.
- No transaction costs, turnover, capacity, portfolio construction or implementation constraints are evaluated in PV-001.
- Statistical predictive information does not imply economic value.
- PV-001 does not recommend production deployment or strategy changes.
"""
    (OUTPUT_DIR / "limitations.md").write_text(limitations, encoding="utf-8")

    summary = f"""# Executive Summary

CSM-001 / PV-001 evaluated whether the Canonical 12-1 Cross-Sectional Momentum State contains statistical predictive information at 21, 63 and 126 trading-day horizons.

Overall classification: **{overall}**.

This is the first CSM-001 stage that evaluates future outcomes. The evidence is statistical only; economic validation remains untested and must be handled separately in EV-001.
"""
    (OUTPUT_DIR / "executive_summary.md").write_text(summary, encoding="utf-8")

    next_goal = """# CSM-001 / EV-001 Economic Validation

Purpose: evaluate whether the predictive information identified in PV-001 provides measurable economic utility under preregistered portfolio and implementation workflows.

Forbidden before preregistration:

- Parameter optimization
- Threshold tuning
- Strategy redesign
- Production recommendation

EV-001 must define all portfolio rules, benchmark models, costs, turnover assumptions and decision workflows before execution.
"""
    (OUTPUT_DIR / "next_stage_goal_ev001.md").write_text(next_goal, encoding="utf-8")

    manifest = {
        "construct_id": "CSM-001",
        "stage": "PV-001",
        "horizons": HORIZONS,
        "overall_classification": overall,
        "horizon_verdicts": verdicts,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "bootstrap_iterations": BOOTSTRAP_ITERATIONS,
    }
    (OUTPUT_DIR / "pv001_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    frame = _add_future_outcomes(_load_state())
    ic = _information_coefficient(frame)
    deciles = _decile_analysis(frame)
    top_rest = _top_vs_rest(frame)
    yearly = _yearly_validation(frame)
    horizon_summary, verdicts = _horizon_summary(ic, top_rest, yearly)

    ic.to_csv(OUTPUT_DIR / "information_coefficient.csv", index=False)
    deciles.to_csv(OUTPUT_DIR / "decile_predictive_analysis.csv", index=False)
    top_rest.to_csv(OUTPUT_DIR / "top_decile_vs_rest.csv", index=False)
    yearly.to_csv(OUTPUT_DIR / "yearly_predictive_validation.csv", index=False)
    horizon_summary.to_csv(OUTPUT_DIR / "predictive_metrics.csv", index=False)

    _write_reports(ic, deciles, top_rest, yearly, horizon_summary, verdicts)
    print(json.dumps({"status": "PASSED", "output_dir": str(OUTPUT_DIR)}, indent=2))


if __name__ == "__main__":
    main()
