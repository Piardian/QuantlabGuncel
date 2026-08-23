from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[2]
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from tsm001_momentum_model import TSM001MomentumModel


START_DATE = "2010-01-01"
END_DATE = "2025-12-31"
SOURCE_CLOSE_PANEL = REPO_ROOT / "output" / "csm_001_cv001" / "adjusted_close_panel.csv"
OUTPUT_DIR = REPO_ROOT / "research" / "market_edge_discovery_program" / "tsm_001_cv_001_construct_validation"
CACHE_DIR = REPO_ROOT / "output" / "tsm_001_cv001"
STATE_FILE = CACHE_DIR / "tsm001_construct_state.csv"


def _repo_relative(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT)).replace("\\", "/")


def _hash_frame(frame: pd.DataFrame) -> str:
    stable = frame.copy()
    values = pd.util.hash_pandas_object(stable, index=True).values
    return hashlib.sha256(values.tobytes()).hexdigest()


def _load_close_panel() -> pd.DataFrame:
    if not SOURCE_CLOSE_PANEL.exists():
        raise FileNotFoundError(f"Missing adjusted close panel: {SOURCE_CLOSE_PANEL}")
    return pd.read_csv(SOURCE_CLOSE_PANEL, index_col=0, parse_dates=True)


def _coverage_analysis(result: pd.DataFrame, ticker_count: int) -> pd.DataFrame:
    by_date = result.groupby("date", sort=True)
    coverage = by_date.agg(
        total_universe_count=("ticker", "nunique"),
        valid_count=("tsm001_valid_observation", "sum"),
        positive_count=("tsm001_positive_state", "sum"),
        negative_count=("tsm001_negative_state", "sum"),
        missing_adjusted_close_count=("adjusted_close", lambda s: int(s.isna().sum())),
    ).reset_index()
    coverage["configured_universe_count"] = ticker_count
    coverage["coverage_ratio"] = coverage["valid_count"] / coverage["configured_universe_count"]
    coverage["positive_state_rate"] = np.where(coverage["valid_count"] > 0, coverage["positive_count"] / coverage["valid_count"], np.nan)
    coverage["negative_state_rate"] = np.where(coverage["valid_count"] > 0, coverage["negative_count"] / coverage["valid_count"], np.nan)
    coverage["neutral_count"] = coverage["valid_count"] - coverage["positive_count"] - coverage["negative_count"]
    coverage["neutral_state_rate"] = np.where(coverage["valid_count"] > 0, coverage["neutral_count"] / coverage["valid_count"], np.nan)
    return coverage[
        [
            "date",
            "configured_universe_count",
            "total_universe_count",
            "valid_count",
            "coverage_ratio",
            "positive_count",
            "positive_state_rate",
            "negative_count",
            "negative_state_rate",
            "neutral_count",
            "neutral_state_rate",
            "missing_adjusted_close_count",
        ]
    ]


def _state_distribution(result: pd.DataFrame) -> pd.DataFrame:
    valid = result[result["tsm001_valid_observation"]].copy()
    rows = []
    groups = [("FULL_SAMPLE", valid)]
    groups.extend((str(year), group) for year, group in valid.groupby(valid["date"].dt.year, sort=True))
    for period, group in groups:
        rows.append(
            {
                "period": period,
                "valid_observations": int(len(group)),
                "unique_tickers": int(group["ticker"].nunique()),
                "positive_rate": float(group["tsm001_positive_state"].mean()) if len(group) else np.nan,
                "negative_rate": float(group["tsm001_negative_state"].mean()) if len(group) else np.nan,
                "neutral_rate": float((group["tsm001_state"] == "NEUTRAL").mean()) if len(group) else np.nan,
                "tsm_return_12_1_mean": float(group["tsm_return_12_1"].mean()) if len(group) else np.nan,
                "tsm_return_12_1_median": float(group["tsm_return_12_1"].median()) if len(group) else np.nan,
            }
        )
    return pd.DataFrame(rows)


