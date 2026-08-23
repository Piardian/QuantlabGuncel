"""RC-D1 reproducibility comparison of RC-C1 and a disjoint production OOS population."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

FEATURES = [
    "rs20", "rs60", "rs120", "leadership_quality", "distance_above_ema200",
    "ema200_slope", "distance_above_ema50", "atr_expansion_magnitude",
    "breakout_distance", "entry_atr", "entry_price", "initial_risk", "position_size",
]


def main() -> None:
    args = _args()
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    c1 = pd.read_csv(args.c1_dir / "entry_feature_correlations.csv").set_index("feature")
    oos = pd.read_csv(args.oos_dir / "entry_feature_correlations.csv").set_index("feature")
    comparison = _compare(c1.loc[FEATURES], oos.loc[FEATURES])
    comparison.to_csv(output / "feature_reproducibility.csv", index=False)
    oos.reset_index().to_csv(output / "feature_oos_correlations.csv", index=False)

    yearly = _yearly(args.c1_dir, args.oos_dir, c1)
    yearly.to_csv(output / "yearly_reproducibility.csv", index=False)
    symbols = _symbols(args.c1_dir, args.oos_dir)
    symbols.to_csv(output / "symbol_reproducibility.csv", index=False)
    summary = _summary(comparison, yearly, symbols)
    pd.DataFrame([summary]).to_csv(output / "reproducibility_summary.csv", index=False)
    (output / "reproducibility_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    _report(output / "oos_reproducibility_audit.md", comparison, summary)


def _compare(c1, oos):
    rows = []
    for feature in c1.index:
        train, test = c1.loc[feature], oos.loc[feature]
        train_r, test_r = train.correlation_with_R, test.correlation_with_R
        train_strength, test_strength = train.association_strength_R, test.association_strength_R
        if not bool(train.feature_has_variation) or not bool(test.feature_has_variation):
            status = "Inconclusive"
        elif train_strength == "NONE":
            status = "Inconclusive"
        elif test_strength == "NONE" or _sign(train_r) != _sign(test_r):
            status = "Not Reproduced"
        elif train_strength == test_strength:
            status = "Reproduced"
        else:
            status = "Partially Reproduced"
        rows.append({
            "feature": feature, "c1_correlation_with_R": train_r, "oos_correlation_with_R": test_r,
            "c1_correlation_with_win": train.correlation_with_win, "oos_correlation_with_win": test.correlation_with_win,
            "direction_agreement": _sign(train_r) == _sign(test_r) if pd.notna(train_r) and pd.notna(test_r) else None,
            "magnitude_agreement": train_strength == test_strength,
            "c1_strength": train_strength, "oos_strength": test_strength, "classification": status,
        })
    return pd.DataFrame(rows)


def _yearly(c1_dir, oos_dir, c1):
    oos = pd.read_csv(oos_dir / "entry_feature_yearly.csv")
    if oos.empty:
        return pd.DataFrame(columns=["year", "feature", "trade_count", "correlation_with_R", "agreement_with_c1_direction"])
    oos = oos.loc[oos.feature.isin(FEATURES)].copy()
    oos["agreement_with_c1_direction"] = oos.apply(lambda row: _sign(row.correlation_with_R) == _sign(c1.loc[row.feature, "correlation_with_R"]), axis=1)
    return oos


def _symbols(c1_dir, oos_dir):
    oos = pd.read_csv(oos_dir / "entry_feature_symbol.csv")
    if oos.empty:
        return pd.DataFrame(columns=["ticker", "feature", "trade_count", "correlation_with_R", "reproducibility_status"])
    return oos.loc[oos.feature.isin(FEATURES)].assign(reproducibility_status="OOS_SYMBOL_ASSOCIATIONS_AVAILABLE")


def _summary(comparison, yearly, symbols):
    counts = comparison.classification.value_counts().to_dict()
    comparable = comparison.loc[comparison.classification != "Inconclusive"]
    overall = "Inconclusive" if comparable.empty or yearly.year.nunique() < 2 or symbols.empty else "Mixed"
    return {
        "experiment_id": "RC-D1", "classification_counts": counts,
        "direction_agreement_count": int(comparison.direction_agreement.fillna(False).sum()),
        "magnitude_agreement_count": int(comparison.magnitude_agreement.fillna(False).sum()),
        "oos_year_count": int(yearly.year.nunique()) if not yearly.empty else 0,
        "oos_symbol_association_rows": int(len(symbols)),
        "overall_reproducibility_classification": overall,
        "scope": "Observational reproducibility only; no causal contribution, edge creation, or production recommendation is inferred.",
        "limitation": "The OOS period contains one partial calendar year and no symbols with the RC-C1 minimum of 20 OOS trades, so annual repetition and symbol-level reproducibility are insufficient.",
    }


def _sign(value):
    if pd.isna(value) or abs(value) < .01:
        return 0
    return 1 if value > 0 else -1


def _report(path, comparison, summary):
    lines = ["# RC-D1 Out-of-Sample Reproducibility Audit", "", "## Scope", "", "RC-D1 compares observational feature-outcome associations in disjoint production-selected trade populations. Successful reproduction does not establish causality; failure does not prove an original observation false.", "", "## Feature Reproducibility", "", comparison.to_string(index=False), "", "## Summary", "", json.dumps(summary, indent=2)]
    path.write_text("\n".join(lines), encoding="utf-8")


def _args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--c1-dir", type=Path, required=True)
    parser.add_argument("--oos-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


if __name__ == "__main__":
    main()
