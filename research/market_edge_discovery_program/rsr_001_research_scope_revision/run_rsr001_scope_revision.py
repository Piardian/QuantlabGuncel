from __future__ import annotations

import csv
import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent

PRICE_PANEL = ROOT / "output/csm_001_cv001/adjusted_close_panel.csv"
CSM_STATE = ROOT / "output/csm_001_cv001/csm001_construct_state.csv"
TSM_STATE = ROOT / "output/tsm_001_cv001/tsm001_construct_state.csv"
CURRENT_UNIVERSE = ROOT / "sp500_current_universe.csv"
PAPER_UNIVERSE = ROOT / "config/paper_universe.csv"
YAHOO_SOURCE = ROOT / "data/yahoo_data.py"
KF49 = ROOT / "data/ism_001/ken_french_49_industry_value_weighted_monthly.csv"
FF3 = ROOT / "data/rsm_001/fama_french_3_factor_monthly.csv"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_text(name: str, content: str) -> None:
    (OUT / name).write_text(content.strip() + "\n", encoding="utf-8")


def write_csv(name: str, rows: list[dict]) -> None:
    fieldnames = list(rows[0].keys()) if rows else ["empty"]
    with (OUT / name).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def price_stats() -> dict:
    if not PRICE_PANEL.exists():
        return {}
    df = pd.read_csv(PRICE_PANEL)
    date_col = "Date" if "Date" in df.columns else df.columns[0]
    symbols = [c for c in df.columns if c != date_col]
    return {
        "earliest_date": str(pd.to_datetime(df[date_col]).min().date()),
        "latest_date": str(pd.to_datetime(df[date_col]).max().date()),
        "security_count": len(symbols),
        "row_count": len(df),
        "identifier_type": "ticker_column",
        "missing_rate": float(df[symbols].isna().sum().sum() / (len(df) * max(len(symbols), 1))),
        "duplicate_dates": int(df[date_col].duplicated().sum()),
    }


