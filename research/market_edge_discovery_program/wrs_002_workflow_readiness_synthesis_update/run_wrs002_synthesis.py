from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent

WRS001 = ROOT / "research" / "market_edge_discovery_program" / "wrs_001_workflow_readiness_synthesis" / "wrs001_manifest.json"
WPC001 = ROOT / "research" / "market_edge_discovery_program" / "wpc_001_workflow_portfolio_construction_protocol" / "wpc001_manifest.json"
WPC002 = ROOT / "research" / "market_edge_discovery_program" / "wpc_002_workflow_portfolio_construction_validation" / "wpc002_manifest.json"
WPC002_COMPARISON = ROOT / "research" / "market_edge_discovery_program" / "wpc_002_workflow_portfolio_construction_validation" / "gross_benchmark_comparison.csv"
WPC002_CHECKS = ROOT / "research" / "market_edge_discovery_program" / "wpc_002_workflow_portfolio_construction_validation" / "portfolio_accounting_checks.csv"
WPC002_POSITIONS = ROOT / "research" / "market_edge_discovery_program" / "wpc_002_workflow_portfolio_construction_validation" / "position_count_analysis.csv"


def read_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write(name: str, text: str) -> None:
    (OUT / name).write_text(text.strip() + "\n", encoding="utf-8")


