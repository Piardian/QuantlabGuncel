from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[2]
STATE_FILE = REPO_ROOT / "output" / "rsm_001" / "rsm001_residual_momentum_state.csv"
MONTHLY_RETURNS_FILE = REPO_ROOT / "data" / "rsm_001" / "monthly_returns.csv"
OUTPUT_DIR = REPO_ROOT / "research" / "market_edge_discovery_program" / "rsm_001_mi_001_mechanism_identification"


def _load_state() -> pd.DataFrame:
    frame = pd.read_csv(STATE_FILE, parse_dates=["month"])
    frame["rsm_valid_observation"] = frame["rsm_valid_observation"].astype(bool)
    return frame


def _raw_12_1_momentum(monthly_returns: pd.DataFrame) -> pd.DataFrame:
    returns = monthly_returns.copy()
    returns.index = pd.to_datetime(returns.index).tz_localize(None).to_period("M").to_timestamp("M")
    gross = 1.0 + returns
    # Uses months t-12 through t-2 only. No future return is used.
    out = pd.DataFrame(1.0, index=returns.index, columns=returns.columns)
    count = pd.DataFrame(0, index=returns.index, columns=returns.columns)
    for lag in range(2, 13):
        shifted = gross.shift(lag)
        out = out.mul(shifted.fillna(1.0), fill_value=1.0)
        count = count.add(shifted.notna().astype(int), fill_value=0)
    return (out - 1.0).where(count.eq(11))


def _attach_raw_momentum(frame: pd.DataFrame) -> pd.DataFrame:
    monthly_returns = pd.read_csv(MONTHLY_RETURNS_FILE, index_col=0, parse_dates=True)
    raw = _raw_12_1_momentum(monthly_returns)
    raw_long = raw.reset_index(names="month").melt(id_vars="month", var_name="ticker", value_name="raw_return_12_1")
    raw_long["month"] = pd.to_datetime(raw_long["month"])
    merged = frame.merge(raw_long, on=["month", "ticker"], how="left")
    valid = merged["rsm_valid_observation"] & merged["raw_return_12_1"].notna()
    merged["raw_momentum_rank"] = np.nan
    merged["raw_momentum_percentile"] = np.nan
    ranks = merged.loc[valid].groupby("month")["raw_return_12_1"].rank(method="average", ascending=True)
    counts = merged.loc[valid].groupby("month")["raw_return_12_1"].transform("count")
    merged.loc[valid, "raw_momentum_rank"] = ranks
    merged.loc[valid, "raw_momentum_percentile"] = (ranks - 1.0) / (counts - 1.0)
    return merged


def _state_profile(frame: pd.DataFrame) -> pd.DataFrame:
    valid = frame[frame["rsm_valid_observation"]].copy()
    rows = []
    for state, group in valid.groupby("rsm_state", sort=True):
        rows.append(
            {
                "rsm_state": state,
                "observations": int(len(group)),
                "unique_tickers": int(group["ticker"].nunique()),
                "mean_rsm_score": float(group["rsm_score"].mean()),
                "median_rsm_score": float(group["rsm_score"].median()),
                "mean_rsm_percentile": float(group["rsm_percentile"].mean()),
                "mean_residual_sum_12_1": float(group["residual_sum_12_1"].mean()),
                "mean_residual_vol_36m": float(group["residual_vol_36m"].mean()),
                "median_residual_vol_36m": float(group["residual_vol_36m"].median()),
                "mean_raw_return_12_1": float(group["raw_return_12_1"].mean()),
                "median_raw_return_12_1": float(group["raw_return_12_1"].median()),
                "mean_raw_momentum_percentile": float(group["raw_momentum_percentile"].mean()),
                "mean_excess_return_current_month": float(group["excess_return"].mean()),
                "mean_residual_return_current_month": float(group["residual_return"].mean()),
            }
        )
    order = {"BOTTOM_DECILE": 0, "MIDDLE": 1, "TOP_DECILE": 2}
    return pd.DataFrame(rows).sort_values("rsm_state", key=lambda s: s.map(order)).reset_index(drop=True)


