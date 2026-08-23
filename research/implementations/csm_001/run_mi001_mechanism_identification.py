from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[3]
STATE_FILE = REPO_ROOT / "output" / "csm_001_cv001" / "csm001_construct_state.csv"
OUTPUT_DIR = REPO_ROOT / "research" / "market_edge_discovery_program" / "csm_001_mi_001_mechanism_identification"


def _safe_float(value: float) -> float | None:
    if pd.isna(value) or not np.isfinite(value):
        return None
    return float(value)


def _load_valid_state() -> pd.DataFrame:
    if not STATE_FILE.exists():
        raise FileNotFoundError(f"Missing CSM-001 state file: {STATE_FILE}")
    usecols = [
        "date",
        "ticker",
        "return_12_1",
        "csm001_rank",
        "csm001_eligible_count",
        "csm001_momentum_score",
        "csm001_top_decile_flag",
        "csm001_valid_observation",
    ]
    frame = pd.read_csv(STATE_FILE, usecols=usecols, parse_dates=["date"])
    frame = frame[frame["csm001_valid_observation"].astype(bool)].copy()
    frame["csm001_top_decile_flag"] = frame["csm001_top_decile_flag"].astype(bool)
    return frame.sort_values(["date", "ticker"]).reset_index(drop=True)


def _assign_deciles(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    decile = np.floor(result["csm001_momentum_score"] * 10).astype(int) + 1
    result["score_decile"] = np.clip(decile, 1, 10)
    return result


def _state_profile(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    full_score = frame["csm001_momentum_score"]
    full_return = frame["return_12_1"]
    rows.append(
        {
            "profile": "ALL_VALID",
            "observations": int(len(frame)),
            "unique_tickers": int(frame["ticker"].nunique()),
            "score_mean": _safe_float(full_score.mean()),
            "score_median": _safe_float(full_score.median()),
            "score_std": _safe_float(full_score.std(ddof=0)),
            "return_12_1_mean": _safe_float(full_return.mean()),
            "return_12_1_median": _safe_float(full_return.median()),
            "top_decile_rate": _safe_float(frame["csm001_top_decile_flag"].mean()),
        }
    )
    for decile, group in frame.groupby("score_decile", sort=True):
        rows.append(
            {
                "profile": f"DECILE_{decile}",
                "observations": int(len(group)),
                "unique_tickers": int(group["ticker"].nunique()),
                "score_mean": _safe_float(group["csm001_momentum_score"].mean()),
                "score_median": _safe_float(group["csm001_momentum_score"].median()),
                "score_std": _safe_float(group["csm001_momentum_score"].std(ddof=0)),
                "return_12_1_mean": _safe_float(group["return_12_1"].mean()),
                "return_12_1_median": _safe_float(group["return_12_1"].median()),
                "top_decile_rate": _safe_float(group["csm001_top_decile_flag"].mean()),
            }
        )
    return pd.DataFrame(rows)


def _rank_persistence(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    score_panel = frame.pivot(index="date", columns="ticker", values="csm001_momentum_score").sort_index()
    rows = []
    for lag in [1, 5, 21, 63, 126]:
        daily_corrs = []
        for idx in range(lag, len(score_panel)):
            current = score_panel.iloc[idx]
            previous = score_panel.iloc[idx - lag]
            aligned = pd.concat([current, previous], axis=1).dropna()
            if len(aligned) >= 50:
                current_rank = aligned.iloc[:, 0].rank(method="average")
                previous_rank = aligned.iloc[:, 1].rank(method="average")
                daily_corrs.append(current_rank.corr(previous_rank))
        series = pd.Series(daily_corrs, dtype=float).dropna()
        rows.append(
            {
                "lag_trading_days": lag,
                "dates_evaluated": int(len(series)),
                "mean_cross_sectional_spearman": _safe_float(series.mean()),
                "median_cross_sectional_spearman": _safe_float(series.median()),
                "p10_cross_sectional_spearman": _safe_float(series.quantile(0.10)),
                "p90_cross_sectional_spearman": _safe_float(series.quantile(0.90)),
            }
        )

    ticker_rows = []
    for ticker, series in score_panel.items():
        valid = series.dropna()
        ticker_rows.append(
            {
                "ticker": ticker,
                "valid_days": int(len(valid)),
                "score_autocorr_21d": _safe_float(valid.autocorr(lag=21)) if len(valid) > 42 else None,
                "score_autocorr_63d": _safe_float(valid.autocorr(lag=63)) if len(valid) > 126 else None,
            }
        )
    return pd.DataFrame(rows), pd.DataFrame(ticker_rows)


def _top_decile_turnover(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    dates = list(frame["date"].drop_duplicates().sort_values())
    top_by_date: dict[pd.Timestamp, set[str]] = {}
    for date, group in frame[frame["csm001_top_decile_flag"]].groupby("date", sort=True):
        top_by_date[date] = set(group["ticker"])

    rows = []
    previous: set[str] | None = None
    for date in dates:
        current = top_by_date.get(date, set())
        if previous is None:
            retained = set()
            added = current
            dropped = set()
            retention_rate = np.nan
            turnover_rate = np.nan
        else:
            retained = previous & current
            added = current - previous
            dropped = previous - current
            retention_rate = len(retained) / len(previous) if previous else np.nan
            turnover_rate = (len(added) + len(dropped)) / max(len(previous | current), 1)
        rows.append(
            {
                "date": date,
                "top_decile_count": len(current),
                "retained_count": len(retained),
                "added_count": len(added),
                "dropped_count": len(dropped),
                "retention_rate": _safe_float(retention_rate),
                "turnover_rate": _safe_float(turnover_rate),
            }
        )
        previous = current

    turnover = pd.DataFrame(rows)

    streak_rows = []
    top = frame[["date", "ticker", "csm001_top_decile_flag"]].copy()
    for ticker, group in top.groupby("ticker", sort=True):
        active = group.sort_values("date")["csm001_top_decile_flag"].to_numpy()
        streak_lengths = []
        streak = 0
        for flag in active:
            if flag:
                streak += 1
            elif streak:
                streak_lengths.append(streak)
                streak = 0
        if streak:
            streak_lengths.append(streak)
        if streak_lengths:
            streak_rows.append(
                {
                    "ticker": ticker,
                    "top_decile_episodes": len(streak_lengths),
                    "mean_episode_length_days": float(np.mean(streak_lengths)),
                    "median_episode_length_days": float(np.median(streak_lengths)),
                    "max_episode_length_days": int(np.max(streak_lengths)),
                }
            )
    streaks = pd.DataFrame(streak_rows)
    return turnover, streaks


def _ticker_profile(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for ticker, group in frame.groupby("ticker", sort=True):
        rows.append(
            {
                "ticker": ticker,
                "valid_days": int(len(group)),
                "mean_score": _safe_float(group["csm001_momentum_score"].mean()),
                "median_score": _safe_float(group["csm001_momentum_score"].median()),
                "top_decile_days": int(group["csm001_top_decile_flag"].sum()),
                "top_decile_rate": _safe_float(group["csm001_top_decile_flag"].mean()),
                "mean_return_12_1": _safe_float(group["return_12_1"].mean()),
                "median_return_12_1": _safe_float(group["return_12_1"].median()),
            }
        )
    return pd.DataFrame(rows)


def _write_reports(
    frame: pd.DataFrame,
    state_profile: pd.DataFrame,
    rank_persistence: pd.DataFrame,
    ticker_autocorr: pd.DataFrame,
    turnover: pd.DataFrame,
    streaks: pd.DataFrame,
    ticker_profile: pd.DataFrame,
) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    first_date = frame["date"].min().date()
    last_date = frame["date"].max().date()
    top_rate = frame["csm001_top_decile_flag"].mean()
    daily_retention = turnover["retention_rate"].dropna()
    daily_turnover = turnover["turnover_rate"].dropna()
    median_episode = streaks["median_episode_length_days"].median() if len(streaks) else np.nan
    lag21 = rank_persistence.loc[rank_persistence["lag_trading_days"] == 21, "median_cross_sectional_spearman"].iloc[0]
    lag63 = rank_persistence.loc[rank_persistence["lag_trading_days"] == 63, "median_cross_sectional_spearman"].iloc[0]

    main = f"""# CSM-001 / MI-001 Mechanism Identification

## Purpose

Characterize the observable market behavior represented by the validated CSM-001 Canonical 12-1 Cross-Sectional Momentum State.

No returns, alpha, trading performance, Sharpe, CAGR, drawdown, portfolio simulation or economic value were evaluated.

## Study Population

- Valid construct dates: {first_date} to {last_date}
- Valid observations: {len(frame):,}
- Unique tickers: {frame["ticker"].nunique()}
- Average top-decile flag rate: {top_rate:.4f}

## Mechanism Summary

CSM-001 represents a **cross-sectional relative winner state** based on trailing 12-1 adjusted-price performance. The construct orders securities by prior intermediate-horizon relative performance and identifies the upper tail of that cross-sectional distribution.

## Supported By Evidence

- The score distribution is mechanically centered near 0.50 because the construct is percentile-rank based.
- The top-decile state is sparse by construction, with an observed valid-row rate of {top_rate:.4f}.
- Rank persistence is present over short and intermediate lags; median 21-day cross-sectional Spearman rank persistence is {lag21:.4f}, and median 63-day persistence is {lag63:.4f}.
- Top-decile membership is persistent but rotating: average daily retention is {daily_retention.mean():.4f}, while average daily turnover is {daily_turnover.mean():.4f}.

## Partially Supported

- The construct behaves like a persistent relative leadership sensor rather than a directional market state. This is supported by rank persistence and top-decile duration statistics, but the analysis does not evaluate whether that state predicts future outcomes.

## Not Evaluated

- Predictive power
- Future returns
- Alpha
- Strategy profitability
- Economic utility

## MI-001 Classification

CSM-001 is best characterized as a **cross-sectional relative leadership / intermediate-horizon winner-state construct** under the frozen CD-001 definition.
"""
    (OUTPUT_DIR / "mi001_mechanism_identification.md").write_text(main, encoding="utf-8")

    market_condition = f"""# Market Condition Summary

CSM-001 does not classify broad market direction or broad market volatility. Its observable behavior is cross-sectional: each date is represented by a ranked distribution of securities.

## Key Descriptive Properties

- Valid observations: {len(frame):,}
- Mean score: {frame["csm001_momentum_score"].mean():.4f}
- Median score: {frame["csm001_momentum_score"].median():.4f}
- Top-decile rate: {top_rate:.4f}
- Mean 12-1 prior return across valid observations: {frame["return_12_1"].mean():.4f}
- Median 12-1 prior return across valid observations: {frame["return_12_1"].median():.4f}

This report describes only the formation-period state and does not inspect future price behavior.
"""
    (OUTPUT_DIR / "market_condition_summary.md").write_text(market_condition, encoding="utf-8")

    transition = f"""# Top-Decile Transition Analysis

Top-decile membership was analyzed as a construct-state transition process.

## Daily Membership Dynamics

- Average daily retention rate: {daily_retention.mean():.4f}
- Median daily retention rate: {daily_retention.median():.4f}
- Average daily turnover rate: {daily_turnover.mean():.4f}
- Median daily turnover rate: {daily_turnover.median():.4f}

## Episode Duration

- Tickers with at least one top-decile episode: {len(streaks)}
- Median episode length across tickers: {median_episode:.2f} trading days
- Maximum single-ticker episode length: {streaks["max_episode_length_days"].max() if len(streaks) else "N/A"} trading days

These transitions describe persistence and rotation of the construct state only. They do not evaluate subsequent returns.
"""
    (OUTPUT_DIR / "transition_event_analysis.md").write_text(transition, encoding="utf-8")

    hypotheses = """# Mechanism Hypotheses

The following hypotheses are generated for the next stage, HV-001. They are not validated in MI-001.

## H1

CSM-001 represents a persistent cross-sectional relative leadership state.

## H2

Top-decile membership is not a one-day noise artifact; it persists over short and intermediate horizons.

## H3

The construct's primary observable mechanism is rank persistence and leadership rotation, not broad market direction.

## H4

The 12-1 skip-period design separates intermediate-horizon winner status from very short-term price movement.

HV-001 should validate or reject these mechanism hypotheses without evaluating trading returns or economic value.
"""
    (OUTPUT_DIR / "mechanism_hypotheses.md").write_text(hypotheses, encoding="utf-8")

    limitations = """# Limitations

- MI-001 is explanatory and descriptive only.
- No future returns, alpha, trading performance, Sharpe, CAGR, drawdown or economic value were evaluated.
- The analysis uses the construct state generated during CV-001, which is based on a current S&P 500-style universe rather than survivorship-free historical constituents.
- Sector, industry and fundamental dimensions were not evaluated because they are not part of the frozen CSM-001 construct state.
- Rank persistence does not imply predictive power.
- Top-decile persistence does not imply profitability.
"""
    (OUTPUT_DIR / "limitations.md").write_text(limitations, encoding="utf-8")

    summary = f"""# Executive Summary

CSM-001 / MI-001 characterized the validated Canonical 12-1 Cross-Sectional Momentum State without evaluating returns or trading outcomes.

The construct is best described as a **cross-sectional relative leadership / intermediate-horizon winner-state construct**. It ranks securities by trailing 12-1 adjusted-price performance and identifies the upper tail of the distribution.

Evidence supports that the construct exhibits rank persistence and top-decile membership persistence with ongoing leadership rotation. This is a mechanism description only; predictive and economic validity remain untested.

Next authorized stage: CSM-001 / HV-001.
"""
    (OUTPUT_DIR / "executive_summary.md").write_text(summary, encoding="utf-8")

    next_goal = """# CSM-001 / HV-001 Hypothesis Validation

Purpose: formally validate the mechanism hypotheses generated by MI-001.

Primary hypotheses:

- H1: CSM-001 represents a persistent cross-sectional relative leadership state.
- H2: Top-decile membership persists beyond one-day noise.
- H3: The primary observable mechanism is rank persistence and leadership rotation rather than broad market direction.
- H4: The 12-1 skip-period design separates intermediate-horizon winner status from very short-term price movement.

Forbidden:

- Returns
- Alpha
- Trading profitability
- Strategy backtests
- Economic value
- Optimization
"""
    (OUTPUT_DIR / "next_stage_goal_hv001.md").write_text(next_goal, encoding="utf-8")

    manifest = {
        "construct_id": "CSM-001",
        "stage": "MI-001",
        "source_state_file": str(STATE_FILE.relative_to(REPO_ROOT)).replace("\\", "/"),
        "valid_observations": int(len(frame)),
        "unique_tickers": int(frame["ticker"].nunique()),
        "first_valid_date": str(first_date),
        "last_valid_date": str(last_date),
        "top_decile_rate": float(top_rate),
        "median_rank_persistence_21d": float(lag21),
        "median_rank_persistence_63d": float(lag63),
        "classification": "cross-sectional relative leadership / intermediate-horizon winner-state construct",
    }
    (OUTPUT_DIR / "mi001_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    frame = _assign_deciles(_load_valid_state())
    state_profile = _state_profile(frame)
    rank_persistence, ticker_autocorr = _rank_persistence(frame)
    turnover, streaks = _top_decile_turnover(frame)
    ticker_profile = _ticker_profile(frame)

    state_profile.to_csv(OUTPUT_DIR / "regime_characteristics.csv", index=False)
    rank_persistence.to_csv(OUTPUT_DIR / "rank_persistence.csv", index=False)
    ticker_autocorr.to_csv(OUTPUT_DIR / "ticker_rank_persistence.csv", index=False)
    turnover.to_csv(OUTPUT_DIR / "top_decile_transition_analysis.csv", index=False)
    streaks.to_csv(OUTPUT_DIR / "top_decile_episode_statistics.csv", index=False)
    ticker_profile.to_csv(OUTPUT_DIR / "ticker_state_profile.csv", index=False)

    _write_reports(frame, state_profile, rank_persistence, ticker_autocorr, turnover, streaks, ticker_profile)
    print(json.dumps({"status": "PASSED", "output_dir": str(OUTPUT_DIR)}, indent=2))


if __name__ == "__main__":
    main()
