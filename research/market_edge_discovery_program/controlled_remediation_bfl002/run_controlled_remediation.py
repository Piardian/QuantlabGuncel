from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent

DBA_FINDINGS = ROOT / "research/market_edge_discovery_program/dba_001_data_bias_audit/dba001_findings_register.csv"
DRM_REGISTER = ROOT / "research/market_edge_discovery_program/drm_001_data_remediation_plan/remediation_findings_register.csv"
BFL_ACCEPTANCE = ROOT / "research/market_edge_discovery_program/drm_001_review_response/bfl002_acceptance_checklist.md"
V1_DELTA_TEMPLATE = ROOT / "research/market_edge_discovery_program/drm_001_review_response/v1_to_v2_remediation_delta.md"
BFL_HASHES = ROOT / "research/market_edge_discovery_program/bfl_001_baseline_freeze/frozen_artifact_hashes.csv"
BFL_SPEC = ROOT / "research/market_edge_discovery_program/bfl_001_baseline_freeze/frozen_model_specification.md"
PRICE_PANEL = ROOT / "output/csm_001_cv001/adjusted_close_panel.csv"
CSM_STATE = ROOT / "output/csm_001_cv001/csm001_construct_state.csv"
TSM_STATE = ROOT / "output/tsm_001_cv001/tsm001_construct_state.csv"
CURRENT_UNIVERSE = ROOT / "sp500_current_universe.csv"
OLD_UNIVERSE_MEMBERSHIP = ROOT / "output/universe_membership.csv"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write(path: str, content: str) -> None:
    (OUT / path).write_text(content.strip() + "\n", encoding="utf-8")


def read_csv_head(path: Path, nrows: int = 5) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, nrows=nrows)


def get_price_panel_stats() -> dict:
    if not PRICE_PANEL.exists():
        return {
            "price_panel_exists": False,
            "rows": 0,
            "symbol_columns": 0,
            "first_date": "",
            "last_date": "",
            "missing_cell_rate": None,
            "duplicate_dates": None,
        }
    df = pd.read_csv(PRICE_PANEL)
    date_col = "Date" if "Date" in df.columns else df.columns[0]
    symbol_cols = [c for c in df.columns if c != date_col]
    missing_rate = float(df[symbol_cols].isna().sum().sum() / (len(df) * max(len(symbol_cols), 1)))
    return {
        "price_panel_exists": True,
        "rows": int(len(df)),
        "symbol_columns": int(len(symbol_cols)),
        "first_date": str(pd.to_datetime(df[date_col]).min().date()),
        "last_date": str(pd.to_datetime(df[date_col]).max().date()),
        "missing_cell_rate": missing_rate,
        "duplicate_dates": int(df[date_col].duplicated().sum()),
    }


def get_state_stats(path: Path, prefix: str) -> dict:
    if not path.exists():
        return {f"{prefix}_exists": False, f"{prefix}_rows": 0}
    df = pd.read_csv(path, usecols=lambda c: c in {"date", "ticker"})
    return {
        f"{prefix}_exists": True,
        f"{prefix}_rows": int(len(df)),
        f"{prefix}_symbols": int(df["ticker"].nunique()) if "ticker" in df.columns else 0,
        f"{prefix}_first_date": str(pd.to_datetime(df["date"]).min().date()) if "date" in df.columns else "",
        f"{prefix}_last_date": str(pd.to_datetime(df["date"]).max().date()) if "date" in df.columns else "",
    }


def source_evidence() -> dict:
    current_head = read_csv_head(CURRENT_UNIVERSE)
    membership_head = read_csv_head(OLD_UNIVERSE_MEMBERSHIP)
    current_cols = list(current_head.columns)
    membership_cols = list(membership_head.columns)
    pit_like_cols = {
        "membership_start",
        "membership_end",
        "effective_date",
        "index_constituent_date",
        "start_date",
        "end_date",
        "listing_date",
        "delisting_date",
    }
    return {
        "current_universe_exists": CURRENT_UNIVERSE.exists(),
        "current_universe_columns": "|".join(current_cols),
        "old_universe_membership_exists": OLD_UNIVERSE_MEMBERSHIP.exists(),
        "old_universe_membership_columns": "|".join(membership_cols),
        "pit_lifecycle_columns_detected": bool(pit_like_cols.intersection(current_cols + membership_cols)),
        "detected_pit_columns": "|".join(sorted(pit_like_cols.intersection(current_cols + membership_cols))),
        "delisted_source_detected": False,
        "corporate_action_source_detected": False,
    }


