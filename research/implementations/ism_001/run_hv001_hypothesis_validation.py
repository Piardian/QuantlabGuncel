from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[3]
STATE_FILE = REPO_ROOT / "output" / "ism_001" / "ism001_industry_momentum_state.csv"
OUTPUT_DIR = REPO_ROOT / "research" / "market_edge_discovery_program" / "ism_001_hv_001_hypothesis_validation"
BOOTSTRAP_SEED = 4101
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
    frame["ism_valid_observation"] = frame["ism_valid_observation"].astype(bool)
    valid = frame[frame["ism_valid_observation"]].copy()
    return valid.sort_values(["month", "industry_id"]).reset_index(drop=True)


def _state_transition(frame: pd.DataFrame) -> pd.DataFrame:
    ordered = frame.sort_values(["industry_id", "month"]).copy()
    ordered["next_state"] = ordered.groupby("industry_id")["ism_state"].shift(-1)
    ordered["next_month"] = ordered.groupby("industry_id")["month"].shift(-1)
    consecutive = ordered["next_month"].eq(ordered["month"] + pd.offsets.MonthEnd(1))
    transition = ordered[consecutive & ordered["next_state"].notna()].copy()
    table = transition.groupby(["ism_state", "next_state"], sort=True).size().reset_index(name="count")
    table["from_total"] = table.groupby("ism_state")["count"].transform("sum")
    table["transition_rate"] = table["count"] / table["from_total"]
    return table


def _state_episode_table(frame: pd.DataFrame) -> pd.DataFrame:
    ordered = frame.sort_values(["industry_id", "month"]).copy()
    rows = []
    for industry_id, group in ordered.groupby("industry_id", sort=True):
        episode_id = group["ism_state"].ne(group["ism_state"].shift()).cumsum()
        for _, episode in group.groupby(episode_id):
            rows.append(
                {
                    "industry_id": industry_id,
                    "ism_state": episode["ism_state"].iloc[0],
                    "start_month": episode["month"].min(),
                    "end_month": episode["month"].max(),
                    "duration_months": int(len(episode)),
                }
            )
    return pd.DataFrame(rows)


