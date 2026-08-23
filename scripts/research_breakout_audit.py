"""Adversarial audit of volatility expansion / breakout features."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
import pandas as pd


FEATURES = ["breakout_distance", "true_range", "atr14", "atr_percent", "daily_range_percent", "relative_volume"]
MIN_GROUP = 20
BOOTSTRAPS = 2000
SEED = 20260721


def main() -> None:
    args = _parse_args()
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(args.trades)
    frame["R_multiple"] = pd.to_numeric(frame["R_multiple"], errors="coerce")
    frame["_date"] = pd.to_datetime(frame["entry_time"], errors="coerce") if "entry_time" in frame else pd.NaT
    frame["_year"] = frame["_date"].dt.year
    if {"true_range", "atr14"}.issubset(frame.columns):
        frame["range_expansion_ratio"] = pd.to_numeric(frame["true_range"], errors="coerce") / pd.to_numeric(frame["atr14"], errors="coerce")
        features = FEATURES + ["range_expansion_ratio"]
    else:
        features = FEATURES

    buckets, validations, stability = [], [], []
    for feature in features:
        if feature not in frame.columns:
            stability.append({"feature": feature, "test": "availability", "result": "UNAVAILABLE", "confidence": "None"})
            continue
        work = frame[[feature, "R_multiple", "_year"]].copy()
        work[feature] = pd.to_numeric(work[feature], errors="coerce")
        work = work.dropna(subset=[feature, "R_multiple"])
        if work.empty:
            continue
        buckets.extend(_buckets(work, feature))
        validations.extend(_years(work, feature))
        validations.extend(_regimes(work, feature))
        stability.extend(_negative_tests(work, feature))

    bucket_df, validation_df, stability_df = pd.DataFrame(buckets), pd.DataFrame(validations), pd.DataFrame(stability)
    summary = _summary(features, bucket_df, validation_df, stability_df)
    bucket_df.to_csv(out / "breakout_bucket_analysis.csv", index=False)
    validation_df.to_csv(out / "breakout_validation.csv", index=False)
    stability_df.to_csv(out / "breakout_stability.csv", index=False)
    summary.to_csv(out / "breakout_summary.csv", index=False)
    _report(out / "breakout_research.md", args.trades, features, summary, validation_df, stability_df)
    print(out / "breakout_research.md")


def _parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--trades", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    return p.parse_args()


def _buckets(work, feature):
    try:
        labels = ["LOWEST_20", "20_40", "40_60", "60_80", "TOP_20"]
        bucket = pd.qcut(work[feature], 5, labels=labels, duplicates="drop")
    except ValueError:
        return []
    rows = []
    for label in bucket.dropna().unique():
        selected = work.loc[bucket == label, "R_multiple"]
        remainder = work.loc[bucket != label, "R_multiple"]
        rows.append(_stats(feature, "ALL", str(label), selected, remainder))
    return rows


def _years(work, feature):
    rows = []
    for year, segment in work.groupby("_year", dropna=True):
        if len(segment) < MIN_GROUP * 2:
            continue
        cut = segment[feature].median()
        rows.append(_stats(feature, f"YEAR_{int(year)}", "ABOVE_MEDIAN", segment.loc[segment[feature] >= cut, "R_multiple"], segment.loc[segment[feature] < cut, "R_multiple"]))
    return rows


def _regimes(work, feature):
    if feature not in ["atr_percent", "range_expansion_ratio", "true_range", "daily_range_percent"]:
        return []
    rows = []
    cut = work[feature].median()
    for name, segment in work.groupby(np.where(work[feature] >= cut, "HIGH_VOL", "LOW_VOL")):
        if len(segment) >= MIN_GROUP * 2:
            rows.append(_stats(feature, f"{name}_REGIME", "ABOVE_MEDIAN", segment["R_multiple"], work.loc[work.index.difference(segment.index), "R_multiple"]))
    return rows


def _negative_tests(work, feature):
    rows = []
    values = work["R_multiple"].astype(float)
    if len(values) >= MIN_GROUP:
        cutoff = values.abs().quantile(.95)
        trimmed = work.loc[values.abs() <= cutoff].copy()
        original_difference = _median_split_difference(work, feature)
        trimmed_difference = _median_split_difference(trimmed, feature)
        rows.append({"feature": feature, "test": "REMOVE_TOP_5_PERCENT_ABS_R", "sample_size": len(trimmed), "avg_R": trimmed_difference, "original_avg_R": original_difference, "difference": trimmed_difference - original_difference if pd.notna(trimmed_difference) and pd.notna(original_difference) else None, "result": "SURVIVES" if pd.notna(trimmed_difference) and pd.notna(original_difference) and np.sign(trimmed_difference) == np.sign(original_difference) else "DISAPPEARS", "confidence": "Descriptive"})
    yearly_differences = []
    for _, segment in work.groupby("_year", dropna=True):
        if len(segment) >= MIN_GROUP * 2:
            difference = _median_split_difference(segment, feature)
            if pd.notna(difference):
                yearly_differences.append(difference)
    rows.append({"feature": feature, "test": "YEAR_SIGN_CONSISTENCY", "sample_size": len(yearly_differences), "avg_R": float(np.mean(yearly_differences)) if yearly_differences else None, "original_avg_R": _median_split_difference(work, feature), "difference": None, "result": "SURVIVES" if yearly_differences and (np.array(yearly_differences) > 0).mean() >= .75 else "FAILS", "confidence": "Descriptive"})
    return rows


def _median_split_difference(work, feature):
    if len(work) < MIN_GROUP * 2:
        return np.nan
    cut = work[feature].median()
    high = work.loc[work[feature] >= cut, "R_multiple"]
    low = work.loc[work[feature] < cut, "R_multiple"]
    return high.mean() - low.mean() if len(high) and len(low) else np.nan


def _stats(feature, segment, bucket, selected, remainder):
    selected = pd.to_numeric(selected, errors="coerce").dropna().astype(float)
    remainder = pd.to_numeric(remainder, errors="coerce").dropna().astype(float)
    low, high = _bootstrap(selected)
    d = _cohens_d(selected, remainder)
    return {"feature": feature, "segment": segment, "bucket": bucket, "trade_count": len(selected), "winner_count": int((selected > 0).sum()), "loser_count": int((selected < 0).sum()), "win_rate": (selected > 0).mean() * 100 if len(selected) else None, "avg_R": selected.mean() if len(selected) else None, "median_R": selected.median() if len(selected) else None, "expectancy": selected.mean() if len(selected) else None, "profit_factor": _pf(selected), "bootstrap_ci_low": low, "bootstrap_ci_high": high, "mann_whitney_p_value": _mw(selected, remainder), "cohens_d": d, "effect_size": _effect(d), "missing_pct": None, "sample_sufficient": len(selected) >= MIN_GROUP and len(remainder) >= MIN_GROUP}


def _summary(features, buckets, validation, stability):
    rows = []
    for feature in features:
        if feature not in set(buckets.get("feature", [])):
            rows.append({"feature": feature, "top20_avg_R": None, "bottom20_avg_R": None, "difference": None, "years_tested": 0, "positive_years": 0, "outlier_test": "Unavailable", "conclusion": "Unavailable"})
            continue
        top = buckets[(buckets.feature == feature) & (buckets.bucket == "TOP_20")]
        bottom = buckets[(buckets.feature == feature) & (buckets.bucket == "LOWEST_20")]
        top_r = top.avg_R.iloc[0] if not top.empty else np.nan
        bottom_r = bottom.avg_R.iloc[0] if not bottom.empty else np.nan
        years = validation[(validation.feature == feature) & validation.segment.astype(str).str.startswith("YEAR_")]
        tests = stability[stability.feature == feature]
        surviving = (tests.result == "SURVIVES").all() if not tests.empty else False
        rows.append({"feature": feature, "top20_avg_R": top_r, "bottom20_avg_R": bottom_r, "difference": top_r-bottom_r if pd.notna(top_r) and pd.notna(bottom_r) else np.nan, "years_tested": len(years), "positive_years": int((pd.to_numeric(years.avg_R, errors="coerce") > 0).sum()) if not years.empty else 0, "outlier_test": "SURVIVES" if surviving else "FAILS_OR_INSUFFICIENT", "conclusion": "Rejected" if not surviving or pd.isna(top_r) or pd.isna(bottom_r) else "Requires More Data"})
    return pd.DataFrame(rows)


def _pf(v):
    p, l = float(v[v > 0].sum()), abs(float(v[v < 0].sum()))
    return p/l if l else (math.inf if p else 0.0)


def _cohens_d(a, b):
    if len(a) < MIN_GROUP or len(b) < MIN_GROUP: return None
    pooled = math.sqrt(((len(a)-1)*a.var(ddof=1)+(len(b)-1)*b.var(ddof=1))/(len(a)+len(b)-2))
    return (a.mean()-b.mean())/pooled if pooled else 0.0


def _mw(a, b):
    if len(a) < MIN_GROUP or len(b) < MIN_GROUP: return None
    c = pd.concat([a,b], ignore_index=True); r = c.rank(method="average"); n1,n2=len(a),len(b); u=r.iloc[:n1].sum()-n1*(n1+1)/2; ties=c.value_counts(); var=n1*n2/12*((n1+n2+1)-float((ties**3-ties).sum())/((n1+n2)*(n1+n2-1)))
    return math.erfc(abs((u-n1*n2/2)/math.sqrt(var))/math.sqrt(2)) if var > 0 else 1.0


def _bootstrap(v):
    if len(v) < MIN_GROUP: return None,None
    rng=np.random.default_rng(SEED); s=rng.choice(v.to_numpy(), size=(BOOTSTRAPS,len(v)), replace=True).mean(axis=1)
    return float(np.quantile(s,.025)),float(np.quantile(s,.975))


def _effect(d):
    if d is None: return "Insufficient Sample"
    d=abs(d); return "Large" if d>=.8 else "Medium" if d>=.5 else "Small" if d>=.2 else "Negligible"


def _report(path, source, features, summary, validation, stability):
    unavailable = [x for x in features if x not in set(summary.feature)]
    lines=["# Breakout / Volatility Expansion Audit","",f"Source: `{source}`","","This audit attempts to disprove the hypothesis. It does not modify strategy logic or recommend a feature.","","Hypothesis: Volatility expansion / breakout provides predictive information for future trade quality.","","## Summary","",summary.to_string(index=False),"","## Adversarial Tests","",stability.to_string(index=False) if not stability.empty else "No sufficient tests.","","## Limitations","","- Missing features are not reconstructed from future or external data.","- Missing percentage is unavailable for fields not present in the journal.","- P-values are approximate Mann-Whitney tests and multiple comparisons require caution.","- No feature is recommended for strategy inclusion by this study."]
    if unavailable: lines.insert(-4,"Unavailable features: "+", ".join(unavailable))
    path.write_text("\n".join(lines),encoding="utf-8")


if __name__ == "__main__": main()
