from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[3]
STATE_FILE = REPO_ROOT / "output" / "ism_001" / "ism001_industry_momentum_state.csv"
OUTPUT_DIR = REPO_ROOT / "research" / "market_edge_discovery_program" / "ism_001_pv_001_predictive_validation"

HORIZONS_MONTHS = [1, 3, 6, 12]
BOOTSTRAP_SEED = 5101
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
    if len(aligned) < 30:
        return np.nan
    return float(aligned.iloc[:, 0].rank(method="average").corr(aligned.iloc[:, 1].rank(method="average")))


def _load_state() -> pd.DataFrame:
    frame = pd.read_csv(STATE_FILE, parse_dates=["month"])
    frame["ism_valid_observation"] = frame["ism_valid_observation"].astype(bool)
    frame = frame[frame["ism_valid_observation"]].copy()
    return frame.sort_values(["month", "industry_id"]).reset_index(drop=True)


def _future_return_panel(returns: pd.DataFrame, horizon: int) -> pd.DataFrame:
    gross = 1.0 + returns
    future = pd.DataFrame(1.0, index=returns.index, columns=returns.columns)
    count = pd.DataFrame(0, index=returns.index, columns=returns.columns)
    for lead in range(1, horizon + 1):
        shifted = gross.shift(-lead)
        future = future.mul(shifted.fillna(1.0), fill_value=1.0)
        count = count.add(shifted.notna().astype(int), fill_value=0)
    return (future - 1.0).where(count.eq(horizon))


def _add_future_outcomes(frame: pd.DataFrame) -> pd.DataFrame:
    returns = frame.pivot(index="month", columns="industry_id", values="industry_return").sort_index()
    enriched = frame.copy()
    for horizon in HORIZONS_MONTHS:
        future = _future_return_panel(returns, horizon)
        stacked = future.reset_index(names="month").melt(
            id_vars="month",
            var_name="industry_id",
            value_name=f"future_return_{horizon}m",
        )
        stacked["month"] = pd.to_datetime(stacked["month"])
        enriched = enriched.merge(stacked, on=["month", "industry_id"], how="left")
    return enriched