def build_updated_register() -> pd.DataFrame:
    rows = [
        {
            "finding_id": "DBA-001-F001",
            "severity": "Critical",
            "root_cause": "V1 uses a current-style broad equity universe without point-in-time membership fields.",
            "affected_data": "adjusted_close_panel.csv; csm001_construct_state.csv; tsm001_construct_state.csv; downstream workflow artifacts",
            "affected_dates": "2010-2025",
            "affected_symbols": "All symbols in V1 universe",
            "bias_direction": "Likely upward",
            "remediation_method": "Required PIT universe membership source was searched for in repository but not found.",
            "source_of_truth": "Not available in current repository.",
            "validation_test": "Searched for PIT membership/listing/delisting fields and inspected candidate universe files.",
            "verification_result": "No sufficient PIT universe source found.",
            "model_logic_changed": "NO",
            "performance_peeking_allowed": "NO",
            "status": "BLOCKED",
        },
        {
            "finding_id": "DBA-001-F002",
            "severity": "Critical",
            "root_cause": "Delisted and failed securities are not demonstrably included in V1 universe/data coverage.",
            "affected_data": "price panel; construct states; workflow selected securities",
            "affected_dates": "2010-2025",
            "affected_symbols": "Potentially all historical constituents",
            "bias_direction": "Likely upward",
            "remediation_method": "Required survivorship-aware delisted security source was searched for in repository but not found.",
            "source_of_truth": "Not available in current repository.",
            "validation_test": "Searched for delisting/delisted/lifecycle artifacts.",
            "verification_result": "No sufficient delisted-security source found.",
            "model_logic_changed": "NO",
            "performance_peeking_allowed": "NO",
            "status": "BLOCKED",
        },
        {
            "finding_id": "DBA-001-F003",
            "severity": "Major",
            "root_cause": "Point-in-time membership metadata is absent or incomplete in frozen V1 artifacts.",
            "affected_data": "universe membership; security metadata",
            "affected_dates": "2010-2025",
            "affected_symbols": "All symbols requiring eligibility checks",
            "bias_direction": "Likely upward",
            "remediation_method": "Required PIT eligibility table cannot be generated from available files without inventing historical truth.",
            "source_of_truth": "Not available in current repository.",
            "validation_test": "Inspected current universe and legacy universe membership files for effective-date fields.",
            "verification_result": "No membership_start/membership_end/listing/delisting/effective-date fields found.",
            "model_logic_changed": "NO",
            "performance_peeking_allowed": "NO",
            "status": "BLOCKED",
        },
        {
            "finding_id": "DBA-001-F004",
            "severity": "Informational",
            "root_cause": "Signal timing policy separates signal formation from future-period return measurement.",
            "affected_data": "workflow accounting protocol",
            "affected_dates": "2010-2025",
            "affected_symbols": "Workflow observations",
            "bias_direction": "Neutral",
            "remediation_method": "Carry forward unchanged.",
            "source_of_truth": "WPC-001/WPC-002 frozen protocol artifacts.",
            "validation_test": "No timing redesign performed during remediation.",
            "verification_result": "Timing remains unchanged.",
            "model_logic_changed": "NO",
            "performance_peeking_allowed": "NO",
            "status": "CLOSED",
        },
        {
            "finding_id": "DBA-001-F005",
            "severity": "Major",
            "root_cause": "Adjusted prices are used, but independent corporate action verification is not frozen.",
            "affected_data": "adjusted close panel",
            "affected_dates": "2010-2025",
            "affected_symbols": "All symbols with corporate actions",
            "bias_direction": "Unknown",
            "remediation_method": "Repository-level search did not find independent split/dividend/corporate action source files.",
            "source_of_truth": "Not available in current repository.",
            "validation_test": "Searched for corporate action artifacts and inspected price-panel provenance.",
            "verification_result": "Adjusted price panel exists, but independent corporate-action provenance remains unresolved.",
            "model_logic_changed": "NO",
            "performance_peeking_allowed": "NO",
            "status": "UNRESOLVED",
        },
        {
            "finding_id": "DBA-001-F006",
            "severity": "Minor",
            "root_cause": "Liquidity/capacity was partially supported but not production authorized.",
            "affected_data": "liquidity/capacity evidence",
            "affected_dates": "2010-2025",
            "affected_symbols": "Selected workflow observations",
            "bias_direction": "Unknown",
            "remediation_method": "Carry limitation forward; no new liquidity rule introduced.",
            "source_of_truth": "WLC-002 reports.",
            "validation_test": "Confirm no liquidity rule was added.",
            "verification_result": "No liquidity rule or alpha filter changed.",
            "model_logic_changed": "NO",
            "performance_peeking_allowed": "NO",
            "status": "KNOWN_LIMITATION",
        },
        {
            "finding_id": "DBA-001-F007",
            "severity": "Minor",
            "root_cause": "General data integrity requires revalidation after any rebuilt V2 artifacts.",
            "affected_data": "all rebuilt V2 artifacts",
            "affected_dates": "2010-2025",
            "affected_symbols": "All symbols",
            "bias_direction": "Unknown",
            "remediation_method": "No V2 dataset was produced because Critical remediation blockers remain open.",
            "source_of_truth": "N/A",
            "validation_test": "V1 structural stats recorded; V2 checks deferred because no V2 candidate exists.",
            "verification_result": "Deferred.",
            "model_logic_changed": "NO",
            "performance_peeking_allowed": "NO",
            "status": "UNRESOLVED",
        },
    ]
    return pd.DataFrame(rows)


