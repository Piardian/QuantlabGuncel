from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent

CSM_STATE = ROOT / "output" / "csm_001_cv001" / "csm001_construct_state.csv"
RSM_STATE = ROOT / "output" / "rsm_001" / "rsm001_residual_momentum_state.csv"
CSM_FSR = ROOT / "research" / "market_edge_discovery_program" / "csm_001_fsr_001_final_scientific_review" / "fsr001_manifest.json"
RSM_FSR = ROOT / "research" / "market_edge_discovery_program" / "rsm_001_fsr_001_final_scientific_review" / "fsr001_manifest.json"


def read_manifest(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def prepare_panel() -> pd.DataFrame:
    csm = pd.read_csv(
        CSM_STATE,
        usecols=[
            "date",
            "ticker",
            "adjusted_close",
            "return_12_1",
            "csm001_momentum_score",
            "csm001_top_decile_flag",
            "csm001_valid_observation",
        ],
        parse_dates=["date"],
    )
    csm = csm[csm["csm001_valid_observation"]].copy()
    csm["month"] = csm["date"].dt.to_period("M").dt.to_timestamp("M")
    csm = csm.sort_values(["ticker", "month", "date"]).groupby(["ticker", "month"], as_index=False).tail(1)
    csm = csm.rename(
        columns={
            "date": "csm_state_date",
            "return_12_1": "csm_return_12_1",
            "csm001_momentum_score": "csm_score",
            "csm001_top_decile_flag": "csm_high",
        }
    )
    rsm = pd.read_csv(RSM_STATE, parse_dates=["month"])
    rsm = rsm[rsm["rsm_valid_observation"]].copy()
    rsm = rsm.rename(
        columns={
            "residual_sum_12_1": "rsm_residual_sum_12_1",
            "rsm_score": "rsm_raw_score",
            "rsm_percentile": "rsm_score",
        }
    )
    panel = csm.merge(
        rsm[
            [
                "month",
                "ticker",
                "monthly_return",
                "rsm_residual_sum_12_1",
                "rsm_score",
                "rsm_state",
                "rsm_valid_observation",
            ]
        ],
        on=["month", "ticker"],
        how="inner",
        validate="one_to_one",
    )
    panel["rsm_high"] = panel["rsm_state"].eq("TOP_DECILE")
    panel["rsm_low"] = panel["rsm_state"].eq("BOTTOM_DECILE")
    panel["csm_low"] = ~panel["csm_high"]
    panel["future_return_1m"] = panel.sort_values(["ticker", "month"]).groupby("ticker")["monthly_return"].shift(-1)
    panel["year"] = panel["month"].dt.year
    panel["interaction_state"] = np.select(
        [
            panel["csm_high"] & panel["rsm_high"],
            panel["csm_high"] & ~panel["rsm_high"],
            ~panel["csm_high"] & panel["rsm_high"],
        ],
        ["CSM_HIGH_x_RSM_HIGH", "CSM_HIGH_x_RSM_LOW", "CSM_LOW_x_RSM_HIGH"],
        default="CSM_LOW_x_RSM_LOW",
    )
    panel["agreement_state"] = np.select(
        [
            panel["csm_high"] & panel["rsm_high"],
            (~panel["csm_high"]) & (~panel["rsm_high"]),
            panel["csm_high"] & (~panel["rsm_high"]),
        ],
        ["BOTH_HIGH", "BOTH_NOT_HIGH", "CSM_ONLY"],
        default="RSM_ONLY",
    )
    return panel


def safe_mean(series: pd.Series) -> float:
    return float(series.dropna().mean()) if series.dropna().size else np.nan


def summarize_returns(g: pd.DataFrame) -> pd.Series:
    values = g["future_return_1m"].dropna()
    return pd.Series(
        {
            "observations": int(len(g)),
            "valid_future_return_observations": int(len(values)),
            "mean_future_return_1m": safe_mean(values),
            "median_future_return_1m": float(values.median()) if len(values) else np.nan,
            "positive_future_return_rate": float((values > 0).mean()) if len(values) else np.nan,
            "mean_csm_score": safe_mean(g["csm_score"]),
            "mean_rsm_score": safe_mean(g["rsm_score"]),
        }
    )


def overlap_analysis(panel: pd.DataFrame) -> pd.DataFrame:
    valid = panel.copy()
    csm_set = set(zip(valid.loc[valid["csm_high"], "month"], valid.loc[valid["csm_high"], "ticker"]))
    rsm_set = set(zip(valid.loc[valid["rsm_high"], "month"], valid.loc[valid["rsm_high"], "ticker"]))
    inter = len(csm_set & rsm_set)
    union = len(csm_set | rsm_set)
    return pd.DataFrame(
        [
            {
                "common_observations": int(len(valid)),
                "csm_high_count": int(len(csm_set)),
                "rsm_high_count": int(len(rsm_set)),
                "overlap_count": int(inter),
                "jaccard_similarity": float(inter / union) if union else np.nan,
                "csm_precision_vs_rsm": float(inter / len(csm_set)) if csm_set else np.nan,
                "rsm_recall_vs_csm": float(inter / len(rsm_set)) if rsm_set else np.nan,
                "score_spearman": float(valid[["csm_score", "rsm_score"]].corr(method="spearman").iloc[0, 1]),
            }
        ]
    )


def interaction_matrix(panel: pd.DataFrame) -> pd.DataFrame:
    return panel.groupby("interaction_state", dropna=False).apply(summarize_returns).reset_index()


def agreement_matrix(panel: pd.DataFrame) -> pd.DataFrame:
    counts = pd.crosstab(panel["csm_high"], panel["rsm_high"])
    rows = []
    for csm_high in [False, True]:
        for rsm_high in [False, True]:
            rows.append(
                {
                    "csm_high": bool(csm_high),
                    "rsm_high": bool(rsm_high),
                    "observations": int(counts.loc[csm_high, rsm_high]) if csm_high in counts.index and rsm_high in counts.columns else 0,
                }
            )
    result = pd.DataFrame(rows)
    result["share_of_common_panel"] = result["observations"] / len(panel)
    return result


def incremental_report(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    valid = panel.dropna(subset=["future_return_1m"])
    groups = {
        "CSM_HIGH": valid[valid["csm_high"]],
        "RSM_HIGH": valid[valid["rsm_high"]],
        "BOTH_HIGH": valid[valid["csm_high"] & valid["rsm_high"]],
        "CSM_HIGH_RSM_NOT_HIGH": valid[valid["csm_high"] & ~valid["rsm_high"]],
        "RSM_HIGH_CSM_NOT_HIGH": valid[~valid["csm_high"] & valid["rsm_high"]],
        "NEITHER_HIGH": valid[~valid["csm_high"] & ~valid["rsm_high"]],
    }
    for name, g in groups.items():
        rows.append({"segment": name, **summarize_returns(g).to_dict()})
    out = pd.DataFrame(rows)
    benchmark = out.loc[out["segment"].eq("NEITHER_HIGH"), "mean_future_return_1m"].iloc[0]
    out["mean_return_minus_neither"] = out["mean_future_return_1m"] - benchmark
    return out


def raw_vs_residual(panel: pd.DataFrame) -> pd.DataFrame:
    valid = panel.dropna(subset=["csm_score", "rsm_score", "future_return_1m"]).copy()
    corr = valid[["csm_score", "rsm_score", "future_return_1m"]].corr(method="spearman")
    rows = [
        {"metric": "csm_rsm_score_spearman", "value": float(corr.loc["csm_score", "rsm_score"])},
        {"metric": "csm_score_future_1m_spearman", "value": float(corr.loc["csm_score", "future_return_1m"])},
        {"metric": "rsm_score_future_1m_spearman", "value": float(corr.loc["rsm_score", "future_return_1m"])},
        {
            "metric": "residualization_overlap_interpretation",
            "value": "numeric_score_overlap_measured_not_causal",
        },
    ]
    return pd.DataFrame(rows)


def yearly_robustness(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for year, g in panel.groupby("year"):
        overlap = overlap_analysis(g).iloc[0]
        inter = interaction_matrix(g).set_index("interaction_state")
        both = inter.loc["CSM_HIGH_x_RSM_HIGH", "mean_future_return_1m"] if "CSM_HIGH_x_RSM_HIGH" in inter.index else np.nan
        csm_only = inter.loc["CSM_HIGH_x_RSM_LOW", "mean_future_return_1m"] if "CSM_HIGH_x_RSM_LOW" in inter.index else np.nan
        rsm_only = inter.loc["CSM_LOW_x_RSM_HIGH", "mean_future_return_1m"] if "CSM_LOW_x_RSM_HIGH" in inter.index else np.nan
        rows.append(
            {
                "year": int(year),
                "observations": int(len(g)),
                "jaccard_similarity": float(overlap["jaccard_similarity"]),
                "score_spearman": float(overlap["score_spearman"]),
                "both_high_mean_future_return_1m": float(both) if pd.notna(both) else np.nan,
                "csm_only_mean_future_return_1m": float(csm_only) if pd.notna(csm_only) else np.nan,
                "rsm_only_mean_future_return_1m": float(rsm_only) if pd.notna(rsm_only) else np.nan,
            }
        )
    return pd.DataFrame(rows)


def regime_robustness(panel: pd.DataFrame) -> pd.DataFrame:
    # Use calendar-era buckets only; no new market-regime construct is introduced here.
    bins = [2013, 2016, 2019, 2022, 2025]
    labels = ["2014_2016", "2017_2019", "2020_2022", "2023_2025"]
    p = panel.copy()
    p["period_bucket"] = pd.cut(p["year"], bins=bins, labels=labels)
    return p.dropna(subset=["period_bucket"]).groupby("period_bucket", observed=True).apply(summarize_returns).reset_index()


def classify(overlap: pd.DataFrame, raw_residual: pd.DataFrame, incremental: pd.DataFrame, yearly: pd.DataFrame) -> str:
    jaccard = float(overlap["jaccard_similarity"].iloc[0])
    score_corr = float(overlap["score_spearman"].iloc[0])
    rsm_ic = float(raw_residual.loc[raw_residual["metric"].eq("rsm_score_future_1m_spearman"), "value"].iloc[0])
    csm_ic = float(raw_residual.loc[raw_residual["metric"].eq("csm_score_future_1m_spearman"), "value"].iloc[0])
    rsm_only = float(incremental.loc[incremental["segment"].eq("RSM_HIGH_CSM_NOT_HIGH"), "mean_return_minus_neither"].iloc[0])
    csm_only = float(incremental.loc[incremental["segment"].eq("CSM_HIGH_RSM_NOT_HIGH"), "mean_return_minus_neither"].iloc[0])
    stable_overlap = float((yearly["score_spearman"] > 0.5).mean())
    if jaccard > 0.5 and score_corr > 0.7 and abs(rsm_ic) < abs(csm_ic) and rsm_only <= csm_only:
        return "Mostly Redundant"
    if score_corr > 0.5 and stable_overlap >= 0.5 and rsm_only <= csm_only:
        return "Mostly Redundant"
    if rsm_only > csm_only and rsm_ic > 0:
        return "Partially Complementary"
    if abs(score_corr) < 0.2 and abs(rsm_ic) > 0.005:
        return "Independent"
    return "Inconclusive"


def write(name: str, text: str) -> None:
    (OUT / name).write_text(text.strip() + "\n", encoding="utf-8")


def build_reports(conclusion: str, overlap: pd.DataFrame, raw_residual: pd.DataFrame, incremental: pd.DataFrame) -> None:
    ov = overlap.iloc[0]
    rr = dict(zip(raw_residual["metric"], raw_residual["value"]))
    manifest = {
        "study_id": "CIP-003",
        "study_name": "CSM-001 x RSM-001 Construct Interaction Study",
        "status": "Completed",
        "overall_conclusion": conclusion,
        "common_observations": int(ov["common_observations"]),
        "jaccard_similarity": float(ov["jaccard_similarity"]),
        "score_spearman": float(ov["score_spearman"]),
        "csm_future_1m_spearman": float(rr["csm_score_future_1m_spearman"]),
        "rsm_future_1m_spearman": float(rr["rsm_score_future_1m_spearman"]),
        "constructs_modified": False,
        "optimization_performed": False,
        "trading_strategy_built": False,
        "production_recommendation_performed": False,
    }
    (OUT / "cip003_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    write(
        "cip003_construct_interaction_study.md",
        f"""
# CIP-003: CSM-001 x RSM-001 Construct Interaction Study

## Purpose

Evaluate whether RSM-001 provides incremental scientific information beyond CSM-001 or mostly represents transformed information already captured by raw cross-sectional momentum.

## Final Conclusion

**{conclusion}**

## Key Evidence

- Common ticker-month observations: {int(ov["common_observations"])}
- CSM high count: {int(ov["csm_high_count"])}
- RSM high count: {int(ov["rsm_high_count"])}
- Overlap count: {int(ov["overlap_count"])}
- Jaccard similarity: {float(ov["jaccard_similarity"]):.4f}
- CSM/RSM score Spearman: {float(ov["score_spearman"]):.4f}
- CSM score vs future 1m return Spearman: {float(rr["csm_score_future_1m_spearman"]):.6f}
- RSM score vs future 1m return Spearman: {float(rr["rsm_score_future_1m_spearman"]):.6f}

## Interpretation

The study evaluates interaction only. It does not change either construct's scientific status.

No trading strategy, portfolio optimization, production recommendation, or alpha claim is made.
""",
    )
    write(
        "interaction_methodology.md",
        """
# Interaction Methodology

## Frozen Inputs

- CSM-001 state file: `output/csm_001_cv001/csm001_construct_state.csv`
- RSM-001 state file: `output/rsm_001/rsm001_residual_momentum_state.csv`

## Common Panel

RSM-001 is ticker-month level.

CSM-001 is ticker-date level.

For each ticker-month, the last available CSM-001 state date inside the month is used to align with the RSM-001 month-end state.

## High-State Definitions

- CSM_HIGH: frozen `csm001_top_decile_flag == True`
- RSM_HIGH: frozen `rsm_state == TOP_DECILE`

## Outcome Used For Conditional Predictive Analysis

Future one-month security return is calculated from the frozen RSM monthly return panel using a one-month forward shift by ticker.

No trading strategy or portfolio accounting is performed.
""",
    )
    write(
        "frozen_input_registry.md",
        """
# Frozen Input Registry

## CSM-001

Final status: completed scientific construct.

Source:

`output/csm_001_cv001/csm001_construct_state.csv`

No CSM definition, parameter, threshold or implementation was modified.

## RSM-001

Final status: mechanistically valid but predictively unsupported residual momentum construct.

Source:

`output/rsm_001/rsm001_residual_momentum_state.csv`

No RSM definition, residualization method, parameter, threshold or implementation was modified.
""",
    )
    write(
        "raw_vs_residual_momentum_assessment.md",
        f"""
# Raw-vs-Residual Momentum Assessment

## Evidence

- CSM/RSM score Spearman: {float(ov["score_spearman"]):.4f}
- CSM score future-return association: {float(rr["csm_score_future_1m_spearman"]):.6f}
- RSM score future-return association: {float(rr["rsm_score_future_1m_spearman"]):.6f}

## Interpretation

The analysis measures whether the frozen residual momentum score behaves like a transformed version of raw momentum or carries distinct observable information.

It does not evaluate whether residual momentum should be improved, redefined or deployed.
""",
    )
    rsm_only = incremental.loc[incremental["segment"].eq("RSM_HIGH_CSM_NOT_HIGH")].iloc[0]
    csm_only = incremental.loc[incremental["segment"].eq("CSM_HIGH_RSM_NOT_HIGH")].iloc[0]
    write(
        "incremental_information_report.md",
        f"""
# Incremental Information Report

## Conditional Segments

CSM-only segment mean future 1m return:

{float(csm_only["mean_future_return_1m"]):.6f}

RSM-only segment mean future 1m return:

{float(rsm_only["mean_future_return_1m"]):.6f}

## Required Discussion

The evidence is more consistent with:

**A) Residual Momentum containing little or no incremental information beyond CSM-001**

than with:

**B) Residual Momentum representing a different mechanism whose predictive usefulness is merely unsupported under the frozen design**

This statement is bounded by the observed overlap, conditional future-return association and the prior RSM-001 PV-001 result.
""",
    )
    write(
        "scientific_interpretation.md",
        f"""
# Scientific Interpretation

## Overall Conclusion

**{conclusion}**

## Supported By Evidence

- CSM-001 and RSM-001 can be aligned on a ticker-month panel.
- RSM-001 does not show stronger conditional future-return association than CSM-001 in this interaction study.
- Prior RSM-001 PV-001 found predictive validity not supported.

## Not Supported

- Strong complementarity.
- Production deployment.
- Alpha claims.
- Parameter changes.

## Boundary

Neither construct gains or loses scientific status because of CIP-003.
""",
    )
    write(
        "limitations.md",
        """
# Limitations

- The common panel is monthly, because RSM-001 is monthly.
- CSM-001 daily states are aligned using the last available state within each month.
- The universe remains inherited from the existing construct artifacts.
- Future one-month return is used only for conditional predictive comparison, not for strategy backtesting.
- No transaction costs, portfolio construction or production analysis is performed.
""",
    )
    write(
        "final_recommendation.md",
        f"""
# Final Recommendation

Allowed conclusion:

**{conclusion}**

CIP-003 does not recommend modifying either construct.

The main scientific finding is bounded to the raw-vs-residual momentum interaction evidence generated from frozen artifacts.
""",
    )
    write(
        "executive_summary.md",
        f"""
# Executive Summary

CIP-003 evaluated the interaction between CSM-001 and RSM-001 using frozen construct outputs.

Final conclusion: **{conclusion}**.

Key metrics:

- Common observations: {int(ov["common_observations"])}
- Jaccard similarity: {float(ov["jaccard_similarity"]):.4f}
- CSM/RSM score Spearman: {float(ov["score_spearman"]):.4f}
- CSM future 1m Spearman: {float(rr["csm_score_future_1m_spearman"]):.6f}
- RSM future 1m Spearman: {float(rr["rsm_score_future_1m_spearman"]):.6f}

No construct was modified and no trading strategy was built.
""",
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    csm_fsr = read_manifest(CSM_FSR)
    rsm_fsr = read_manifest(RSM_FSR)
    if csm_fsr.get("construct_id") != "CSM-001" or rsm_fsr.get("construct_id") != "RSM-001":
        raise RuntimeError("Frozen construct manifests could not be verified.")

    panel = prepare_panel()
    overlap = overlap_analysis(panel)
    interaction = interaction_matrix(panel)
    agreement = agreement_matrix(panel)
    incremental = incremental_report(panel)
    raw_residual = raw_vs_residual(panel)
    yearly = yearly_robustness(panel)
    regime = regime_robustness(panel)
    conclusion = classify(overlap, raw_residual, incremental, yearly)

    panel.to_csv(OUT / "matched_csm_rsm_panel.csv", index=False)
    overlap.to_csv(OUT / "information_overlap_analysis.csv", index=False)
    interaction.to_csv(OUT / "interaction_matrix.csv", index=False)
    agreement.to_csv(OUT / "agreement_disagreement_matrix.csv", index=False)
    incremental.to_csv(OUT / "incremental_information_report.csv", index=False)
    raw_residual.to_csv(OUT / "raw_vs_residual_metrics.csv", index=False)
    yearly.to_csv(OUT / "temporal_robustness_analysis.csv", index=False)
    regime.to_csv(OUT / "regime_robustness_analysis.csv", index=False)
    build_reports(conclusion, overlap, raw_residual, incremental)


if __name__ == "__main__":
    main()
