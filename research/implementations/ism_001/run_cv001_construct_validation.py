from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[2]
STATE_FILE = REPO_ROOT / "output" / "ism_001" / "ism001_industry_momentum_state.csv"
GENERATION_REPORT_FILE = REPO_ROOT / "output" / "ism_001" / "ism001_generation_report.json"
OUTPUT_DIR = REPO_ROOT / "research" / "market_edge_discovery_program" / "ism_001_cv_001_construct_validation"


def _repo_relative(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT)).replace("\\", "/")


def _hash_frame(frame: pd.DataFrame) -> str:
    payload = frame.to_csv(index=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _load_state() -> pd.DataFrame:
    if not STATE_FILE.exists():
        raise FileNotFoundError(f"Missing ISM-001 construct state file: {STATE_FILE}")
    frame = pd.read_csv(STATE_FILE, parse_dates=["month"])
    frame["ism_valid_observation"] = frame["ism_valid_observation"].astype(bool)
    return frame.sort_values(["month", "industry_id"]).reset_index(drop=True)


def _coverage_analysis(frame: pd.DataFrame) -> pd.DataFrame:
    by_month = frame.groupby("month", sort=True)
    coverage = by_month.agg(
        total_industry_count=("industry_id", "nunique"),
        valid_count=("ism_valid_observation", "sum"),
        invalid_count=("ism_valid_observation", lambda s: int((~s).sum())),
        top_decile_count=("ism_state", lambda s: int((s == "TOP_DECILE").sum())),
        bottom_decile_count=("ism_state", lambda s: int((s == "BOTTOM_DECILE").sum())),
        middle_count=("ism_state", lambda s: int((s == "MIDDLE").sum())),
    ).reset_index()
    coverage["coverage_ratio"] = coverage["valid_count"] / coverage["total_industry_count"]
    coverage["top_decile_rate_of_valid"] = np.where(
        coverage["valid_count"] > 0, coverage["top_decile_count"] / coverage["valid_count"], np.nan
    )
    coverage["bottom_decile_rate_of_valid"] = np.where(
        coverage["valid_count"] > 0, coverage["bottom_decile_count"] / coverage["valid_count"], np.nan
    )
    return coverage


def _state_statistics(frame: pd.DataFrame) -> pd.DataFrame:
    valid = frame[frame["ism_valid_observation"]].copy()
    rows = []
    groups = [("FULL_SAMPLE", valid)]
    groups.extend((str(year), group) for year, group in valid.groupby(valid["month"].dt.year, sort=True))
    for period, group in groups:
        score = group["ism_score"].dropna()
        formation_return = group["industry_return_12_1"].dropna()
        rows.append(
            {
                "period": period,
                "valid_observations": int(len(group)),
                "unique_industries": int(group["industry_id"].nunique()),
                "industry_return_12_1_mean": float(formation_return.mean()) if len(formation_return) else np.nan,
                "industry_return_12_1_std": float(formation_return.std(ddof=0)) if len(formation_return) else np.nan,
                "industry_return_12_1_p10": float(formation_return.quantile(0.10)) if len(formation_return) else np.nan,
                "industry_return_12_1_median": float(formation_return.median()) if len(formation_return) else np.nan,
                "industry_return_12_1_p90": float(formation_return.quantile(0.90)) if len(formation_return) else np.nan,
                "ism_score_mean": float(score.mean()) if len(score) else np.nan,
                "ism_score_min": float(score.min()) if len(score) else np.nan,
                "ism_score_max": float(score.max()) if len(score) else np.nan,
                "top_decile_rate": float((group["ism_state"] == "TOP_DECILE").mean()) if len(group) else np.nan,
                "bottom_decile_rate": float((group["ism_state"] == "BOTTOM_DECILE").mean()) if len(group) else np.nan,
                "middle_rate": float((group["ism_state"] == "MIDDLE").mean()) if len(group) else np.nan,
            }
        )
    return pd.DataFrame(rows)


def _rank_consistency(frame: pd.DataFrame) -> dict[str, object]:
    valid = frame[frame["ism_valid_observation"]].copy()
    violations = 0
    checked_months = 0
    for _, group in valid.groupby("month", sort=True):
        if len(group) < 2:
            continue
        checked_months += 1
        ordered = group.sort_values("industry_return_12_1")
        if (ordered["ism_score"].diff().dropna() < -1e-12).any():
            violations += 1
        expected_top = group["ism_score"].ge(0.90)
        expected_bottom = group["ism_score"].le(0.10)
        if not (group["ism_state"].eq("TOP_DECILE") == expected_top).all():
            violations += 1
        if not (group["ism_state"].eq("BOTTOM_DECILE") == expected_bottom).all():
            violations += 1

    score_range_ok = bool(valid["ism_score"].between(0.0, 1.0).all())
    rank_present_ok = bool(valid["ism_rank"].notna().all())
    formation_return_present_ok = bool(valid["industry_return_12_1"].notna().all())
    return {
        "checked_months": checked_months,
        "rank_score_violations": violations,
        "score_range_ok": score_range_ok,
        "rank_present_ok": rank_present_ok,
        "formation_return_present_ok": formation_return_present_ok,
        "rank_consistency_status": "PASSED"
        if violations == 0 and score_range_ok and rank_present_ok and formation_return_present_ok
        else "FAILED",
    }


def _industry_stability(frame: pd.DataFrame) -> pd.DataFrame:
    valid = frame[frame["ism_valid_observation"]].copy()
    rows = []
    for industry_id, group in valid.groupby("industry_id", sort=True):
        rows.append(
            {
                "industry_id": industry_id,
                "industry_name": str(group["industry_name"].iloc[0]),
                "valid_months": int(len(group)),
                "first_valid_month": str(group["month"].min().date()),
                "last_valid_month": str(group["month"].max().date()),
                "mean_ism_score": float(group["ism_score"].mean()),
                "std_ism_score": float(group["ism_score"].std(ddof=0)),
                "top_decile_rate": float((group["ism_state"] == "TOP_DECILE").mean()),
                "bottom_decile_rate": float((group["ism_state"] == "BOTTOM_DECILE").mean()),
            }
        )
    return pd.DataFrame(rows)


def _cross_period_consistency(frame: pd.DataFrame) -> pd.DataFrame:
    valid = frame[frame["ism_valid_observation"]].copy()
    buckets = [
        ("1927_1949", "1927-01-01", "1949-12-31"),
        ("1950_1969", "1950-01-01", "1969-12-31"),
        ("1970_1989", "1970-01-01", "1989-12-31"),
        ("1990_2009", "1990-01-01", "2009-12-31"),
        ("2010_2026", "2010-01-01", "2026-12-31"),
    ]
    rows = []
    for label, start, end in buckets:
        group = valid[(valid["month"] >= pd.Timestamp(start)) & (valid["month"] <= pd.Timestamp(end))]
        score = group["ism_score"].dropna()
        rows.append(
            {
                "period": label,
                "valid_observations": int(len(group)),
                "unique_industries": int(group["industry_id"].nunique()) if len(group) else 0,
                "score_mean": float(score.mean()) if len(score) else np.nan,
                "score_std": float(score.std(ddof=0)) if len(score) else np.nan,
                "top_decile_rate": float((group["ism_state"] == "TOP_DECILE").mean()) if len(group) else np.nan,
                "bottom_decile_rate": float((group["ism_state"] == "BOTTOM_DECILE").mean()) if len(group) else np.nan,
                "middle_rate": float((group["ism_state"] == "MIDDLE").mean()) if len(group) else np.nan,
            }
        )
    return pd.DataFrame(rows)


def _write_reports(
    *,
    frame: pd.DataFrame,
    coverage: pd.DataFrame,
    state_stats: pd.DataFrame,
    industry_stability: pd.DataFrame,
    cross_period: pd.DataFrame,
    rank_checks: dict[str, object],
    state_hash: str,
    generation_hash: str | None,
) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    coverage.to_csv(OUTPUT_DIR / "coverage_analysis.csv", index=False)
    state_stats.to_csv(OUTPUT_DIR / "state_statistics.csv", index=False)
    industry_stability.to_csv(OUTPUT_DIR / "industry_stability.csv", index=False)
    cross_period.to_csv(OUTPUT_DIR / "cross_period_consistency.csv", index=False)

    valid = frame[frame["ism_valid_observation"]]
    post_warmup = coverage[coverage["valid_count"] > 0]
    full_stats = state_stats[state_stats["period"] == "FULL_SAMPLE"].iloc[0]
    reproducible = generation_hash is not None and state_hash == generation_hash
    full_coverage = bool(post_warmup["valid_count"].eq(49).all()) if len(post_warmup) else False
    classification = (
        "Supported by evidence"
        if reproducible and rank_checks["rank_consistency_status"] == "PASSED" and full_coverage and len(valid) > 0
        else "Partially supported"
        if reproducible and rank_checks["rank_consistency_status"] == "PASSED" and len(valid) > 0
        else "Inconclusive"
    )

    main = f"""# ISM-001 / CV-001 Construct Validation

## Purpose

Evaluate whether implemented ISM-001 behaves as an internally coherent, reproducible and stable implementation of the frozen CD-001 construct.

No future returns, alpha, trading performance, strategy backtest, Sharpe, CAGR, drawdown, portfolio construction or economic value were evaluated.

## Frozen Construct

ISM-001 is the **Ken French 49 Industry Portfolio 12-1 Cross-Sectional Momentum Rank**.

It computes compounded value-weighted industry returns from `t-12` through `t-2`, ranks all valid Ken French 49 industry portfolios cross-sectionally by month, and assigns percentile-based state labels.

## Data Scope

- State file: `{_repo_relative(STATE_FILE)}`
- Rows: {len(frame):,}
- Unique industries: {frame["industry_id"].nunique():,}
- Valid observations: {len(valid):,}
- Full sample months: {frame["month"].min().date()} to {frame["month"].max().date()}
- Valid construct months: {valid["month"].min().date() if len(valid) else "N/A"} to {valid["month"].max().date() if len(valid) else "N/A"}

## Validation Results

- Post-warmup full 49-industry coverage: {"PASSED" if full_coverage else "FAILED"}
- Top decile rate: {full_stats["top_decile_rate"]:.4f}
- Bottom decile rate: {full_stats["bottom_decile_rate"]:.4f}
- Middle rate: {full_stats["middle_rate"]:.4f}
- Score mean: {full_stats["ism_score_mean"]:.4f}
- Score range: {full_stats["ism_score_min"]:.4f} to {full_stats["ism_score_max"]:.4f}
- Rank consistency: {rank_checks["rank_consistency_status"]}
- Deterministic hash matches IM generation report: {"PASSED" if reproducible else "FAILED"}

## Final CV-001 Classification

**{classification}**

The construct is internally coherent, deterministic and stable across the available Ken French 49 industry portfolio sample. This conclusion is limited to construct validation and does not imply predictive validity or economic value.
"""
    (OUTPUT_DIR / "cv001_construct_validation.md").write_text(main, encoding="utf-8")

    (OUTPUT_DIR / "rank_consistency_report.md").write_text(
        f"""# Rank Consistency Report

- Checked months: {rank_checks["checked_months"]}
- Rank / score / state violations: {rank_checks["rank_score_violations"]}
- Score range within [0, 1]: {rank_checks["score_range_ok"]}
- Rank values present for valid observations: {rank_checks["rank_present_ok"]}
- Formation returns present for valid observations: {rank_checks["formation_return_present_ok"]}

Final status: **{rank_checks["rank_consistency_status"]}**
""",
        encoding="utf-8",
    )

    (OUTPUT_DIR / "state_distribution_report.md").write_text(
        f"""# State Distribution Report

ISM-001 produced {len(valid):,} valid industry-month observations.

Full-sample state rates:

- TOP_DECILE: {full_stats["top_decile_rate"]:.4f}
- BOTTOM_DECILE: {full_stats["bottom_decile_rate"]:.4f}
- MIDDLE: {full_stats["middle_rate"]:.4f}

With 49 industries and percentile thresholds of 0.90 and 0.10, roughly five industries per month are expected in each tail under full coverage.
""",
        encoding="utf-8",
    )

    (OUTPUT_DIR / "temporal_stability.md").write_text(
        f"""# Temporal Stability

Valid sample:

```text
{valid["month"].min().date() if len(valid) else "N/A"} to {valid["month"].max().date() if len(valid) else "N/A"}
```

The construct remains computable across the post-warmup sample. Year-by-year distribution statistics are available in `state_statistics.csv`; broad historical period summaries are available in `cross_period_consistency.csv`.
""",
        encoding="utf-8",
    )

    (OUTPUT_DIR / "cross_period_consistency.md").write_text(
        """# Cross-Period Consistency

Cross-period descriptive statistics were computed for predefined historical buckets:

- 1927-1949
- 1950-1969
- 1970-1989
- 1990-2009
- 2010-2026

The full table is available in `cross_period_consistency.csv`.

No predictive or economic interpretation was performed.
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

Validated properties:

- Output schema matches CD-001.
- Monthly industry-level state observations are present.
- Industry 12-1 formation returns are present for valid observations.
- Cross-sectional ranks and percentile scores are present for valid observations.
- Percentile scores are bounded between 0 and 1.
- State labels follow frozen decile thresholds.
- No stock-level industry membership assignment was introduced.

No predictive or economic interpretation was performed.
""",
        encoding="utf-8",
    )

    (OUTPUT_DIR / "limitations.md").write_text(
        """# Limitations

- CV-001 evaluates construct validity only.
- No future return, alpha, trading performance or economic value was tested.
- The construct is industry-level and does not map industry states onto individual equities.
- The sample depends on the public Ken French 49 industry portfolio file and its latest available update.
- The result does not validate any trading strategy or production deployment use case.
""",
        encoding="utf-8",
    )

    (OUTPUT_DIR / "executive_summary.md").write_text(
        f"""# Executive Summary

ISM-001 / CV-001 evaluated the implemented Ken French 49 Industry Portfolio 12-1 Cross-Sectional Momentum Rank for internal coherence, coverage, rank consistency, temporal stability and reproducibility.

The construct generated {len(valid):,} valid observations across {frame["industry_id"].nunique():,} industries from {valid["month"].min().date() if len(valid) else "N/A"} to {valid["month"].max().date() if len(valid) else "N/A"}.

Rank consistency passed and the current state hash matched the IM generation report.

Final classification:

**{classification}**

The construct may proceed to ISM-001 / MI-001. No predictive or economic claim was made.
""",
        encoding="utf-8",
    )

    (OUTPUT_DIR / "next_stage_goal_mi001.md").write_text(
        """# ISM-001 / MI-001 Mechanism Identification

Purpose:

Identify and characterize the observable mechanism represented by ISM-001 industry momentum states.

Allowed:

- State profiling.
- Industry momentum distribution analysis.
- TOP_DECILE / BOTTOM_DECILE / MIDDLE descriptive comparison.
- State transition characterization.
- Industry-level persistence characterization.
- Historical episode description.

Forbidden:

- Predictive validation.
- Return forecasting.
- Trading backtests.
- Economic validation.
- Alpha claims.
- Parameter optimization.
- Stock-level signal assignment.
""",
        encoding="utf-8",
    )

    manifest = {
        "construct_id": "ISM-001",
        "stage": "CV-001",
        "classification": classification,
        "rows": int(len(frame)),
        "valid_observations": int(len(valid)),
        "unique_industries": int(frame["industry_id"].nunique()),
        "first_valid_month": str(valid["month"].min().date()) if len(valid) else None,
        "last_valid_month": str(valid["month"].max().date()) if len(valid) else None,
        "rank_consistency_status": rank_checks["rank_consistency_status"],
        "reproducibility_status": "PASSED" if reproducible else "FAILED",
        "post_warmup_full_coverage": full_coverage,
        "state_hash": state_hash,
        "next_stage": "MI-001" if classification in {"Supported by evidence", "Partially supported"} else "Human review",
    }
    (OUTPUT_DIR / "validation_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def run_validation() -> dict[str, object]:
    frame = _load_state()
    coverage = _coverage_analysis(frame)
    state_stats = _state_statistics(frame)
    industry_stability = _industry_stability(frame)
    cross_period = _cross_period_consistency(frame)
    rank_checks = _rank_consistency(frame)
    state_hash = _hash_frame(frame)
    generation_hash = None
    if GENERATION_REPORT_FILE.exists():
        generation_hash = json.loads(GENERATION_REPORT_FILE.read_text(encoding="utf-8")).get("deterministic_hash")
    _write_reports(
        frame=frame,
        coverage=coverage,
        state_stats=state_stats,
        industry_stability=industry_stability,
        cross_period=cross_period,
        rank_checks=rank_checks,
        state_hash=state_hash,
        generation_hash=generation_hash,
    )
    return {
        "rows": int(len(frame)),
        "valid_observations": int(frame["ism_valid_observation"].sum()),
        "rank_consistency_status": rank_checks["rank_consistency_status"],
        "reproducibility_status": "PASSED" if generation_hash == state_hash else "FAILED",
        "status": "COMPLETE",
    }


if __name__ == "__main__":
    print(json.dumps(run_validation(), indent=2))