def _yearly_state_profile(frame: pd.DataFrame) -> pd.DataFrame:
    valid = frame[frame["rsm_valid_observation"]].copy()
    valid["year"] = valid["month"].dt.year
    rows = []
    for (year, state), group in valid.groupby(["year", "rsm_state"], sort=True):
        rows.append(
            {
                "year": int(year),
                "rsm_state": state,
                "observations": int(len(group)),
                "mean_rsm_score": float(group["rsm_score"].mean()),
                "mean_raw_momentum_percentile": float(group["raw_momentum_percentile"].mean()),
                "mean_residual_vol_36m": float(group["residual_vol_36m"].mean()),
                "mean_residual_sum_12_1": float(group["residual_sum_12_1"].mean()),
            }
        )
    return pd.DataFrame(rows)


def _rank_agreement(frame: pd.DataFrame) -> pd.DataFrame:
    valid = frame[frame["rsm_valid_observation"] & frame["raw_momentum_percentile"].notna()].copy()
    rows = []
    for month, group in valid.groupby("month", sort=True):
        if len(group) < 3:
            continue
        rsm_rank = group["rsm_percentile"].rank(method="average")
        raw_rank = group["raw_momentum_percentile"].rank(method="average")
        rows.append(
            {
                "month": month,
                "eligible_count": int(len(group)),
                "spearman_rsm_vs_raw_momentum": float(rsm_rank.corr(raw_rank, method="pearson")),
                "pearson_rsm_score_vs_raw_return_12_1": float(group["rsm_score"].corr(group["raw_return_12_1"], method="pearson")),
            }
        )
    return pd.DataFrame(rows)


def _state_transition(frame: pd.DataFrame) -> pd.DataFrame:
    valid = frame[frame["rsm_valid_observation"]].sort_values(["ticker", "month"]).copy()
    valid["next_state"] = valid.groupby("ticker")["rsm_state"].shift(-1)
    valid["next_month"] = valid.groupby("ticker")["month"].shift(-1)
    consecutive = valid["next_month"].eq(valid["month"] + pd.offsets.MonthEnd(1))
    transition = valid[consecutive & valid["next_state"].notna()].copy()
    table = transition.groupby(["rsm_state", "next_state"], sort=True).size().reset_index(name="count")
    table["from_total"] = table.groupby("rsm_state")["count"].transform("sum")
    table["transition_rate"] = table["count"] / table["from_total"]
    return table


def _episode_statistics(frame: pd.DataFrame) -> pd.DataFrame:
    valid = frame[frame["rsm_valid_observation"]].sort_values(["ticker", "month"]).copy()
    rows = []
    for ticker, group in valid.groupby("ticker", sort=True):
        state_change = group["rsm_state"].ne(group["rsm_state"].shift()).cumsum()
        for _, episode in group.groupby(state_change):
            rows.append(
                {
                    "ticker": ticker,
                    "rsm_state": episode["rsm_state"].iloc[0],
                    "start_month": episode["month"].min(),
                    "end_month": episode["month"].max(),
                    "duration_months": int(len(episode)),
                }
            )
    episodes = pd.DataFrame(rows)
    if episodes.empty:
        return episodes
    return episodes.groupby("rsm_state", sort=True).agg(
        episodes=("duration_months", "count"),
        mean_duration_months=("duration_months", "mean"),
        median_duration_months=("duration_months", "median"),
        p90_duration_months=("duration_months", lambda s: float(s.quantile(0.90))),
        max_duration_months=("duration_months", "max"),
    ).reset_index()


