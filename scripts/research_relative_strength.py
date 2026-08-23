"""Literature-style validation study for relative strength.

This script is descriptive only. It does not alter strategy parameters or
create a trading rule. Input must contain signal-time RS20/RS60/RS120 and
post-trade R_multiple values.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
import pandas as pd


RS_FEATURES = ["rs20", "rs60", "rs120"]
BUCKET_LABELS = ["LOWEST_20", "20_40", "40_60", "60_80", "TOP_20"]
MIN_BUCKET = 20
BOOTSTRAP_ITERATIONS = 2000
SEED = 20260720


def main() -> None:
    args = _parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    trades = pd.read_csv(args.trades)
    required = set(RS_FEATURES + ["R_multiple"])
    missing = sorted(required.difference(trades.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    trades = _prepare(trades)

    bucket_rows = []
    validation_rows = []
    for feature in RS_FEATURES:
        feature_data = trades.dropna(subset=[feature, "R_multiple"]).copy()
        if len(feature_data) >= len(BUCKET_LABELS):
            feature_data["bucket"] = _bucket(feature_data[feature])
        else:
            feature_data["bucket"] = pd.Series(pd.NA, index=feature_data.index, dtype="object")
        for bucket in BUCKET_LABELS:
            selected = feature_data[feature_data["bucket"] == bucket]["R_multiple"]
            remainder = feature_data[feature_data["bucket"] != bucket]["R_multiple"]
            bucket_rows.append(_row(feature, "ALL", bucket, selected, remainder))
        validation_rows.extend(_period_rows(feature_data, feature))
        validation_rows.extend(_regime_rows(feature_data, feature))

    bucket_analysis = pd.DataFrame(bucket_rows)
    validation = pd.DataFrame(validation_rows)
    summary = _build_summary(bucket_analysis, validation)
    bucket_analysis.to_csv(output_dir / "relative_strength_bucket_analysis.csv", index=False)
    validation.to_csv(output_dir / "relative_strength_validation.csv", index=False)
    summary.to_csv(output_dir / "relative_strength_summary.csv", index=False)
    _write_report(output_dir / "relative_strength_research.md", args.trades, bucket_analysis, validation, summary)
    print(output_dir / "relative_strength_research.md")
    print(output_dir / "relative_strength_summary.csv")
    print(output_dir / "relative_strength_bucket_analysis.csv")
    print(output_dir / "relative_strength_validation.csv")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trades", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def _prepare(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    for column in RS_FEATURES + ["R_multiple"]:
        result[column] = pd.to_numeric(result[column], errors="coerce")
    if "entry_time" in result:
        result["entry_time"] = pd.to_datetime(result["entry_time"], errors="coerce")
        result["year"] = result["entry_time"].dt.year
    elif "signal_timestamp" in result:
        result["signal_timestamp"] = pd.to_datetime(result["signal_timestamp"], errors="coerce")
        result["year"] = result["signal_timestamp"].dt.year
    else:
        result["year"] = np.nan
    if "spy_above_ema200" in result:
        result["market_regime"] = np.where(result["spy_above_ema200"].astype(str).str.lower().isin(["true", "1"]), "BULL_PROXY", "NON_BULL_PROXY")
    else:
        result["market_regime"] = "UNKNOWN"
    return result


def _bucket(values: pd.Series) -> pd.Series:
    try:
        return pd.qcut(values, q=5, labels=BUCKET_LABELS, duplicates="drop")
    except ValueError:
        return pd.Series([pd.NA] * len(values), index=values.index, dtype="object")


def _row(feature: str, segment: str, bucket: str, selected: pd.Series, remainder: pd.Series) -> dict[str, object]:
    selected = selected.dropna().astype(float)
    remainder = remainder.dropna().astype(float)
    ci_low, ci_high = _bootstrap_ci(selected)
    return {
        "feature": feature, "segment": segment, "bucket": bucket,
        "trade_count": len(selected), "winner_count": int((selected > 0).sum()),
        "loser_count": int((selected < 0).sum()), "win_rate": float((selected > 0).mean() * 100) if len(selected) else None,
        "avg_R": float(selected.mean()) if len(selected) else None,
        "expectancy": float(selected.mean()) if len(selected) else None,
        "profit_factor": _profit_factor(selected), "median_R": float(selected.median()) if len(selected) else None,
        "bootstrap_ci_low": ci_low, "bootstrap_ci_high": ci_high,
        "mann_whitney_p_value_vs_remainder": _mann_whitney(selected, remainder),
        "cohens_d_vs_remainder": _cohens_d(selected, remainder),
        "sample_sufficient": len(selected) >= MIN_BUCKET and len(remainder) >= MIN_BUCKET,
    }


def _period_rows(frame: pd.DataFrame, feature: str) -> list[dict[str, object]]:
    rows = []
    years = sorted(frame["year"].dropna().astype(int).unique())
    if not years:
        return rows
    for year in years:
        segment = frame[frame["year"] == year]
        if len(segment) < MIN_BUCKET * 2:
            continue
        ranked = segment[feature].rank(pct=True)
        top = segment.loc[ranked >= 0.8, "R_multiple"]
        bottom = segment.loc[ranked <= 0.2, "R_multiple"]
        rows.append(_row(feature, f"YEAR_{year}", "TOP20_VS_BOTTOM20", top, bottom))
    return rows


def _regime_rows(frame: pd.DataFrame, feature: str) -> list[dict[str, object]]:
    rows = []
    for regime, segment in frame.groupby("market_regime", dropna=False):
        if regime == "UNKNOWN" or len(segment) < MIN_BUCKET * 2:
            continue
        ranked = segment[feature].rank(pct=True)
        top = segment.loc[ranked >= 0.8, "R_multiple"]
        bottom = segment.loc[ranked <= 0.2, "R_multiple"]
        rows.append(_row(feature, f"REGIME_{regime}", "TOP20_VS_BOTTOM20", top, bottom))
    return rows


def _build_summary(bucket: pd.DataFrame, validation: pd.DataFrame) -> pd.DataFrame:
    if "feature" not in validation.columns:
        validation = pd.DataFrame(columns=["feature", "segment", "avg_R"])
    rows = []
    for feature in RS_FEATURES:
        data = bucket[bucket["feature"] == feature]
        top = data[data["bucket"] == "TOP_20"]
        bottom = data[data["bucket"] == "LOWEST_20"]
        top_mean = top["avg_R"].iloc[0] if not top.empty else np.nan
        bottom_mean = bottom["avg_R"].iloc[0] if not bottom.empty else np.nan
        valid_oos = validation[(validation["feature"] == feature) & (validation["segment"].str.startswith(("YEAR_", "REGIME_"), na=False))]
        positive_segments = int((pd.to_numeric(valid_oos["avg_R"], errors="coerce") > 0).sum()) if not valid_oos.empty else 0
        rows.append({
            "feature": feature,
            "top20_avg_R": top_mean,
            "bottom20_avg_R": bottom_mean,
            "top_minus_bottom_avg_R": top_mean - bottom_mean if pd.notna(top_mean) and pd.notna(bottom_mean) else np.nan,
            "segments_tested": len(valid_oos),
            "positive_segments": positive_segments,
            "stability_ratio": positive_segments / len(valid_oos) if len(valid_oos) else np.nan,
            "conclusion": _conclusion(top_mean, bottom_mean, valid_oos),
        })
    return pd.DataFrame(rows)


def _conclusion(top: float, bottom: float, validation: pd.DataFrame) -> str:
    if pd.isna(top) or pd.isna(bottom):
        return "Requires More Data"
    if validation.empty:
        return "Requires More Data"
    positive = (pd.to_numeric(validation["avg_R"], errors="coerce") > 0).mean()
    difference = top - bottom
    if difference > 0 and positive >= 0.75:
        return "Promising"
    if difference > 0:
        return "Weak Evidence"
    return "Rejected"


def _bootstrap_ci(values: pd.Series) -> tuple[float | None, float | None]:
    if len(values) < MIN_BUCKET:
        return None, None
    rng = np.random.default_rng(SEED)
    samples = rng.choice(values.to_numpy(), size=(BOOTSTRAP_ITERATIONS, len(values)), replace=True).mean(axis=1)
    return float(np.quantile(samples, 0.025)), float(np.quantile(samples, 0.975))


def _profit_factor(values: pd.Series) -> float | None:
    if values.empty:
        return None
    wins = float(values[values > 0].sum())
    losses = abs(float(values[values < 0].sum()))
    return wins / losses if losses else (math.inf if wins else 0.0)


def _cohens_d(left: pd.Series, right: pd.Series) -> float | None:
    if len(left) < MIN_BUCKET or len(right) < MIN_BUCKET:
        return None
    pooled = math.sqrt(((len(left)-1)*left.var(ddof=1) + (len(right)-1)*right.var(ddof=1)) / (len(left)+len(right)-2))
    return float((left.mean() - right.mean()) / pooled) if pooled else 0.0


def _mann_whitney(left: pd.Series, right: pd.Series) -> float | None:
    if len(left) < MIN_BUCKET or len(right) < MIN_BUCKET:
        return None
    combined = pd.concat([left, right], ignore_index=True)
    ranks = combined.rank(method="average")
    n1, n2 = len(left), len(right)
    u = ranks.iloc[:n1].sum() - n1 * (n1 + 1) / 2
    ties = combined.value_counts()
    tie_term = float((ties**3 - ties).sum())
    variance = n1*n2/12 * ((n1+n2+1) - tie_term/((n1+n2)*(n1+n2-1)))
    if variance <= 0:
        return 1.0
    z = (u - n1*n2/2) / math.sqrt(variance)
    return float(math.erfc(abs(z) / math.sqrt(2)))


def _write_report(path: Path, source: Path, buckets: pd.DataFrame, validation: pd.DataFrame, summary: pd.DataFrame) -> None:
    lines = [
        "# Relative Strength Research",
        "",
        f"Source: `{source}`",
        "",
        "## Research Question",
        "",
        "H0: Relative Strength has no meaningful relationship with future trade outcome.",
        "H1: Higher Relative Strength is associated with better future trade quality.",
        "",
        "This report is descriptive and does not optimize or modify the strategy.",
        "",
        "## Summary",
        "",
        summary.to_string(index=False) if not summary.empty else "Insufficient data.",
        "",
        "## Interpretation",
        "",
        "A positive bucket gradient is evidence for further research, not proof of causality or live profitability.",
        "Evidence is considered unstable when it does not repeat across time/regime segments or when sample sizes are insufficient.",
        "No conclusion should be used to add a filter without independent out-of-sample validation.",
        "",
        "## Limitations",
        "",
        "- Quantile buckets are descriptive and are not proposed trading thresholds.",
        "- P-values use a normal-approximation Mann-Whitney test.",
        "- Multiple comparisons require cautious interpretation.",
        "- Regime analysis requires signal-time market-state columns in the input.",
        "- Results can be concentrated by symbol unless the input includes a broad fixed universe.",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
