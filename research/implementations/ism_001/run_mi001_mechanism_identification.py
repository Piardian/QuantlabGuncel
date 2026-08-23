from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[2]
STATE_FILE = REPO_ROOT / "output" / "ism_001" / "ism001_industry_momentum_state.csv"
OUTPUT_DIR = REPO_ROOT / "research" / "market_edge_discovery_program" / "ism_001_mi_001_mechanism_identification"


def _load_state() -> pd.DataFrame:
    if not STATE_FILE.exists():
        raise FileNotFoundError(f"Missing ISM-001 construct state file: {STATE_FILE}")
    frame = pd.read_csv(STATE_FILE, parse_dates=["month"])
    frame["ism_valid_observation"] = frame["ism_valid_observation"].astype(bool)
    return frame.sort_values(["industry_id", "month"]).reset_index(drop=True)


def _state_profile(frame: pd.DataFrame) -> pd.DataFrame:
    valid = frame[frame["ism_valid_observation"]].copy()
    rows = []
    for state, group in valid.groupby("ism_state", sort=True):
        formation_return = group["industry_return_12_1"].dropna()
        current_return = group["industry_return"].dropna()
        rows.append(
            {
                "ism_state": state,
                "observations": int(len(group)),
                "unique_industries": int(group["industry_id"].nunique()),
                "mean_ism_score": float(group["ism_score"].mean()),
                "median_ism_score": float(group["ism_score"].median()),
                "mean_formation_return_12_1": float(formation_return.mean()) if len(formation_return) else np.nan,
                "median_formation_return_12_1": float(formation_return.median()) if len(formation_return) else np.nan,
                "p10_formation_return_12_1": float(formation_return.quantile(0.10)) if len(formation_return) else np.nan,
                "p90_formation_return_12_1": float(formation_return.quantile(0.90)) if len(formation_return) else np.nan,
                "mean_current_month_return": float(current_return.mean()) if len(current_return) else np.nan,
                "median_current_month_return": float(current_return.median()) if len(current_return) else np.nan,
            }
        )
    order = {"BOTTOM_DECILE": 0, "MIDDLE": 1, "TOP_DECILE": 2}
    return pd.DataFrame(rows).sort_values("ism_state", key=lambda s: s.map(order)).reset_index(drop=True)


def _yearly_state_profile(frame: pd.DataFrame) -> pd.DataFrame:
    valid = frame[frame["ism_valid_observation"]].copy()
    valid["year"] = valid["month"].dt.year
    rows = []
    for (year, state), group in valid.groupby(["year", "ism_state"], sort=True):
        rows.append(
            {
                "year": int(year),
                "ism_state": state,
                "observations": int(len(group)),
                "unique_industries": int(group["industry_id"].nunique()),
                "mean_ism_score": float(group["ism_score"].mean()),
                "mean_formation_return_12_1": float(group["industry_return_12_1"].mean()),
                "median_formation_return_12_1": float(group["industry_return_12_1"].median()),
            }
        )
    return pd.DataFrame(rows)


def _state_transition(frame: pd.DataFrame) -> pd.DataFrame:
    valid = frame[frame["ism_valid_observation"]].sort_values(["industry_id", "month"]).copy()
    valid["next_state"] = valid.groupby("industry_id")["ism_state"].shift(-1)
    valid["next_month"] = valid.groupby("industry_id")["month"].shift(-1)
    consecutive = valid["next_month"].eq(valid["month"] + pd.offsets.MonthEnd(1))
    transition = valid[consecutive & valid["next_state"].notna()].copy()
    table = transition.groupby(["ism_state", "next_state"], sort=True).size().reset_index(name="count")
    table["from_total"] = table.groupby("ism_state")["count"].transform("sum")
    table["transition_rate"] = table["count"] / table["from_total"]
    return table


def _episode_statistics(frame: pd.DataFrame) -> pd.DataFrame:
    valid = frame[frame["ism_valid_observation"]].sort_values(["industry_id", "month"]).copy()
    rows = []
    for industry_id, group in valid.groupby("industry_id", sort=True):
        state_change = group["ism_state"].ne(group["ism_state"].shift()).cumsum()
        for _, episode in group.groupby(state_change):
            rows.append(
                {
                    "industry_id": industry_id,
                    "industry_name": str(episode["industry_name"].iloc[0]),
                    "ism_state": episode["ism_state"].iloc[0],
                    "start_month": episode["month"].min(),
                    "end_month": episode["month"].max(),
                    "duration_months": int(len(episode)),
                    "mean_formation_return_12_1": float(episode["industry_return_12_1"].mean()),
                }
            )
    episodes = pd.DataFrame(rows)
    if episodes.empty:
        return episodes
    return episodes.groupby("ism_state", sort=True).agg(
        episodes=("duration_months", "count"),
        mean_duration_months=("duration_months", "mean"),
        median_duration_months=("duration_months", "median"),
        p90_duration_months=("duration_months", lambda s: float(s.quantile(0.90))),
        max_duration_months=("duration_months", "max"),
    ).reset_index()


