"""Analyze completed-trade metadata without changing strategy behavior.

Usage:
    python scripts/research_feature_engine.py --trades output/trades.csv \
        --output-dir output/feature_research
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import pandas as pd


CORE_COLUMNS = {
    "entry_time", "exit_time", "direction", "entry_price", "exit_price",
    "stop_loss", "take_profit", "position_size", "pnl_dollars", "pnl_percent",
    "R_multiple", "trade_duration_bars", "exit_reason",
}
OUTCOME_COLUMNS = {"mae", "mfe", "holding_days"}


def main() -> None:
    args = _parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    trades = pd.read_csv(args.trades)
    if trades.empty:
        raise ValueError(f"Trade file is empty: {args.trades}")

    features = [column for column in trades.columns if column not in CORE_COLUMNS]
    numeric_features = []
    for feature in features:
        values = pd.to_numeric(trades[feature], errors="coerce")
        if values.notna().sum() >= 2:
            trades[f"{feature}_zscore"] = _zscore(values)
            numeric_features.append(feature)

    trades["outcome"] = trades["pnl_dollars"].apply(_outcome)
    trades.to_csv(output_dir / "feature_research_trades.csv", index=False)

    rows = []
    winners = trades[trades["outcome"] == "WIN"]
    losers = trades[trades["outcome"] == "LOSS"]
    for feature in numeric_features:
        all_values = pd.to_numeric(trades[feature], errors="coerce")
        winner_values = pd.to_numeric(winners[feature], errors="coerce").dropna()
        loser_values = pd.to_numeric(losers[feature], errors="coerce").dropna()
        rows.append({
            "feature_name": feature,
            "feature_group": "outcome" if feature in OUTCOME_COLUMNS else "entry_context",
            "winner_count": int(len(winner_values)),
            "loser_count": int(len(loser_values)),
            "winner_mean": _mean(winner_values),
            "loser_mean": _mean(loser_values),
            "difference": _mean(winner_values) - _mean(loser_values),
            "winner_median": _median(winner_values),
            "loser_median": _median(loser_values),
            "cohens_d": _cohens_d(winner_values, loser_values),
            "correlation_with_R": _correlation(all_values, pd.to_numeric(trades["R_multiple"], errors="coerce")),
            "missing_pct": float(all_values.isna().mean() * 100.0),
        })

    summary = pd.DataFrame(rows)
    if not summary.empty:
        summary = summary.sort_values("cohens_d", key=lambda s: s.abs(), ascending=False)
    else:
        summary = pd.DataFrame(columns=[
            "feature_name", "feature_group", "winner_count", "loser_count",
            "winner_mean", "loser_mean", "difference", "winner_median",
            "loser_median", "cohens_d", "correlation_with_R", "missing_pct",
        ])
    summary.to_csv(output_dir / "feature_research_summary.csv", index=False)
    summary[summary["feature_group"] == "entry_context"].to_csv(
        output_dir / "winner_loser_entry_features.csv", index=False
    )
    _write_report(output_dir / "feature_research_report.md", trades, summary)
    print(output_dir / "feature_research_summary.csv")
    print(output_dir / "feature_research_report.md")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trades", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def _outcome(value: object) -> str:
    number = float(value)
    if number > 0:
        return "WIN"
    if number < 0:
        return "LOSS"
    return "FLAT"


def _zscore(values: pd.Series) -> pd.Series:
    mean = values.mean()
    std = values.std(ddof=1)
    if pd.isna(std) or std == 0:
        return pd.Series(0.0, index=values.index)
    return (values - mean) / std


def _mean(values: pd.Series) -> float | None:
    return float(values.mean()) if not values.empty else None


def _median(values: pd.Series) -> float | None:
    return float(values.median()) if not values.empty else None


def _cohens_d(winners: pd.Series, losers: pd.Series) -> float | None:
    if len(winners) < 2 or len(losers) < 2:
        return None
    pooled = math.sqrt(((len(winners) - 1) * winners.var(ddof=1) + (len(losers) - 1) * losers.var(ddof=1)) / (len(winners) + len(losers) - 2))
    return float((winners.mean() - losers.mean()) / pooled) if pooled > 0 else 0.0


def _correlation(left: pd.Series, right: pd.Series) -> float | None:
    values = pd.concat([left, right], axis=1).dropna()
    if len(values) < 3 or values.iloc[:, 0].nunique() < 2:
        return None
    return float(values.iloc[:, 0].corr(values.iloc[:, 1]))


def _write_report(path: Path, trades: pd.DataFrame, summary: pd.DataFrame) -> None:
    entry = summary[summary["feature_group"] == "entry_context"].head(10)
    lines = [
        "# Feature Research Report",
        "",
        f"Completed trades: {len(trades)}",
        f"Wins: {(trades['outcome'] == 'WIN').sum()}",
        f"Losses: {(trades['outcome'] == 'LOSS').sum()}",
        "",
        "This report is descriptive attribution, not a strategy change or optimization.",
        "The outcome fields MAE/MFE/holding_days are excluded from entry-context conclusions.",
        "",
        "## Largest Entry-Context Differences",
        "",
        entry.to_string(index=False) if not entry.empty else "No comparable entry features were available.",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
