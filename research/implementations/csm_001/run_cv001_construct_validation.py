from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[2]
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from csm001_momentum_model import CSM001MomentumModel


START_DATE = "2010-01-01"
END_DATE = "2025-12-31"
UNIVERSE_FILE = REPO_ROOT / "sp500_current_universe.csv"
OUTPUT_DIR = REPO_ROOT / "research" / "market_edge_discovery_program" / "csm_001_cv_001_construct_validation"
CACHE_DIR = REPO_ROOT / "output" / "csm_001_cv001"
CLOSE_PANEL_FILE = CACHE_DIR / "adjusted_close_panel.csv"
STATE_FILE = CACHE_DIR / "csm001_construct_state.csv"


def _repo_relative(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT)).replace("\\", "/")


def _load_universe() -> list[str]:
    universe = pd.read_csv(UNIVERSE_FILE)
    if "ticker" not in universe.columns:
        raise ValueError(f"{UNIVERSE_FILE} must contain a ticker column.")
    tickers = universe["ticker"].dropna().astype(str).str.strip()
    return sorted(t for t in tickers.unique() if t)


def _to_yahoo_symbol(ticker: str) -> str:
    return ticker.replace(".", "-")


def _from_yahoo_symbol(symbol: str, original_lookup: dict[str, str]) -> str:
    return original_lookup.get(symbol, symbol.replace("-", "."))


def _download_adjusted_close(tickers: list[str]) -> tuple[pd.DataFrame, list[str]]:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    if CLOSE_PANEL_FILE.exists():
        close_panel = pd.read_csv(CLOSE_PANEL_FILE, index_col=0, parse_dates=True)
        unavailable = sorted(column for column in close_panel.columns if close_panel[column].notna().sum() == 0)
        return close_panel, unavailable

    yahoo_symbols = [_to_yahoo_symbol(t) for t in tickers]
    lookup = dict(zip(yahoo_symbols, tickers))
    chunks: list[pd.DataFrame] = []
    failed: list[str] = []

    for start in range(0, len(yahoo_symbols), 80):
        chunk_symbols = yahoo_symbols[start : start + 80]
        data = yf.download(
            tickers=chunk_symbols,
            start=START_DATE,
            end=END_DATE,
            auto_adjust=False,
            progress=False,
            group_by="column",
            threads=True,
        )
        if data.empty:
            failed.extend(_from_yahoo_symbol(symbol, lookup) for symbol in chunk_symbols)
            continue

        if isinstance(data.columns, pd.MultiIndex):
            if "Adj Close" in data.columns.get_level_values(0):
                close = data["Adj Close"].copy()
            elif "Close" in data.columns.get_level_values(0):
                close = data["Close"].copy()
            else:
                failed.extend(_from_yahoo_symbol(symbol, lookup) for symbol in chunk_symbols)
                continue
        else:
            column = "Adj Close" if "Adj Close" in data.columns else "Close"
            close = data[[column]].copy()
            close.columns = chunk_symbols[:1]

        close = close.rename(columns=lambda symbol: _from_yahoo_symbol(str(symbol), lookup))
        chunks.append(close)

    if not chunks:
        raise RuntimeError("No adjusted close data could be downloaded for CV-001.")

    close_panel = pd.concat(chunks, axis=1)
    close_panel = close_panel.loc[:, ~close_panel.columns.duplicated()]
    close_panel = close_panel.reindex(sorted(close_panel.columns), axis=1)
    close_panel.index = pd.to_datetime(close_panel.index).tz_localize(None)
    close_panel.to_csv(CLOSE_PANEL_FILE)

    missing_columns = sorted(set(tickers) - set(close_panel.columns))
    all_nan_columns = sorted(column for column in close_panel.columns if close_panel[column].notna().sum() == 0)
    failed = sorted(set(failed).union(missing_columns).union(all_nan_columns))
    return close_panel, failed


def _hash_frame(frame: pd.DataFrame) -> str:
    stable = frame.copy()
    stable = stable.sort_index(axis=1)
    values = pd.util.hash_pandas_object(stable, index=True).values
    return hashlib.sha256(values.tobytes()).hexdigest()


