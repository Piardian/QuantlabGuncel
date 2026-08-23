"""RC-C1 observational attribution audit for the frozen production trade population."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

ENTRY_FEATURES = [
    "rs20", "rs60", "rs120", "leadership_quality", "distance_above_ema200",
    "ema200_slope", "distance_above_ema50", "ema50_slope", "atr_expansion_magnitude",
    "breakout_distance", "entry_atr", "entry_price", "initial_risk", "position_size",
    "atr_percent", "daily_range_percent", "relative_volume", "spy_trend", "spy_return60",
]
MIN_SEGMENT_TRADES = 20


def main() -> None:
    args = _args()
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    trades = pd.read_csv(args.trades, parse_dates=["entry_time", "exit_time"])
    _require_columns(trades)
    trades = _prepare(trades)

    summary = _feature_summary(trades)
    summary.to_csv(output / "entry_feature_summary.csv", index=False)
    correlations = _associations(trades, "pooled")
    correlations.to_csv(output / "entry_feature_correlations.csv", index=False)
    yearly = _segmented_associations(trades, "year")
    yearly.to_csv(output / "entry_feature_yearly.csv", index=False)
    symbols = _segmented_associations(trades, "ticker")
    symbols.to_csv(output / "entry_feature_symbol.csv", index=False)

    lifecycle = _lifecycle_summary(trades)
    lifecycle.to_csv(output / "trade_lifecycle_summary.csv", index=False)
    _lifecycle_segmented(trades, "year").to_csv(output / "trade_lifecycle_yearly.csv", index=False)
    _lifecycle_segmented(trades, "ticker").to_csv(output / "trade_lifecycle_symbol.csv", index=False)

    association_summary = _association_summary(correlations, yearly, symbols, trades)
    (output / "association_summary.json").write_text(json.dumps(association_summary, indent=2), encoding="utf-8")
    _report(output / "core_signal_attribution_audit.md", association_summary, summary, correlations, lifecycle)


def _prepare(trades: pd.DataFrame) -> pd.DataFrame:
    trades = trades.copy()
    trades["year"] = trades["entry_time"].dt.year
    trades["win"] = (pd.to_numeric(trades["R_multiple"], errors="coerce") > 0).astype(int)
    trades["leadership_quality"] = ((trades["rs20"] > 0) | (trades["rs120"] > 0.10)).astype(int)
    trades["atr_expansion_magnitude"] = trades["true_range"] / trades["atr14"]
    return trades


def _feature_summary(trades: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for feature in ENTRY_FEATURES:
        values = pd.to_numeric(trades[feature], errors="coerce").dropna()
        rows.append({
            "feature": feature, "trade_count": len(values), "missing_pct": (1 - len(values) / len(trades)) * 100,
            "mean": values.mean(), "median": values.median(), "std": values.std(),
            "q1": values.quantile(.25), "q3": values.quantile(.75), "min": values.min(), "max": values.max(),
        })
    return pd.DataFrame(rows)


def _associations(trades: pd.DataFrame, population: str) -> pd.DataFrame:
    rows = []
    for feature in ENTRY_FEATURES:
        frame = trades[[feature, "R_multiple", "win"]].apply(pd.to_numeric, errors="coerce").dropna()
        has_variation = frame[feature].nunique() > 1
        correlation_r = frame[feature].corr(frame["R_multiple"]) if has_variation else np.nan
        correlation_win = frame[feature].corr(frame["win"]) if has_variation else np.nan
        rows.append({
            "population": population, "feature": feature, "trade_count": len(frame),
            "feature_has_variation": has_variation,
            "correlation_with_R": correlation_r, "correlation_with_win": correlation_win,
            "effect_direction_R": _direction(correlation_r), "association_strength_R": _strength(correlation_r),
            "effect_direction_win": _direction(correlation_win), "association_strength_win": _strength(correlation_win),
        })
    return pd.DataFrame(rows)


def _segmented_associations(trades: pd.DataFrame, dimension: str) -> pd.DataFrame:
    rows = []
    for segment, group in trades.groupby(dimension):
        if len(group) < MIN_SEGMENT_TRADES:
            continue
        result = _associations(group, str(segment))
        result.insert(0, dimension, segment)
        rows.append(result)
    return pd.concat(rows, ignore_index=True) if rows else _associations(trades.iloc[0:0], "NO_SEGMENTS").iloc[0:0]


def _lifecycle_summary(trades: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for population, group in [("ALL_TRADES", trades), ("WIN", trades[trades.win == 1]), ("NON_WIN", trades[trades.win == 0])]:
        rows.append(_lifecycle_row(population, group))
    for exit_reason, group in trades.groupby("exit_reason", dropna=False):
        rows.append(_lifecycle_row(f"EXIT_REASON:{exit_reason}", group))
    return pd.DataFrame(rows)


def _lifecycle_segmented(trades: pd.DataFrame, dimension: str) -> pd.DataFrame:
    rows = []
    for segment, group in trades.groupby(dimension):
        if len(group) >= MIN_SEGMENT_TRADES:
            row = _lifecycle_row(str(segment), group)
            row[dimension] = segment
            rows.append(row)
    return pd.DataFrame(rows)


def _lifecycle_row(population: str, trades: pd.DataFrame) -> dict:
    r = pd.to_numeric(trades["R_multiple"], errors="coerce")
    return {
        "population": population, "trade_count": len(trades), "avg_R": r.mean(), "median_R": r.median(),
        "win_rate": (r > 0).mean() * 100, "avg_pnl_dollars": pd.to_numeric(trades["pnl_dollars"], errors="coerce").mean(),
        "average_holding_days": pd.to_numeric(trades["holding_days"], errors="coerce").mean(),
        "median_holding_days": pd.to_numeric(trades["holding_days"], errors="coerce").median(),
        "average_mae": pd.to_numeric(trades["mae"], errors="coerce").mean(),
        "average_mfe": pd.to_numeric(trades["mfe"], errors="coerce").mean(),
    }


def _association_summary(pooled, yearly, symbols, trades):
    features = []
    for row in pooled.itertuples(index=False):
        yearly_values = yearly.loc[yearly.feature == row.feature, "correlation_with_R"].dropna()
        symbol_values = symbols.loc[symbols.feature == row.feature, "correlation_with_R"].dropna()
        strength = row.association_strength_R
        stability = "NO_MEANINGFUL_ASSOCIATION" if strength == "NONE" else _stability(yearly_values, symbol_values)
        features.append({
            "feature": row.feature, "pooled_correlation_with_R": row.correlation_with_R,
            "pooled_correlation_with_win": row.correlation_with_win,
            "pooled_direction_R": row.effect_direction_R,
            "pooled_strength_R": strength,
            "positive_year_fraction": float((yearly_values > 0).mean()) if len(yearly_values) else None,
            "positive_symbol_fraction": float((symbol_values > 0).mean()) if len(symbol_values) else None,
            "year_segment_count": len(yearly_values), "symbol_segment_count": len(symbol_values),
            "stability": stability,
        })
    return {
        "experiment_id": "RC-C1", "study_population": "Executed production-selected trades only",
        "trade_count": len(trades), "entry_date_start": str(trades.entry_time.min().date()), "entry_date_end": str(trades.entry_time.max().date()),
        "methodological_scope": "Observational feature-outcome associations within the selected trade population; not independent contribution, causation, edge creation, or predictive validation.",
        "entry_feature_associations": features,
        "lifecycle_scope": "Lifecycle variables describe performance realization after entry and are not interpreted as entry information.",
        "unavailable_lifecycle_data": "Trailing-stop activation and stop-movement history are not recorded; final exit reason is available.",
    }


def _direction(value):
    if pd.isna(value) or abs(value) < .01:
        return "NO_OBSERVABLE_ASSOCIATION"
    return "POSITIVE_ASSOCIATION" if value > 0 else "NEGATIVE_ASSOCIATION"


def _strength(value):
    if pd.isna(value) or abs(value) < .05:
        return "NONE"
    if abs(value) < .10:
        return "WEAK"
    if abs(value) < .20:
        return "MODERATE"
    return "STRONG"


def _stability(years, symbols):
    if not len(years) or not len(symbols):
        return "INSUFFICIENT_SEGMENTS"
    pooled_direction = np.sign(np.nanmedian(np.r_[years.to_numpy(), symbols.to_numpy()]))
    if pooled_direction == 0:
        return "NO_OBSERVABLE_ASSOCIATION"
    same_years = (np.sign(years) == pooled_direction).mean()
    same_symbols = (np.sign(symbols) == pooled_direction).mean()
    return "REASONABLY_STABLE" if same_years >= .70 and same_symbols >= .70 else "UNSTABLE"


def _require_columns(trades):
    required = set(ENTRY_FEATURES) - {"leadership_quality", "atr_expansion_magnitude"}
    required |= {"true_range", "atr14", "R_multiple", "entry_time", "exit_time", "holding_days", "mae", "mfe", "exit_reason", "pnl_dollars"}
    missing = sorted(required - set(trades.columns))
    if missing:
        raise ValueError(f"Missing required frozen trade-journal columns: {missing}")


def _report(path, summary, distributions, correlations, lifecycle):
    lines = [
        "# RC-C1 Core Signal Attribution Audit", "", "## Methodological Scope", "",
        "RC-C1 is an observational attribution study conducted exclusively on the production-selected trade population. It identifies feature-outcome associations within selected trades. It does not estimate independent causal contributions, edge creation, or predictive performance.",
        "", "## Section A: Entry Features", "", "Only values known at entry are included below.", "", distributions.to_string(index=False), "", correlations.to_string(index=False),
        "", "## Section B: Trade Lifecycle", "", "Lifecycle variables occur after entry and describe performance realization; they are not entry information.", "", lifecycle.to_string(index=False),
        "", "## Data Availability", "", summary["unavailable_lifecycle_data"],
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def _args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trades", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


if __name__ == "__main__":
    main()
