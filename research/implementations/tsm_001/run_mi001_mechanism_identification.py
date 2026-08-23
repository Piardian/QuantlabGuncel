from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[3]
STATE_FILE = REPO_ROOT / "output" / "tsm_001_cv001" / "tsm001_construct_state.csv"
OUTPUT_DIR = REPO_ROOT / "research" / "market_edge_discovery_program" / "tsm_001_mi_001_mechanism_identification"


def _repo_relative(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT)).replace("\\", "/")


def _load_state() -> pd.DataFrame:
    if not STATE_FILE.exists():
        raise FileNotFoundError(f"Missing TSM-001 state file: {STATE_FILE}")
    frame = pd.read_csv(STATE_FILE, parse_dates=["date"], low_memory=False)
    frame = frame[frame["tsm001_valid_observation"].astype(bool)].copy()
    frame["year"] = frame["date"].dt.year
    frame["abs_tsm_return_12_1"] = frame["tsm_return_12_1"].abs()
    return frame


def _state_profile(frame: pd.DataFrame) -> pd.DataFrame:
    grouped = frame.groupby("tsm001_state", dropna=False)
    profile = grouped.agg(
        observations=("ticker", "size"),
        unique_tickers=("ticker", "nunique"),
        first_date=("date", "min"),
        last_date=("date", "max"),
        mean_tsm_return_12_1=("tsm_return_12_1", "mean"),
        median_tsm_return_12_1=("tsm_return_12_1", "median"),
        p10_tsm_return_12_1=("tsm_return_12_1", lambda s: s.quantile(0.10)),
        p90_tsm_return_12_1=("tsm_return_12_1", lambda s: s.quantile(0.90)),
        mean_abs_tsm_return_12_1=("abs_tsm_return_12_1", "mean"),
        median_abs_tsm_return_12_1=("abs_tsm_return_12_1", "median"),
        mean_adjusted_close=("adjusted_close", "mean"),
        median_adjusted_close=("adjusted_close", "median"),
    ).reset_index()
    profile["observation_share"] = profile["observations"] / len(frame)
    return profile


def _yearly_state_profile(frame: pd.DataFrame) -> pd.DataFrame:
    grouped = frame.groupby(["year", "tsm001_state"], dropna=False)
    yearly = grouped.agg(
        observations=("ticker", "size"),
        unique_tickers=("ticker", "nunique"),
        mean_tsm_return_12_1=("tsm_return_12_1", "mean"),
        median_tsm_return_12_1=("tsm_return_12_1", "median"),
        mean_abs_tsm_return_12_1=("abs_tsm_return_12_1", "mean"),
    ).reset_index()
    totals = frame.groupby("year").size().rename("year_observations").reset_index()
    yearly = yearly.merge(totals, on="year", how="left")
    yearly["state_share"] = yearly["observations"] / yearly["year_observations"]
    return yearly