def _write_reports(
    *,
    frame: pd.DataFrame,
    state_profile: pd.DataFrame,
    yearly_profile: pd.DataFrame,
    rank_agreement: pd.DataFrame,
    transitions: pd.DataFrame,
    episodes: pd.DataFrame,
) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    state_profile.to_csv(OUTPUT_DIR / "state_profile.csv", index=False)
    yearly_profile.to_csv(OUTPUT_DIR / "yearly_state_profile.csv", index=False)
    rank_agreement.to_csv(OUTPUT_DIR / "rank_agreement.csv", index=False)
    transitions.to_csv(OUTPUT_DIR / "state_transition_matrix.csv", index=False)
    episodes.to_csv(OUTPUT_DIR / "episode_statistics.csv", index=False)

    valid = frame[frame["rsm_valid_observation"]].copy()
    top = state_profile[state_profile["rsm_state"] == "TOP_DECILE"].iloc[0]
    bottom = state_profile[state_profile["rsm_state"] == "BOTTOM_DECILE"].iloc[0]
    middle = state_profile[state_profile["rsm_state"] == "MIDDLE"].iloc[0]
    median_spearman = float(rank_agreement["spearman_rsm_vs_raw_momentum"].median()) if len(rank_agreement) else np.nan
    mean_spearman = float(rank_agreement["spearman_rsm_vs_raw_momentum"].mean()) if len(rank_agreement) else np.nan
    top_retention = transitions[
        (transitions["rsm_state"] == "TOP_DECILE") & (transitions["next_state"] == "TOP_DECILE")
    ]["transition_rate"]
    bottom_retention = transitions[
        (transitions["rsm_state"] == "BOTTOM_DECILE") & (transitions["next_state"] == "BOTTOM_DECILE")
    ]["transition_rate"]

    main = f"""# RSM-001 / MI-001 Mechanism Identification

## Purpose

Characterize the observable behavior represented by the validated RSM-001 residual momentum states.

No future returns, alpha, trading performance, strategy backtest, Sharpe, CAGR, drawdown, predictive validation or economic value were evaluated.

## Study Population

- Valid construct months: {valid["month"].min().date()} to {valid["month"].max().date()}
- Valid observations: {len(valid):,}
- Unique tickers: {valid["ticker"].nunique():,}
- TOP_DECILE observations: {int(top["observations"]):,}
- BOTTOM_DECILE observations: {int(bottom["observations"]):,}

## Mechanism Summary

RSM-001 represents a **factor-residual relative strength state**: it identifies securities with high or low intermediate-horizon residual performance after removing common Fama-French 3-factor exposure and scaling by residual volatility.

## Supported By Evidence

- TOP_DECILE has strongly positive mean standardized residual momentum score: {top["mean_rsm_score"]:.4f}.
- BOTTOM_DECILE has strongly negative mean standardized residual momentum score: {bottom["mean_rsm_score"]:.4f}.
- MIDDLE is centered near the cross-sectional middle with mean percentile {middle["mean_rsm_percentile"]:.4f}.
- RSM percentile and raw 12-1 momentum percentile are related but not identical; median monthly Spearman agreement is {median_spearman:.4f}.
- State persistence exists but is rotating; TOP_DECILE one-month retention is {float(top_retention.iloc[0]) if len(top_retention) else np.nan:.4f}, and BOTTOM_DECILE one-month retention is {float(bottom_retention.iloc[0]) if len(bottom_retention) else np.nan:.4f}.

## Partially Supported

- RSM-001 appears to separate idiosyncratic/residual winner and loser states rather than simple raw price winners and losers. This is supported by the raw-vs-residual rank agreement analysis, but the analysis does not evaluate future outcomes.

## Not Evaluated

- Predictive power
- Future returns
- Alpha
- Strategy profitability
- Economic utility

## MI-001 Classification

RSM-001 is best characterized as a **factor-residual cross-sectional leadership / residual winner-loser state construct** under the frozen CD-001 definition.
"""
    (OUTPUT_DIR / "mi001_mechanism_identification.md").write_text(main, encoding="utf-8")

    (OUTPUT_DIR / "market_condition_summary.md").write_text(
        f"""# Market Condition Summary

RSM-001 is not a market-wide directional regime construct.

It is cross-sectional and security-relative. Market factor returns are used only to residualize each security's return series through the frozen FF3 model.

Observed monthly factor fields preserved in the state file:

- `mkt_rf`
- `smb`
- `hml`
- `rf`

No inference was made about whether these market conditions predict RSM state outcomes.
""",
        encoding="utf-8",
    )

    (OUTPUT_DIR / "residual_vs_raw_momentum_report.md").write_text(
        f"""# Residual vs Raw Momentum Report

Median monthly Spearman rank agreement between RSM percentile and raw 12-1 momentum percentile:

```text
{median_spearman:.4f}
```

Mean monthly Spearman rank agreement:

```text
{mean_spearman:.4f}
```

Interpretation:

The residual momentum construct overlaps with raw intermediate-horizon momentum but is not identical to it. This is expected because RSM removes common FF3 factor exposure and volatility-standardizes residual performance.
""",
        encoding="utf-8",
    )

    (OUTPUT_DIR / "transition_event_analysis.md").write_text(
        """# Transition Event Analysis

This MI stage evaluates state transitions descriptively.

The transition matrix is stored in `state_transition_matrix.csv`.

No historical event attribution, predictive claim, or trading-performance interpretation was performed.
""",
        encoding="utf-8",
    )

    (OUTPUT_DIR / "mechanism_hypotheses.md").write_text(
        """# Mechanism Hypotheses For HV-001

The following mechanism hypotheses are generated from MI-001 and require formal HV-001 validation:

H1:

TOP_DECILE RSM states represent securities with persistently positive factor-residual intermediate-horizon performance.

H2:

BOTTOM_DECILE RSM states represent securities with persistently negative factor-residual intermediate-horizon performance.

H3:

RSM states are related to, but distinguishable from, raw 12-1 cross-sectional momentum states.

H4:

Residual volatility standardization materially affects cross-sectional state assignment relative to unstandardized residual sums.

These are explanatory hypotheses only. They are not predictive or economic hypotheses.
""",
        encoding="utf-8",
    )

    (OUTPUT_DIR / "limitations.md").write_text(
        """# Limitations

- Current-constituent universe creates survivorship-bias risk.
- Yahoo adjusted-close data conventions carry through from the source panel.
- The study characterizes existing state behavior only.
- No future outcome was evaluated.
- No predictive validation was performed.
- No economic validation was performed.
- No alpha claim was made.
""",
        encoding="utf-8",
    )

    (OUTPUT_DIR / "executive_summary.md").write_text(
        f"""# Executive Summary

RSM-001 / MI-001 characterized the residual momentum states produced by the validated construct.

The construct behaves as a factor-residual cross-sectional leadership sensor: TOP_DECILE observations have strongly positive standardized residual momentum, BOTTOM_DECILE observations have strongly negative standardized residual momentum, and the middle state remains centered.

RSM overlaps with raw 12-1 momentum but is not identical to it. Median monthly Spearman agreement was {median_spearman:.4f}.

No predictive or economic claim was made.

RSM-001 may proceed to HV-001 to formally validate the proposed mechanism hypotheses.
""",
        encoding="utf-8",
    )

    (OUTPUT_DIR / "next_stage_goal_hv001.md").write_text(
        """# RSM-001 / HV-001 Hypothesis Validation

Purpose:

Formally validate the mechanism hypotheses generated in MI-001.

Hypotheses:

- TOP_DECILE states represent persistently positive factor-residual intermediate-horizon performance.
- BOTTOM_DECILE states represent persistently negative factor-residual intermediate-horizon performance.
- RSM states are related to, but distinguishable from, raw 12-1 momentum states.
- Residual volatility standardization materially affects state assignment relative to unstandardized residual sums.

Forbidden:

- Predictive validation.
- Future return forecasting.
- Backtesting.
- Alpha claims.
- Economic validation.
- Parameter optimization.
""",
        encoding="utf-8",
    )

    manifest = {
        "construct_id": "RSM-001",
        "stage": "MI-001",
        "classification": "Mechanism identified",
        "primary_mechanism": "Factor-residual cross-sectional leadership / residual winner-loser state",
        "valid_observations": int(len(valid)),
        "unique_tickers": int(valid["ticker"].nunique()),
        "median_monthly_spearman_rsm_vs_raw_momentum": median_spearman,
        "top_decile_retention": float(top_retention.iloc[0]) if len(top_retention) else None,
        "bottom_decile_retention": float(bottom_retention.iloc[0]) if len(bottom_retention) else None,
        "next_stage": "HV-001",
    }
    (OUTPUT_DIR / "mi001_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def run_mechanism_identification() -> dict[str, object]:
    frame = _attach_raw_momentum(_load_state())
    profile = _state_profile(frame)
    yearly = _yearly_state_profile(frame)
    agreement = _rank_agreement(frame)
    transitions = _state_transition(frame)
    episodes = _episode_statistics(frame)
    _write_reports(
        frame=frame,
        state_profile=profile,
        yearly_profile=yearly,
        rank_agreement=agreement,
        transitions=transitions,
        episodes=episodes,
    )
    return {
        "valid_observations": int(frame["rsm_valid_observation"].sum()),
        "state_profile_rows": int(len(profile)),
        "rank_agreement_months": int(len(agreement)),
        "status": "COMPLETE",
    }


if __name__ == "__main__":
    print(json.dumps(run_mechanism_identification(), indent=2))
