"""Validate time-series momentum using the frozen master trade dataset."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
import pandas as pd


MIN_GROUP = 20
BOOTSTRAP_ITERATIONS = 2000
SEED = 20260721


def main() -> None:
    args = _parse_args()
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(args.trades)
    frame = _prepare(frame)
    definitions = _definitions(frame)

    bucket_rows: list[dict[str, object]] = []
    validation_rows: list[dict[str, object]] = []
    regime_rows: list[dict[str, object]] = []
    for name, values, available in definitions:
        if not available:
            continue
        work = frame.assign(_trend_value=values).dropna(subset=["_trend_value", "R_multiple"])
        if work.empty:
            continue
        bucket_rows.extend(_bucket_analysis(work, name))
        validation_rows.extend(_time_validation(work, name))
        regime_rows.extend(_regime_analysis(work, name))

    buckets = pd.DataFrame(bucket_rows)
    validation = pd.DataFrame(validation_rows)
    regimes = pd.DataFrame(regime_rows)
    summary = _summary(definitions, buckets, validation, regimes)
    buckets.to_csv(out / "trend_bucket_analysis.csv", index=False)
    validation.to_csv(out / "trend_validation.csv", index=False)
    regimes.to_csv(out / "trend_regime_analysis.csv", index=False)
    summary.to_csv(out / "trend_following_summary.csv", index=False)
    _report(out / "trend_following_research.md", args.trades, frame, definitions, summary, validation, regimes)
    print(out / "trend_following_research.md")


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--trades", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    return p.parse_args()


def _prepare(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    for col in ["R_multiple", "ema50_slope", "ema200_slope", "distance_above_ema50", "distance_above_ema200", "atr_percent", "spy_return60"]:
        if col in result:
            result[col] = pd.to_numeric(result[col], errors="coerce")
    date_col = "entry_time" if "entry_time" in result else "signal_timestamp"
    result["_date"] = pd.to_datetime(result[date_col], errors="coerce")
    result["_year"] = result["_date"].dt.year
    return result


def _definitions(frame: pd.DataFrame) -> list[tuple[str, pd.Series, bool]]:
    def col(name: str) -> tuple[pd.Series, bool]:
        if name in frame:
            return pd.to_numeric(frame[name], errors="coerce"), True
        return pd.Series(np.nan, index=frame.index), False

    ema50_dist, has_ema50_dist = col("distance_above_ema50")
    ema200_dist, has_ema200_dist = col("distance_above_ema200")
    ema50_slope, has_ema50_slope = col("ema50_slope")
    ema200_slope, has_ema200_slope = col("ema200_slope")
    spy_above = frame["spy_above_ema200"].astype(str).str.lower().isin(["true", "1"]) if "spy_above_ema200" in frame else pd.Series(np.nan, index=frame.index)
    return [
        ("PRICE_ABOVE_EMA50", ema50_dist > 0, has_ema50_dist),
        ("PRICE_ABOVE_EMA200", ema200_dist > 0, has_ema200_dist),
        ("EMA50_SLOPE_POSITIVE", ema50_slope > 0, has_ema50_slope),
        ("EMA200_SLOPE_POSITIVE", ema200_slope > 0, has_ema200_slope),
        ("EMA50_SLOPE", ema50_slope, has_ema50_slope),
        ("EMA200_SLOPE", ema200_slope, has_ema200_slope),
        ("DISTANCE_ABOVE_EMA50", ema50_dist, has_ema50_dist),
        ("DISTANCE_ABOVE_EMA200", ema200_dist, has_ema200_dist),
        ("SPY_ABOVE_EMA200", spy_above, "spy_above_ema200" in frame),
        ("EMA100", pd.Series(np.nan, index=frame.index), False),
        ("EMA50_ABOVE_EMA200", pd.Series(np.nan, index=frame.index), False),
    ]


def _bucket_analysis(work: pd.DataFrame, name: str) -> list[dict[str, object]]:
    values = work["_trend_value"]
    if values.dtype == bool or set(values.dropna().unique()).issubset({True, False}):
        buckets = pd.Series(np.where(values, "ALIGNED", "NOT_ALIGNED"), index=work.index)
    else:
        try:
            buckets = pd.qcut(values, 5, labels=["LOWEST_20", "20_40", "40_60", "60_80", "TOP_20"], duplicates="drop")
        except ValueError:
            buckets = pd.Series(pd.NA, index=work.index)
    rows = []
    for bucket in pd.Series(buckets).dropna().unique():
        selected = work.loc[buckets == bucket, "R_multiple"]
        remainder = work.loc[buckets != bucket, "R_multiple"]
        rows.append(_stats(name, "ALL", str(bucket), selected, remainder))
    return rows


def _time_validation(work: pd.DataFrame, name: str) -> list[dict[str, object]]:
    rows = []
    for year, segment in work.groupby("_year", dropna=True):
        if len(segment) < MIN_GROUP * 2:
            continue
        if segment["_trend_value"].dtype == bool or set(segment["_trend_value"].dropna().unique()).issubset({True, False}):
            selected = segment.loc[segment["_trend_value"], "R_multiple"]
            remainder = segment.loc[~segment["_trend_value"], "R_multiple"]
        else:
            cut = segment["_trend_value"].median()
            selected = segment.loc[segment["_trend_value"] >= cut, "R_multiple"]
            remainder = segment.loc[segment["_trend_value"] < cut, "R_multiple"]
        rows.append(_stats(name, f"YEAR_{int(year)}", "ALIGNED_VS_REMAINDER", selected, remainder))
    return rows


def _regime_analysis(work: pd.DataFrame, name: str) -> list[dict[str, object]]:
    rows = []
    if "spy_above_ema200" in work:
        for regime, segment in work.groupby(work["spy_above_ema200"].astype(str), dropna=False):
            if len(segment) >= MIN_GROUP * 2:
                rows.append(_regime_stats(segment, name, f"SPY_{regime}"))
    if "atr_percent" in work:
        median = work["atr_percent"].median()
        for regime, segment in work.groupby(np.where(work["atr_percent"] >= median, "HIGH_VOL", "LOW_VOL")):
            if len(segment) >= MIN_GROUP * 2:
                rows.append(_regime_stats(segment, name, regime))
    return rows


def _regime_stats(segment: pd.DataFrame, feature: str, regime: str) -> dict[str, object]:
    values = segment["R_multiple"].dropna().astype(float)
    return {"feature": feature, "regime": regime, "trade_count": len(values), "avg_R": values.mean() if len(values) else None, "win_rate": (values > 0).mean() * 100 if len(values) else None, "median_R": values.median() if len(values) else None, "profit_factor": _profit_factor(values), "sample_sufficient": len(values) >= MIN_GROUP}


def _stats(feature: str, segment: str, bucket: str, selected: pd.Series, remainder: pd.Series) -> dict[str, object]:
    selected = pd.to_numeric(selected, errors="coerce").dropna().astype(float)
    remainder = pd.to_numeric(remainder, errors="coerce").dropna().astype(float)
    low, high = _bootstrap(selected)
    return {"feature": feature, "segment": segment, "bucket": bucket, "trade_count": len(selected), "winner_count": int((selected > 0).sum()), "loser_count": int((selected < 0).sum()), "win_rate": (selected > 0).mean() * 100 if len(selected) else None, "avg_R": selected.mean() if len(selected) else None, "median_R": selected.median() if len(selected) else None, "expectancy": selected.mean() if len(selected) else None, "profit_factor": _profit_factor(selected), "bootstrap_ci_low": low, "bootstrap_ci_high": high, "mann_whitney_p_value": _mann_whitney(selected, remainder), "cohens_d": _cohens_d(selected, remainder), "effect_size": _effect_label(_cohens_d(selected, remainder)), "missing_data_pct": None, "sample_sufficient": len(selected) >= MIN_GROUP and len(remainder) >= MIN_GROUP}


def _summary(definitions, buckets: pd.DataFrame, validation: pd.DataFrame, regimes: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for name, _, available in definitions:
        if not available:
            rows.append({"trend_definition": name, "available": False, "conclusion": "Unavailable - feature not recorded"})
            continue
        data = buckets[buckets["feature"] == name]
        top = data[data["bucket"].isin(["TOP_20", "ALIGNED"])]
        bottom = data[data["bucket"].isin(["LOWEST_20", "NOT_ALIGNED"])]
        top_r = float(top["avg_R"].iloc[0]) if not top.empty else np.nan
        bottom_r = float(bottom["avg_R"].iloc[0]) if not bottom.empty else np.nan
        val = validation[validation["feature"] == name]
        positive = (pd.to_numeric(val.get("avg_R", pd.Series(dtype=float)), errors="coerce") > 0).mean() if not val.empty else np.nan
        rows.append({"trend_definition": name, "available": True, "top_or_aligned_avg_R": top_r, "bottom_or_unaligned_avg_R": bottom_r, "difference": top_r - bottom_r if pd.notna(top_r) and pd.notna(bottom_r) else np.nan, "validation_segments": len(val), "positive_segments": int((pd.to_numeric(val.get("avg_R", pd.Series(dtype=float)), errors="coerce") > 0).sum()) if not val.empty else 0, "stability_ratio": positive, "conclusion": "Promising" if pd.notna(top_r) and pd.notna(bottom_r) and top_r > bottom_r and pd.notna(positive) and positive >= .75 else "Weak Evidence" if pd.notna(top_r) and pd.notna(bottom_r) and top_r > bottom_r else "Requires More Data"})
    return pd.DataFrame(rows)


def _profit_factor(values):
    wins = float(values[values > 0].sum())
    losses = abs(float(values[values < 0].sum()))
    return wins / losses if losses else (math.inf if wins else 0.0)


def _cohens_d(left, right):
    if len(left) < MIN_GROUP or len(right) < MIN_GROUP:
        return None
    pooled = math.sqrt(((len(left)-1)*left.var(ddof=1)+(len(right)-1)*right.var(ddof=1))/(len(left)+len(right)-2))
    return (left.mean()-right.mean())/pooled if pooled else 0.0


def _mann_whitney(left, right):
    if len(left) < MIN_GROUP or len(right) < MIN_GROUP:
        return None
    values = pd.concat([left, right], ignore_index=True)
    ranks = values.rank(method="average")
    n1, n2 = len(left), len(right)
    u = ranks.iloc[:n1].sum()-n1*(n1+1)/2
    ties = values.value_counts()
    variance = n1*n2/12*((n1+n2+1)-float((ties**3-ties).sum())/((n1+n2)*(n1+n2-1)))
    return float(math.erfc(abs((u-n1*n2/2)/math.sqrt(variance))/math.sqrt(2))) if variance > 0 else 1.0


def _bootstrap(values):
    if len(values) < MIN_GROUP:
        return None, None
    rng = np.random.default_rng(SEED)
    samples = rng.choice(values.to_numpy(), size=(BOOTSTRAP_ITERATIONS, len(values)), replace=True).mean(axis=1)
    return float(np.quantile(samples, .025)), float(np.quantile(samples, .975))


def _effect_label(value):
    if value is None:
        return "Insufficient Sample"
    value = abs(value)
    return "Large" if value >= .8 else "Medium" if value >= .5 else "Small" if value >= .2 else "Negligible"


def _report(path, source, frame, definitions, summary, validation, regimes):
    unavailable = [name for name, _, available in definitions if not available]
    lines = ["# Time-Series Momentum Research", "", f"Source: `{source}`", "", "H0: Long-term trend alignment has no meaningful relationship with future trade quality.", "H1: Trades aligned with long-term trend produce better outcomes.", "", "This is a descriptive scientific validation study. No strategy rule or parameter was changed.", "", "## Summary", "", summary.to_string(index=False), "", "## Robustness", "", f"Year segments tested: {validation['segment'].nunique() if not validation.empty else 0}", f"Regime rows: {len(regimes)}", "", "## Limitations", "", "- EMA100 and direct EMA50 > EMA200 were not recorded in the master dataset and were not reconstructed.", "- This is trade-level attribution; it does not establish causality.", "- Multiple definitions and segments require cautious interpretation.", "- Results must be confirmed with independent out-of-sample data."]
    if unavailable:
        lines.insert(-4, "Unavailable definitions: " + ", ".join(unavailable))
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
