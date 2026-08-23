from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent

ARTIFACTS = [
    ("approved_roadmap", "research/market_edge_discovery_program/roadmap_revision_2026_08_04_v2/roadmap_revision_manifest.json"),
    ("approved_gate_sequence", "research/market_edge_discovery_program/roadmap_revision_2026_08_04_v2/gate_sequence.csv"),
    ("csm_state", "output/csm_001_cv001/csm001_construct_state.csv"),
    ("csm_price_panel", "output/csm_001_cv001/adjusted_close_panel.csv"),
    ("tsm_state", "output/tsm_001_cv001/tsm001_construct_state.csv"),
    ("csm_fsr", "research/market_edge_discovery_program/csm_001_fsr_001_final_scientific_review/fsr001_manifest.json"),
    ("tsm_fsr", "research/market_edge_discovery_program/tsm_001_fsr_001_final_scientific_review/fsr001_manifest.json"),
    ("cip001_manifest", "research/market_edge_discovery_program/cip_001_csm_tsm_construct_interaction_study/cip001_manifest.json"),
    ("cwf001_manifest", "research/market_edge_discovery_program/cwf_001_final_composite_workflow_review/cwf001_manifest.json"),
    ("wor002_manifest", "research/market_edge_discovery_program/wor_002_workflow_oos_reproducibility_audit/wor002_manifest.json"),
    ("wev002_manifest", "research/market_edge_discovery_program/wev_002_workflow_economic_validation/wev002_manifest.json"),
    ("wer002_manifest", "research/market_edge_discovery_program/wer_002_workflow_execution_realism_audit/wer002_manifest.json"),
    ("wlc002_manifest", "research/market_edge_discovery_program/wlc_002_workflow_liquidity_capacity_audit/wlc002_manifest.json"),
    ("wpc002_manifest", "research/market_edge_discovery_program/wpc_002_workflow_portfolio_construction_validation/wpc002_manifest.json"),
    ("wpc002_returns", "research/market_edge_discovery_program/wpc_002_workflow_portfolio_construction_validation/portfolio_return_series.csv"),
    ("wpc002_comparison", "research/market_edge_discovery_program/wpc_002_workflow_portfolio_construction_validation/gross_benchmark_comparison.csv"),
    ("wrs002_manifest", "research/market_edge_discovery_program/wrs_002_workflow_readiness_synthesis_update/wrs002_manifest.json"),
    ("workflow_archive_manifest", "research/market_edge_discovery_program/workflow_branch_archive_csm_tsm/archive_manifest.json"),
]


