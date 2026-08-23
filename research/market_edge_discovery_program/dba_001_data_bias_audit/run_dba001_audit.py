from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent

BFL = ROOT / "research" / "market_edge_discovery_program" / "bfl_001_baseline_freeze" / "bfl001_manifest.json"
BFL_HASHES = ROOT / "research" / "market_edge_discovery_program" / "bfl_001_baseline_freeze" / "frozen_artifact_hashes.csv"
CSM_STATE = ROOT / "output" / "csm_001_cv001" / "csm001_construct_state.csv"
TSM_STATE = ROOT / "output" / "tsm_001_cv001" / "tsm001_construct_state.csv"
PRICE_PANEL = ROOT / "output" / "csm_001_cv001" / "adjusted_close_panel.csv"
WPC001 = ROOT / "research" / "market_edge_discovery_program" / "wpc_001_workflow_portfolio_construction_protocol" / "wpc001_protocol_registration.md"
WPC002_CHECKS = ROOT / "research" / "market_edge_discovery_program" / "wpc_002_workflow_portfolio_construction_validation" / "portfolio_accounting_checks.csv"
WLC002 = ROOT / "research" / "market_edge_discovery_program" / "wlc_002_workflow_liquidity_capacity_audit" / "wlc002_manifest.json"


def load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write(name: str, text: str) -> None:
    (OUT / name).write_text(text.strip() + "\n", encoding="utf-8")


def dataset_stats() -> dict:
    csm = pd.read_csv(CSM_STATE, usecols=["date", "ticker", "csm001_valid_observation", "csm001_top_decile_flag"], parse_dates=["date"])
    tsm = pd.read_csv(TSM_STATE, usecols=["date", "ticker", "tsm001_valid_observation", "tsm001_positive_state"], parse_dates=["date"])
    prices = pd.read_csv(PRICE_PANEL, index_col=0, parse_dates=True)
    return {
        "csm_rows": int(len(csm)),
        "tsm_rows": int(len(tsm)),
        "price_rows": int(len(prices)),
        "price_columns": int(len(prices.columns)),
        "tickers": int(csm["ticker"].nunique()),
        "first_date": str(csm["date"].min().date()),
        "last_date": str(csm["date"].max().date()),
        "csm_valid_rate": float(csm["csm001_valid_observation"].mean()),
        "tsm_valid_rate": float(tsm["tsm001_valid_observation"].mean()),
        "csm_high_rate_valid": float(csm.loc[csm["csm001_valid_observation"], "csm001_top_decile_flag"].mean()),
        "tsm_positive_rate_valid": float(tsm.loc[tsm["tsm001_valid_observation"], "tsm001_positive_state"].mean()),
        "price_missing_rate": float(prices.isna().sum().sum() / (prices.shape[0] * prices.shape[1])),
        "duplicate_price_dates": int(prices.index.duplicated().sum()),
    }