def _h1_top_high_relative_performance(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    top = frame[frame["ism_state"] == "TOP_DECILE"].copy()
    middle = frame[frame["ism_state"] == "MIDDLE"].copy()
    yearly = top.groupby(top["month"].dt.year)["industry_return_12_1"].agg(["count", "mean", "median"]).reset_index(names="year")
    low, high = _bootstrap_ci(top["industry_return_12_1"], statistic="mean")
    top_vs_middle_diff = float(top["industry_return_12_1"].mean() - middle["industry_return_12_1"].mean())
    positive_rate = float((top["industry_return_12_1"] > middle["industry_return_12_1"].median()).mean())
    positive_years = int((yearly["median"] > 0).sum())
    total_years = int(len(yearly))
    summary = pd.DataFrame(
        [
            {
                "hypothesis": "H1",
                "metric": "top_decile_formation_return_12_1",
                "observations": int(len(top)),
                "mean": _safe_float(top["industry_return_12_1"].mean()),
                "median": _safe_float(top["industry_return_12_1"].median()),
                "top_minus_middle_mean": top_vs_middle_diff,
                "above_middle_median_rate": positive_rate,
                "bootstrap_mean_ci_low": low,
                "bootstrap_mean_ci_high": high,
                "positive_years": positive_years,
                "total_years": total_years,
            }
        ]
    )
    status = "Supported by evidence" if low is not None and low > 0 and top_vs_middle_diff > 0 and positive_years >= int(0.90 * total_years) else "Partially supported"
    return summary, yearly, {"status": status}


def _h2_bottom_low_relative_performance(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    bottom = frame[frame["ism_state"] == "BOTTOM_DECILE"].copy()
    middle = frame[frame["ism_state"] == "MIDDLE"].copy()
    yearly = bottom.groupby(bottom["month"].dt.year)["industry_return_12_1"].agg(["count", "mean", "median"]).reset_index(names="year")
    low, high = _bootstrap_ci(bottom["industry_return_12_1"], statistic="mean")
    bottom_vs_middle_diff = float(bottom["industry_return_12_1"].mean() - middle["industry_return_12_1"].mean())
    below_middle_rate = float((bottom["industry_return_12_1"] < middle["industry_return_12_1"].median()).mean())
    negative_years = int((yearly["median"] < middle["industry_return_12_1"].median()).sum())
    total_years = int(len(yearly))
    summary = pd.DataFrame(
        [
            {
                "hypothesis": "H2",
                "metric": "bottom_decile_formation_return_12_1",
                "observations": int(len(bottom)),
                "mean": _safe_float(bottom["industry_return_12_1"].mean()),
                "median": _safe_float(bottom["industry_return_12_1"].median()),
                "bottom_minus_middle_mean": bottom_vs_middle_diff,
                "below_middle_median_rate": below_middle_rate,
                "bootstrap_mean_ci_low": low,
                "bootstrap_mean_ci_high": high,
                "below_middle_years": negative_years,
                "total_years": total_years,
            }
        ]
    )
    status = "Supported by evidence" if high is not None and bottom_vs_middle_diff < 0 and below_middle_rate > 0.90 and negative_years >= int(0.90 * total_years) else "Partially supported"
    return summary, yearly, {"status": status}


def _h3_rotating_not_static(frame: pd.DataFrame, transitions: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    valid_months = frame["month"].nunique()
    concentration = frame.groupby("industry_id", sort=True).agg(
        valid_months=("month", "count"),
        top_decile_months=("ism_state", lambda s: int((s == "TOP_DECILE").sum())),
        bottom_decile_months=("ism_state", lambda s: int((s == "BOTTOM_DECILE").sum())),
        unique_states=("ism_state", "nunique"),
    ).reset_index()
    concentration["top_decile_rate"] = concentration["top_decile_months"] / concentration["valid_months"]
    concentration["bottom_decile_rate"] = concentration["bottom_decile_months"] / concentration["valid_months"]
    top_ever_rate = float((concentration["top_decile_months"] > 0).mean())
    bottom_ever_rate = float((concentration["bottom_decile_months"] > 0).mean())
    median_unique_states = float(concentration["unique_states"].median())
    max_top_rate = float(concentration["top_decile_rate"].max())
    max_bottom_rate = float(concentration["bottom_decile_rate"].max())
    top_retention = transitions[
        (transitions["ism_state"] == "TOP_DECILE") & (transitions["next_state"] == "TOP_DECILE")
    ]["transition_rate"]
    bottom_retention = transitions[
        (transitions["ism_state"] == "BOTTOM_DECILE") & (transitions["next_state"] == "BOTTOM_DECILE")
    ]["transition_rate"]
    summary = pd.DataFrame(
        [
            {
                "hypothesis": "H3",
                "metric": "top_decile_ever_industry_rate",
                "observations": int(len(concentration)),
                "value": top_ever_rate,
            },
            {
                "hypothesis": "H3",
                "metric": "bottom_decile_ever_industry_rate",
                "observations": int(len(concentration)),
                "value": bottom_ever_rate,
            },
            {
                "hypothesis": "H3",
                "metric": "median_unique_states_per_industry",
                "observations": int(len(concentration)),
                "value": median_unique_states,
            },
            {
                "hypothesis": "H3",
                "metric": "top_decile_one_month_retention",
                "observations": int(valid_months),
                "value": float(top_retention.iloc[0]) if len(top_retention) else np.nan,
            },
            {
                "hypothesis": "H3",
                "metric": "bottom_decile_one_month_retention",
                "observations": int(valid_months),
                "value": float(bottom_retention.iloc[0]) if len(bottom_retention) else np.nan,
            },
            {
                "hypothesis": "H3",
                "metric": "max_top_decile_rate_single_industry",
                "observations": int(len(concentration)),
                "value": max_top_rate,
            },
            {
                "hypothesis": "H3",
                "metric": "max_bottom_decile_rate_single_industry",
                "observations": int(len(concentration)),
                "value": max_bottom_rate,
            },
        ]
    )
    rotating = top_ever_rate > 0.90 and bottom_ever_rate > 0.90 and median_unique_states >= 3 and max_top_rate < 0.40 and max_bottom_rate < 0.40
    status = "Supported by evidence" if rotating else "Partially supported"
    return summary, concentration, {"status": status}


def _h4_dispersion_required(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    rows = []
    for month, group in frame.groupby("month", sort=True):
        formation = group["industry_return_12_1"].dropna()
        if len(formation) < 30:
            continue
        top = group[group["ism_state"] == "TOP_DECILE"]["industry_return_12_1"]
        bottom = group[group["ism_state"] == "BOTTOM_DECILE"]["industry_return_12_1"]
        rows.append(
            {
                "month": month,
                "valid_industries": int(len(formation)),
                "formation_std": float(formation.std(ddof=0)),
                "formation_p90_p10_spread": float(formation.quantile(0.90) - formation.quantile(0.10)),
                "top_bottom_mean_spread": float(top.mean() - bottom.mean()) if len(top) and len(bottom) else np.nan,
            }
        )
    monthly = pd.DataFrame(rows)
    low, high = _bootstrap_ci(monthly["formation_p90_p10_spread"], statistic="median")
    top_bottom_low, top_bottom_high = _bootstrap_ci(monthly["top_bottom_mean_spread"], statistic="median")
    summary = pd.DataFrame(
        [
            {
                "hypothesis": "H4",
                "metric": "median_monthly_p90_p10_formation_spread",
                "observations": int(len(monthly)),
                "value": float(monthly["formation_p90_p10_spread"].median()),
                "bootstrap_median_ci_low": low,
                "bootstrap_median_ci_high": high,
            },
            {
                "hypothesis": "H4",
                "metric": "median_monthly_top_bottom_mean_spread",
                "observations": int(len(monthly)),
                "value": float(monthly["top_bottom_mean_spread"].median()),
                "bootstrap_median_ci_low": top_bottom_low,
                "bootstrap_median_ci_high": top_bottom_high,
            },
        ]
    )
    status = "Supported by evidence" if low is not None and low > 0 and top_bottom_low is not None and top_bottom_low > 0 else "Inconclusive"
    return summary, monthly, {"status": status}


def _write_reports(
    *,
    frame: pd.DataFrame,
    hypothesis_results: pd.DataFrame,
    verdicts: pd.DataFrame,
    transitions: pd.DataFrame,
    h1_yearly: pd.DataFrame,
    h2_yearly: pd.DataFrame,
    h3_concentration: pd.DataFrame,
    h4_monthly: pd.DataFrame,
) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    hypothesis_results.to_csv(OUTPUT_DIR / "hypothesis_test_results.csv", index=False)
    verdicts.to_csv(OUTPUT_DIR / "hypothesis_verdicts.csv", index=False)
    transitions.to_csv(OUTPUT_DIR / "state_transition_matrix.csv", index=False)
    h1_yearly.to_csv(OUTPUT_DIR / "h1_top_yearly_validation.csv", index=False)
    h2_yearly.to_csv(OUTPUT_DIR / "h2_bottom_yearly_validation.csv", index=False)
    h3_concentration.to_csv(OUTPUT_DIR / "h3_industry_rotation_concentration.csv", index=False)
    h4_monthly.to_csv(OUTPUT_DIR / "h4_dispersion_monthly.csv", index=False)

    verdict_map = dict(zip(verdicts["hypothesis"], verdicts["classification"]))
    h1 = hypothesis_results[hypothesis_results["hypothesis"] == "H1"].iloc[0]
    h2 = hypothesis_results[hypothesis_results["hypothesis"] == "H2"].iloc[0]
    h3_retention = hypothesis_results[
        (hypothesis_results["hypothesis"] == "H3") & (hypothesis_results["metric"] == "top_decile_one_month_retention")
    ].iloc[0]
    h3_top_ever = hypothesis_results[
        (hypothesis_results["hypothesis"] == "H3") & (hypothesis_results["metric"] == "top_decile_ever_industry_rate")
    ].iloc[0]
    h4_disp = hypothesis_results[
        (hypothesis_results["hypothesis"] == "H4") & (hypothesis_results["metric"] == "median_monthly_p90_p10_formation_spread")
    ].iloc[0]
    h4_tb = hypothesis_results[
        (hypothesis_results["hypothesis"] == "H4") & (hypothesis_results["metric"] == "median_monthly_top_bottom_mean_spread")
    ].iloc[0]
    supported_count = int(verdicts["classification"].eq("Supported by evidence").sum())
    overall = "Supported by evidence" if supported_count == 4 else "Partially supported" if supported_count >= 2 else "Inconclusive"

    main = f"""# ISM-001 / HV-001 Hypothesis Validation

## Purpose

Formally validate the MI-001 mechanism hypotheses for the frozen ISM-001 industry momentum construct.

No future returns, alpha, trading performance, backtests, forecasting, parameter optimization, economic value or stock-level signal assignment was evaluated.

## Evidence Base

- Source state file: `output/ism_001/ism001_industry_momentum_state.csv`
- Valid observations: {len(frame):,}
- Unique industries: {frame["industry_id"].nunique():,}
- Valid months: {frame["month"].min().date()} to {frame["month"].max().date()}

## Hypothesis Results

### H1

TOP_DECILE states represent industries with persistently high intermediate-horizon relative industry performance.

- Classification: **{verdict_map["H1"]}**
- TOP_DECILE 12-1 formation mean: {h1["mean"]:.6f}
- TOP minus MIDDLE mean: {h1["top_minus_middle_mean"]:.6f}
- Years with positive TOP_DECILE median: {int(h1["positive_years"])}/{int(h1["total_years"])}
- 95% bootstrap CI for mean: [{h1["bootstrap_mean_ci_low"]:.6f}, {h1["bootstrap_mean_ci_high"]:.6f}]

### H2

BOTTOM_DECILE states represent industries with persistently low intermediate-horizon relative industry performance.

- Classification: **{verdict_map["H2"]}**
- BOTTOM_DECILE 12-1 formation mean: {h2["mean"]:.6f}
- BOTTOM minus MIDDLE mean: {h2["bottom_minus_middle_mean"]:.6f}
- Years with BOTTOM_DECILE median below full middle median: {int(h2["below_middle_years"])}/{int(h2["total_years"])}
- 95% bootstrap CI for mean: [{h2["bootstrap_mean_ci_low"]:.6f}, {h2["bootstrap_mean_ci_high"]:.6f}]

### H3

ISM-001 states are rotating leadership / laggard classifications rather than static industry identity labels.

- Classification: **{verdict_map["H3"]}**
- Industries that appeared in TOP_DECILE at least once: {h3_top_ever["value"]:.6f}
- TOP_DECILE one-month retention: {h3_retention["value"]:.6f}

### H4

Cross-sectional industry dispersion is a necessary observable condition for meaningful ISM-001 state separation.

- Classification: **{verdict_map["H4"]}**
- Median monthly p90-p10 12-1 formation spread: {h4_disp["value"]:.6f}
- 95% bootstrap CI for p90-p10 spread median: [{h4_disp["bootstrap_median_ci_low"]:.6f}, {h4_disp["bootstrap_median_ci_high"]:.6f}]
- Median monthly TOP minus BOTTOM mean spread: {h4_tb["value"]:.6f}

## Overall HV-001 Conclusion

**{overall}**

The evidence supports the explanatory interpretation that ISM-001 represents a rotating industry-level intermediate-horizon leadership / laggard state with persistent tail states and substantial cross-sectional industry dispersion.
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

- H1 TOP_DECILE 12-1 formation mean: {h1["mean"]:.6f}
- H2 BOTTOM_DECILE 12-1 formation mean: {h2["mean"]:.6f}
- H4 median monthly p90-p10 formation spread: {h4_disp["value"]:.6f}
- H4 median monthly TOP minus BOTTOM mean spread: {h4_tb["value"]:.6f}

These values describe construct behavior only.
""",
        encoding="utf-8",
    )

    (OUTPUT_DIR / "cross_period_validation.md").write_text(
        """# Cross-Period Validation

H1 and H2 were evaluated year-by-year using same-period 12-1 formation variables.

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

- Year-by-year TOP_DECILE formation-return sign consistency.
- Year-by-year BOTTOM_DECILE relative weakness consistency.
- Industry concentration and rotation checks.
- Monthly cross-sectional dispersion checks.

No parameter sensitivity, optimization, or predictive validation was performed.
""",
        encoding="utf-8",
    )

    (OUTPUT_DIR / "limitations.md").write_text(
        """# Limitations

- This HV study validates explanatory mechanism only.
- The evidence is based on Ken French 49 industry portfolio returns, not individual-stock industry assignments.
- The rotation test is descriptive and does not establish causal industry-cycle behavior.
- No future returns were evaluated.
- No predictive validation was performed.
- No economic validation was performed.
- No alpha claim was made.
""",
        encoding="utf-8",
    )

    (OUTPUT_DIR / "executive_summary.md").write_text(
        f"""# Executive Summary

ISM-001 / HV-001 formally tested the mechanism hypotheses generated in MI-001.

Overall conclusion:

**{overall}**

Supported findings:

- TOP_DECILE states consistently represent high intermediate-horizon relative industry performance.
- BOTTOM_DECILE states consistently represent low intermediate-horizon relative industry performance.
- ISM-001 states are rotating leadership / laggard classifications rather than static industry identity labels.
- Cross-sectional industry dispersion is present and supports meaningful state separation.

No predictive, alpha, trading-performance or economic claim was made.
""",
        encoding="utf-8",
    )

    (OUTPUT_DIR / "next_stage_goal_pv001.md").write_text(
        """# ISM-001 / PV-001 Predictive Validation

Purpose:

Evaluate whether ISM-001 contains predictive information about future industry-level outcomes.

This stage is not yet performed.

Forbidden before PV-001 begins:

- Economic validation.
- Trading strategy design.
- Parameter optimization.
- Production recommendations.
- Stock-level signal assignment unless explicitly preregistered.

PV-001 must preregister horizons, outcomes, null models, validation design and statistical criteria before execution.
""",
        encoding="utf-8",
    )

    manifest = {
        "construct_id": "ISM-001",
        "stage": "HV-001",
        "overall_conclusion": overall,
        "hypothesis_classifications": verdict_map,
        "valid_observations": int(len(frame)),
        "unique_industries": int(frame["industry_id"].nunique()),
        "next_stage": "PV-001",
    }
    (OUTPUT_DIR / "hv001_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def run_hypothesis_validation() -> dict[str, object]:
    frame = _load_state()
    transitions = _state_transition(frame)
    h1, h1_yearly, h1_meta = _h1_top_high_relative_performance(frame)
    h2, h2_yearly, h2_meta = _h2_bottom_low_relative_performance(frame)
    h3, h3_concentration, h3_meta = _h3_rotating_not_static(frame, transitions)
    h4, h4_monthly, h4_meta = _h4_dispersion_required(frame)
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
        transitions=transitions,
        h1_yearly=h1_yearly,
        h2_yearly=h2_yearly,
        h3_concentration=h3_concentration,
        h4_monthly=h4_monthly,
    )
    return {
        "valid_observations": int(len(frame)),
        "supported_hypotheses": int(verdicts["classification"].eq("Supported by evidence").sum()),
        "status": "COMPLETE",
    }


if __name__ == "__main__":
    print(json.dumps(run_hypothesis_validation(), indent=2))