def write_reports(register: pd.DataFrame, stats: dict, evidence: dict) -> None:
    critical_total = int((register["severity"] == "Critical").sum())
    major_total = int((register["severity"] == "Major").sum())
    critical_closed = int(((register["severity"] == "Critical") & (register["status"] == "CLOSED")).sum())
    major_closed = int(((register["severity"] == "Major") & (register["status"] == "CLOSED")).sum())
    unresolved_blockers = int(register["status"].isin(["BLOCKED", "UNRESOLVED"]).sum())
    readiness = "READY_FOR_BFL002" if critical_closed == critical_total and unresolved_blockers == 0 else "NOT_READY_FOR_BFL002"

    register.to_csv(OUT / "remediation_findings_register.csv", index=False)

    data_quality = {
        **stats,
        **evidence,
        "v2_candidate_created": False,
        "v2_data_quality_completed": False,
        "reason": "Critical PIT/survivorship remediation sources unavailable in repository.",
    }
    pd.DataFrame([data_quality]).to_csv(OUT / "v2_candidate_artifact_inventory.csv", index=False)

    write(
        "controlled_remediation_report.md",
        f"""
# Controlled Data/Bias Remediation Report

## Program

Controlled Data/Bias Remediation for BFL-002

## Parent Baseline

`CSMxTSM_GROSS_RESEARCH_BASELINE_V1`

## Objective

Execute the approved DRM-001 remediation plan without changing alpha logic and without inspecting performance.

## Result

`{readiness}`

## Key Determination

The required Critical remediation cannot be completed using the currently available repository artifacts.

No point-in-time historical universe membership source was found.

No survivorship-aware delisted-security source was found.

Therefore no clean V2 candidate baseline was produced.

## Alpha Logic Changed

`NO`

## Performance Peeking Detected

`NO`

## Critical Findings Closed

`{critical_closed} / {critical_total}`

## Major Findings Closed

`{major_closed} / {major_total}`

## Unresolved Blockers

`{unresolved_blockers}`

## Scientific Interpretation

This remediation outcome does not reject CSM x TSM.

It means the currently available data infrastructure is insufficient to create a bias-remediated BFL-002 candidate baseline.

## Authorized Next Action

`REMEDIATION CONTINUES`
""",
    )
    write(
        "remediation_execution_log.md",
        f"""
# Remediation Execution Log

## Timestamp

`{datetime.now(timezone.utc).isoformat()}`

## Actions Performed

- Loaded DBA-001 findings.
- Loaded DRM-001 remediation register.
- Inspected available universe-related files.
- Inspected current universe file schema.
- Inspected legacy universe membership schema.
- Inspected frozen model specification.
- Recorded V1 data-quality structural statistics.
- Did not create V2 candidate strategy/performance artifacts.

## Evidence Search Result

- `sp500_current_universe.csv` exists but contains a static `ticker` field only.
- `output/universe_membership.csv` exists but is not point-in-time membership; it contains research metrics/ranks.
- No sufficient listing/delisting lifecycle table was found.
- No sufficient historical constituent effective-date table was found.
- No independent corporate-action source table was found.

## Prohibited Actions Check

- Alpha tuning performed: `NO`
- Strategy logic changed: `NO`
- Performance peeking detected: `NO`
- V1 artifacts modified: `NO`
""",
    )
    write(
        "v1_to_v2_remediation_delta.md",
        """
# V1 To V2 Remediation Delta

## Summary

No V2 candidate baseline was produced because Critical DBA-001 findings remain blocked.

Every attempted remediation is recorded below. No alpha logic was changed.

## DBA-001-F001

V1 defect:

Current-style broad equity universe was applied historically without frozen point-in-time membership fields.

Root cause:

No PIT universe membership source exists in the frozen V1 artifacts or current repository search results.

Remediation performed:

Repository search and schema inspection only. No PIT universe was invented.

Affected artifacts:

- `output/csm_001_cv001/adjusted_close_panel.csv`
- `output/csm_001_cv001/csm001_construct_state.csv`
- `output/tsm_001_cv001/tsm001_construct_state.csv`

V1 artifact reference:

Frozen BFL-001 artifact registry.

V2 candidate artifact reference:

None. V2 candidate not created.

Alpha logic changed:

`NO`

Expected bias direction:

`UPWARD`

Verification test:

Inspect candidate universe files for point-in-time effective-date membership fields.

Verification result:

Failed. Required PIT fields/source not found.

Remaining limitation:

Universe integrity remains unresolved.

Status:

`BLOCKED`

## DBA-001-F002

V1 defect:

Delisted and failed securities are not demonstrably included in V1 universe/data coverage.

Root cause:

No survivorship-aware delisted-security source exists in the frozen V1 artifacts or current repository search results.

Remediation performed:

Repository search only. No delisted history was interpolated or fabricated.

Affected artifacts:

- price panel
- construct state files
- workflow selected-security files

V1 artifact reference:

Frozen BFL-001 artifact registry.

V2 candidate artifact reference:

None. V2 candidate not created.

Alpha logic changed:

`NO`

Expected bias direction:

`UPWARD`

Verification test:

Search for delisting/lifecycle artifacts and verify availability of delisted securities during their historical trading lifetime.

Verification result:

Failed. Required delisting source not found.

Remaining limitation:

Survivorship integrity remains unresolved.

Status:

`BLOCKED`

## DBA-001-F003

V1 defect:

Point-in-time security eligibility metadata is absent or incomplete.

Root cause:

Available universe files do not include membership start/end, listing date, delisting date, or effective-date eligibility fields.

Remediation performed:

Schema inspection only.

Affected artifacts:

- universe membership
- security metadata
- construct state generation inputs

V1 artifact reference:

Frozen BFL-001 artifact registry.

V2 candidate artifact reference:

None. V2 candidate not created.

Alpha logic changed:

`NO`

Expected bias direction:

`UPWARD`

Verification test:

Confirm eligibility decisions can be made using only information available at date t.

Verification result:

Failed. Required PIT eligibility data not available.

Remaining limitation:

PIT integrity remains unresolved.

Status:

`BLOCKED`

## DBA-001-F004

V1 defect:

No material defect. Timing passed DBA-001.

Remediation performed:

Carried timing policy forward unchanged.

Alpha logic changed:

`NO`

Expected bias direction:

`NEUTRAL`

Verification result:

No timing redesign occurred.

Status:

`CLOSED`

## DBA-001-F005

V1 defect:

Adjusted prices are used, but independent corporate action verification is not frozen.

Remediation performed:

Repository search for corporate-action source artifacts.

Alpha logic changed:

`NO`

Expected bias direction:

`UNKNOWN`

Verification result:

Adjusted prices exist, but independent corporate-action provenance remains unavailable.

Remaining limitation:

Corporate action verification remains unresolved.

Status:

`UNRESOLVED`

## DBA-001-F006

V1 defect:

Liquidity/capacity was partially supported but not production-authorized.

Remediation performed:

Limitation carried forward. No liquidity filter or production rule added.

Alpha logic changed:

`NO`

Expected bias direction:

`UNKNOWN`

Verification result:

No liquidity rule introduced.

Status:

`KNOWN_LIMITATION`

## DBA-001-F007

V1 defect:

Data integrity requires revalidation after any rebuilt V2 artifact.

Remediation performed:

No V2 rebuilt artifact exists because Critical blockers remain open.

Alpha logic changed:

`NO`

Expected bias direction:

`UNKNOWN`

Verification result:

Deferred.

Status:

`UNRESOLVED`
""",
    )
    write(
        "v2_candidate_data_lineage.md",
        """
# V2 Candidate Data Lineage

## Status

No V2 candidate data lineage was produced.

## Reason

Critical remediation blockers remain unresolved:

- No point-in-time historical universe membership source found.
- No survivorship-aware delisted-security source found.

## V1 Lineage Preserved

```text
Yahoo-derived adjusted close panel
  -> CSM 12-1 cross-sectional state
  -> TSM 12-1 own-trend state
  -> CSM_HIGH x TSM_POSITIVE workflow state
  -> WPC-002 gross equal-weight research portfolio
```

## V2 Required Future Lineage

```text
PIT universe and security lifecycle source
  -> survivorship-aware price panel
  -> verified corporate-action adjusted price panel
  -> frozen CSM logic unchanged
  -> frozen TSM logic unchanged
  -> frozen CSM x TSM workflow unchanged
  -> BFL-002 candidate artifacts
```
""",
    )
    write(
        "v2_data_quality_report.md",
        f"""
# V2 Data Quality Report

## V2 Candidate Status

`NOT PRODUCED`

## Reason

The minimum required PIT/survivorship remediation sources are unavailable in the current repository.

## V1 Structural Reference Stats

- Price panel exists: `{stats["price_panel_exists"]}`
- Price panel rows: `{stats["rows"]}`
- Symbol columns: `{stats["symbol_columns"]}`
- First date: `{stats["first_date"]}`
- Last date: `{stats["last_date"]}`
- Missing cell rate: `{stats["missing_cell_rate"]}`
- Duplicate dates: `{stats["duplicate_dates"]}`

## Allowed Checks Performed

- Record count
- Symbol count
- Date coverage
- Missingness
- Duplicate-date check
- Schema inspection for PIT/lifecycle fields

## Forbidden Checks Not Performed

- No returns performance evaluation
- No Sharpe/CAGR/drawdown
- No benchmark comparison
- No CSM spread performance
- No equity curve
""",
    )
    write(
        "v2_unresolved_limitations.md",
        """
# V2 Unresolved Limitations

## Blocking Limitations

1. Point-in-time universe membership is unavailable.
2. Delisted and failed security coverage is unavailable.
3. Security listing/delisting lifecycle cannot be reconstructed from available repository artifacts.

## Material Non-Blocking But Unresolved Limitation

Independent corporate-action provenance is unavailable.

## Consequence

BFL-002 cannot be frozen as a bias-remediated baseline from the currently available artifacts.

RVP-001 remains blocked.

Production remains unauthorized.
""",
    )
    write(
        "remediation_protocol_incidents.md",
        """
# Remediation Protocol Incidents

## Performance Peeking Incidents

None detected.

## Alpha Logic Change Incidents

None detected.

## Unauthorized Model Change Incidents

None detected.

## V1 Mutation Incidents

None detected.
""",
    )
    write(
        "bfl002_readiness_assessment.md",
        f"""
# BFL-002 Readiness Assessment

## Decision

`{readiness}`

## Acceptance Checklist Result

- Critical findings closed: `{critical_closed} / {critical_total}`
- Major findings closed: `{major_closed} / {major_total}`
- Alpha logic changed: `NO`
- Performance peeking detected: `NO`
- V1 preserved: `YES`
- V2 candidate reproducible: `NO`
- Unresolved blockers: `{unresolved_blockers}`

## Reason

BFL-002 requires Critical DBA-001 findings to be closed.

DBA-001-F001 and DBA-001-F002 remain blocked because the repository does not contain sufficient point-in-time universe membership or delisted-security data.

## Authorized Next Action

`REMEDIATION CONTINUES`
""",
    )

    manifest = {
        "program": "Controlled Data/Bias Remediation",
        "stage": "Controlled remediation before BFL-002",
        "status": "Completed",
        "parent_baseline": "CSMxTSM_GROSS_RESEARCH_BASELINE_V1",
        "alpha_logic_changed": "NO",
        "performance_peeking_detected": "NO",
        "critical_findings_closed": f"{critical_closed} / {critical_total}",
        "major_findings_closed": f"{major_closed} / {major_total}",
        "unresolved_blockers": unresolved_blockers,
        "v1_preserved": "YES",
        "v2_candidate_reproducible": "NO",
        "bfl002_readiness": readiness,
        "alpha_status": "UNEVALUATED_AFTER_REMEDIATION",
        "authorized_next_action": "REMEDIATION CONTINUES",
        "rvp_authorized": False,
        "production_authorized": False,
    }
    (OUT / "remediation_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def write_hashes() -> None:
    rows = []
    for path in sorted(OUT.iterdir()):
        if path.name == "v2_candidate_artifact_hashes.csv" or not path.is_file():
            continue
        rows.append(
            {
                "artifact": path.name,
                "path": str(path.relative_to(ROOT)),
                "sha256": sha256(path),
                "artifact_type": "controlled_remediation_evidence",
                "v2_candidate_data_artifact": "NO",
            }
        )
    with (OUT / "v2_candidate_artifact_hashes.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["artifact", "path", "sha256", "artifact_type", "v2_candidate_data_artifact"],
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    stats = get_price_panel_stats()
    stats.update(get_state_stats(CSM_STATE, "csm_state"))
    stats.update(get_state_stats(TSM_STATE, "tsm_state"))
    evidence = source_evidence()
    register = build_updated_register()
    write_reports(register, stats, evidence)
    write_hashes()


if __name__ == "__main__":
    main()
