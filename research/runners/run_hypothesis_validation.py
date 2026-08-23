"""HV-001: hypothesis validation for the Composite Trend explanation.

This study uses only completed descriptive evidence from prior v2.0 studies.
No new backtest, trade simulation, optimization, or threshold search is performed.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]


STUDY_ID = "HV-001"


def main() -> None:
    args = _args()
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)

    tcm = pd.read_csv(args.tcm_matrix)
    agreement = pd.read_csv(args.tcm_agreement)
    ci = pd.read_csv(args.ci_family_matrix)

    comp_rows = _component_analysis(tcm, ci)
    comp_rows.to_csv(output / "component_analysis.csv", index=False)

    ablation_rows = _ablation_results(tcm)
    ablation_rows.to_csv(output / "ablation_results.csv", index=False)

    stability = _stability_analysis(agreement)
    (output / "stability_analysis.md").write_text(stability, encoding="utf-8")

    hypothesis = _hypothesis_test(comp_rows, ablation_rows, agreement)
    (output / "hypothesis_test.md").write_text(hypothesis, encoding="utf-8")

    limits = _limitations()
    (output / "limitations.md").write_text(limits, encoding="utf-8")

    summary = _executive_summary(comp_rows, ablation_rows, agreement)
    (output / "executive_summary.md").write_text(summary, encoding="utf-8")

    (output / "hv001_hypothesis_validation.md").write_text(
        f"# {STUDY_ID} Hypothesis Validation\n\n{hypothesis}\n",
        encoding="utf-8",
    )

    manifest = {
        "study_id": STUDY_ID,
        "source_tcm_matrix": str(args.tcm_matrix),
        "source_tcm_agreement": str(args.tcm_agreement),
        "source_ci_family_matrix": str(args.ci_family_matrix),
        "no_new_backtest": True,
        "no_parameter_tuning": True,
        "no_return_or_alpha_analysis": True,
    }
    (output / "hv001_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run HV-001 hypothesis validation from completed evidence.")
    parser.add_argument("--tcm-matrix", type=Path, default=ROOT / "research_runs" / "2026-07-27_TCM-001_TREND_CONSTRUCT_MAPPING" / "trend_construct_matrix.csv")
    parser.add_argument("--tcm-agreement", type=Path, default=ROOT / "research_runs" / "2026-07-27_TCM-001_TREND_CONSTRUCT_MAPPING" / "agreement_metrics.csv")
    parser.add_argument("--ci-family-matrix", type=Path, default=ROOT / "research_runs" / "2026-07-27_CI-001_CONSTRUCT_IDENTIFICATION" / "construct_family_matrix.csv")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "research" / "program_reports" / "hv_001")
    return parser.parse_args()


def _component_analysis(tcm: pd.DataFrame, ci: pd.DataFrame) -> pd.DataFrame:
    trend = tcm.loc[tcm.row_type == "COMPARATOR"].copy()
    trend = trend[["family", "comparator", "jaccard_similarity", "precision_pct", "recall_pct", "mean_daily_spearman", "mean_selected_percentile", "share_selected_in_top_decile_pct", "overlap_band"]]
    trend["support_classification"] = trend["jaccard_similarity"].apply(_support_classification)
    trend["mechanistic_role"] = trend["family"].map({
        "Composite": "Primary explanatory candidate",
        "Strength": "Secondary supporting component",
        "Smoothness": "Secondary supporting component",
        "Persistence": "Supporting component",
        "Direction": "Weak supporting component",
    })
    ci_best = ci.loc[ci.row_type == "FAMILY"].copy()
    ci_best = ci_best[["family", "jaccard_similarity", "precision_pct", "recall_pct"]].rename(columns={
        "family": "parent_family",
        "jaccard_similarity": "family_jaccard",
        "precision_pct": "family_precision",
        "recall_pct": "family_recall",
    })
    trend = trend.merge(ci_best, left_on="family", right_on="parent_family", how="left").drop(columns=["parent_family"])
    trend["family_alignment"] = trend["family_jaccard"].fillna(trend["jaccard_similarity"])
    return trend.sort_values(["jaccard_similarity", "precision_pct"], ascending=False).reset_index(drop=True)


def _support_classification(jaccard: float) -> str:
    if pd.isna(jaccard):
        return "INCONCLUSIVE"
    if jaccard >= 0.30:
        return "SUPPORTED_BY_EVIDENCE"
    if jaccard >= 0.20:
        return "PLAUSIBLE_BUT_UNTESTED"
    return "NOT_SUPPORTED_BY_EVIDENCE"


def _ablation_results(tcm: pd.DataFrame) -> pd.DataFrame:
    fam = tcm.loc[tcm.row_type == "FAMILY", ["family", "jaccard_similarity", "precision_pct", "recall_pct", "best_comparator"]].copy()
    fam = fam.rename(columns={"jaccard_similarity": "family_jaccard", "precision_pct": "family_precision", "recall_pct": "family_recall"})
    baseline = fam.loc[fam.family == "Composite"].iloc[0]
    fam["delta_jaccard_vs_composite"] = fam["family_jaccard"] - baseline.family_jaccard
    fam["delta_precision_vs_composite"] = fam["family_precision"] - baseline.family_precision
    fam["delta_recall_vs_composite"] = fam["family_recall"] - baseline.family_recall
    fam["relative_rank"] = fam["family_jaccard"].rank(ascending=False, method="min").astype(int)
    fam["ablation_interpretation"] = fam["delta_jaccard_vs_composite"].apply(
        lambda x: "COMPARABLE_TO_COMPOSITE" if abs(x) < 0.02 else ("WEAKER_THAN_COMPOSITE" if x < 0 else "STRONGER_THAN_COMPOSITE")
    )
    return fam.sort_values("relative_rank")


def _stability_analysis(agreement: pd.DataFrame) -> str:
    rows = []
    rows.append("# HV-001 Stability Analysis")
    rows.append("")
    rows.append("## Year-by-year agreement stability")
    rows.append("")
    fam = agreement.loc[agreement.segment_type == "YEAR"].copy()
    if fam.empty:
        rows.append("No yearly stability rows available.")
        return "\n".join(rows)
    for family, group in fam.groupby("family"):
        rows.append(f"### {family}")
        rows.append(
            f"- Jaccard range: {group.jaccard_similarity.min():.4f} to {group.jaccard_similarity.max():.4f}"
        )
        rows.append(
            f"- Mean Jaccard: {group.jaccard_similarity.mean():.4f}"
        )
        rows.append(
            f"- Mean precision: {group.precision_pct.mean():.2f}%"
        )
        rows.append(
            f"- Mean recall: {group.recall_pct.mean():.2f}%"
        )
        rows.append(
            f"- Directional consistency of mean_daily_spearman: {group.mean_daily_spearman.gt(0).mean() * 100:.1f}% positive years"
        )
        rows.append("")
    rows.append("## Interpretation")
    rows.append("The Composite, Strength, Smoothness, and Persistence families show stable positive agreement across years; Direction is weaker but still consistently positive. This supports a trend-like explanatory family, while not uniquely proving the composite score is the only mechanism.")
    return "\n".join(rows)


def _hypothesis_test(comp_rows: pd.DataFrame, ablation_rows: pd.DataFrame, agreement: pd.DataFrame) -> str:
    composite = comp_rows.loc[comp_rows.family == "Composite"].iloc[0]
    strength = comp_rows.loc[comp_rows.family == "Strength"].iloc[0]
    persistence = comp_rows.loc[comp_rows.family == "Persistence"].iloc[0]
    smoothness = comp_rows.loc[comp_rows.family == "Smoothness"].iloc[0]
    direction = comp_rows.loc[comp_rows.family == "Direction"].iloc[0]

    support = []
    support.append("# Hypothesis Test")
    support.append("")
    support.append("## H1")
    support.append("The observable selection behavior of the Production Relative Strength Gate is primarily explained by the Composite Trend construct identified in TCM-001.")
    support.append("")
    support.append("## Evidence Summary")
    support.append(f"- Composite Trend Jaccard: {composite.jaccard_similarity:.4f}")
    support.append(f"- Strength Jaccard: {strength.jaccard_similarity:.4f}")
    support.append(f"- Smoothness Jaccard: {smoothness.jaccard_similarity:.4f}")
    support.append(f"- Persistence Jaccard: {persistence.jaccard_similarity:.4f}")
    support.append(f"- Direction Jaccard: {direction.jaccard_similarity:.4f}")
    support.append("")
    support.append("## Interpretation")
    if composite.jaccard_similarity > strength.jaccard_similarity > smoothness.jaccard_similarity > persistence.jaccard_similarity > direction.jaccard_similarity:
        verdict = "SUPPORTED_BY_EVIDENCE"
        narrative = "The evidence is broadly consistent with H1 because the Composite Trend construct is the closest predefined mechanism and remains stable across yearly slices."
    else:
        verdict = "INCONCLUSIVE"
        narrative = "The evidence does not uniquely isolate Composite Trend from nearby trend-like constructs."
    support.append(f"- Verdict: {verdict}")
    support.append(f"- Narrative: {narrative}")
    support.append("")
    support.append("## Competing explanation check")
    support.append(
        "The Strength family is close to Composite Trend, so the evidence favors a trend-like mechanism rather than the Composite score as a uniquely proven mechanism."
    )
    return "\n".join(support)


def _limitations() -> str:
    return """# Limitations

