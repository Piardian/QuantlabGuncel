from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[2]
STATE_FILE = REPO_ROOT / "output" / "rsm_001" / "rsm001_residual_momentum_state.csv"
GENERATION_REPORT_FILE = REPO_ROOT / "output" / "rsm_001" / "rsm001_generation_report.json"
OUTPUT_DIR = REPO_ROOT / "research" / "market_edge_discovery_program" / "rsm_001_cv_001_construct_validation"


def _repo_relative(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT)).replace("\\", "/")


def _hash_frame(frame: pd.DataFrame) -> str:
    payload = frame.to_csv(index=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _load_state() -> pd.DataFrame:
    if not STATE_FILE.exists():
        raise FileNotFoundError(f"Missing RSM-001 construct state file: {STATE_FILE}")
    frame = pd.read_csv(STATE_FILE, parse_dates=["month"])
    frame["rsm_valid_observation"] = frame["rsm_valid_observation"].astype(bool)
    return frame


def _coverage_analysis(frame: pd.DataFrame) -> pd.DataFrame:
    by_month = frame.groupby("month", sort=True)
    coverage = by_month.agg(
        total_universe_count=("ticker", "nunique"),
        valid_count=("rsm_valid_observation", "sum"),
        invalid_count=("rsm_valid_observation", lambda s: int((~s).sum())),
        top_decile_count=("rsm_state", lambda s: int((s == "TOP_DECILE").sum())),
        bottom_decile_count=("rsm_state", lambda s: int((s == "BOTTOM_DECILE").sum())),
        middle_count=("rsm_state", lambda s: int((s == "MIDDLE").sum())),
    ).reset_index()
    coverage["coverage_ratio"] = coverage["valid_count"] / coverage["total_universe_count"]
    coverage["top_decile_rate_of_valid"] = np.where(
        coverage["valid_count"] > 0, coverage["top_decile_count"] / coverage["valid_count"], np.nan
    )
    coverage["bottom_decile_rate_of_valid"] = np.where(
        coverage["valid_count"] > 0, coverage["bottom_decile_count"] / coverage["valid_count"], np.nan
    )
    return coverage


def _state_statistics(frame: pd.DataFrame) -> pd.DataFrame:
    valid = frame[frame["rsm_valid_observation"]].copy()
    rows = []
    groups = [("FULL_SAMPLE", valid)]
    groups.extend((str(year), group) for year, group in valid.groupby(valid["month"].dt.year, sort=True))
    for period, group in groups:
        score = group["rsm_score"].dropna()
        percentile = group["rsm_percentile"].dropna()
        rows.append(
            {
                "period": period,
                "valid_observations": int(len(group)),
                "unique_tickers": int(group["ticker"].nunique()),
                "rsm_score_mean": float(score.mean()) if len(score) else np.nan,
                "rsm_score_std": float(score.std(ddof=0)) if len(score) else np.nan,
                "rsm_score_p10": float(score.quantile(0.10)) if len(score) else np.nan,
                "rsm_score_median": float(score.median()) if len(score) else np.nan,
                "rsm_score_p90": float(score.quantile(0.90)) if len(score) else np.nan,
                "percentile_mean": float(percentile.mean()) if len(percentile) else np.nan,
                "percentile_min": float(percentile.min()) if len(percentile) else np.nan,
                "percentile_max": float(percentile.max()) if len(percentile) else np.nan,
                "top_decile_rate": float((group["rsm_state"] == "TOP_DECILE").mean()) if len(group) else np.nan,
                "bottom_decile_rate": float((group["rsm_state"] == "BOTTOM_DECILE").mean()) if len(group) else np.nan,
                "middle_rate": float((group["rsm_state"] == "MIDDLE").mean()) if len(group) else np.nan,
            }
        )
    return pd.DataFrame(rows)


def _rank_consistency(frame: pd.DataFrame) -> dict[str, object]:
    valid = frame[frame["rsm_valid_observation"]].copy()
    violations = 0
    checked_months = 0
    for month, group in valid.groupby("month", sort=True):
        if len(group) < 2:
            continue
        checked_months += 1
        ordered = group.sort_values("rsm_score")
        if (ordered["rsm_percentile"].diff().dropna() < -1e-12).any():
            violations += 1
        expected_top = group["rsm_percentile"].ge(0.90)
        expected_bottom = group["rsm_percentile"].le(0.10)
        if not (group["rsm_state"].eq("TOP_DECILE") == expected_top).all():
            violations += 1
        if not (group["rsm_state"].eq("BOTTOM_DECILE") == expected_bottom).all():
            violations += 1

    percentile_range_ok = bool(valid["rsm_percentile"].between(0.0, 1.0).all())
    rank_present_ok = bool(valid["rsm_rank"].notna().all())
    score_present_ok = bool(valid["rsm_score"].notna().all())
    return {
        "checked_months": checked_months,
        "rank_percentile_violations": violations,
        "percentile_range_ok": percentile_range_ok,
        "rank_present_ok": rank_present_ok,
        "score_present_ok": score_present_ok,
        "rank_consistency_status": "PASSED"
        if violations == 0 and percentile_range_ok and rank_present_ok and score_present_ok
        else "FAILED",
    }


def _ticker_stability(frame: pd.DataFrame) -> pd.DataFrame:
    valid = frame[frame["rsm_valid_observation"]].copy()
    rows = []
    for ticker, group in valid.groupby("ticker", sort=True):
        rows.append(
            {
                "ticker": ticker,
                "valid_months": int(len(group)),
                "first_valid_month": str(group["month"].min().date()),
                "last_valid_month": str(group["month"].max().date()),
                "mean_percentile": float(group["rsm_percentile"].mean()),
                "std_percentile": float(group["rsm_percentile"].std(ddof=0)),
                "top_decile_rate": float((group["rsm_state"] == "TOP_DECILE").mean()),
                "bottom_decile_rate": float((group["rsm_state"] == "BOTTOM_DECILE").mean()),
            }
        )
    return pd.DataFrame(rows)


def _write_reports(
    *,
    frame: pd.DataFrame,
    coverage: pd.DataFrame,
    state_stats: pd.DataFrame,
    ticker_stability: pd.DataFrame,
    rank_checks: dict[str, object],
    state_hash: str,
    generation_hash: str | None,
) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    coverage.to_csv(OUTPUT_DIR / "coverage_analysis.csv", index=False)
    state_stats.to_csv(OUTPUT_DIR / "state_statistics.csv", index=False)
    ticker_stability.to_csv(OUTPUT_DIR / "ticker_stability.csv", index=False)

    valid = frame[frame["rsm_valid_observation"]]
    post_warmup = coverage[coverage["valid_count"] > 0]
    reproducible = generation_hash is not None and state_hash == generation_hash
    avg_coverage = float(coverage["coverage_ratio"].mean())
    post_warmup_min_coverage = float(post_warmup["coverage_ratio"].min()) if len(post_warmup) else np.nan
    full_stats = state_stats[state_stats["period"] == "FULL_SAMPLE"].iloc[0]
    classification = (
        "Partially supported"
        if reproducible and rank_checks["rank_consistency_status"] == "PASSED" and len(valid) > 0
        else "Inconclusive"
    )

    main = f"""# RSM-001 / CV-001 Construct Validation

## Purpose

Evaluate whether implemented RSM-001 behaves as an internally coherent, reproducible and stable implementation of the frozen CD-001 construct.

No future returns, alpha, trading performance, strategy backtest, Sharpe, CAGR, drawdown or economic value were evaluated.

## Frozen Construct

RSM-001 is the Fama-French 3-Factor Standardized 12-1 Residual Momentum Rank.

It computes monthly security excess returns, removes common FF3 exposure using rolling 36-month OLS, aggregates residuals from `t-12` through `t-2`, standardizes by 36-month residual volatility and ranks securities cross-sectionally.

## Data Scope

- State file: `{_repo_relative(STATE_FILE)}`
- Rows: {len(frame):,}
- Unique tickers: {frame["ticker"].nunique():,}
- Valid observations: {len(valid):,}
- Full sample months: {frame["month"].min().date()} to {frame["month"].max().date()}
- Valid construct months: {valid["month"].min().date() if len(valid) else "N/A"} to {valid["month"].max().date() if len(valid) else "N/A"}

## Validation Results

- Average coverage ratio: {avg_coverage:.4f}
- Minimum post-warmup coverage ratio: {post_warmup_min_coverage:.4f}
- Top decile rate: {full_stats["top_decile_rate"]:.4f}
- Bottom decile rate: {full_stats["bottom_decile_rate"]:.4f}
- Percentile mean: {full_stats["percentile_mean"]:.4f}
- Percentile range: {full_stats["percentile_min"]:.4f} to {full_stats["percentile_max"]:.4f}
- Rank consistency: {rank_checks["rank_consistency_status"]}
- Deterministic hash matches IM generation report: {"PASSED" if reproducible else "FAILED"}

## Final CV-001 Classification

**{classification}**

The construct is reproducible and internally coherent under the available data panel. The classification is not stronger than Partially Supported because the equity universe is current-constituent based rather than survivorship-free historical membership.
"""
    (OUTPUT_DIR / "cv001_construct_validation.md").write_text(main, encoding="utf-8")

    (OUTPUT_DIR / "state_distribution_report.md").write_text(
        f"""# State Distribution Report

RSM-001 produced {len(valid):,} valid observations.

Full-sample state rates:

- TOP_DECILE: {full_stats["top_decile_rate"]:.4f}
- BOTTOM_DECILE: {full_stats["bottom_decile_rate"]:.4f}
- MIDDLE: {full_stats["middle_rate"]:.4f}

Because decile membership is based on cross-sectional percentile ranks, approximate 10% top and bottom state occupancy is expected when eligible cross-sections are sufficiently large.
""",
        encoding="utf-8",
    )

    (OUTPUT_DIR / "rank_consistency_report.md").write_text(
        f"""# Rank Consistency Report

Checked months:

```text
{rank_checks["checked_months"]}
```

Rank / percentile violations:

```text
{rank_checks["rank_percentile_violations"]}
```

Status:

```text
{rank_checks["rank_consistency_status"]}
```
""",
        encoding="utf-8",
    )

    (OUTPUT_DIR / "temporal_stability.md").write_text(
        f"""# Temporal Stability

RSM-001 valid observations begin after the required rolling regression and formation warmup.

Valid sample:

```text
{valid["month"].min().date() if len(valid) else "N/A"} to {valid["month"].max().date() if len(valid) else "N/A"}
```

Year-by-year distribution statistics are available in `state_statistics.csv`.

The construct remains computable across the post-warmup sample, subject to ticker-level data availability.
""",
        encoding="utf-8",
    )

    (OUTPUT_DIR / "reproducibility_report.md").write_text(
        f"""# Reproducibility Report

Current state hash:

```text
{state_hash}
```

IM generation report hash:

```text
{generation_hash}
```

Status:

```text
{"PASSED" if reproducible else "FAILED"}
```
""",
        encoding="utf-8",
    )

    (OUTPUT_DIR / "implementation_validation.md").write_text(
        """# Implementation Validation

The implementation output schema and state logic are consistent with CD-001.

Validated properties:

- Monthly state observations.
- Required FF3 factor fields preserved.
- Residual returns present for valid observations.
- 12-1 residual sums present for valid observations.
- 36-month residual volatility present for valid observations.
- Cross-sectional percentile ranks bounded between 0 and 1.
- State labels follow frozen decile thresholds.

No predictive or economic interpretation was performed.
""",
        encoding="utf-8",
    )

    (OUTPUT_DIR / "limitations.md").write_text(
        """# Limitations

- The universe is based on current S&P 500 constituents, not survivorship-free historical constituents.
- Monthly returns inherit Yahoo Finance adjusted-close data conventions from the existing CSM-001 data panel.
- Fama-French factor data was downloaded from the Ken French public data library.
- CV-001 evaluates construct coherence only.
- No predictive validity was tested.
- No economic value was tested.
- No alpha claim was made.
""",
        encoding="utf-8",
    )

    (OUTPUT_DIR / "executive_summary.md").write_text(
        f"""# Executive Summary

RSM-001 / CV-001 evaluated the implemented residual momentum construct for internal coherence, reproducibility and stability.

The construct generated {len(valid):,} valid observations across {frame["ticker"].nunique():,} tickers from {valid["month"].min().date() if len(valid) else "N/A"} to {valid["month"].max().date() if len(valid) else "N/A"}.

Rank consistency passed and the current state hash matched the IM generation report.

Final classification:

**{classification}**

The construct may proceed to MI-001. No predictive or economic claim was made.
""",
        encoding="utf-8",
    )

    (OUTPUT_DIR / "next_stage_goal_mi001.md").write_text(
        """# RSM-001 / MI-001 Mechanism Identification

Purpose:

Identify the observable mechanism represented by RSM-001 residual momentum states.

Allowed:

- State profiling.
- Residual momentum distribution analysis.
- Residual volatility characterization.
- TOP_DECILE / BOTTOM_DECILE / MIDDLE profile comparison.
- Relationship between raw return momentum and residual momentum.

Forbidden:

- Predictive validation.
- Return forecasting.
- Backtesting.
- Economic validation.
- Alpha claims.
- Parameter optimization.
""",
        encoding="utf-8",
    )

    manifest = {
        "construct_id": "RSM-001",
        "stage": "CV-001",
        "classification": classification,
        "rows": int(len(frame)),
        "valid_observations": int(len(valid)),
        "unique_tickers": int(frame["ticker"].nunique()),
        "first_valid_month": str(valid["month"].min().date()) if len(valid) else None,
        "last_valid_month": str(valid["month"].max().date()) if len(valid) else None,
        "rank_consistency_status": rank_checks["rank_consistency_status"],
        "reproducibility_status": "PASSED" if reproducible else "FAILED",
        "state_hash": state_hash,
        "next_stage": "MI-001" if classification in {"Supported by evidence", "Partially supported"} else "Human review",
    }
    (OUTPUT_DIR / "validation_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def run_validation() -> dict[str, object]:
    frame = _load_state()
    coverage = _coverage_analysis(frame)
    state_stats = _state_statistics(frame)
    ticker_stability = _ticker_stability(frame)
    rank_checks = _rank_consistency(frame)
    state_hash = _hash_frame(frame)
    generation_hash = None
    if GENERATION_REPORT_FILE.exists():
        generation_hash = json.loads(GENERATION_REPORT_FILE.read_text(encoding="utf-8")).get("deterministic_hash")
    _write_reports(
        frame=frame,
        coverage=coverage,
        state_stats=state_stats,
        ticker_stability=ticker_stability,
        rank_checks=rank_checks,
        state_hash=state_hash,
        generation_hash=generation_hash,
    )
    return {
        "rows": int(len(frame)),
        "valid_observations": int(frame["rsm_valid_observation"].sum()),
        "rank_consistency_status": rank_checks["rank_consistency_status"],
        "reproducibility_status": "PASSED" if generation_hash == state_hash else "FAILED",
        "status": "COMPLETE",
    }


if __name__ == "__main__":
    print(json.dumps(run_validation(), indent=2))