def _industry_concentration(frame: pd.DataFrame) -> pd.DataFrame:
    valid = frame[frame["ism_valid_observation"]].copy()
    rows = []
    for industry_id, group in valid.groupby("industry_id", sort=True):
        rows.append(
            {
                "industry_id": industry_id,
                "industry_name": str(group["industry_name"].iloc[0]),
                "valid_months": int(len(group)),
                "mean_ism_score": float(group["ism_score"].mean()),
                "std_ism_score": float(group["ism_score"].std(ddof=0)),
                "top_decile_months": int((group["ism_state"] == "TOP_DECILE").sum()),
                "bottom_decile_months": int((group["ism_state"] == "BOTTOM_DECILE").sum()),
                "top_decile_rate": float((group["ism_state"] == "TOP_DECILE").mean()),
                "bottom_decile_rate": float((group["ism_state"] == "BOTTOM_DECILE").mean()),
            }
        )
    return pd.DataFrame(rows).sort_values(["top_decile_rate", "mean_ism_score"], ascending=[False, False])


def _monthly_dispersion(frame: pd.DataFrame) -> pd.DataFrame:
    valid = frame[frame["ism_valid_observation"]].copy()
    rows = []
    for month, group in valid.groupby("month", sort=True):
        formation = group["industry_return_12_1"].dropna()
        rows.append(
            {
                "month": month,
                "valid_industries": int(len(group)),
                "formation_return_mean": float(formation.mean()) if len(formation) else np.nan,
                "formation_return_std": float(formation.std(ddof=0)) if len(formation) else np.nan,
                "formation_return_spread_p90_p10": float(formation.quantile(0.90) - formation.quantile(0.10))
                if len(formation)
                else np.nan,
                "top_decile_count": int((group["ism_state"] == "TOP_DECILE").sum()),
                "bottom_decile_count": int((group["ism_state"] == "BOTTOM_DECILE").sum()),
            }
        )
    return pd.DataFrame(rows)


def _historical_leadership_examples(frame: pd.DataFrame) -> pd.DataFrame:
    valid = frame[frame["ism_valid_observation"]].copy()
    valid["year"] = valid["month"].dt.year
    rows = []
    for year, group in valid.groupby("year", sort=True):
        top = group[group["ism_state"] == "TOP_DECILE"]
        bottom = group[group["ism_state"] == "BOTTOM_DECILE"]
        top_counts = top["industry_id"].value_counts()
        bottom_counts = bottom["industry_id"].value_counts()
        rows.append(
            {
                "year": int(year),
                "most_frequent_top_decile_industry": str(top_counts.index[0]) if len(top_counts) else None,
                "top_decile_months": int(top_counts.iloc[0]) if len(top_counts) else 0,
                "most_frequent_bottom_decile_industry": str(bottom_counts.index[0]) if len(bottom_counts) else None,
                "bottom_decile_months": int(bottom_counts.iloc[0]) if len(bottom_counts) else 0,
            }
        )
    return pd.DataFrame(rows)