def count_csv_rows(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        return sum(1 for _ in path.open("r", encoding="utf-8")) - 1
    except UnicodeDecodeError:
        return sum(1 for _ in path.open("r")) - 1


def main() -> None:
    now = datetime.now(timezone.utc).isoformat()
    today = str(date.today())
    stats = price_stats()

    inventory = [
        {
            "source_name": "CSM adjusted close panel",
            "source_type": "local_derived_price_panel",
            "local_path": str(PRICE_PANEL.relative_to(ROOT)),
            "acquisition_method": "Yahoo-derived historical adjusted close panel",
            "earliest_date": stats.get("earliest_date", "UNKNOWN"),
            "latest_date": stats.get("latest_date", "UNKNOWN"),
            "number_of_securities": stats.get("security_count", 0),
            "identifier_type": "ticker",
            "delisted_securities_present": "UNKNOWN",
            "historical_membership_present": "NO",
            "pit_semantics": "NONE",
            "reproducible": "PARTIAL",
            "license_status": "UNRESOLVED",
            "known_limitations": "Current-style ticker panel; no permanent IDs; no PIT membership; no delisting lifecycle.",
        },
        {
            "source_name": "CSM construct state",
            "source_type": "local_derived_construct_state",
            "local_path": str(CSM_STATE.relative_to(ROOT)),
            "acquisition_method": "Derived from adjusted close panel",
            "earliest_date": stats.get("earliest_date", "UNKNOWN"),
            "latest_date": stats.get("latest_date", "UNKNOWN"),
            "number_of_securities": stats.get("security_count", 0),
            "identifier_type": "ticker",
            "delisted_securities_present": "UNKNOWN",
            "historical_membership_present": "NO",
            "pit_semantics": "NONE_FOR_UNIVERSE",
            "reproducible": "PARTIAL",
            "license_status": "UNRESOLVED",
            "known_limitations": "Derived state inherits current-universe/survivorship limitations.",
        },
        {
            "source_name": "TSM construct state",
            "source_type": "local_derived_construct_state",
            "local_path": str(TSM_STATE.relative_to(ROOT)),
            "acquisition_method": "Derived from adjusted close panel",
            "earliest_date": stats.get("earliest_date", "UNKNOWN"),
            "latest_date": stats.get("latest_date", "UNKNOWN"),
            "number_of_securities": stats.get("security_count", 0),
            "identifier_type": "ticker",
            "delisted_securities_present": "UNKNOWN",
            "historical_membership_present": "NO",
            "pit_semantics": "NONE_FOR_UNIVERSE",
            "reproducible": "PARTIAL",
            "license_status": "UNRESOLVED",
            "known_limitations": "Derived state inherits current-universe/survivorship limitations.",
        },
        {
            "source_name": "Current S&P 500 universe file",
            "source_type": "local_current_universe_snapshot",
            "local_path": str(CURRENT_UNIVERSE.relative_to(ROOT)),
            "acquisition_method": "Current ticker list",
            "earliest_date": "NOT_APPLICABLE",
            "latest_date": "CURRENT_SNAPSHOT",
            "number_of_securities": count_csv_rows(CURRENT_UNIVERSE),
            "identifier_type": "ticker",
            "delisted_securities_present": "NO",
            "historical_membership_present": "NO",
            "pit_semantics": "NONE",
            "reproducible": "PARTIAL",
            "license_status": "UNRESOLVED",
            "known_limitations": "Cannot be used as historical membership.",
        },
        {
            "source_name": "Paper universe",
            "source_type": "local_live/paper_watchlist",
            "local_path": str(PAPER_UNIVERSE.relative_to(ROOT)),
            "acquisition_method": "Manual/current paper trading universe",
            "earliest_date": "2026-07-20",
            "latest_date": "CURRENT",
            "number_of_securities": count_csv_rows(PAPER_UNIVERSE),
            "identifier_type": "ticker",
            "delisted_securities_present": "NO",
            "historical_membership_present": "NO",
            "pit_semantics": "PROSPECTIVE_ONLY_IF_SNAPSHOT_LOGGED",
            "reproducible": "PARTIAL",
            "license_status": "UNRESOLVED",
            "known_limitations": "Useful for prospective snapshot capture only, not retrospective formal validation.",
        },
        {
            "source_name": "Ken French 49 industry monthly returns",
            "source_type": "external_research_factor_portfolio",
            "local_path": str(KF49.relative_to(ROOT)),
            "acquisition_method": "Downloaded research dataset",
            "earliest_date": "UNKNOWN_FROM_THIS_AUDIT",
            "latest_date": "UNKNOWN_FROM_THIS_AUDIT",
            "number_of_securities": "PORTFOLIO_LEVEL",
            "identifier_type": "industry_portfolio",
            "delisted_securities_present": "NOT_SECURITY_LEVEL",
            "historical_membership_present": "NOT_SECURITY_LEVEL",
            "pit_semantics": "NOT_SECURITY_LEVEL",
            "reproducible": "PARTIAL",
            "license_status": "PUBLIC_RESEARCH_DATA_LIKELY_BUT_UNVERIFIED",
            "known_limitations": "Not a stock-level security universe or lifecycle source.",
        },
        {
            "source_name": "Fama-French 3 factor monthly data",
            "source_type": "external_research_factor_portfolio",
            "local_path": str(FF3.relative_to(ROOT)),
            "acquisition_method": "Downloaded research dataset",
            "earliest_date": "UNKNOWN_FROM_THIS_AUDIT",
            "latest_date": "UNKNOWN_FROM_THIS_AUDIT",
            "number_of_securities": "FACTOR_LEVEL",
            "identifier_type": "factor_series",
            "delisted_securities_present": "NOT_SECURITY_LEVEL",
            "historical_membership_present": "NOT_SECURITY_LEVEL",
            "pit_semantics": "NOT_SECURITY_LEVEL",
            "reproducible": "PARTIAL",
            "license_status": "PUBLIC_RESEARCH_DATA_LIKELY_BUT_UNVERIFIED",
            "known_limitations": "Not a stock-level security universe or lifecycle source.",
        },
    ]
    write_csv("rsr001_actual_data_inventory.csv", inventory)

    scope_rows = [
        {
            "scope_id": "RSR-A",
            "description": "Shorter historical window using existing Yahoo/current-ticker panel",
            "data_source": "Existing adjusted_close_panel.csv",
            "start_date": stats.get("earliest_date", "UNKNOWN"),
            "end_date": stats.get("latest_date", "UNKNOWN"),
            "market": "US equities",
            "exchange": "Mixed/unknown from ticker panel",
            "universe_definition": "Current-style broad ticker panel",
            "approximate_security_count": stats.get("security_count", 0),
            "lifecycle_quality": "FAIL",
            "survivorship_status": "FAIL",
            "pit_status": "FAIL",
            "identifier_status": "FAILED",
            "corporate_action_status": "PARTIAL",
            "price_data_status": "PARTIAL",
            "volume_status": "FAIL",
            "reproducibility_status": "PARTIAL",
            "license_status": "UNRESOLVED",
            "historical_depth": f"{stats.get('earliest_date', 'UNKNOWN')} to {stats.get('latest_date', 'UNKNOWN')}",
            "known_limitations": "Later start date does not fix missing delisted securities or PIT membership.",
            "research_claim_classification": "EXPLORATORY_ONLY",
            "decision": "REJECT_FOR_FORMAL_SCOPE",
        },
        {
            "scope_id": "RSR-B",
            "description": "Narrower verifiable historical universe using current known tickers",
            "data_source": "sp500_current_universe.csv / config paper universe",
            "start_date": "NONE",
            "end_date": "NONE",
            "market": "US equities",
            "exchange": "Unknown/current snapshot only",
            "universe_definition": "Current constituents/watchlist only",
            "approximate_security_count": count_csv_rows(CURRENT_UNIVERSE),
            "lifecycle_quality": "FAIL",
            "survivorship_status": "FAIL",
            "pit_status": "FAIL",
            "identifier_status": "FAILED",
            "corporate_action_status": "FAIL",
            "price_data_status": "PARTIAL",
            "volume_status": "PARTIAL",
            "reproducibility_status": "PARTIAL",
            "license_status": "UNRESOLVED",
            "historical_depth": "No defensible historical membership",
            "known_limitations": "A current known list cannot become historical membership.",
            "research_claim_classification": "EXPLORATORY_ONLY",
            "decision": "REJECT_FOR_FORMAL_SCOPE",
        },
        {
            "scope_id": "RSR-C",
            "description": "Fixed security-master-first historical scope",
            "data_source": "No local security master",
            "start_date": "NONE",
            "end_date": "NONE",
            "market": "US equities",
            "exchange": "NONE",
            "universe_definition": "Would require listing/delisting/security type/exchange lifecycle records",
            "approximate_security_count": 0,
            "lifecycle_quality": "FAIL",
            "survivorship_status": "FAIL",
            "pit_status": "FAIL",
            "identifier_status": "FAILED",
            "corporate_action_status": "FAIL",
            "price_data_status": "FAIL",
            "volume_status": "FAIL",
            "reproducibility_status": "FAIL",
            "license_status": "NOT_APPLICABLE",
            "historical_depth": "NONE",
            "known_limitations": "No local security master exists.",
            "research_claim_classification": "UNUSABLE",
            "decision": "UNAVAILABLE",
        },
        {
            "scope_id": "RSR-D",
            "description": "Prospective research scope from immutable daily universe/security snapshots",
            "data_source": "Future captured snapshots using local ingestion/logging infrastructure",
            "start_date": today,
            "end_date": "ONGOING",
            "market": "US equities",
            "exchange": "To be fixed before capture",
            "universe_definition": "Predefined active tradable universe snapshots recorded at T0 and each update without hindsight",
            "approximate_security_count": "TO_BE_DEFINED_BEFORE_CAPTURE",
            "lifecycle_quality": "PARTIAL",
            "survivorship_status": "PARTIAL",
            "pit_status": "PARTIAL",
            "identifier_status": "PARTIAL",
            "corporate_action_status": "PARTIAL",
            "price_data_status": "PARTIAL",
            "volume_status": "PARTIAL",
            "reproducibility_status": "PARTIAL",
            "license_status": "UNRESOLVED",
            "historical_depth": "Prospective only",
            "known_limitations": "No retrospective historical validation; evidence accumulates only after T0.",
            "research_claim_classification": "LIMITED_RESEARCH_CANDIDATE",
            "decision": "SELECTED_PROSPECTIVE_SCOPE",
        },
        {
            "scope_id": "RSR-E",
            "description": "Exploratory historical scope preserving V1 and current datasets",
            "data_source": "Existing V1/current research artifacts",
            "start_date": stats.get("earliest_date", "UNKNOWN"),
            "end_date": stats.get("latest_date", "UNKNOWN"),
            "market": "US equities",
            "exchange": "Mixed/unknown",
            "universe_definition": "Current-style historical panel",
            "approximate_security_count": stats.get("security_count", 0),
            "lifecycle_quality": "FAIL",
            "survivorship_status": "FAIL",
            "pit_status": "FAIL",
            "identifier_status": "FAILED",
            "corporate_action_status": "PARTIAL",
            "price_data_status": "PARTIAL",
            "volume_status": "PARTIAL",
            "reproducibility_status": "PARTIAL",
            "license_status": "UNRESOLVED",
            "historical_depth": f"{stats.get('earliest_date', 'UNKNOWN')} to {stats.get('latest_date', 'UNKNOWN')}",
            "known_limitations": "Only for hypothesis generation, debugging, pipeline testing and lineage.",
            "research_claim_classification": "EXPLORATORY_ONLY",
            "decision": "RETAIN_AS_EXPLORATORY",
        },
    ]
    write_csv("rsr001_candidate_scope_matrix.csv", scope_rows)

    write_csv(
        "rsr001_survivorship_assessment.csv",
        [
            {"scope_id": r["scope_id"], "contains_dead_securities": "NO/UNKNOWN" if r["scope_id"] != "RSR-D" else "FUTURE_ONLY_IF_CAPTURED", "delistings_preserved": "NO" if r["scope_id"] != "RSR-D" else "TO_BE_CAPTURED", "current_survivors_backfilled": "YES" if r["scope_id"] in ["RSR-A", "RSR-B", "RSR-E"] else "NO_FOR_FUTURE_ONLY", "survivorship_status": r["survivorship_status"], "evidence": r["known_limitations"]}
            for r in scope_rows
        ],
    )
    write_csv(
        "rsr001_point_in_time_assessment.csv",
        [
            {"scope_id": r["scope_id"], "universe_membership_pit": "NO" if r["scope_id"] != "RSR-D" else "CAN_BE_CAPTURED_FROM_T0", "security_status_pit": "NO" if r["scope_id"] != "RSR-D" else "CAN_BE_CAPTURED_FROM_T0", "metadata_pit": "NO" if r["scope_id"] != "RSR-D" else "CAN_BE_CAPTURED_FROM_T0", "pit_status": r["pit_status"], "evidence": r["known_limitations"]}
            for r in scope_rows
        ],
    )

    write_text(
        "rsr001_research_scope_revision_report.md",
        f"""
# RSR-001 Research Scope Revision Report

## Final Decision

`PROSPECTIVE_SCOPE_ONLY`

## Existing V1 Status

`EXPLORATORY / NON_PRODUCTION_VALID`

## Alpha Hypothesis

`CSM-001 x TSM-001`

## Core Finding

No verified historical scope exists inside the current project environment.

The project has historical price/state artifacts, but they are not supported by point-in-time universe membership, delisted-security coverage, or permanent security lifecycle records.

The only scientifically defensible forward path available without new data access is a prospective capture program starting from a predefined T0.

## Selected Scope

`RSR-D`

## Selected Start Date

`{today}`

## Scientific Meaning

RSR-D does not create historical validation.

It only creates a clean prospective environment in which future evidence can be collected without reconstructing historical truth from present-day data.

## Prohibited Conclusions

- No claim that CSM x TSM works.
- No historical production alpha claim.
- No RVP authorization.
- No BFL-002 authorization.
""",
    )

    write_text(
        "rsr001_security_lifecycle_assessment.md",
        """
# Security Lifecycle Assessment

## Historical Local Data

The historical local data does not contain sufficient lifecycle fields:

- listing date: unavailable
- first trading date: inferred from prices only, not authoritative
- delisting date: unavailable
- delisting reason: unavailable
- inactive status: unavailable
- ticker change history: unavailable
- exchange change history: unavailable
- share-class change history: unavailable
- merger/acquisition handling: unavailable
- bankruptcy handling: unavailable

Can a security that no longer exists today still appear correctly in historical research?

`NO`

## Prospective Scope

A prospective capture program can record lifecycle state from T0 forward if the source snapshots include active status, listing state, identifier state and corporate-action updates.

Status:

`PARTIAL`
""",
    )
    write_text(
        "rsr001_identifier_integrity_report.md",
        """
# Identifier Integrity Report

## Historical Local Data

Identifier quality:

`FAILED`

Reason:

The main historical equity panel uses ticker columns. Ticker alone is not a stable historical security identifier because it cannot reliably distinguish ticker reuse, ticker changes, share classes, mergers, relistings or company/security identity changes.

## Prospective Scope

Identifier quality:

`PARTIAL`

Reason:

The project can prospectively record source identifiers, tickers, exchange, security type and snapshot hashes. However, this remains partial unless a vendor supplies immutable security IDs or a documented identifier mapping table.
""",
    )
    write_text(
        "rsr001_corporate_action_assessment.md",
        """
# Corporate Action Assessment

## Historical Local Data

Corporate-action integrity:

`PARTIAL`

Reason:

Adjusted close data exists, but no independent split/dividend/corporate-action source table or adjustment-factor audit exists locally.

Adjusted prices therefore cannot be treated as fully audited corporate-action history.

## Prospective Scope

Corporate-action integrity:

`PARTIAL`

Prospective capture can log corporate-action state and adjustment source from T0 forward, but the source and schema must be fixed before capture begins.
""",
    )
    write_text(
        "rsr001_universe_definition_candidates.md",
        """
# Universe Definition Candidates

## Rejected Historical Candidates

### Current S&P 500 / broad current ticker panel

Rejected for formal validation because present-day constituents are projected backward.

### Current paper universe

Rejected for historical validation because it is a current watchlist, not historical membership.

### Security-master-first historical scope

Unavailable because no local security master exists.

## Selected Candidate

### RSR-D Prospective Snapshot Universe

Definition:

An explicitly predefined list or source query of active tradable US equity securities captured from T0 forward with immutable daily or periodic snapshots.

Rules must be fixed before capture:

- eligible exchanges
- eligible security types
- active status
- listing status
- ticker and source identifier
- universe entry timestamp
- universe exit timestamp
- corporate-action state
- source timestamp
- ingestion timestamp

This is not historical validation.
""",
    )
    write_text(
        "rsr001_historical_start_date_assessment.md",
        f"""
# Historical Start-Date Assessment

## Historical Scope

No defensible historical start date was identified.

The existing panel starts at:

`{stats.get('earliest_date', 'UNKNOWN')}`

But earliest stored date is not the same as earliest scientifically defensible date.

## Reason

No later historical date inside the existing data solves:

- missing delisted securities
- missing PIT membership
- missing permanent security lifecycle
- missing corporate-action provenance

## Selected Start Date

For the selected prospective scope:

`{today}`

This is a prospective T0, not a historical validation start date.
""",
    )
    write_text(
        "rsr001_data_lineage.md",
        """
# RSR-001 Data Lineage

## Existing V1 Lineage

```text
Yahoo-derived adjusted close panel
  -> current-style ticker panel
  -> CSM state
  -> TSM state
  -> CSM x TSM workflow
  -> exploratory historical baseline
```

Classification:

`EXPLORATORY_ONLY`

## Selected Prospective Lineage

```text
predefined T0
  -> universe/security snapshot
  -> market data snapshot
  -> corporate-action snapshot
  -> immutable raw artifact hashes
  -> frozen transformation config
  -> future research dataset
```

Classification:

`LIMITED_RESEARCH_CANDIDATE`
""",
    )
    write_text(
        "rsr001_reproducibility_assessment.md",
        """
# Reproducibility Assessment

## Historical Local Scope

Reproducibility:

`PARTIAL`

Existing artifacts can be hashed and regenerated in parts, but historical universe truth cannot be reproduced because PIT membership and security lifecycle sources are absent.

## Prospective Scope

Reproducibility:

`PARTIAL`

A prospective program can become reproducible if it records:

- raw snapshots
- source timestamps
- ingestion timestamps
- schema versions
- transformation versions
- daily hashes
- immutable logs

Until this capture program is implemented, reproducibility remains partial.
""",
    )
    write_text(
        "rsr001_license_operational_assessment.md",
        """
# License And Operational Assessment

## Current Historical Sources

License status:

`UNRESOLVED`

Yahoo-derived and downloaded research data may be usable for exploratory work, but production/commercial/live trading rights are not established in this audit.

## Prospective Scope

License status:

`UNRESOLVED`

Before prospective capture becomes formal evidence, the project must document whether the data source permits:

- local storage
- derived data storage
- automated research
- live trading support
- server/cloud deployment
- future commercial use

No rights are inferred.
""",
    )
    write_text(
        "rsr001_model_scope_compatibility.md",
        """
# Model Scope Compatibility

## Frozen Model

`CSM-001 x TSM-001`

## Historical Local Scope

Compatibility:

`PARTIAL`

The model can technically compute on the existing price panel, but the scope is not scientifically valid for production-quality historical claims.

## Prospective Scope

Compatibility:

`PARTIAL`

The frozen model can operate prospectively if the capture program provides:

- sufficient lookback history after warmup
- adjusted close or frozen equivalent price field
- deterministic eligible universe
- monthly rebalance dates
- missing-data policy
- stable identifiers

No alpha logic change is required, but evidence cannot begin until enough lookback history has accumulated.
""",
    )
    write_text(
        "rsr001_historical_scope_limitations.md",
        """
# Historical Scope Limitations

- Present-day survivor universe is projected backward in existing broad panel.
- Delisted securities are not demonstrably present.
- Historical membership cannot be reconstructed.
- Future security survival may influence historical eligibility.
- Ticker reuse cannot be controlled with ticker-only identifiers.
- Key lifecycle records are unavailable.
- PIT semantics are unavailable.
- Corporate-action provenance is incomplete.
- Formal production-quality historical alpha claims are blocked.
""",
    )
    write_text(
        "rsr001_prospective_capture_plan.md",
        f"""
# Prospective Capture Plan

## Scope ID

`RSR-D`

## T0

`{today}`

## Required Daily / Periodic Security Universe Snapshot

- security ID if available
- ticker
- exchange
- security type
- active status
- listing date if available
- delisting status
- sector / industry if used
- source timestamp
- ingestion timestamp

## Required Market Data Snapshot

- timestamp
- open
- high
- low
- close
- adjusted close or adjustment state
- volume
- source timestamp
- ingestion timestamp

## Required Corporate Actions

- event type
- announcement date
- effective date
- old identifier
- new identifier
- adjustment factor

## Auditability

Generate:

- ingestion logs
- daily hashes
- schema versions
- transformation versions
- immutable raw snapshots

## Important Limitation

This program creates future PIT evidence only. It does not repair historical V1 evidence.
""",
    )
    write_text(
        "rsr001_research_claim_classification.md",
        """
# Research Claim Classification

## Existing V1

`EXPLORATORY_ONLY`

Permitted uses:

- hypothesis generation
- debugging
- infrastructure testing
- educational analysis
- lineage review

Forbidden uses:

- formal alpha validation
- production claims
- investor-facing evidence
- formal OOS claims
- live capital authorization

## Selected Prospective Scope

`LIMITED_RESEARCH_CANDIDATE`

Permitted future uses after implementation:

- prospective evidence collection
- shadow-style observational evidence
- future out-of-sample record

Forbidden current uses:

- historical production validation
- immediate BFL-002
- RVP-001
- production authorization
""",
    )
    write_text(
        "rsr001_protocol_incidents.md",
        """
# Protocol Incidents

Performance peeking incidents:

`NONE DETECTED`

Alpha logic change incidents:

`NONE DETECTED`

V1 mutation incidents:

`NONE DETECTED`
""",
    )
    write_text(
        "rsr001_final_decision.md",
        f"""
# RSR-001 Final Decision

## Overall Decision

`PROSPECTIVE_SCOPE_ONLY`

## Selected Scope

`RSR-D`

## Selected Start Date

`{today}`

## Baseline Lineage Decision

`NONE`

Reason:

No historical baseline-freeze protocol is authorized. The selected path is a prospective data capture program, not a new historical baseline.

## BFL-002

`NOT AUTHORIZED`

## RVP-001

`NOT AUTHORIZED`

## Production

`NOT AUTHORIZED`

## Authorized Next Action

`PROSPECTIVE DATA CAPTURE PROGRAM`
""",
    )

    output_files = [
        "rsr001_research_scope_revision_report.md",
        "rsr001_candidate_scope_matrix.csv",
        "rsr001_actual_data_inventory.csv",
        "rsr001_security_lifecycle_assessment.md",
        "rsr001_survivorship_assessment.csv",
        "rsr001_point_in_time_assessment.csv",
        "rsr001_identifier_integrity_report.md",
        "rsr001_corporate_action_assessment.md",
        "rsr001_universe_definition_candidates.md",
        "rsr001_historical_start_date_assessment.md",
        "rsr001_data_lineage.md",
        "rsr001_reproducibility_assessment.md",
        "rsr001_license_operational_assessment.md",
        "rsr001_model_scope_compatibility.md",
        "rsr001_historical_scope_limitations.md",
        "rsr001_prospective_capture_plan.md",
        "rsr001_research_claim_classification.md",
        "rsr001_protocol_incidents.md",
        "rsr001_final_decision.md",
    ]
    hashes = []
    for name in output_files:
        path = OUT / name
        hashes.append({"artifact": name, "sha256": sha256(path), "path": str(path.relative_to(ROOT))})
    write_csv("rsr001_artifact_hashes.csv", hashes)
    output_files.append("rsr001_artifact_hashes.csv")

    manifest = {
        "program_id": "RSR-001",
        "program_name": "Research Scope Revision",
        "execution_date": now,
        "parent_programs": ["BFL-001", "DBA-001", "DRM-001", "Controlled Remediation", "DSA-001", "DSA-002"],
        "input_artifacts": [
            "dsa002_manifest.json",
            "controlled_remediation_report.md",
            "dba001_findings_register.csv",
            "CSMxTSM_GROSS_RESEARCH_BASELINE_V1",
        ],
        "output_artifacts": output_files,
        "artifact_hashes": "rsr001_artifact_hashes.csv",
        "alpha_logic_changed": "NO",
        "performance_evaluation_performed": "NO",
        "performance_peeking_detected": "NO",
        "candidate_scope_count": len(scope_rows),
        "selected_scope": "RSR-D",
        "selected_start_date": today,
        "selected_universe": "Prospective immutable active tradable US equity universe snapshots, to be fixed before capture",
        "survivorship_status": "PARTIAL",
        "pit_status": "PARTIAL",
        "lifecycle_status": "PARTIAL",
        "identifier_status": "PARTIAL",
        "reproducibility_status": "PARTIAL",
        "research_claim_classification": "LIMITED_RESEARCH_CANDIDATE",
        "baseline_lineage_decision": "NONE",
        "overall_decision": "PROSPECTIVE_SCOPE_ONLY",
        "bfl002_authorized": "NO",
        "rvp001_authorized": "NO",
        "production_authorized": "NO",
        "authorized_next_action": "PROSPECTIVE DATA CAPTURE PROGRAM",
    }
    (OUT / "rsr001_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