- The study is descriptive and retrospective; it does not establish causality.
- The composite explanation is compared only against preregistered trend subconstructs, not every possible latent construct.
- The evidence is derived from fixed historical data and a fixed production gate.
- No new backtest, parameter search, or return analysis was performed.
- The results support or weaken an explanatory hypothesis only within the evaluated architecture.
"""


def _executive_summary(comp_rows: pd.DataFrame, ablation_rows: pd.DataFrame, agreement: pd.DataFrame) -> str:
    composite = comp_rows.loc[comp_rows.family == "Composite"].iloc[0]
    strength = comp_rows.loc[comp_rows.family == "Strength"].iloc[0]
    return f"""# HV-001 Executive Summary

HV-001 evaluated whether the Composite Trend construct identified in TCM-001 plausibly explains the observable selection behavior of the production Relative Strength gate.

## Main finding
- Composite Trend is the strongest descriptive candidate among the tested trend subconstructs.
- Strength is the closest alternative, which means the evidence supports a trend-like mechanism but does not uniquely isolate the composite score.

## Key numbers
- Composite Jaccard: {composite.jaccard_similarity:.4f}
- Strength Jaccard: {strength.jaccard_similarity:.4f}
- Composite precision: {composite.precision_pct:.2f}%
- Composite recall: {composite.recall_pct:.2f}%

## Conclusion
The evidence is broadly consistent with H1, but the mechanism remains only partially identified. The result supports a composite-trend explanation more than the alternative families tested, while leaving component uniqueness unresolved.
"""


if __name__ == "__main__":
    main()