def _write_reports(
    *,
    frame: pd.DataFrame,
    profile: pd.DataFrame,
    yearly: pd.DataFrame,
    transitions: pd.DataFrame,
    episodes: pd.DataFrame,
    concentration: pd.DataFrame,
    dispersion: pd.DataFrame,
    historical: pd.DataFrame,
) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    profile.to_csv(OUTPUT_DIR / "state_profile.csv", index=False)
    yearly.to_csv(OUTPUT_DIR / "yearly_state_profile.csv", index=False)
    transitions.to_csv(OUTPUT_DIR / "state_transition_matrix.csv", index=False)
    episodes.to_csv(OUTPUT_DIR / "episode_statistics.csv", index=False)
    concentration.to_csv(OUTPUT_DIR / "industry_concentration.csv", index=False)
    dispersion.to_csv(OUTPUT_DIR / "monthly_dispersion.csv", index=False)
    historical.to_csv(OUTPUT_DIR / "historical_leadership_examples.csv", index=False)

    valid = frame[frame["ism_valid_observation"]].copy()
    top = profile[profile["ism_state"] == "TOP_DECILE"].iloc[0]
    bottom = profile[profile["ism_state"] == "BOTTOM_DECILE"].iloc[0]
    middle = profile[profile["ism_state"] == "MIDDLE"].iloc[0]
    top_retention = transitions[
        (transitions["ism_state"] == "TOP_DECILE") & (transitions["next_state"] == "TOP_DECILE")
    ]["transition_rate"]
    bottom_retention = transitions[
        (transitions["ism_state"] == "BOTTOM_DECILE") & (transitions["next_state"] == "BOTTOM_DECILE")
    ]["transition_rate"]
    median_dispersion = float(dispersion["formation_return_spread_p90_p10"].median())
    top_concentration = concentration.head(5)

    main = f"""# ISM-001 / MI-001 Mechanism Identification

## Purpose

Characterize the observable behavior represented by the validated ISM-001 industry momentum states.

No future returns, alpha, trading performance, strategy backtest, Sharpe, CAGR, drawdown, predictive validation, economic validation or stock-level signal assignment was evaluated.

## Study Population

- Valid construct months: {valid["month"].min().date()} to {valid["month"].max().date()}
- Valid observations: {len(valid):,}
- Unique industries: {valid["industry_id"].nunique():,}
- TOP_DECILE observations: {int(top["observations"]):,}
- BOTTOM_DECILE observations: {int(bottom["observations"]):,}

## Mechanism Summary

ISM-001 represents an **industry-level cross-sectional intermediate-horizon leadership / laggard state**.

The construct identifies industries whose compounded returns over months `t-12` through `t-2` are in the upper or lower cross-sectional tails of the Ken French 49 industry universe.

## Supported By Evidence

- TOP_DECILE has high mean percentile score: {top["mean_ism_score"]:.4f}.
- BOTTOM_DECILE has low mean percentile score: {bottom["mean_ism_score"]:.4f}.
- MIDDLE is centered with mean percentile score: {middle["mean_ism_score"]:.4f}.
- TOP_DECILE mean 12-1 formation return is {top["mean_formation_return_12_1"]:.4f}.
- BOTTOM_DECILE mean 12-1 formation return is {bottom["mean_formation_return_12_1"]:.4f}.
- Median monthly p90-p10 12-1 industry dispersion is {median_dispersion:.4f}.
- State persistence exists but is rotating; TOP_DECILE one-month retention is {float(top_retention.iloc[0]) if len(top_retention) else np.nan:.4f}, and BOTTOM_DECILE one-month retention is {float(bottom_retention.iloc[0]) if len(bottom_retention) else np.nan:.4f}.

## Partially Supported

- Industry leadership is not uniformly distributed across industries. Some industries appear in TOP_DECILE more frequently than others, but this is descriptive concentration, not predictive evidence.

## Not Evaluated

- Predictive power
- Future returns
- Alpha
- Strategy profitability
- Economic utility
- Stock-level industry signal assignment

## MI-001 Classification

ISM-001 is best characterized as an **industry-level cross-sectional leadership / laggard state construct based on intermediate-horizon prior industry returns** under the frozen CD-001 definition.
"""
    (OUTPUT_DIR / "mi001_mechanism_identification.md").write_text(main, encoding="utf-8")

    top_table = top_concentration[
        ["industry_id", "top_decile_rate", "bottom_decile_rate", "mean_ism_score"]
    ].to_string(index=False)
    (OUTPUT_DIR / "industry_leadership_concentration.md").write_text(
        f"""# Industry Leadership Concentration

Top five industries by TOP_DECILE frequency:

```text
{top_table}
```

Interpretation:

This table describes historical state concentration only. It does not imply that these industries have predictive superiority or economic value.
""",
        encoding="utf-8",
    )

    (OUTPUT_DIR / "transition_event_analysis.md").write_text(
        """# Transition Event Analysis

ISM-001 transition behavior was evaluated descriptively through month-to-month state changes within each industry.

The transition matrix is stored in `state_transition_matrix.csv`.

No historical event attribution, predictive claim, or trading-performance interpretation was performed.
""",
        encoding="utf-8",
    )

    (OUTPUT_DIR / "market_condition_summary.md").write_text(
        f"""# Market Condition Summary

ISM-001 is not a market-wide regime construct.

It is a cross-sectional industry-relative state construct. It describes which industries are leaders, laggards or middle-ranked based on lagged industry portfolio returns.

Median monthly cross-sectional 12-1 formation-return p90-p10 spread:

```text
{median_dispersion:.4f}
```

This spread describes the amount of cross-industry separation available to the construct.
""",
        encoding="utf-8",
    )

    (OUTPUT_DIR / "mechanism_hypotheses.md").write_text(
        """# Mechanism Hypotheses For HV-001

The following explanatory hypotheses are generated from MI-001 and require formal HV-001 validation:

H1:

TOP_DECILE states represent industries with persistently high intermediate-horizon relative industry performance.

H2:

BOTTOM_DECILE states represent industries with persistently low intermediate-horizon relative industry performance.

H3:

ISM-001 states are rotating leadership / laggard classifications rather than static industry identity labels.

H4:

Cross-sectional industry dispersion is a necessary observable condition for meaningful ISM-001 state separation.

These are explanatory hypotheses only. They are not predictive or economic hypotheses.
""",
        encoding="utf-8",
    )

    (OUTPUT_DIR / "limitations.md").write_text(
        """# Limitations

- MI-001 characterizes existing state behavior only.
- No future outcome was evaluated.
- No predictive validation was performed.
- No economic validation was performed.
- No alpha claim was made.
- The construct is industry-level and does not assign states to individual stocks.
- Ken French 49 industry definitions are fixed by the external data source and are not redesigned here.
""",
        encoding="utf-8",
    )

    (OUTPUT_DIR / "executive_summary.md").write_text(
        f"""# Executive Summary

ISM-001 / MI-001 characterized the industry momentum states produced by the validated construct.

The construct behaves as an industry-level cross-sectional leadership / laggard sensor: TOP_DECILE observations have high 12-1 industry momentum ranks, BOTTOM_DECILE observations have low 12-1 industry momentum ranks, and MIDDLE observations remain centered.

The states show rotation and persistence. TOP_DECILE one-month retention was {float(top_retention.iloc[0]) if len(top_retention) else np.nan:.4f}; BOTTOM_DECILE one-month retention was {float(bottom_retention.iloc[0]) if len(bottom_retention) else np.nan:.4f}.

No predictive or economic claim was made.

ISM-001 may proceed to HV-001 to formally validate the proposed mechanism hypotheses.
""",
        encoding="utf-8",
    )

    (OUTPUT_DIR / "next_stage_goal_hv001.md").write_text(
        """# ISM-001 / HV-001 Hypothesis Validation

Purpose:

Formally validate the mechanism hypotheses generated in MI-001.

Hypotheses:

- TOP_DECILE states represent persistently high intermediate-horizon relative industry performance.
- BOTTOM_DECILE states represent persistently low intermediate-horizon relative industry performance.
- ISM-001 states are rotating leadership / laggard classifications rather than static industry identity labels.
- Cross-sectional industry dispersion is a necessary observable condition for meaningful ISM-001 state separation.

Forbidden:

- Predictive validation.
- Future return forecasting.
- Trading backtests.
- Alpha claims.
- Economic validation.
- Parameter optimization.
- Stock-level signal assignment.
""",
        encoding="utf-8",
    )

    manifest = {
        "construct_id": "ISM-001",
        "stage": "MI-001",
        "classification": "Mechanism identified",
        "primary_mechanism": "Industry-level cross-sectional intermediate-horizon leadership / laggard state",
        "valid_observations": int(len(valid)),
        "unique_industries": int(valid["industry_id"].nunique()),
        "median_monthly_p90_p10_formation_return_spread": median_dispersion,
        "top_decile_retention": float(top_retention.iloc[0]) if len(top_retention) else None,
        "bottom_decile_retention": float(bottom_retention.iloc[0]) if len(bottom_retention) else None,
        "next_stage": "HV-001",
    }
    (OUTPUT_DIR / "mi001_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def run_mechanism_identification() -> dict[str, object]:
    frame = _load_state()
    profile = _state_profile(frame)
    yearly = _yearly_state_profile(frame)
    transitions = _state_transition(frame)
    episodes = _episode_statistics(frame)
    concentration = _industry_concentration(frame)
    dispersion = _monthly_dispersion(frame)
    historical = _historical_leadership_examples(frame)
    _write_reports(
        frame=frame,
        profile=profile,
        yearly=yearly,
        transitions=transitions,
        episodes=episodes,
        concentration=concentration,
        dispersion=dispersion,
        historical=historical,
    )
    return {
        "valid_observations": int(frame["ism_valid_observation"].sum()),
        "state_profile_rows": int(len(profile)),
        "transition_rows": int(len(transitions)),
        "status": "COMPLETE",
    }


if __name__ == "__main__":
    print(json.dumps(run_mechanism_identification(), indent=2))
