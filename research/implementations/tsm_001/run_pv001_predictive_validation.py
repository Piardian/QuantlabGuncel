from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[3]
STATE_FILE = REPO_ROOT / "output" / "tsm_001_cv001" / "tsm001_construct_state.csv"
OUTPUT_DIR = REPO_ROOT / "research" / "market_edge_discovery_program" / "tsm_001_pv_001_predictive_validation"
HORIZONS = [21, 63, 126]


def _repo_relative(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT)).replace("\\", "/")


def _load_state() -> pd.DataFrame:
    if not STATE_FILE.exists():
        raise FileNotFoundError(f"Missing TSM-001 state file: {STATE_FILE}")
    frame = pd.read_csv(STATE_FILE, parse_dates=["date"], low_memory=False)
    frame = frame[frame["tsm001_valid_observation"].astype(bool)].copy()
    frame = frame.sort_values(["ticker", "date"]).reset_index(drop=True)
    frame["year"] = frame["date"].dt.year
    return frame


def _add_future_outcomes(frame: pd.DataFrame) -> pd.DataFrame:
    pieces = []
    for _, group in frame.groupby("ticker", sort=True):
        group = group.sort_values("date").copy()
        close = group["adjusted_close"].astype(float)
        log_ret_1d = np.log(close / close.shift(1))
        for horizon in HORIZONS:
            future_close = close.shift(-horizon)
            group[f"future_return_{horizon}d"] = (future_close / close) - 1.0
            group[f"future_realized_vol_{horizon}d"] = (
                log_ret_1d.shift(-1).rolling(horizon, min_periods=horizon).std().shift(-(horizon - 1)) * np.sqrt(252)
            )
            future_lows = pd.concat([close.shift(-step) for step in range(1, horizon + 1)], axis=1).min(axis=1)
            group[f"future_max_drawdown_{horizon}d"] = (future_lows / close) - 1.0
        pieces.append(group)
    return pd.concat(pieces, ignore_index=True)


def _mean_diff_ci(a: pd.Series, b: pd.Series) -> tuple[float, float]:
    x = a.dropna().to_numpy(dtype=float)
    y = b.dropna().to_numpy(dtype=float)
    if len(x) == 0 or len(y) == 0:
        return np.nan, np.nan
    diff = x.mean() - y.mean()
    se = np.sqrt((x.var(ddof=1) / len(x)) + (y.var(ddof=1) / len(y)))
    return float(diff - 1.96 * se), float(diff + 1.96 * se)


def _spearman_corr(left: pd.Series, right: pd.Series) -> float:
    pair = pd.concat([left, right], axis=1).dropna()
    if len(pair) < 2:
        return np.nan
    ranks = pair.rank(method="average")
    return float(ranks.iloc[:, 0].corr(ranks.iloc[:, 1], method="pearson"))