def _information_coefficient(enriched: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for horizon in HORIZONS_MONTHS:
        target = f"future_return_{horizon}m"
        monthly = []
        for month, group in enriched.groupby("month", sort=True):
            ic = _spearman_no_scipy(group["ism_score"], group[target])
            if pd.notna(ic):
                monthly.append({"month": month, "ic": ic})
        monthly_df = pd.DataFrame(monthly)
        low, high = _bootstrap_ci(monthly_df["ic"])
        rows.append(
            {
                "horizon_months": horizon,
                "metric": "monthly_spearman_ic",
                "observations": int(len(monthly_df)),
                "mean": _safe_float(monthly_df["ic"].mean()),
                "median": _safe_float(monthly_df["ic"].median()),
                "bootstrap_mean_ci_low": low,
                "bootstrap_mean_ci_high": high,
                "positive_month_rate": _safe_float((monthly_df["ic"] > 0).mean()),
            }
        )
    return pd.DataFrame(rows)


def _state_outcome_summary(enriched: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for horizon in HORIZONS_MONTHS:
        target = f"future_return_{horizon}m"
        for state, group in enriched.groupby("ism_state", sort=True):
            values = group[target].dropna()
            low, high = _bootstrap_ci(values)
            rows.append(
                {
                    "horizon_months": horizon,
                    "ism_state": state,
                    "observations": int(len(values)),
                    "mean_future_return": _safe_float(values.mean()),
                    "median_future_return": _safe_float(values.median()),
                    "positive_future_return_rate": _safe_float((values > 0).mean()),
                    "bootstrap_mean_ci_low": low,
                    "bootstrap_mean_ci_high": high,
                }
            )
    return pd.DataFrame(rows)


def _state_spreads(enriched: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for horizon in HORIZONS_MONTHS:
        target = f"future_return_{horizon}m"
        monthly = []
        for month, group in enriched.groupby("month", sort=True):
            top = group.loc[group["ism_state"] == "TOP_DECILE", target].dropna()
            bottom = group.loc[group["ism_state"] == "BOTTOM_DECILE", target].dropna()
            middle = group.loc[group["ism_state"] == "MIDDLE", target].dropna()
            if len(top) >= 4 and len(bottom) >= 4 and len(middle) >= 20:
                monthly.append(
                    {
                        "month": month,
                        "top_minus_middle": top.mean() - middle.mean(),
                        "bottom_minus_middle": bottom.mean() - middle.mean(),
                        "top_minus_bottom": top.mean() - bottom.mean(),
                    }
                )
        monthly_df = pd.DataFrame(monthly)
        for metric in ["top_minus_middle", "bottom_minus_middle", "top_minus_bottom"]:
            low, high = _bootstrap_ci(monthly_df[metric])
            rows.append(
                {
                    "horizon_months": horizon,
                    "metric": metric,
                    "observations": int(len(monthly_df)),
                    "mean": _safe_float(monthly_df[metric].mean()),
                    "median": _safe_float(monthly_df[metric].median()),
                    "bootstrap_mean_ci_low": low,
                    "bootstrap_mean_ci_high": high,
                    "positive_month_rate": _safe_float((monthly_df[metric] > 0).mean()),
                }
            )
    return pd.DataFrame(rows)


def _yearly_validation(enriched: pd.DataFrame) -> pd.DataFrame:
    rows = []
    enriched = enriched.copy()
    enriched["year"] = enriched["month"].dt.year
    for horizon in HORIZONS_MONTHS:
        target = f"future_return_{horizon}m"
        for year, year_frame in enriched.groupby("year", sort=True):
            monthly_ics = []
            monthly_spreads = []
            for _, group in year_frame.groupby("month", sort=True):
                ic = _spearman_no_scipy(group["ism_score"], group[target])
                if pd.notna(ic):
                    monthly_ics.append(ic)
                top = group.loc[group["ism_state"] == "TOP_DECILE", target].dropna()
                bottom = group.loc[group["ism_state"] == "BOTTOM_DECILE", target].dropna()
                if len(top) >= 4 and len(bottom) >= 4:
                    monthly_spreads.append(top.mean() - bottom.mean())
            mean_ic = pd.Series(monthly_ics, dtype=float).mean()
            mean_spread = pd.Series(monthly_spreads, dtype=float).mean()
            rows.append(
                {
                    "year": int(year),
                    "horizon_months": horizon,
                    "ic_observations": int(len(monthly_ics)),
                    "mean_monthly_ic": _safe_float(mean_ic),
                    "mean_top_minus_bottom": _safe_float(mean_spread),
                    "ic_positive": bool(mean_ic > 0) if pd.notna(mean_ic) else False,
                    "top_minus_bottom_positive": bool(mean_spread > 0) if pd.notna(mean_spread) else False,
                }
            )
    return pd.DataFrame(rows)


def _horizon_summary(ic: pd.DataFrame, spreads: pd.DataFrame, yearly: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str]]:
    rows = []
    verdicts = {}
    for horizon in HORIZONS_MONTHS:
        ic_row = ic[ic["horizon_months"] == horizon].iloc[0]
        tmb = spreads[(spreads["horizon_months"] == horizon) & (spreads["metric"] == "top_minus_bottom")].iloc[0]
        tmm = spreads[(spreads["horizon_months"] == horizon) & (spreads["metric"] == "top_minus_middle")].iloc[0]
        year_rows = yearly[yearly["horizon_months"] == horizon]
        ic_supported = pd.notna(ic_row["bootstrap_mean_ci_low"]) and ic_row["bootstrap_mean_ci_low"] > 0
        spread_supported = pd.notna(tmb["bootstrap_mean_ci_low"]) and tmb["bootstrap_mean_ci_low"] > 0
        top_mid_supported = pd.notna(tmm["bootstrap_mean_ci_low"]) and tmm["bootstrap_mean_ci_low"] > 0
        year_stability = float(year_rows["ic_positive"].mean()) if len(year_rows) else np.nan
        spread_year_stability = float(year_rows["top_minus_bottom_positive"].mean()) if len(year_rows) else np.nan
        if ic_supported and spread_supported and year_stability >= 0.60 and spread_year_stability >= 0.60:
            verdict = "Supported by evidence"
        elif (ic_supported or spread_supported or top_mid_supported) and max(year_stability, spread_year_stability) >= 0.50:
            verdict = "Partially supported"
        elif pd.notna(year_stability):
            verdict = "Not supported"
        else:
            verdict = "Inconclusive"
        verdicts[str(horizon)] = verdict
        rows.append(
            {
                "horizon_months": horizon,
                "ic_mean": ic_row["mean"],
                "ic_ci_low": ic_row["bootstrap_mean_ci_low"],
                "ic_ci_high": ic_row["bootstrap_mean_ci_high"],
                "top_minus_middle_mean": tmm["mean"],
                "top_minus_middle_ci_low": tmm["bootstrap_mean_ci_low"],
                "top_minus_middle_ci_high": tmm["bootstrap_mean_ci_high"],
                "top_minus_bottom_mean": tmb["mean"],
                "top_minus_bottom_ci_low": tmb["bootstrap_mean_ci_low"],
                "top_minus_bottom_ci_high": tmb["bootstrap_mean_ci_high"],
                "ic_positive_year_rate": year_stability,
                "top_minus_bottom_positive_year_rate": spread_year_stability,
                "classification": verdict,
            }
        )
    return pd.DataFrame(rows), verdicts


def _write_reports(
    ic: pd.DataFrame,
    states: pd.DataFrame,
    spreads: pd.DataFrame,
    yearly: pd.DataFrame,
    summary: pd.DataFrame,
    verdicts: dict[str, str],
    enriched: pd.DataFrame,
) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ic.to_csv(OUTPUT_DIR / "predictive_metrics.csv", index=False)
    states.to_csv(OUTPUT_DIR / "state_outcome_summary.csv", index=False)
    spreads.to_csv(OUTPUT_DIR / "state_spread_analysis.csv", index=False)
    yearly.to_csv(OUTPUT_DIR / "yearly_predictive_validation.csv", index=False)
    summary.to_csv(OUTPUT_DIR / "forecast_horizon_analysis.csv", index=False)

    supported = sum(v == "Supported by evidence" for v in verdicts.values())
    partial = sum(v == "Partially supported" for v in verdicts.values())
    if supported >= 2:
        overall = "Supported by evidence"
    elif supported + partial >= 2:
        overall = "Partially supported"
    else:
        overall = "Not supported"

    horizon_lines = "\n".join(
        f"- {int(row['horizon_months'])}m: **{row['classification']}**, mean IC {row['ic_mean']:.6f}, "
        f"mean TOP_MINUS_BOTTOM {row['top_minus_bottom_mean']:.6f}"
        for _, row in summary.iterrows()
    )

    main = f"""# ISM-001 / PV-001 Predictive Validation

## Purpose

Evaluate whether validated ISM-001 states contain statistical predictive information about predefined future industry-level outcomes.

This is predictive validation only. It is not economic validation, not a trading strategy backtest, and not a production recommendation.

## Preregistered Forecast Horizons

- 1 month
- 3 months
- 6 months
- 12 months

## Preregistered Outcomes

- Future compounded Ken French industry return over each horizon.
- Cross-sectional information coefficient between ISM score and future industry return.
- TOP_DECILE minus MIDDLE future-return difference.
- TOP_DECILE minus BOTTOM_DECILE future-return difference.

## Results By Horizon

{horizon_lines}

## Overall PV-001 Classification

**{overall}**

The conclusion is limited to statistical predictive information in the evaluated Ken French 49 industry universe and predefined horizons. No economic utility or trade profitability is inferred.
"""
    (OUTPUT_DIR / "pv001_predictive_validation.md").write_text(main, encoding="utf-8")

    (OUTPUT_DIR / "baseline_comparison.md").write_text(
        """# Baseline Comparison

Predefined null comparisons:

- Monthly cross-sectional information coefficient equal to zero.
- TOP_DECILE future industry return versus MIDDLE state future industry return.
- TOP_DECILE future industry return versus BOTTOM_DECILE future industry return.

No benchmark portfolio, trading strategy, Sharpe ratio or economic metric was evaluated.
""",
        encoding="utf-8",
    )

    (OUTPUT_DIR / "confidence_interval_report.md").write_text(
        f"""# Confidence Interval Report

Bootstrap confidence intervals used {BOOTSTRAP_ITERATIONS} monthly resamples with seed `{BOOTSTRAP_SEED}`.

Confidence intervals were calculated for:

- Mean monthly Spearman IC.
- Mean monthly state-spread statistics.

These intervals describe predictive-statistical uncertainty only, not economic uncertainty.
""",
        encoding="utf-8",
    )

    (OUTPUT_DIR / "effect_size_analysis.md").write_text(
        """# Effect Size Analysis

Effect size is represented by:

- Mean monthly Spearman information coefficient.
- Mean TOP_DECILE minus MIDDLE future-return difference.
- Mean TOP_DECILE minus BOTTOM_DECILE future-return difference.
- Positive-year rate for cross-period stability.

No Sharpe, CAGR, alpha or portfolio-level economic metric is calculated.
""",
        encoding="utf-8",
    )

    (OUTPUT_DIR / "cross_period_validation.md").write_text(
        """# Cross-Period Validation

Year-by-year stability is reported in:

- `yearly_predictive_validation.csv`

The validation evaluates sign consistency of IC and TOP_MINUS_BOTTOM spreads across calendar years.
""",
        encoding="utf-8",
    )

    (OUTPUT_DIR / "calibration_analysis.md").write_text(
        """# Calibration Analysis

ISM-001 is a ranking construct, not a probability forecast.

Calibration was therefore limited to monotonic state/outcome summaries by ISM state.

See:

- `state_outcome_summary.csv`
""",
        encoding="utf-8",
    )

    (OUTPUT_DIR / "limitations.md").write_text(
        """# Limitations

- PV-001 evaluates statistical predictive information only.
- The construct is industry-level and does not assign signals to individual securities.
- The test uses Ken French 49 value-weighted industry portfolio returns.
- Overlapping multi-month horizons introduce dependence across observations.
- No transaction costs, turnover, capacity, portfolio construction or implementation constraints are evaluated.
- Statistical predictive information does not imply economic value.
- PV-001 does not recommend production deployment or strategy changes.
""",
        encoding="utf-8",
    )

    next_file = "next_stage_goal_ev001.md" if overall in {"Supported by evidence", "Partially supported"} else "next_stage_human_review.md"
    next_text = (
        """# ISM-001 / EV-001 Economic Validation

Purpose:

Evaluate whether the predictive information identified in PV-001 provides measurable economic utility under preregistered industry-level decision workflows.

Forbidden before preregistration:

- Parameter optimization
- Threshold tuning
- Strategy redesign
- Production recommendation
- Stock-level signal assignment unless explicitly defined

EV-001 must define all portfolio rules, benchmark models, costs, turnover assumptions and decision workflows before execution.
"""
        if overall in {"Supported by evidence", "Partially supported"}
        else """# ISM-001 / Post-PV Human Review

Purpose:

Review the PV-001 result before deciding whether ISM-001 should proceed, pause, be archived, or require an additional preregistered replication study.

No EV-001 should begin automatically from this result.
"""
    )
    (OUTPUT_DIR / next_file).write_text(next_text, encoding="utf-8")

    (OUTPUT_DIR / "executive_summary.md").write_text(
        f"""# Executive Summary

ISM-001 / PV-001 evaluated whether the validated industry momentum construct contains predictive information about future industry-level returns.

Overall classification:

**{overall}**

The strongest evidence is summarized in `forecast_horizon_analysis.csv`.

No economic validation, trading backtest, alpha claim or production recommendation was made.
""",
        encoding="utf-8",
    )

    manifest = {
        "construct_id": "ISM-001",
        "stage": "PV-001",
        "overall_conclusion": overall,
        "horizon_classifications": verdicts,
        "valid_rows_with_any_future_outcome": int(
            enriched[[f"future_return_{h}m" for h in HORIZONS_MONTHS]].notna().any(axis=1).sum()
        ),
        "unique_industries": int(enriched["industry_id"].nunique()),
        "next_stage": "EV-001" if overall in {"Supported by evidence", "Partially supported"} else "Human review",
    }
    (OUTPUT_DIR / "pv001_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def run_predictive_validation() -> dict[str, object]:
    state = _load_state()
    enriched = _add_future_outcomes(state)
    ic = _information_coefficient(enriched)
    states = _state_outcome_summary(enriched)
    spreads = _state_spreads(enriched)
    yearly = _yearly_validation(enriched)
    summary, verdicts = _horizon_summary(ic, spreads, yearly)
    _write_reports(ic, states, spreads, yearly, summary, verdicts, enriched)
    return {
        "valid_observations": int(len(state)),
        "horizons": HORIZONS_MONTHS,
        "horizon_classifications": verdicts,
        "status": "COMPLETE",
    }


if __name__ == "__main__":
    print(json.dumps(run_predictive_validation(), indent=2))