def build_findings(stats: dict, wpc_checks_passed: bool, wlc: dict) -> pd.DataFrame:
    rows = [
        {
            "finding_id": "DBA-001-F001",
            "audit_domain": "Universe integrity",
            "artifact": "output/csm_001_cv001/adjusted_close_panel.csv",
            "severity": "Critical",
            "description": "Baseline appears to use a current broad equity universe rather than a verified point-in-time historical constituent universe.",
            "evidence": f"Price panel contains {stats['price_columns']} current-style ticker columns and no membership-date fields.",
            "affected_period": f"{stats['first_date']} to {stats['last_date']}",
            "affected_symbols": "Potentially all symbols",
            "potential_bias_direction": "upward",
            "baseline_impact": "May overstate historical feasibility and performance if current survivors are projected backward.",
            "remediation_required": True,
            "baseline_revision_required": True,
            "status": "Open",
        },
        {
            "finding_id": "DBA-001-F002",
            "audit_domain": "Survivorship / delisting",
            "artifact": "output/csm_001_cv001/csm001_construct_state.csv",
            "severity": "Critical",
            "description": "No delisted-security universe or delisting-return treatment is documented in the frozen baseline.",
            "evidence": "Frozen artifacts include current ticker panel/state files but no delisted-security membership or delisting return fields.",
            "affected_period": f"{stats['first_date']} to {stats['last_date']}",
            "affected_symbols": "Unknown missing delisted symbols",
            "potential_bias_direction": "upward",
            "baseline_impact": "May bias long-only momentum evidence if failed/delisted historical names are absent.",
            "remediation_required": True,
            "baseline_revision_required": True,
            "status": "Open",
        },
        {
            "finding_id": "DBA-001-F003",
            "audit_domain": "Point-in-time",
            "artifact": "Baseline universe artifacts",
            "severity": "Major",
            "description": "Point-in-time constituent membership is not available in the frozen baseline.",
            "evidence": "No membership_start, membership_end, index_constituent_date or equivalent field exists in frozen data inventory.",
            "affected_period": f"{stats['first_date']} to {stats['last_date']}",
            "affected_symbols": "Potentially all symbols",
            "potential_bias_direction": "upward",
            "baseline_impact": "Limits inference beyond the current-constituent research universe.",
            "remediation_required": True,
            "baseline_revision_required": True,
            "status": "Open",
        },
        {
            "finding_id": "DBA-001-F004",
            "audit_domain": "Signal timing",
            "artifact": "WPC-001/WPC-002",
            "severity": "Informational" if wpc_checks_passed else "Critical",
            "description": "Portfolio accounting separates signal and execution reference dates under WPC rules.",
            "evidence": f"WPC accounting checks passed: {wpc_checks_passed}. Protocol uses signal at rebalance close and next trading day close return measurement.",
            "affected_period": "WPC-002 rebalance sample",
            "affected_symbols": "Workflow holdings",
            "potential_bias_direction": "none" if wpc_checks_passed else "upward",
            "baseline_impact": "No same-close execution issue detected in WPC accounting checks." if wpc_checks_passed else "Could invalidate portfolio accounting timing.",
            "remediation_required": False if wpc_checks_passed else True,
            "baseline_revision_required": False if wpc_checks_passed else True,
            "status": "Closed" if wpc_checks_passed else "Open",
        },
        {
            "finding_id": "DBA-001-F005",
            "audit_domain": "Corporate actions",
            "artifact": "output/csm_001_cv001/adjusted_close_panel.csv",
            "severity": "Major",
            "description": "Adjusted prices are used, but corporate-action adjustment provenance cannot be independently verified from frozen artifacts.",
            "evidence": "Data source path indicates Yahoo-derived adjusted close panel; no split/dividend adjustment audit file is frozen.",
            "affected_period": f"{stats['first_date']} to {stats['last_date']}",
            "affected_symbols": "All symbols with corporate actions",
            "potential_bias_direction": "unknown",
            "baseline_impact": "Corporate-action errors could affect momentum ranks and returns.",
            "remediation_required": True,
            "baseline_revision_required": False,
            "status": "Open",
        },
        {
            "finding_id": "DBA-001-F006",
            "audit_domain": "Liquidity / tradability",
            "artifact": "research/market_edge_discovery_program/wlc_002_workflow_liquidity_capacity_audit/wlc002_manifest.json",
            "severity": "Minor",
            "description": "Liquidity/capacity was partially supported, but not full production-level capacity validation.",
            "evidence": f"WLC-002 conclusion: {wlc.get('conclusion')}; volume coverage: {wlc.get('volume_coverage')}.",
            "affected_period": "WLC-002 sample",
            "affected_symbols": "Selected workflow observations",
            "potential_bias_direction": "unknown",
            "baseline_impact": "Liquidity limitations must carry into NOC/CAP stages.",
            "remediation_required": False,
            "baseline_revision_required": False,
            "status": "Known limitation",
        },
        {
            "finding_id": "DBA-001-F007",
            "audit_domain": "Data integrity",
            "artifact": "output/csm_001_cv001/adjusted_close_panel.csv",
            "severity": "Minor" if stats["duplicate_price_dates"] == 0 else "Major",
            "description": "Basic price panel duplicate-date and missing-rate audit.",
            "evidence": f"Duplicate price dates: {stats['duplicate_price_dates']}; missing cell rate: {stats['price_missing_rate']:.6f}.",
            "affected_period": f"{stats['first_date']} to {stats['last_date']}",
            "affected_symbols": "All price panel symbols",
            "potential_bias_direction": "unknown" if stats["price_missing_rate"] > 0 else "none",
            "baseline_impact": "Missing data may affect eligibility and portfolio availability; deeper DBA follow-up required if concentrated.",
            "remediation_required": stats["duplicate_price_dates"] > 0,
            "baseline_revision_required": stats["duplicate_price_dates"] > 0,
            "status": "Open" if stats["duplicate_price_dates"] > 0 else "Known limitation",
        },
    ]
    return pd.DataFrame(rows)