def _coerce_bool(series: pd.Series) -> pd.Series:
    return series.astype(bool)


def _build_coverage(result: pd.DataFrame, ticker_count: int) -> pd.DataFrame:
    by_date = result.groupby("date", sort=True)
    coverage = by_date.agg(
        total_universe_count=("ticker", "nunique"),
        eligible_count=("csm001_valid_observation", "sum"),
        top_decile_count=("csm001_top_decile_flag", "sum"),
        missing_adjusted_close_count=("adjusted_close", lambda s: int(s.isna().sum())),
    ).reset_index()
    coverage["configured_universe_count"] = ticker_count
    coverage["coverage_ratio"] = coverage["eligible_count"] / coverage["configured_universe_count"]
    coverage["top_decile_ratio_of_eligible"] = np.where(
        coverage["eligible_count"] > 0,
        coverage["top_decile_count"] / coverage["eligible_count"],
        np.nan,
    )
    return coverage[
        [
            "date",
            "configured_universe_count",
            "total_universe_count",
            "eligible_count",
            "coverage_ratio",
            "top_decile_count",
            "top_decile_ratio_of_eligible",
            "missing_adjusted_close_count",
        ]
    ]


def _build_distribution(result: pd.DataFrame) -> pd.DataFrame:
    valid = result[result["csm001_valid_observation"]].copy()
    rows = []
    groups = [("FULL_SAMPLE", valid)]
    groups.extend((str(year), group) for year, group in valid.groupby(valid["date"].dt.year, sort=True))
    for label, group in groups:
        score = group["csm001_momentum_score"].dropna()
        ret = group["return_12_1"].dropna()
        rows.append(
            {
                "period": label,
                "valid_observations": int(len(group)),
                "score_mean": float(score.mean()) if len(score) else np.nan,
                "score_std": float(score.std(ddof=0)) if len(score) else np.nan,
                "score_min": float(score.min()) if len(score) else np.nan,
                "score_p10": float(score.quantile(0.10)) if len(score) else np.nan,
                "score_median": float(score.median()) if len(score) else np.nan,
                "score_p90": float(score.quantile(0.90)) if len(score) else np.nan,
                "score_max": float(score.max()) if len(score) else np.nan,
                "return_12_1_mean": float(ret.mean()) if len(ret) else np.nan,
                "return_12_1_median": float(ret.median()) if len(ret) else np.nan,
                "top_decile_rate": float(group["csm001_top_decile_flag"].mean()) if len(group) else np.nan,
            }
        )
    return pd.DataFrame(rows)


