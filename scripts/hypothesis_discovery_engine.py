"""Discover descriptive, research-only hypotheses from trade metadata.

This module never changes a strategy or selects live trades. It ranks simple
entry-context conditions for subsequent out-of-sample testing.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
import pandas as pd


CORE = {
    "entry_time", "exit_time", "direction", "entry_price", "exit_price",
    "stop_loss", "take_profit", "position_size", "pnl_dollars", "pnl_percent",
    "R_multiple", "trade_duration_bars", "exit_reason", "mae", "mfe", "holding_days",
}
MIN_GROUP = 10
BOOTSTRAP_ITERATIONS = 2000
SEED = 20260720


def main() -> None:
    args = _parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    trades = pd.read_csv(args.trades)
    if trades.empty:
        raise ValueError("Input trade file is empty")
    trades["R_multiple"] = pd.to_numeric(trades["R_multiple"], errors="coerce")
    trades["pnl_dollars"] = pd.to_numeric(trades["pnl_dollars"], errors="coerce")
    candidates = _generate_candidates(trades)
    rows = [_evaluate(trades, candidate) for candidate in candidates]
    result = pd.DataFrame(rows)
    if result.empty:
        result = pd.DataFrame(columns=_columns())
    else:
        result["score"] = result.apply(_score, axis=1)
        result = result.sort_values(["score", "p_value"], ascending=[False, True])
        result["hypothesis_id"] = [f"H{i:04d}" for i in range(1, len(result) + 1)]
    result.to_csv(output_dir / "hypothesis_candidates.csv", index=False)
    result.head(10).to_csv(output_dir / "top_hypotheses.csv", index=False)
    _write_report(output_dir / "hypothesis_report.md", result, args.trades)
    print(output_dir / "hypothesis_candidates.csv")
    print(output_dir / "top_hypotheses.csv")
    print(output_dir / "hypothesis_report.md")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trades", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def _generate_candidates(frame: pd.DataFrame) -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = []
    feature_names = []
    for column in frame.columns:
        if column in CORE or column.endswith("_zscore"):
            continue
        values = pd.to_numeric(frame[column], errors="coerce")
        if values.notna().sum() >= MIN_GROUP * 2 and values.nunique() >= 4:
            feature_names.append(column)
            candidates.extend(_single_feature_candidates(column, values))

    # Only pair the strongest descriptive features, preventing pair explosion.
    effects = []
    for feature in feature_names:
        values = pd.to_numeric(frame[feature], errors="coerce")
        effects.append((feature, abs(_correlation(values, frame["R_multiple"]) or 0.0)))
    strongest = [name for name, _ in sorted(effects, key=lambda item: item[1], reverse=True)[:6]]
    for left_index, left in enumerate(strongest):
        for right in strongest[left_index + 1:]:
            left_values = pd.to_numeric(frame[left], errors="coerce")
            right_values = pd.to_numeric(frame[right], errors="coerce")
            left_threshold = float(left_values.median())
            right_threshold = float(right_values.median())
            candidates.append({
                "kind": "combination",
                "description": f"{left} >= median AND {right} >= median",
                "features": f"{left}|{right}",
                "thresholds": f"median({left})={left_threshold:.6g}; median({right})={right_threshold:.6g}",
                "mask": (left_values >= left_threshold) & (right_values >= right_threshold),
            })
    return candidates


def _single_feature_candidates(name: str, values: pd.Series) -> list[dict[str, object]]:
    result = []
    for quantile, label in [(0.25, "Q1+"), (0.50, "Q2+"), (0.75, "Q3+")]:
        threshold = float(values.quantile(quantile))
        result.append({
            "kind": "single_feature",
            "description": f"{name} >= {label} threshold",
            "features": name,
            "thresholds": f"{name} >= {threshold:.6g} ({label})",
            "mask": values >= threshold,
        })
    return result


def _evaluate(frame: pd.DataFrame, candidate: dict[str, object]) -> dict[str, object]:
    mask = pd.Series(candidate["mask"], index=frame.index).fillna(False)
    selected = frame.loc[mask, "R_multiple"].dropna().astype(float)
    excluded = frame.loc[~mask, "R_multiple"].dropna().astype(float)
    all_r = frame["R_multiple"].dropna().astype(float)
    minimum_ok = len(selected) >= MIN_GROUP and len(excluded) >= MIN_GROUP
    ci_low, ci_high = _bootstrap_ci(selected)
    p_value = _mann_whitney_pvalue(selected, excluded)
    selected_pf = _profit_factor(frame.loc[mask, "pnl_dollars"])
    wins = int((selected > 0).sum())
    losses = int((selected < 0).sum())
    return {
        "hypothesis_id": "",
        "kind": candidate["kind"],
        "description": candidate["description"],
        "features": candidate["features"],
        "thresholds": candidate["thresholds"],
        "trade_count": len(selected),
        "winner_count": wins,
        "loser_count": losses,
        "win_rate": float((selected > 0).mean() * 100.0) if len(selected) else None,
        "mean_R": float(selected.mean()) if len(selected) else None,
        "median_R": float(selected.median()) if len(selected) else None,
        "expectancy_R": float(selected.mean()) if len(selected) else None,
        "profit_factor": selected_pf,
        "cohens_d_vs_remainder": _cohens_d(selected, excluded),
        "correlation_with_R": _correlation(pd.Series(candidate["mask"], dtype=float), frame["R_multiple"]),
        "p_value": p_value,
        "bootstrap_ci_low": ci_low,
        "bootstrap_ci_high": ci_high,
        "outlier_sensitivity": _outlier_sensitivity(selected),
        "minimum_sample_ok": minimum_ok,
        "recommendation": _recommendation(minimum_ok, p_value, selected, all_r, _outlier_sensitivity(selected)),
    }


def _score(row: pd.Series) -> float:
    if not bool(row["minimum_sample_ok"]):
        return -100.0
    effect = min(abs(float(row["cohens_d_vs_remainder"] or 0.0)), 2.0) / 2.0
    significance = max(0.0, min(1.0, -math.log10(max(float(row["p_value"] or 1.0), 1e-12)) / 4.0))
    stability = max(0.0, 1.0 - float(row["outlier_sensitivity"] or 1.0))
    simplicity = 1.0 if row["kind"] == "single_feature" else 0.65
    generality = min(float(row["trade_count"]) / 50.0, 1.0)
    return round(0.25 * effect + 0.20 * significance + 0.20 * stability + 0.20 * simplicity + 0.15 * generality, 6)


def _recommendation(minimum_ok: bool, p_value: float | None, selected: pd.Series, all_r: pd.Series, outlier: float) -> str:
    if not minimum_ok:
        return "Reject"
    if outlier > 0.50 or p_value is None or p_value > 0.10:
        return "Weak"
    if p_value <= 0.05 and len(selected) >= 30:
        return "High Priority Research"
    if p_value <= 0.10 and selected.mean() > all_r.mean():
        return "Promising"
    return "Interesting"


def _profit_factor(pnl: pd.Series) -> float:
    values = pd.to_numeric(pnl, errors="coerce").dropna()
    profit = float(values[values > 0].sum())
    loss = abs(float(values[values < 0].sum()))
    return profit / loss if loss else (math.inf if profit else 0.0)


def _cohens_d(left: pd.Series, right: pd.Series) -> float | None:
    if len(left) < 2 or len(right) < 2:
        return None
    pooled = math.sqrt(((len(left)-1)*left.var(ddof=1) + (len(right)-1)*right.var(ddof=1)) / (len(left)+len(right)-2))
    return float((left.mean() - right.mean()) / pooled) if pooled else 0.0


def _correlation(left: pd.Series, right: pd.Series) -> float | None:
    values = pd.concat([left, right], axis=1).dropna()
    if len(values) < 3 or values.iloc[:, 0].nunique() < 2:
        return None
    return float(values.iloc[:, 0].corr(values.iloc[:, 1]))


def _bootstrap_ci(values: pd.Series) -> tuple[float | None, float | None]:
    if len(values) < MIN_GROUP:
        return None, None
    rng = np.random.default_rng(SEED)
    samples = rng.choice(values.to_numpy(), size=(BOOTSTRAP_ITERATIONS, len(values)), replace=True).mean(axis=1)
    return float(np.quantile(samples, 0.025)), float(np.quantile(samples, 0.975))


def _mann_whitney_pvalue(left: pd.Series, right: pd.Series) -> float | None:
    if len(left) < MIN_GROUP or len(right) < MIN_GROUP:
        return None
    combined = pd.concat([left, right], ignore_index=True)
    ranks = combined.rank(method="average")
    n1, n2 = len(left), len(right)
    u1 = ranks.iloc[:n1].sum() - n1 * (n1 + 1) / 2
    mean_u = n1 * n2 / 2
    tie_counts = combined.value_counts()
    tie_term = float((tie_counts**3 - tie_counts).sum())
    variance = n1 * n2 / 12 * ((n1 + n2 + 1) - tie_term / ((n1 + n2) * (n1 + n2 - 1)))
    if variance <= 0:
        return 1.0
    z = (u1 - mean_u) / math.sqrt(variance)
    return float(math.erfc(abs(z) / math.sqrt(2.0)))


def _outlier_sensitivity(values: pd.Series) -> float:
    if len(values) < MIN_GROUP:
        return 1.0
    baseline = float(values.mean())
    trimmed = values.drop(values.abs().idxmax())
    if baseline == 0:
        return float(abs(trimmed.mean()))
    return float(min(abs(baseline - trimmed.mean()) / abs(baseline), 1.0))


def _write_report(path: Path, result: pd.DataFrame, source: Path) -> None:
    lines = [
        "# Hypothesis Discovery Report",
        "",
        f"Source: `{source}`",
        "",
        "This is a descriptive research assistant, not an optimizer or strategy builder.",
        "No hypothesis is accepted as true. Every candidate requires out-of-sample validation.",
        "",
        "## Workflow",
        "",
        "`feature_research_trades.csv -> simple candidates -> statistical tests -> safeguards -> ranked hypotheses`",
        "",
        "## Top Candidates",
        "",
    ]
    if result.empty:
        lines.append("No candidates were generated. The dataset likely has insufficient trades.")
    else:
        lines.append(result.head(10).to_string(index=False))
    lines.extend([
        "",
        "## Safeguards",
        "",
        f"Minimum selected and remainder group size: {MIN_GROUP} trades.",
        "Thresholds are simple quantile boundaries, not arbitrary decimal searches.",
        "Two-feature combinations are limited to the six strongest descriptive features.",
        "Bootstrap uses a fixed seed for deterministic confidence intervals.",
        "MAE/MFE/holding_days are excluded as entry features because they contain post-entry information.",
        "P-values are normal-approximation Mann-Whitney tests and should not be treated as proof after multiple testing.",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def _columns() -> list[str]:
    return ["hypothesis_id", "kind", "description", "features", "thresholds", "trade_count", "winner_count", "loser_count", "win_rate", "mean_R", "median_R", "expectancy_R", "profit_factor", "cohens_d_vs_remainder", "correlation_with_R", "p_value", "bootstrap_ci_low", "bootstrap_ci_high", "outlier_sensitivity", "minimum_sample_ok", "recommendation"]


if __name__ == "__main__":
    main()