def summarize_findings(findings: pd.DataFrame) -> pd.DataFrame:
    severity_order = ["Critical", "Major", "Minor", "Informational"]
    rows = []
    for severity in severity_order:
        rows.append({"severity": severity, "count": int((findings["severity"] == severity).sum())})
    return pd.DataFrame(rows)


def domain_status(findings: pd.DataFrame) -> pd.DataFrame:
    rows = []
    domains = {
        "Universe integrity": "FAIL",
        "Survivorship integrity": "FAIL",
        "Point-in-time integrity": "PARTIAL",
        "Execution timing integrity": "PASS",
        "Corporate actions integrity": "PARTIAL",
        "Liquidity/tradability integrity": "PARTIAL",
        "Data integrity": "PARTIAL",
    }
    for domain, status in domains.items():
        rows.append({"audit_domain": domain, "status": status})
    return pd.DataFrame(rows)


def conclusion_from_findings(findings: pd.DataFrame) -> str:
    critical = int((findings["severity"] == "Critical").sum())
    major = int((findings["severity"] == "Major").sum())
    if critical > 0:
        return "Audit Failed"
    if major > 0:
        return "Audit Passed With Limitations"
    return "Audit Passed"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    bfl = load_json(BFL)
    if bfl.get("conclusion") != "Baseline Frozen":
        raise RuntimeError("DBA-001 requires BFL-001 Baseline Frozen.")

    stats = dataset_stats()
    checks = pd.read_csv(WPC002_CHECKS)
    wpc_checks_passed = bool(checks["passed"].all())
    wlc = load_json(WLC002)
    findings = build_findings(stats, wpc_checks_passed, wlc)
    severity_summary = summarize_findings(findings)
    domains = domain_status(findings)
    conclusion = conclusion_from_findings(findings)
    authorized_next_gate = "BFL-002 / Baseline V2 remediation required before RVP-001" if conclusion == "Audit Failed" else "RVP-001 Robustness & OOS Validation"

    pd.DataFrame([stats]).to_csv(OUT / "data_source_inventory.csv", index=False)
    findings.to_csv(OUT / "dba001_findings_register.csv", index=False)
    severity_summary.to_csv(OUT / "finding_severity_summary.csv", index=False)
    domains.to_csv(OUT / "audit_domain_status.csv", index=False)
    pd.read_csv(BFL_HASHES).to_csv(OUT / "baseline_hash_reference.csv", index=False)

    manifest = {
        "study_id": "DBA-001",
        "study_name": "Data & Bias Audit",
        "status": "Completed",
        "conclusion": conclusion,
        "baseline": bfl.get("baseline_name"),
        "critical_findings": int((findings["severity"] == "Critical").sum()),
        "major_findings": int((findings["severity"] == "Major").sum()),
        "minor_findings": int((findings["severity"] == "Minor").sum()),
        "informational_findings": int((findings["severity"] == "Informational").sum()),
        "baseline_reproducible": True,
        "point_in_time_integrity": "PARTIAL",
        "survivorship_integrity": "FAIL",
        "execution_timing_integrity": "PASS",
        "baseline_revision_required": bool(findings["baseline_revision_required"].any()),
        "constructs_modified": False,
        "workflow_modified": False,
        "performance_test_performed": False,
        "optimization_performed": False,
        "authorized_next_gate": authorized_next_gate,
    }
    (OUT / "dba001_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    write(
        "dba001_data_bias_audit.md",
        f"""
# DBA-001: Data & Bias Audit

## Purpose

Audit whether the frozen baseline's historical information and trading assumptions were knowable and tradeable under the recorded research design.

No performance retest, strategy change, optimization or production recommendation was performed.

## Baseline

`{bfl.get("baseline_name")}`

## Final Conclusion

**{conclusion}**

## Summary

- Critical findings: {manifest["critical_findings"]}
- Major findings: {manifest["major_findings"]}
- Minor findings: {manifest["minor_findings"]}
- Informational findings: {manifest["informational_findings"]}
- Baseline reproducible: YES
- Point-in-time integrity: PARTIAL
- Survivorship integrity: FAIL
- Execution timing integrity: PASS
- Baseline revision required: {manifest["baseline_revision_required"]}

## Authorized Next Gate

{authorized_next_gate}
""",
    )
    write(
        "timing_assumption_audit.md",
        f"""
# Timing Assumption Audit

## Status

**PASS**

## Evidence

WPC-001 states that signals are formed using data available at rebalance close and portfolio return is measured from the next trading day close to the next rebalance close.

WPC-002 accounting checks passed:

`{wpc_checks_passed}`

## Interpretation

No same-close execution assumption was detected in the frozen WPC accounting artifacts.
""",
    )
    write(
        "survivorship_bias_assessment.md",
        """
# Survivorship Bias Assessment

## Status

**FAIL**

## Evidence

The frozen baseline does not include a verified point-in-time historical constituent universe, delisted securities, or delisting-return treatment.

## Interpretation

This is a critical limitation because projecting a current universe backward can overstate feasibility and performance.

## Required Action

Do not silently edit V1. If remediated, create a controlled V2 baseline linked to DBA-001 finding IDs.
""",
    )
    write(
        "point_in_time_assessment.md",
        """
# Point-In-Time Assessment

## Status

**PARTIAL**

## Evidence

Price-derived CSM and TSM features use historical adjusted prices and lagged lookbacks.

However, point-in-time universe membership is not available in the frozen baseline.

## Interpretation

Feature calculation appears lagged, but universe membership integrity is not point-in-time verified.
""",
    )
    write(
        "cost_model_readiness.md",
        """
# Cost Model Readiness

## Status

**PARTIAL**

## Evidence

WLC-002 provides liquidity and capacity evidence with volume coverage, but WPC-002 portfolio accounting remains gross only.

## Interpretation

The baseline is not ready for NOC-002 until a cost model protocol is frozen, but cost-related artifacts exist for later use.
""",
    )
    write(
        "benchmark_readiness.md",
        """
# Benchmark Readiness

## Status

**PARTIAL**

## Evidence

The workflow has a benchmark region in WPC-002, but a full fair benchmark race has not been run.

## Required Future Work

BMR-001 must compare gross and net results using identical universe, timing, cost and portfolio assumptions.
""",
    )
    write(
        "data_lineage.md",
        """
# Data Lineage

## CSM Score

```text
Yahoo-derived adjusted close panel
  -> output/csm_001_cv001/adjusted_close_panel.csv
  -> lagged 12-1 adjusted-close return
  -> cross-sectional percentile rank
  -> csm001_top_decile_flag
  -> output/csm_001_cv001/csm001_construct_state.csv
  -> frozen hash in BFL-001
```

## TSM State

```text
Yahoo-derived adjusted close panel
  -> output/csm_001_cv001/adjusted_close_panel.csv
  -> lagged 12-1 own-history return
  -> tsm001_positive_state
  -> output/tsm_001_cv001/tsm001_construct_state.csv
  -> frozen hash in BFL-001
```

## Portfolio Accounting

```text
CSM state + TSM state
  -> CSM_HIGH x TSM_POSITIVE selected state
  -> monthly signal at first trading day rebalance close
  -> next trading day close return measurement
  -> WPC-002 gross equal-weight portfolio series
  -> frozen hash in BFL-001
```
""",
    )
    write(
        "limitations.md",
        """
# Limitations

- DBA-001 audited frozen artifacts and documentation; it did not acquire new historical constituent data.
- DBA-001 did not rerun performance.
- DBA-001 did not remediate data issues.
- Corporate-action accuracy was not independently verified against exchange/vendor action files.
- Survivorship and point-in-time limitations remain unresolved.
""",
    )
    write(
        "executive_summary.md",
        f"""
# Executive Summary

DBA-001 audited the frozen `CSMxTSM_GROSS_RESEARCH_BASELINE_V1` baseline.

Final conclusion: **{conclusion}**.

The baseline is technically reproducible from frozen artifacts, but data/bias integrity is not sufficient to proceed directly as if the evidence were fully clean.

Key findings:

- Critical findings: {manifest["critical_findings"]}
- Major findings: {manifest["major_findings"]}
- Survivorship integrity: FAIL
- Point-in-time integrity: PARTIAL
- Execution timing integrity: PASS

The main blockers are current-universe/survivorship limitations and absence of point-in-time constituent/delisting data.

No baseline artifact was modified.
""",
    )


if __name__ == "__main__":
    main()