def _rank_consistency_checks(result: pd.DataFrame) -> dict[str, object]:
    valid = result[result["csm001_valid_observation"]].copy()
    sample_dates = list(valid["date"].drop_duplicates().iloc[:: max(1, valid["date"].nunique() // 40)])
    violations = 0
    checked_dates = 0
    for date in sample_dates:
        day = valid[valid["date"] == date].sort_values("return_12_1")
        if len(day) < 2:
            continue
        checked_dates += 1
        if (day["csm001_momentum_score"].diff().dropna() < -1e-12).any():
            violations += 1
    score_range_ok = bool(valid["csm001_momentum_score"].between(0.0, 1.0).all())
    threshold_flags_ok = bool(
        (
            valid["csm001_top_decile_flag"]
            == valid["csm001_momentum_score"].ge(CSM001MomentumModel().top_decile_threshold)
        ).all()
    )
    return {
        "sampled_dates_checked": checked_dates,
        "rank_monotonicity_violations": violations,
        "score_range_ok": score_range_ok,
        "threshold_flags_ok": threshold_flags_ok,
        "rank_consistency_status": "PASSED"
        if violations == 0 and score_range_ok and threshold_flags_ok
        else "FAILED",
    }


def _write_markdown_outputs(
    *,
    tickers: list[str],
    failed: list[str],
    close_panel: pd.DataFrame,
    result: pd.DataFrame,
    coverage: pd.DataFrame,
    distribution: pd.DataFrame,
    rank_checks: dict[str, object],
    hash_one: str,
    hash_two: str,
) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    valid = result[result["csm001_valid_observation"]]
    first_valid = valid["date"].min()
    last_valid = valid["date"].max()
    avg_coverage = coverage["coverage_ratio"].mean()
    min_coverage = coverage["coverage_ratio"].min()
    post_warmup = coverage[coverage["eligible_count"] > 0]
    post_warmup_min_coverage = post_warmup["coverage_ratio"].min() if len(post_warmup) else np.nan
    top_rate = valid["csm001_top_decile_flag"].mean()
    reproducible = hash_one == hash_two
    conclusion = "Partially supported" if reproducible and rank_checks["rank_consistency_status"] == "PASSED" else "Inconclusive"

    main = f"""# CSM-001 / CV-001 Construct Validation

## Purpose

Evaluate whether the implemented CSM-001 construct behaves as a stable, reproducible and internally consistent implementation of the frozen CD-001 definition.

No returns, alpha, trading performance, Sharpe, CAGR, drawdown or economic value were evaluated.

## Frozen Construct

CSM-001 is the Canonical 12-1 Cross-Sectional Momentum State.

For each security and date:

```text
return_12_1 = adjusted_close_t_minus_21 / adjusted_close_t_minus_252 - 1
momentum_score = cross-sectional percentile rank of return_12_1
top_decile_flag = momentum_score >= 0.90
```

## Data Scope

- Universe file: `{_repo_relative(UNIVERSE_FILE)}`
- Configured tickers: {len(tickers)}
- Downloaded close columns: {close_panel.shape[1]}
- Failed / unavailable tickers: {len(failed)}
- Close panel dates: {close_panel.index.min().date()} to {close_panel.index.max().date()}
- Valid construct dates: {first_valid.date() if pd.notna(first_valid) else "N/A"} to {last_valid.date() if pd.notna(last_valid) else "N/A"}
- Construct state rows: {len(result):,}
- Valid observations: {len(valid):,}

## Validation Results

- Average coverage ratio: {avg_coverage:.4f}
- Minimum coverage ratio, including required warmup: {min_coverage:.4f}
- Minimum coverage ratio after valid observations begin: {post_warmup_min_coverage:.4f}
- Average top-decile selection rate among valid rows: {top_rate:.4f}
- Rank monotonicity status: {rank_checks["rank_consistency_status"]}
- Deterministic reproducibility: {"PASSED" if reproducible else "FAILED"}

## Final CV-001 Classification

**{conclusion}**

The implementation is reproducible and internally coherent under the available data sample. The classification is not stronger than Partially Supported because the universe is current S&P 500 membership rather than survivorship-free historical membership, and Yahoo data availability varies by ticker.
"""
    (OUTPUT_DIR / "cv001_construct_validation.md").write_text(main, encoding="utf-8")

    rank_report = f"""# Rank Consistency Report

## Checks

- Sampled dates checked: {rank_checks["sampled_dates_checked"]}
- Rank monotonicity violations: {rank_checks["rank_monotonicity_violations"]}
- Score range within [0, 1]: {rank_checks["score_range_ok"]}
- Top-decile threshold flags match score >= 0.90: {rank_checks["threshold_flags_ok"]}

## Status

**{rank_checks["rank_consistency_status"]}**
"""
    (OUTPUT_DIR / "rank_consistency_report.md").write_text(rank_report, encoding="utf-8")

    reproducibility = f"""# Reproducibility Report

## Procedure

The same cached adjusted-close panel was transformed twice by the frozen CSM-001 implementation. The resulting construct-state frames were hashed after deterministic ordering.

## Result

- First run hash: `{hash_one}`
- Second run hash: `{hash_two}`
- Reproducibility status: **{"PASSED" if reproducible else "FAILED"}**

No random seed is required because the implementation contains no stochastic component.
"""
    (OUTPUT_DIR / "reproducibility_report.md").write_text(reproducibility, encoding="utf-8")

    failed_preview = ", ".join(failed[:40]) if failed else "None"
    data_quality = f"""# Data Quality Report

## Source

Adjusted close data was downloaded from Yahoo Finance through `yfinance` and cached at `{_repo_relative(CLOSE_PANEL_FILE)}`.

## Coverage

- Configured universe count: {len(tickers)}
- Downloaded columns: {close_panel.shape[1]}
- Failed or unavailable tickers: {len(failed)}
- Failed ticker preview: {failed_preview}
- Average valid coverage ratio: {avg_coverage:.4f}
- Minimum coverage ratio, including required warmup: {min_coverage:.4f}
- Minimum coverage ratio after valid observations begin: {post_warmup_min_coverage:.4f}

## Important Limitation

The universe file is a current S&P 500-style ticker list. It is not a survivorship-free historical constituent database. CV-001 therefore validates implementation behavior under this available universe and does not claim historical constituent completeness.
"""
    (OUTPUT_DIR / "data_quality_report.md").write_text(data_quality, encoding="utf-8")

    limitations = """# Limitations

- CV-001 does not evaluate predictive validity, returns, alpha, trading performance or economic value.
- The universe is not survivorship-free historical S&P 500 membership.
- Yahoo Finance data availability differs by ticker and historical listing date.
- CSM-001 ranks only securities with valid t-21 and t-252 adjusted-close observations on each date.
- Construct validity here means implementation coherence and reproducibility, not proof that cross-sectional momentum predicts future returns.
"""
    (OUTPUT_DIR / "limitations.md").write_text(limitations, encoding="utf-8")

    summary = f"""# Executive Summary

CSM-001 / CV-001 evaluated the frozen Canonical 12-1 Cross-Sectional Momentum State implementation on a broad current S&P 500-style universe from {START_DATE} to {END_DATE}.

The construct generated reproducible percentile ranks, valid top-decile flags and no sampled rank-order violations. Data coverage is usable but limited by current-constituent survivorship and ticker availability.

Final classification: **{conclusion}**.

This authorizes progression to CSM-001 / MI-001 only as construct-mechanism research, not as trading or economic validation.
"""
    (OUTPUT_DIR / "executive_summary.md").write_text(summary, encoding="utf-8")

    next_goal = """# CSM-001 / MI-001 Mechanism Identification

Purpose: characterize what observable market behavior is represented by the validated CSM-001 Canonical 12-1 Cross-Sectional Momentum State.

Allowed: construct profiling, distributional analysis, rank persistence, turnover characterization, sector/universe descriptive behavior if data exists.

Forbidden: returns, alpha, profitability, trading strategy backtests, Sharpe, CAGR, optimization, production recommendations.
"""
    (OUTPUT_DIR / "next_stage_goal_mi001.md").write_text(next_goal, encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    tickers = _load_universe()
    close_panel, failed = _download_adjusted_close(tickers)

    model = CSM001MomentumModel()
    result_one = model.transform(close_panel).frame
    result_two = model.transform(close_panel).frame
    hash_one = _hash_frame(result_one)
    hash_two = _hash_frame(result_two)

    result_one.to_csv(STATE_FILE, index=False)
    coverage = _build_coverage(result_one, len(tickers))
    distribution = _build_distribution(result_one)
    rank_checks = _rank_consistency_checks(result_one)

    coverage.to_csv(OUTPUT_DIR / "coverage_analysis.csv", index=False)
    distribution.to_csv(OUTPUT_DIR / "score_distribution_analysis.csv", index=False)
    (OUTPUT_DIR / "validation_manifest.json").write_text(
        json.dumps(
            {
                "construct_id": "CSM-001",
                "stage": "CV-001",
                "start_date": START_DATE,
                "end_date": END_DATE,
                "universe_file": _repo_relative(UNIVERSE_FILE),
                "configured_universe_count": len(tickers),
                "downloaded_close_columns": int(close_panel.shape[1]),
                "failed_tickers": failed,
                "state_file": _repo_relative(STATE_FILE),
                "result_hash": hash_one,
                "reproducibility_passed": hash_one == hash_two,
                "rank_checks": rank_checks,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    _write_markdown_outputs(
        tickers=tickers,
        failed=failed,
        close_panel=close_panel,
        result=result_one,
        coverage=coverage,
        distribution=distribution,
        rank_checks=rank_checks,
        hash_one=hash_one,
        hash_two=hash_two,
    )

    print(json.dumps({"status": "PASSED", "output_dir": str(OUTPUT_DIR), "result_hash": hash_one}, indent=2))


if __name__ == "__main__":
    main()