def _state_outcome_summary(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for horizon in HORIZONS:
        for state, group in frame.groupby("tsm001_state", sort=True):
            if state not in {"POSITIVE", "NEGATIVE"}:
                continue
            ret = group[f"future_return_{horizon}d"].dropna()
            vol = group[f"future_realized_vol_{horizon}d"].dropna()
            dd = group[f"future_max_drawdown_{horizon}d"].dropna()
            rows.append(
                {
                    "horizon_days": horizon,
                    "state": state,
                    "return_observations": int(len(ret)),
                    "mean_future_return": float(ret.mean()) if len(ret) else np.nan,
                    "median_future_return": float(ret.median()) if len(ret) else np.nan,
                    "win_rate_future_return": float((ret > 0).mean()) if len(ret) else np.nan,
                    "vol_observations": int(len(vol)),
                    "mean_future_realized_vol": float(vol.mean()) if len(vol) else np.nan,
                    "median_future_realized_vol": float(vol.median()) if len(vol) else np.nan,
                    "drawdown_observations": int(len(dd)),
                    "mean_future_max_drawdown": float(dd.mean()) if len(dd) else np.nan,
                    "median_future_max_drawdown": float(dd.median()) if len(dd) else np.nan,
                }
            )
    return pd.DataFrame(rows)


def _predictive_metrics(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for horizon in HORIZONS:
        pos = frame[frame["tsm001_state"] == "POSITIVE"]
        neg = frame[frame["tsm001_state"] == "NEGATIVE"]
        ret_pos = pos[f"future_return_{horizon}d"]
        ret_neg = neg[f"future_return_{horizon}d"]
        vol_pos = pos[f"future_realized_vol_{horizon}d"]
        vol_neg = neg[f"future_realized_vol_{horizon}d"]
        dd_pos = pos[f"future_max_drawdown_{horizon}d"]
        dd_neg = neg[f"future_max_drawdown_{horizon}d"]

        ret_diff = ret_pos.mean() - ret_neg.mean()
        vol_diff = vol_pos.mean() - vol_neg.mean()
        dd_diff = dd_pos.mean() - dd_neg.mean()
        ret_ci = _mean_diff_ci(ret_pos, ret_neg)
        vol_ci = _mean_diff_ci(vol_pos, vol_neg)
        dd_ci = _mean_diff_ci(dd_pos, dd_neg)

        valid = frame[[f"future_return_{horizon}d", f"future_realized_vol_{horizon}d", f"future_max_drawdown_{horizon}d", "tsm001_direction_score"]].dropna()
        rows.append(
            {
                "horizon_days": horizon,
                "observations": int(len(valid)),
                "mean_return_positive_minus_negative": float(ret_diff),
                "return_diff_ci95_low": ret_ci[0],
                "return_diff_ci95_high": ret_ci[1],
                "mean_vol_positive_minus_negative": float(vol_diff),
                "vol_diff_ci95_low": vol_ci[0],
                "vol_diff_ci95_high": vol_ci[1],
                "mean_drawdown_positive_minus_negative": float(dd_diff),
                "drawdown_diff_ci95_low": dd_ci[0],
                "drawdown_diff_ci95_high": dd_ci[1],
                "pearson_state_future_return": float(valid["tsm001_direction_score"].corr(valid[f"future_return_{horizon}d"], method="pearson")),
                "spearman_state_future_return": _spearman_corr(valid["tsm001_direction_score"], valid[f"future_return_{horizon}d"]),
                "pearson_state_future_vol": float(valid["tsm001_direction_score"].corr(valid[f"future_realized_vol_{horizon}d"], method="pearson")),
                "spearman_state_future_vol": _spearman_corr(valid["tsm001_direction_score"], valid[f"future_realized_vol_{horizon}d"]),
                "pearson_state_future_drawdown": float(valid["tsm001_direction_score"].corr(valid[f"future_max_drawdown_{horizon}d"], method="pearson")),
                "spearman_state_future_drawdown": _spearman_corr(valid["tsm001_direction_score"], valid[f"future_max_drawdown_{horizon}d"]),
            }
        )
    metrics = pd.DataFrame(rows)
    metrics["return_classification"] = np.where(
        (metrics["return_diff_ci95_low"] > 0) & (metrics["mean_return_positive_minus_negative"] > 0),
        "Supported by evidence",
        "Not supported",
    )
    metrics["volatility_classification"] = np.where(
        metrics["vol_diff_ci95_high"] < 0,
        "Supported by evidence",
        np.where(metrics["vol_diff_ci95_low"] < 0, "Partially supported", "Not supported"),
    )
    metrics["drawdown_classification"] = np.where(
        metrics["drawdown_diff_ci95_low"] > 0,
        "Supported by evidence",
        np.where(metrics["drawdown_diff_ci95_high"] > 0, "Partially supported", "Not supported"),
    )
    return metrics


def _yearly_validation(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for horizon in HORIZONS:
        for year, group in frame.groupby("year", sort=True):
            pos = group[group["tsm001_state"] == "POSITIVE"][f"future_return_{horizon}d"].dropna()
            neg = group[group["tsm001_state"] == "NEGATIVE"][f"future_return_{horizon}d"].dropna()
            pos_vol = group[group["tsm001_state"] == "POSITIVE"][f"future_realized_vol_{horizon}d"].dropna()
            neg_vol = group[group["tsm001_state"] == "NEGATIVE"][f"future_realized_vol_{horizon}d"].dropna()
            pos_dd = group[group["tsm001_state"] == "POSITIVE"][f"future_max_drawdown_{horizon}d"].dropna()
            neg_dd = group[group["tsm001_state"] == "NEGATIVE"][f"future_max_drawdown_{horizon}d"].dropna()
            rows.append(
                {
                    "year": int(year),
                    "horizon_days": horizon,
                    "positive_count": int(len(pos)),
                    "negative_count": int(len(neg)),
                    "return_positive_minus_negative": float(pos.mean() - neg.mean()) if len(pos) and len(neg) else np.nan,
                    "vol_positive_minus_negative": float(pos_vol.mean() - neg_vol.mean()) if len(pos_vol) and len(neg_vol) else np.nan,
                    "drawdown_positive_minus_negative": float(pos_dd.mean() - neg_dd.mean()) if len(pos_dd) and len(neg_dd) else np.nan,
                }
            )
    return pd.DataFrame(rows)


def _write_markdown(name: str, content: str) -> None:
    (OUTPUT_DIR / name).write_text(content.strip() + "\n", encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    frame = _add_future_outcomes(_load_state())
    metrics = _predictive_metrics(frame)
    state_summary = _state_outcome_summary(frame)
    yearly = _yearly_validation(frame)

    metrics.to_csv(OUTPUT_DIR / "predictive_metrics.csv", index=False)
    state_summary.to_csv(OUTPUT_DIR / "state_outcome_summary.csv", index=False)
    yearly.to_csv(OUTPUT_DIR / "cross_period_validation.csv", index=False)

    return_supported = int((metrics["return_classification"] == "Supported by evidence").sum())
    vol_supported = int((metrics["volatility_classification"] == "Supported by evidence").sum())
    dd_supported = int((metrics["drawdown_classification"] == "Supported by evidence").sum())
    if return_supported >= 2 and (vol_supported + dd_supported) >= 1:
        overall = "Supported by evidence"
    elif return_supported >= 1 or vol_supported >= 1 or dd_supported >= 1:
        overall = "Partially supported"
    else:
        overall = "Not supported"

    manifest = {
        "construct_id": "TSM-001",
        "stage": "PV-001",
        "source_state_file": _repo_relative(STATE_FILE),
        "horizons": HORIZONS,
        "observations": int(len(frame)),
        "unique_tickers": int(frame["ticker"].nunique()),
        "first_date": frame["date"].min().strftime("%Y-%m-%d"),
        "last_date": frame["date"].max().strftime("%Y-%m-%d"),
        "return_supported_horizons": return_supported,
        "volatility_supported_horizons": vol_supported,
        "drawdown_supported_horizons": dd_supported,
        "overall_conclusion": overall,
    }
    (OUTPUT_DIR / "pv001_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    lines = []
    for _, row in metrics.iterrows():
        lines.append(
            f"- {int(row['horizon_days'])}d: return {row['return_classification']}, "
            f"volatility {row['volatility_classification']}, drawdown {row['drawdown_classification']}; "
            f"return diff {row['mean_return_positive_minus_negative']:.6f}, "
            f"vol diff {row['mean_vol_positive_minus_negative']:.6f}, "
            f"drawdown diff {row['mean_drawdown_positive_minus_negative']:.6f}"
        )

    _write_markdown(
        "pv001_predictive_validation.md",
        f"""
# TSM-001 / PV-001 Predictive Validation

## Purpose

Evaluate whether the validated TSM-001 raw 12-1 time-series momentum construct contains statistical predictive information about predefined future own-asset outcomes.

This is predictive validation only. It is not a trading strategy backtest, not economic validation, and not a production recommendation.

## Preregistered Forecast Horizons

- 21 trading days
- 63 trading days
- 126 trading days

## Preregistered Outcomes

- Future own-asset adjusted-close return
- Future own-asset realized volatility
- Future own-asset max drawdown over the horizon

## Evidence Base

- Source state file: `{_repo_relative(STATE_FILE)}`
- Observations: {len(frame):,}
- Unique tickers: {frame['ticker'].nunique():,}
- Date range: {frame['date'].min().date()} to {frame['date'].max().date()}

## Results By Horizon

{chr(10).join(lines)}

## Overall PV-001 Classification

**{overall}**

The conclusion is limited to statistical predictive information in the evaluated current-constituent universe and predefined horizons. No economic utility, portfolio value, alpha or trading profitability is inferred.
""",
    )
    _write_markdown(
        "forecast_horizon_analysis.md",
        """
# Forecast Horizon Analysis

PV-001 evaluates 21, 63 and 126 trading-day horizons. The horizon-level metrics are stored in `predictive_metrics.csv`.
""",
    )
    _write_markdown(
        "baseline_comparison.md",
        """
# Baseline Comparison

The predefined baseline is the NEGATIVE TSM-001 state for state-conditional comparisons. POSITIVE-minus-NEGATIVE differences are reported for future return, realized volatility and max drawdown.

No trading benchmark, buy-and-hold benchmark or portfolio benchmark was evaluated.
""",
    )
    _write_markdown(
        "confidence_interval_report.md",
        """
# Confidence Interval Report

Deterministic normal-approximation confidence intervals were calculated for POSITIVE-minus-NEGATIVE mean differences by horizon and outcome.

These intervals describe sampling uncertainty for predictive validation only.
""",
    )
    _write_markdown(
        "effect_size_analysis.md",
        """
# Effect Size Analysis

Effect size is represented by POSITIVE-minus-NEGATIVE differences and state-outcome correlations. These are statistical association measures, not economic value estimates.
""",
    )
    _write_markdown(
        "cross_period_validation.md",
        """
# Cross-Period Validation

Year-by-year POSITIVE-minus-NEGATIVE outcome differences are stored in `cross_period_validation.csv`.

This file is intended to identify whether predictive evidence is broad-based or concentrated in specific periods.
""",
    )
    _write_markdown(
        "calibration_analysis.md",
        """
# Calibration Analysis

TSM-001 is a discrete signed-state construct rather than a calibrated probability model. Calibration analysis is therefore limited to state-conditional realized outcome distributions.
""",
    )
    _write_markdown(
        "limitations.md",
        """
# Limitations

- The source panel is current-constituent based and not survivorship-free.
- Future outcomes are statistical validation targets, not trading strategy results.
- Overlapping forward horizons create dependent observations.
- No transaction costs, position sizing, capital constraints or execution assumptions were evaluated.
- No volatility scaling was added to TSM-001.
""",
    )
    _write_markdown(
        "executive_summary.md",
        f"""
# Executive Summary

TSM-001 / PV-001 is complete.

Overall conclusion: **{overall}**

The validated raw 12-1 own-trend state was evaluated against future own-asset returns, realized volatility and drawdown risk over 21, 63 and 126 trading-day horizons.

No economic or trading-performance conclusions were made.
""",
    )
    _write_markdown(
        "next_stage_goal_ev001.md",
        """
# TSM-001 / EV-001 Economic Validation

Purpose: evaluate whether the statistically validated predictive information from TSM-001 provides measurable economic utility in predefined workflows.

Potential use cases must be preregistered before execution.

Forbidden:

- Post-hoc parameter tuning
- Construct modification
- Strategy redesign
- Unsupported alpha claims
""",
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