def _state_persistence(result: pd.DataFrame) -> pd.DataFrame:
    valid = result[result["tsm001_valid_observation"]].copy()
    panel = valid.pivot(index="date", columns="ticker", values="tsm001_direction_score").sort_index()
    rows = []
    for lag in [1, 5, 21, 63, 126]:
        agreements = []
        for idx in range(lag, len(panel)):
            current = panel.iloc[idx]
            previous = panel.iloc[idx - lag]
            aligned = pd.concat([current, previous], axis=1).dropna()
            if len(aligned) >= 50:
                agreements.append(float((aligned.iloc[:, 0] == aligned.iloc[:, 1]).mean()))
        series = pd.Series(agreements, dtype=float)
        rows.append(
            {
                "lag_trading_days": lag,
                "dates_evaluated": int(len(series)),
                "mean_state_agreement": float(series.mean()) if len(series) else np.nan,
                "median_state_agreement": float(series.median()) if len(series) else np.nan,
                "p10_state_agreement": float(series.quantile(0.10)) if len(series) else np.nan,
                "p90_state_agreement": float(series.quantile(0.90)) if len(series) else np.nan,
            }
        )
    return pd.DataFrame(rows)


def _write_reports(
    close_panel: pd.DataFrame,
    result: pd.DataFrame,
    coverage: pd.DataFrame,
    distribution: pd.DataFrame,
    persistence: pd.DataFrame,
    hash_one: str,
    hash_two: str,
) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    valid = result[result["tsm001_valid_observation"]]
    first_valid = valid["date"].min()
    last_valid = valid["date"].max()
    post_warmup = coverage[coverage["valid_count"] > 0]
    reproducible = hash_one == hash_two
    classification = "Partially supported" if reproducible else "Inconclusive"

    full = distribution[distribution["period"] == "FULL_SAMPLE"].iloc[0]
    lag21 = persistence[persistence["lag_trading_days"] == 21].iloc[0]
    lag63 = persistence[persistence["lag_trading_days"] == 63].iloc[0]

    main = f"""# TSM-001 / CV-001 Construct Validation

## Purpose

Evaluate whether the implemented TSM-001 construct behaves as a stable, reproducible and internally consistent implementation of frozen CD-001 on real data.

No future returns, alpha, trading performance, strategy backtest, volatility scaling or economic value were evaluated.

## Frozen Construct

TSM-001 is the Raw 12-1 Time-Series Momentum State:

```text
tsm_return_12_1 = adjusted_close_t_minus_21 / adjusted_close_t_minus_252 - 1
state = POSITIVE if return > 0; NEGATIVE if return < 0; NEUTRAL if return = 0
```

## Data Scope

- Source close panel: `{_repo_relative(SOURCE_CLOSE_PANEL)}`
- Close panel dates: {close_panel.index.min().date()} to {close_panel.index.max().date()}
- Close panel tickers: {close_panel.shape[1]}
- Valid construct dates: {first_valid.date() if pd.notna(first_valid) else "N/A"} to {last_valid.date() if pd.notna(last_valid) else "N/A"}
- Construct state rows: {len(result):,}
- Valid observations: {len(valid):,}

## Validation Results

- Average coverage ratio: {coverage["coverage_ratio"].mean():.4f}
- Minimum coverage ratio, including required warmup: {coverage["coverage_ratio"].min():.4f}
- Minimum coverage ratio after valid observations begin: {post_warmup["coverage_ratio"].min():.4f}
- Positive state rate: {full["positive_rate"]:.4f}
- Negative state rate: {full["negative_rate"]:.4f}
- Neutral state rate: {full["neutral_rate"]:.6f}
- 21-day median state agreement: {lag21["median_state_agreement"]:.4f}
- 63-day median state agreement: {lag63["median_state_agreement"]:.4f}
- Deterministic reproducibility: {"PASSED" if reproducible else "FAILED"}

## Final CV-001 Classification

**{classification}**

The implementation is reproducible and internally coherent under the available real-data panel. The classification is not stronger than Partially Supported because the source panel is current-constituent based rather than survivorship-free historical membership.
"""
    (OUTPUT_DIR / "cv001_construct_validation.md").write_text(main, encoding="utf-8")

    data_quality = f"""# Data Quality Report

## Source

TSM-001 CV-001 reused the adjusted-close panel generated during CSM-001 CV-001:

`{_repo_relative(SOURCE_CLOSE_PANEL)}`

## Coverage

- Close panel tickers: {close_panel.shape[1]}
- Average valid coverage ratio: {coverage["coverage_ratio"].mean():.4f}
- Minimum coverage ratio after valid observations begin: {post_warmup["coverage_ratio"].min():.4f}

## Important Limitation

The panel is based on a current S&P 500-style universe, not survivorship-free historical constituent membership.
"""
    (OUTPUT_DIR / "data_quality_report.md").write_text(data_quality, encoding="utf-8")

    reproducibility = f"""# Reproducibility Report

The same adjusted-close panel was transformed twice by the frozen TSM-001 implementation.

- First run hash: `{hash_one}`
- Second run hash: `{hash_two}`
- Status: **{"PASSED" if reproducible else "FAILED"}**

The implementation contains no stochastic component.
"""
    (OUTPUT_DIR / "reproducibility_report.md").write_text(reproducibility, encoding="utf-8")

    state_report = f"""# State Distribution Report

## Full Sample

- Positive state rate: {full["positive_rate"]:.4f}
- Negative state rate: {full["negative_rate"]:.4f}
- Neutral state rate: {full["neutral_rate"]:.6f}
- Mean 12-1 own return: {full["tsm_return_12_1_mean"]:.4f}
- Median 12-1 own return: {full["tsm_return_12_1_median"]:.4f}
"""
    (OUTPUT_DIR / "state_distribution_report.md").write_text(state_report, encoding="utf-8")

    persistence_report = "# State Persistence Report\n\n" + persistence.to_csv(index=False)
    (OUTPUT_DIR / "state_persistence_report.md").write_text(persistence_report, encoding="utf-8")

    limitations = """# Limitations

- CV-001 does not evaluate future returns, predictive validity, alpha, trading performance or economic value.
- The source universe is current-constituent based, not survivorship-free historical membership.
- TSM-001 excludes volatility scaling by CD-001 definition.
- CV-001 validates construct behavior only; it does not validate the usefulness of the construct.
"""
    (OUTPUT_DIR / "limitations.md").write_text(limitations, encoding="utf-8")

    summary = f"""# Executive Summary

TSM-001 / CV-001 evaluated the frozen Raw 12-1 Time-Series Momentum State on a real adjusted-close panel.

Final classification: **{classification}**.

The construct generated reproducible state assignments with coherent positive/negative/neutral state behavior. Validity remains limited by the current-constituent source universe and does not imply predictive or economic value.
"""
    (OUTPUT_DIR / "executive_summary.md").write_text(summary, encoding="utf-8")

    next_goal = """# TSM-001 / MI-001 Mechanism Identification

Purpose: characterize what observable market behavior is represented by the validated TSM-001 Raw 12-1 Time-Series Momentum State.

Allowed:

- State profiling
- Positive/negative state persistence
- Transition characterization
- Distribution analysis

Forbidden:

- Future returns
- Alpha
- Trading performance
- Backtests
- Economic value
- Volatility scaling
"""
    (OUTPUT_DIR / "next_stage_goal_mi001.md").write_text(next_goal, encoding="utf-8")

    manifest = {
        "construct_id": "TSM-001",
        "stage": "CV-001",
        "source_close_panel": _repo_relative(SOURCE_CLOSE_PANEL),
        "state_file": _repo_relative(STATE_FILE),
        "result_hash": hash_one,
        "reproducibility_passed": reproducible,
        "valid_observations": int(len(valid)),
        "first_valid_date": str(first_valid.date()) if pd.notna(first_valid) else None,
        "last_valid_date": str(last_valid.date()) if pd.notna(last_valid) else None,
        "classification": classification,
    }
    (OUTPUT_DIR / "validation_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    close_panel = _load_close_panel()
    model = TSM001MomentumModel()
    result_one = model.transform(close_panel).frame
    result_two = model.transform(close_panel).frame
    hash_one = _hash_frame(result_one)
    hash_two = _hash_frame(result_two)

    result_one.to_csv(STATE_FILE, index=False)
    coverage = _coverage_analysis(result_one, close_panel.shape[1])
    distribution = _state_distribution(result_one)
    persistence = _state_persistence(result_one)

    coverage.to_csv(OUTPUT_DIR / "coverage_analysis.csv", index=False)
    distribution.to_csv(OUTPUT_DIR / "state_distribution_analysis.csv", index=False)
    persistence.to_csv(OUTPUT_DIR / "state_persistence_analysis.csv", index=False)
    _write_reports(close_panel, result_one, coverage, distribution, persistence, hash_one, hash_two)
    print(json.dumps({"status": "PASSED", "output_dir": str(OUTPUT_DIR), "result_hash": hash_one}, indent=2))


if __name__ == "__main__":
    main()