RESEARCH_STAGES = [
    ("CSM-001", "Completed lifecycle", "Supported edge construct with limitations"),
    ("TSM-001", "Completed lifecycle", "Supported own-trend/state construct"),
    ("CIP-001", "Completed", "CSM x TSM partially complementary"),
    ("CWP-001", "Completed", "Composite workflow protocol registered"),
    ("CWS-001", "Completed", "Workflow supported"),
    ("CWF-001", "Completed", "Scientifically supported nested composite workflow"),
    ("WOR-002", "Completed", "OOS reproduced"),
    ("WEV-002", "Completed", "Economic utility partially supported"),
    ("WER-002", "Completed", "Execution realism partially supported"),
    ("WLC-002", "Completed", "Liquidity/capacity partially supported"),
    ("WPC-002", "Completed", "Gross portfolio construction supported"),
    ("WRS-002", "Completed", "Research-validated portfolio workflow, not production ready"),
    ("CIP-002", "Completed", "CSM x ISM inconclusive due no stock-to-industry bridge"),
    ("SIB-003", "Completed", "Stock-to-industry bridge definition blocked"),
    ("CIP-003", "Completed", "CSM x RSM mostly redundant"),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_hash_inventory() -> pd.DataFrame:
    rows = []
    for label, rel in ARTIFACTS:
        path = ROOT / rel
        rows.append(
            {
                "artifact_label": label,
                "relative_path": rel,
                "exists": path.exists(),
                "size_bytes": path.stat().st_size if path.exists() else None,
                "modified_utc": pd.Timestamp(path.stat().st_mtime, unit="s", tz="UTC").isoformat() if path.exists() else None,
                "sha256": sha256(path) if path.exists() else None,
            }
        )
    return pd.DataFrame(rows)


def build_data_inventory() -> pd.DataFrame:
    rows = []
    for label, rel in ARTIFACTS:
        if label in {"csm_state", "csm_price_panel", "tsm_state", "wpc002_returns", "wpc002_comparison"}:
            path = ROOT / rel
            if path.exists():
                df = pd.read_csv(path, nrows=5)
                rows.append(
                    {
                        "artifact_label": label,
                        "relative_path": rel,
                        "columns": "|".join(df.columns.astype(str)),
                        "sample_rows_loaded": int(len(df)),
                    }
                )
    return pd.DataFrame(rows)


def write(name: str, text: str) -> None:
    (OUT / name).write_text(text.strip() + "\n", encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    hashes = build_hash_inventory()
    data_inventory = build_data_inventory()

    missing = hashes[~hashes["exists"]]
    conclusion = "Baseline Frozen" if missing.empty else "Baseline Frozen With Limitations"

    csm_fsr = load_json(ROOT / "research/market_edge_discovery_program/csm_001_fsr_001_final_scientific_review/fsr001_manifest.json")
    tsm_fsr = load_json(ROOT / "research/market_edge_discovery_program/tsm_001_fsr_001_final_scientific_review/fsr001_manifest.json")
    wpc002 = load_json(ROOT / "research/market_edge_discovery_program/wpc_002_workflow_portfolio_construction_validation/wpc002_manifest.json")
    wrs002 = load_json(ROOT / "research/market_edge_discovery_program/wrs_002_workflow_readiness_synthesis_update/wrs002_manifest.json")

    hashes.to_csv(OUT / "frozen_artifact_hashes.csv", index=False)
    data_inventory.to_csv(OUT / "frozen_data_inventory.csv", index=False)
    pd.DataFrame(RESEARCH_STAGES, columns=["stage", "status", "result"]).to_csv(OUT / "research_ledger.csv", index=False)

    manifest = {
        "study_id": "BFL-001",
        "study_name": "Baseline Freeze & Research Ledger",
        "status": "Completed",
        "conclusion": conclusion,
        "baseline_name": "CSMxTSM_GROSS_RESEARCH_BASELINE_V1",
        "current_classification": "Provisionally research-supported momentum leadership workflow + risk construct library",
        "primary_workflow": "CSM-001 x TSM-001",
        "artifacts_registered": int(len(hashes)),
        "missing_artifacts": int(len(missing)),
        "constructs_modified": False,
        "workflow_modified": False,
        "optimization_performed": False,
        "performance_test_performed": False,
        "production_recommendation_performed": False,
        "authorized_next_stage": "DBA-001 Data & Bias Audit" if missing.empty else "DBA-001 with limitations review",
    }
    (OUT / "bfl001_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    write(
        "bfl001_baseline_freeze.md",
        f"""
# BFL-001: Baseline Freeze & Research Ledger

## Purpose

Freeze the current CSM-001 x TSM-001 research baseline before DBA-001, RVP-001, NOC, benchmark, capacity or production-readiness work.

## Final Conclusion

**{conclusion}**

## Frozen Baseline

`CSMxTSM_GROSS_RESEARCH_BASELINE_V1`

## Current Classification

**Provisionally research-supported momentum leadership workflow + risk construct library**

## Scope Frozen

- CSM-001 frozen construct artifact.
- TSM-001 frozen construct artifact.
- CSM x TSM interaction evidence.
- CSM x TSM workflow evidence.
- WPC-002 monthly equal-weight gross portfolio accounting evidence.
- WRS-002 readiness synthesis.

## Evidence Boundary

This freeze does not claim production readiness.

This freeze does not claim net-of-cost profitability.

This freeze only records the exact baseline carried forward into validation.
""",
    )

    write(
        "frozen_model_specification.md",
        f"""
# Frozen Model Specification

## Baseline Name

`CSMxTSM_GROSS_RESEARCH_BASELINE_V1`

## Primary Workflow

CSM-001 x TSM-001

## CSM-001

Final status:

`{csm_fsr.get("final_status", csm_fsr.get("final_classification", "UNKNOWN"))}`

Role:

Stock-level cross-sectional relative leadership.

Frozen high state:

`csm001_top_decile_flag == True`

## TSM-001

Final status:

`{tsm_fsr.get("final_classification", tsm_fsr.get("final_status", "UNKNOWN"))}`

Role:

Own-trend / positive state gate.

Frozen positive state:

`tsm001_positive_state == True`

## Workflow State

CSM x TSM selected state:

`csm001_top_decile_flag == True AND tsm001_positive_state == True`

## Portfolio Accounting Currently Frozen

WPC-002:

`{wpc002.get("conclusion")}`

Policy:

- monthly rebalance
- equal-weight
- gross accounting only
- no costs
- no production execution

## Workflow Readiness

WRS-002:

`{wrs002.get("final_classification")}`
""",
    )

    write(
        "research_ledger.md",
        """
# Research Ledger

| Stage | Status | Result |
|---|---|---|
"""
        + "\n".join(f"| {stage} | {status} | {result} |" for stage, status, result in RESEARCH_STAGES),
    )

    write(
        "validation_carry_forward_assumptions.md",
        """
# Validation Carry-Forward Assumptions

## Carried Forward

- Current construct artifacts are frozen.
- CSM x TSM remains the primary workflow under validation.
- WPC-002 gross equal-weight monthly accounting is the current portfolio baseline.
- Existing evidence remains provisional until DBA-001 and RVP-001 are completed.

## Known Limitations Carried Forward

- Current-constituent universe risk.
- Survivorship and delisting risk require DBA-001 review.
- Point-in-time membership limitations require DBA-001 review.
- Gross accounting does not establish net profitability.
- No live execution, broker integration, operations or kill-switch validation exists.
""",
    )

    write(
        "modification_policy.md",
        """
# Modification Policy

## Frozen Baseline Policy

After BFL-001, no validation stage may modify:

- CSM-001 definition
- TSM-001 definition
- CSM x TSM workflow rule
- lookback windows
- ranking method
- high-state thresholds
- rebalance frequency
- WPC-002 gross accounting policy

## If A Change Is Required

Any change requires a new baseline release.

The modified workflow must not be mixed with `CSMxTSM_GROSS_RESEARCH_BASELINE_V1` evidence.

## Allowed During Later Stages

Later stages may audit, evaluate, stress test or reject the baseline.

They may not silently improve it.
""",
    )

    write(
        "limitations.md",
        """
# Limitations

- Git commit information was not recorded because this workspace is not assumed to be a git repository.
- File hashes freeze current artifact contents, not external data-provider history.
- BFL-001 does not verify data correctness; DBA-001 will do that.
- BFL-001 does not run performance tests.
- BFL-001 does not validate production readiness.
""",
    )

    write(
        "executive_summary.md",
        f"""
# Executive Summary

BFL-001 froze the current CSM-001 x TSM-001 validation baseline.

Conclusion: **{conclusion}**

Baseline name:

`CSMxTSM_GROSS_RESEARCH_BASELINE_V1`

Artifacts registered:

{len(hashes)}

Missing artifacts:

{len(missing)}

The baseline is now ready for DBA-001 Data & Bias Audit.

No construct was modified, no workflow was modified, no optimization was performed and no new performance test was run.
""",
    )


if __name__ == "__main__":
    main()