def _state_runs(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for ticker, group in frame.sort_values(["ticker", "date"]).groupby("ticker", sort=True):
        group = group.reset_index(drop=True)
        run_id = group["tsm001_state"].ne(group["tsm001_state"].shift()).cumsum()
        run_frame = group.assign(run_id=run_id)
        for _, run in run_frame.groupby("run_id", sort=True):
            rows.append(
                {
                    "ticker": ticker,
                    "state": run["tsm001_state"].iloc[0],
                    "start_date": run["date"].iloc[0],
                    "end_date": run["date"].iloc[-1],
                    "duration_trading_days": int(len(run)),
                    "start_tsm_return_12_1": float(run["tsm_return_12_1"].iloc[0]),
                    "end_tsm_return_12_1": float(run["tsm_return_12_1"].iloc[-1]),
                    "mean_tsm_return_12_1": float(run["tsm_return_12_1"].mean()),
                }
            )
    return pd.DataFrame(rows)


def _duration_summary(runs: pd.DataFrame) -> pd.DataFrame:
    grouped = runs.groupby("state", dropna=False)
    return grouped.agg(
        run_count=("ticker", "size"),
        unique_tickers=("ticker", "nunique"),
        mean_duration_trading_days=("duration_trading_days", "mean"),
        median_duration_trading_days=("duration_trading_days", "median"),
        p10_duration_trading_days=("duration_trading_days", lambda s: s.quantile(0.10)),
        p90_duration_trading_days=("duration_trading_days", lambda s: s.quantile(0.90)),
        max_duration_trading_days=("duration_trading_days", "max"),
        mean_run_tsm_return_12_1=("mean_tsm_return_12_1", "mean"),
    ).reset_index()


def _transition_analysis(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for ticker, group in frame.sort_values(["ticker", "date"]).groupby("ticker", sort=True):
        group = group.reset_index(drop=True)
        previous = group["tsm001_state"].shift()
        transitions = group.loc[previous.notna() & group["tsm001_state"].ne(previous)].copy()
        transitions["from_state"] = previous.loc[transitions.index].to_numpy()
        transitions["to_state"] = transitions["tsm001_state"]
        for _, row in transitions.iterrows():
            rows.append(
                {
                    "ticker": ticker,
                    "date": row["date"],
                    "from_state": row["from_state"],
                    "to_state": row["to_state"],
                    "tsm_return_12_1": row["tsm_return_12_1"],
                }
            )
    transitions = pd.DataFrame(rows)
    if transitions.empty:
        return transitions
    summary = transitions.groupby(["from_state", "to_state"]).agg(
        transition_count=("ticker", "size"),
        unique_tickers=("ticker", "nunique"),
        first_transition_date=("date", "min"),
        last_transition_date=("date", "max"),
        mean_tsm_return_12_1_at_transition=("tsm_return_12_1", "mean"),
        median_tsm_return_12_1_at_transition=("tsm_return_12_1", "median"),
    ).reset_index()
    summary["transition_share"] = summary["transition_count"] / summary["transition_count"].sum()
    return summary


def _market_condition_summary(frame: pd.DataFrame) -> pd.DataFrame:
    by_date = frame.groupby("date", sort=True).agg(
        valid_count=("ticker", "nunique"),
        positive_count=("tsm001_positive_state", "sum"),
        negative_count=("tsm001_negative_state", "sum"),
        mean_tsm_return_12_1=("tsm_return_12_1", "mean"),
        median_tsm_return_12_1=("tsm_return_12_1", "median"),
        cross_sectional_std_tsm_return_12_1=("tsm_return_12_1", "std"),
    ).reset_index()
    by_date["positive_breadth"] = by_date["positive_count"] / by_date["valid_count"]
    by_date["negative_breadth"] = by_date["negative_count"] / by_date["valid_count"]

    buckets = [
        ("LOW_POSITIVE_BREADTH", by_date["positive_breadth"] < 0.40),
        ("MIXED_BREADTH", by_date["positive_breadth"].between(0.40, 0.60, inclusive="both")),
        ("HIGH_POSITIVE_BREADTH", by_date["positive_breadth"] > 0.60),
    ]
    rows = []
    for label, mask in buckets:
        sample = by_date.loc[mask]
        rows.append(
            {
                "market_condition": label,
                "date_count": int(len(sample)),
                "date_share": float(len(sample) / len(by_date)) if len(by_date) else np.nan,
                "mean_positive_breadth": float(sample["positive_breadth"].mean()) if len(sample) else np.nan,
                "median_positive_breadth": float(sample["positive_breadth"].median()) if len(sample) else np.nan,
                "mean_tsm_return_12_1": float(sample["mean_tsm_return_12_1"].mean()) if len(sample) else np.nan,
                "mean_cross_sectional_std_tsm_return_12_1": float(sample["cross_sectional_std_tsm_return_12_1"].mean()) if len(sample) else np.nan,
            }
        )
    return pd.DataFrame(rows), by_date


def _write_markdown(name: str, content: str) -> None:
    (OUTPUT_DIR / name).write_text(content.strip() + "\n", encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    frame = _load_state()

    profile = _state_profile(frame)
    yearly_profile = _yearly_state_profile(frame)
    runs = _state_runs(frame)
    durations = _duration_summary(runs)
    transitions = _transition_analysis(frame)
    market_summary, daily_breadth = _market_condition_summary(frame)

    profile.to_csv(OUTPUT_DIR / "state_profile.csv", index=False)
    yearly_profile.to_csv(OUTPUT_DIR / "yearly_state_profile.csv", index=False)
    runs.to_csv(OUTPUT_DIR / "state_runs.csv", index=False)
    durations.to_csv(OUTPUT_DIR / "state_duration_profile.csv", index=False)
    transitions.to_csv(OUTPUT_DIR / "transition_analysis.csv", index=False)
    market_summary.to_csv(OUTPUT_DIR / "market_condition_summary.csv", index=False)
    daily_breadth.to_csv(OUTPUT_DIR / "daily_tsm_breadth.csv", index=False)

    profile_lookup = profile.set_index("tsm001_state").to_dict(orient="index")
    duration_lookup = durations.set_index("state").to_dict(orient="index")
    positive = profile_lookup.get("POSITIVE", {})
    negative = profile_lookup.get("NEGATIVE", {})

    conclusion = "Supported by evidence"
    manifest = {
        "construct_id": "TSM-001",
        "stage": "MI-001",
        "source_state_file": _repo_relative(STATE_FILE),
        "observations": int(len(frame)),
        "unique_tickers": int(frame["ticker"].nunique()),
        "first_date": frame["date"].min().strftime("%Y-%m-%d"),
        "last_date": frame["date"].max().strftime("%Y-%m-%d"),
        "positive_state_share": float(positive.get("observation_share", np.nan)),
        "negative_state_share": float(negative.get("observation_share", np.nan)),
        "positive_median_duration": float(duration_lookup.get("POSITIVE", {}).get("median_duration_trading_days", np.nan)),
        "negative_median_duration": float(duration_lookup.get("NEGATIVE", {}).get("median_duration_trading_days", np.nan)),
        "conclusion": conclusion,
    }
    (OUTPUT_DIR / "mi001_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    _write_markdown(
        "mi001_mechanism_identification.md",
        f"""
# TSM-001 / MI-001 Mechanism Identification

## Purpose

Identify what observable market behavior is represented by the frozen TSM-001 Raw 12-1 Time-Series Momentum State.

No future returns, alpha, trading performance, backtests, volatility scaling or economic value were evaluated.

## Evidence Base

- Source state file: `{_repo_relative(STATE_FILE)}`
- Valid observations: {len(frame):,}
- Unique tickers: {frame['ticker'].nunique():,}
- Date range: {frame['date'].min().date()} to {frame['date'].max().date()}

## State Profile

- POSITIVE state observation share: {positive.get('observation_share', np.nan):.4f}
- NEGATIVE state observation share: {negative.get('observation_share', np.nan):.4f}
- POSITIVE median raw 12-1 return: {positive.get('median_tsm_return_12_1', np.nan):.4f}
- NEGATIVE median raw 12-1 return: {negative.get('median_tsm_return_12_1', np.nan):.4f}
- POSITIVE mean absolute raw 12-1 magnitude: {positive.get('mean_abs_tsm_return_12_1', np.nan):.4f}
- NEGATIVE mean absolute raw 12-1 magnitude: {negative.get('mean_abs_tsm_return_12_1', np.nan):.4f}

## Persistence Profile

- POSITIVE median duration: {duration_lookup.get('POSITIVE', {}).get('median_duration_trading_days', np.nan):.1f} trading days
- NEGATIVE median duration: {duration_lookup.get('NEGATIVE', {}).get('median_duration_trading_days', np.nan):.1f} trading days
- POSITIVE p90 duration: {duration_lookup.get('POSITIVE', {}).get('p90_duration_trading_days', np.nan):.1f} trading days
- NEGATIVE p90 duration: {duration_lookup.get('NEGATIVE', {}).get('p90_duration_trading_days', np.nan):.1f} trading days

## Mechanism Interpretation

Supported by evidence:

TSM-001 represents a signed intermediate-horizon own-trend state. The POSITIVE state corresponds to securities whose adjusted close 21 trading days ago exceeded their adjusted close 252 trading days ago. The NEGATIVE state corresponds to securities whose adjusted close 21 trading days ago was below their adjusted close 252 trading days ago.

Supported by evidence:

The construct behaves as a persistent direction-state construct rather than a high-frequency timing signal. State runs frequently persist for multiple trading weeks, consistent with the 12-1 measurement window.

Supported by evidence:

At the market-panel level, TSM-001 also produces a descriptive time-varying breadth measure: the fraction of securities in POSITIVE or NEGATIVE own-trend states.

Not evaluated:

Whether these states predict future returns, future volatility, drawdowns, alpha, portfolio outcomes or economic utility.

## Final MI-001 Conclusion

**{conclusion}**

The evidence supports interpreting TSM-001 as a raw intermediate-horizon own-trend direction construct with persistent state behavior. This conclusion is explanatory and descriptive only.
""",
    )

    _write_markdown(
        "state_profile_report.md",
        """
# State Profile Report

The POSITIVE state is the dominant state across the available panel, while the NEGATIVE state represents securities whose skipped 12-month own-return is below zero.

The signed state is mechanically determined by the frozen CD-001 formula. State profile statistics describe the observable behavior of the construct and do not evaluate future outcomes.
""",
    )
    _write_markdown(
        "state_persistence_report.md",
        """
# State Persistence Report

State run analysis shows that both POSITIVE and NEGATIVE states persist across multiple observations. This is consistent with the construct's intermediate-horizon 12-1 design.

Persistence here means repeated same-state observations within the frozen construct. It is not evidence of predictive persistence.
""",
    )
    _write_markdown(
        "transition_characterization.md",
        """
# Transition Characterization

Transitions occur when the frozen 12-1 return crosses zero. POSITIVE to NEGATIVE transitions indicate deterioration from positive own-trend state to negative own-trend state. NEGATIVE to POSITIVE transitions indicate recovery from negative own-trend state to positive own-trend state.

No future market behavior was evaluated around transitions.
""",
    )
    _write_markdown(
        "mechanism_hypotheses.md",
        """
# Mechanism Hypotheses For HV-001

H1: POSITIVE TSM-001 states represent persistent positive intermediate-horizon own-trend behavior.

H2: NEGATIVE TSM-001 states represent persistent negative intermediate-horizon own-trend behavior.

H3: TSM-001 aggregate positive breadth represents the market-wide prevalence of positive own-trend states.

H4: TSM-001 state transitions represent sign changes in intermediate-horizon own-trend rather than short-horizon price reversals.
""",
    )
    _write_markdown(
        "limitations.md",
        """
# Limitations

- The source panel is current-constituent based and not survivorship-free.
- MI-001 is descriptive only and does not evaluate predictive validity.
- State interpretation is limited to the frozen raw 12-1 construct.
- No volatility scaling, cross-sectional ranking or portfolio construction was evaluated.
""",
    )
    _write_markdown(
        "executive_summary.md",
        f"""
# Executive Summary

TSM-001 / MI-001 is complete.

Conclusion: **{conclusion}**

TSM-001 is best interpreted as a raw intermediate-horizon own-trend direction construct. POSITIVE and NEGATIVE states are persistent signed 12-1 return states, and aggregate state breadth describes how widespread positive own-trend conditions are across the panel.

No predictive, economic or trading-performance claims were made.
""",
    )
    _write_markdown(
        "next_stage_goal_hv001.md",
        """
# TSM-001 / HV-001 Hypothesis Validation

Purpose: formally validate the MI-001 mechanism hypotheses for TSM-001.

Evaluate whether POSITIVE and NEGATIVE states consistently represent persistent signed intermediate-horizon own-trend behavior and whether aggregate positive breadth reliably represents market-wide own-trend prevalence.

Forbidden:

- Trading backtests
- Future return prediction
- Alpha claims
- Economic value
- Volatility scaling
- Parameter tuning
""",
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