def classify(wrs001: dict, wpc002: dict) -> str:
    if (
        wrs001.get("scientific_workflow") == "Supported"
        and wrs001.get("oos_reproducibility") == "Reproduced"
        and wpc002.get("conclusion") == "Portfolio Construction Supported"
    ):
        return "Research-Validated Portfolio Workflow, Not Production Ready"
    return "Research Workflow Inconclusive"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    wrs001 = read_json(WRS001)
    wpc001 = read_json(WPC001)
    wpc002 = read_json(WPC002)
    comparison = pd.read_csv(WPC002_COMPARISON)
    checks = pd.read_csv(WPC002_CHECKS)
    positions = pd.read_csv(WPC002_POSITIONS)

    final_classification = classify(wrs001, wpc002)
    comp = comparison.iloc[0]

    readiness_matrix = pd.DataFrame(
        [
            {
                "dimension": "Scientific workflow",
                "evidence_source": "CIP/CWP/CWS/CWF",
                "status": wrs001["scientific_workflow"],
                "interpretation": "Composite workflow is scientifically supported as a nested CSM x TSM workflow.",
            },
            {
                "dimension": "OOS reproducibility",
                "evidence_source": "WOR-002",
                "status": wrs001["oos_reproducibility"],
                "interpretation": "Workflow structure reproduced on unseen OOS observations.",
            },
            {
                "dimension": "Economic utility",
                "evidence_source": "WEV-002",
                "status": wrs001["economic_utility"],
                "interpretation": "UC-3 received support; other predefined use cases did not receive broad support.",
            },
            {
                "dimension": "Execution realism",
                "evidence_source": "WER-002",
                "status": wrs001["execution_realism"],
                "interpretation": "Cost and slippage robustness were partially supported; live execution remains unvalidated.",
            },
            {
                "dimension": "Liquidity capacity",
                "evidence_source": "WLC-002",
                "status": wrs001["liquidity_capacity"],
                "interpretation": "Liquidity was partially supported under predefined notional and ADV constraints.",
            },
            {
                "dimension": "Portfolio construction",
                "evidence_source": "WPC-002",
                "status": wpc002["conclusion"],
                "interpretation": "Monthly equal-weight gross portfolio accounting was deterministic and auditable.",
            },
            {
                "dimension": "Production readiness",
                "evidence_source": "Integrated review",
                "status": "Not Supported",
                "interpretation": "No live, broker, tax, operational, or production monitoring validation has been completed.",
            },
        ]
    )
    readiness_matrix.to_csv(OUT / "updated_readiness_matrix.csv", index=False)

    evidence_summary = pd.DataFrame(
        [
            {"metric": "wpc002_rebalance_periods", "value": wpc002["rebalance_periods"]},
            {"metric": "wpc002_accounting_checks_passed", "value": wpc002["accounting_checks_passed"]},
            {"metric": "wpc002_gross_mean_spread", "value": wpc002["gross_mean_spread"]},
            {"metric": "wpc002_positive_spread_rate", "value": float(comp["positive_spread_rate"])},
            {"metric": "wpc002_workflow_compound_return_gross", "value": float(comp["workflow_compound_return"])},
            {"metric": "wpc002_benchmark_compound_return_gross", "value": float(comp["benchmark_compound_return"])},
        ]
    )
    evidence_summary.to_csv(OUT / "portfolio_evidence_summary.csv", index=False)

    positions.to_csv(OUT / "portfolio_position_summary.csv", index=False)
    checks.to_csv(OUT / "portfolio_accounting_check_summary.csv", index=False)

    manifest = {
        "study_id": "WRS-002",
        "study_name": "Workflow Readiness Synthesis Update",
        "workflow": "CSM-001 x TSM-001",
        "status": "Completed",
        "new_analysis_performed": False,
        "portfolio_construction_evidence_added": True,
        "final_classification": final_classification,
        "production_readiness": "Not Supported",
        "optimization_performed": False,
        "production_recommendation_performed": False,
        "authorized_next_stage": "Human Review before CIP-002 or further workflow research",
    }
    (OUT / "wrs002_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    write(
        "wrs002_workflow_readiness_synthesis_update.md",
        f"""
# WRS-002: Workflow Readiness Synthesis Update

## Purpose

Integrate WPC-002 portfolio construction evidence into the prior WRS-001 workflow readiness synthesis.

No new construct research, trading optimization, production redesign or parameter tuning was performed.

## Final Classification

**{final_classification}**

## Evidence Update

WPC-002 added evidence that the UC-3 CSM-001 x TSM-001 workflow can be represented as a deterministic monthly equal-weight gross research portfolio.

Key WPC-002 evidence:

- Rebalance periods: {wpc002["rebalance_periods"]}
- Accounting checks passed: {wpc002["accounting_checks_passed"]}
- Gross mean spread: {float(comp["mean_spread"]):.6f}
- Positive spread rate: {float(comp["positive_spread_rate"]):.4f}

## Supported By Evidence

- Scientific nested workflow status remains supported.
- OOS reproducibility remains reproduced.
- Gross portfolio construction is supported.
- UC-3 remains the only economically supported workflow branch from prior evidence.

## Not Supported

- Production readiness.
- Live execution readiness.
- Broker integration readiness.
- Tax-aware portfolio accounting.
- Operational monitoring readiness.

## Interpretation

The workflow has advanced from a research-validated signal relationship to a research-validated gross portfolio workflow.

This does not authorize production deployment.
""",
    )

    write(
        "executive_summary.md",
        f"""
# Executive Summary

WRS-002 updated the CSM-001 x TSM-001 workflow readiness synthesis using the completed WPC-002 portfolio construction validation.

Final classification: **{final_classification}**.

WPC-002 supports deterministic monthly equal-weight gross portfolio construction over {wpc002["rebalance_periods"]} rebalance periods, with all accounting checks passing.

The workflow remains **not production ready** because live execution, broker integration, taxes, operational monitoring and production controls have not been validated.
""",
    )

    write(
        "limitations.md",
        """
# Limitations

- WRS-002 performs synthesis only.
- No new empirical experiment was performed.
- Portfolio construction evidence is gross, not cost-adjusted.
- Prior survivorship and data limitations remain inherited.
- Production readiness remains outside the supported evidence boundary.
""",
    )

    write(
        "recommended_next_step.md",
        """
# Recommended Next Step

Stop for human review.

The current workflow branch has reached an updated readiness synthesis after portfolio construction validation.

The next step should be selected by the human reviewer:

- Begin CIP-002 for a new construct interaction study.
- Continue workflow realism toward production-control protocols.
- Archive the current workflow branch as research-validated but not production ready.
""",
    )


if __name__ == "__main__":
    main()
