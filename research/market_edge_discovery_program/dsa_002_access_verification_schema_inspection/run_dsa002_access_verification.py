from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_text(name: str, content: str) -> None:
    (OUT / name).write_text(content.strip() + "\n", encoding="utf-8")


def write_csv(name: str, rows: list[dict]) -> None:
    path = OUT / name
    fieldnames = list(rows[0].keys()) if rows else ["empty"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    generated_at = datetime.now(timezone.utc).isoformat()

    stack_rows = [
        {
            "source_stack": "Institutional",
            "components": "CRSP + Compustat PIT + CCM + I/B/E/S + GICS History",
            "access_available": "NO",
            "access_method": "None verified",
            "account_type": "UNVERIFIED",
            "institution_dependency": "YES",
            "api_availability": "UNVERIFIED",
            "bulk_download_availability": "UNVERIFIED",
            "local_export_capability": "NO",
            "authentication_method": "UNVERIFIED",
            "historical_depth_available_to_current_account": "UNVERIFIED",
            "sample_dataset_obtainable": "NO",
            "data_dictionary_obtainable": "NO",
            "documentation_obtainable": "YES_PUBLIC_ONLY",
            "access_decision": "ACCESS_UNAVAILABLE",
            "technical_decision": "TECHNICALLY_UNSUITABLE",
            "license_decision": "LICENSE_UNRESOLVED",
        },
        {
            "source_stack": "Accessible commercial",
            "components": "Sharadar + Nasdaq Data Link + QuantRocket integration",
            "access_available": "NO",
            "access_method": "No local subscription/API key/sample export found",
            "account_type": "UNVERIFIED",
            "institution_dependency": "NO_OR_PARTIAL",
            "api_availability": "PUBLIC_DOCS_ONLY",
            "bulk_download_availability": "UNVERIFIED",
            "local_export_capability": "NO",
            "authentication_method": "UNVERIFIED",
            "historical_depth_available_to_current_account": "UNVERIFIED",
            "sample_dataset_obtainable": "NO",
            "data_dictionary_obtainable": "NO",
            "documentation_obtainable": "YES_PUBLIC_ONLY",
            "access_decision": "ACCESS_UNAVAILABLE",
            "technical_decision": "TECHNICALLY_UNSUITABLE",
            "license_decision": "LICENSE_UNRESOLVED",
        },
    ]
    write_csv("dsa002_schema_inventory.csv", stack_rows)

    license_rows = [
        {
            "source_stack": row["source_stack"],
            "personal_research": "LICENSE_UNRESOLVED",
            "academic_research": "LICENSE_UNRESOLVED",
            "commercial_research": "LICENSE_UNRESOLVED",
            "company_internal_use": "LICENSE_UNRESOLVED",
            "automated_trading_research": "LICENSE_UNRESOLVED",
            "live_trading": "LICENSE_UNRESOLVED",
            "derived_data_storage": "LICENSE_UNRESOLVED",
            "local_caching": "LICENSE_UNRESOLVED",
            "redistribution": "LICENSE_UNRESOLVED",
            "model_output_commercialization": "LICENSE_UNRESOLVED",
            "team_access": "LICENSE_UNRESOLVED",
            "server_cloud_deployment": "LICENSE_UNRESOLVED",
            "historical_data_retention_after_subscription": "LICENSE_UNRESOLVED",
            "license_status": "LICENSE_UNRESOLVED",
            "evidence": "No executed license agreement or authenticated account documentation exists in repository.",
        }
        for row in stack_rows
    ]
    write_csv("dsa002_license_matrix.csv", license_rows)

    canonical_fields = [
        "security_id",
        "company_id",
        "ticker",
        "exchange",
        "share_class",
        "security_type",
        "trade_date",
        "raw_close",
        "adjusted_close",
        "volume",
        "shares_outstanding",
        "listing_date",
        "delisting_date",
        "delisting_code",
        "active_flag",
        "corporate_action_factor",
        "universe_effective_from",
        "universe_effective_to",
        "industry_code",
        "industry_valid_from",
        "industry_valid_to",
        "source_asof_timestamp",
        "filing_date",
        "announcement_timestamp",
        "forecast_timestamp",
        "revision_timestamp",
    ]
    mapping_rows = []
    for field in canonical_fields:
        mapping_rows.append(
            {
                "canonical_field": field,
                "institutional_stack_field": "UNAVAILABLE_NO_LOCAL_SCHEMA",
                "accessible_stack_field": "UNAVAILABLE_NO_LOCAL_SCHEMA",
                "mapping_status": "UNVERIFIED",
                "notes": "No authenticated sample schema or data dictionary was available for inspection.",
            }
        )
    write_csv("canonical_schema_mapping.csv", mapping_rows)

    survivorship_rows = [
        {
            "sample_case": case,
            "institutional_stack_evidence": "NO_LOCAL_ACCESS",
            "accessible_stack_evidence": "NO_LOCAL_ACCESS",
            "identifier": "UNAVAILABLE",
            "lifecycle_event": case,
            "last_observable_date": "UNAVAILABLE",
            "delisting_metadata": "UNAVAILABLE",
            "post_event_representation": "UNAVAILABLE",
            "survivorship_bias_result": "UNVERIFIED",
        }
        for case in [
            "normal_delisting",
            "acquisition",
            "bankruptcy",
            "ticker_change",
            "exchange_move",
            "long_inactive_security",
        ]
    ]
    write_csv("dsa002_survivorship_sample_checks.csv", survivorship_rows)

    pit_rows = [
        {
            "sample_domain": domain,
            "institutional_stack_evidence": "NO_LOCAL_ACCESS",
            "accessible_stack_evidence": "NO_LOCAL_ACCESS",
            "historical_value_available": "UNVERIFIED",
            "historically_knowable_value_available": "UNVERIFIED",
            "effective_date_field": "UNAVAILABLE",
            "publication_date_field": "UNAVAILABLE",
            "revision_date_field": "UNAVAILABLE",
            "asof_semantics": "UNVERIFIED",
            "pit_result": "UNVERIFIED",
        }
        for domain in [
            "security_membership",
            "financial_statement",
            "earnings_announcement",
            "analyst_expectation",
            "industry_classification",
        ]
    ]
    write_csv("dsa002_point_in_time_sample_checks.csv", pit_rows)

    coverage_rows = [
        {
            "dba_finding": "DBA-001-F001",
            "required_data_capability": "PIT universe reconstruction",
            "candidate_source": "Institutional stack; Accessible commercial stack",
            "actual_evidence": "Public documentation only; no authenticated schema/sample access",
            "status": "UNSATISFIED",
        },
        {
            "dba_finding": "DBA-001-F002",
            "required_data_capability": "Delisted securities and survivorship handling",
            "candidate_source": "Institutional stack; Accessible commercial stack",
            "actual_evidence": "Public documentation only; no local sample case verification",
            "status": "UNSATISFIED",
        },
        {
            "dba_finding": "DBA-001-F003",
            "required_data_capability": "Point-in-time eligibility metadata",
            "candidate_source": "Institutional stack; Accessible commercial stack",
            "actual_evidence": "No local effective-date membership fields inspected",
            "status": "UNSATISFIED",
        },
        {
            "dba_finding": "DBA-001-F005",
            "required_data_capability": "Corporate-action source/provenance",
            "candidate_source": "Institutional stack; Accessible commercial stack",
            "actual_evidence": "No local corporate-action schema or adjustment factor sample inspected",
            "status": "UNSATISFIED",
        },
    ]
    write_csv("dba_finding_source_coverage_matrix.csv", coverage_rows)

    sample_inventory = [
        {
            "sample_artifact_id": "NONE",
            "source_stack": "N/A",
            "artifact_path": "N/A",
            "stored_locally": "NO",
            "reason": "No authenticated source access; no legally permitted sample extract obtained.",
        }
    ]
    write_csv("sample_artifact_inventory.csv", sample_inventory)

    sample_hashes = [
        {
            "sample_artifact_id": "NONE",
            "artifact_path": "N/A",
            "sha256": "N/A",
            "reason": "No local sample artifact exists.",
        }
    ]
    write_csv("sample_artifact_hashes.csv", sample_hashes)

    write_text(
        "dsa002_access_verification_report.md",
        """
# DSA-002 Access Verification & Sample Schema Inspection

## Final Decision

`SOURCE_STACK_UNAVAILABLE`

## Key Finding

No approved candidate source stack has verified real access in the current project environment.

Public documentation supports that credible source families exist, but DSA-002 requires actual access, data dictionary or sample schema inspection. That requirement was not met.

## Institutional Stack

```text
CRSP + Compustat PIT + CCM + I/B/E/S + GICS History
```

Access decision:

`ACCESS_UNAVAILABLE`

Technical decision:

`TECHNICALLY_UNSUITABLE`

License decision:

`LICENSE_UNRESOLVED`

Reason:

No WRDS/CRSP/Compustat/I/B/E/S/GICS credentials, local exports, data dictionaries or sample schemas were found in the repository or environment.

## Accessible Commercial Stack

```text
Sharadar + Nasdaq Data Link + QuantRocket
```

Access decision:

`ACCESS_UNAVAILABLE`

Technical decision:

`TECHNICALLY_UNSUITABLE`

License decision:

`LICENSE_UNRESOLVED`

Reason:

No Nasdaq Data Link/Sharadar API key, subscription artifact, local data dictionary, local sample extract or QuantRocket database was found.

## Performance Controls

- Performance evaluation performed: `NO`
- Alpha logic changed: `NO`
- BFL-002 created: `NO`
""",
    )

    write_text(
        "dsa002_identifier_linkage_report.md",
        """
# Identifier Linkage Report

## Required Linkage Chain

```text
security
  -> company
  -> fundamentals
  -> industry classification
  -> analyst estimates
```

## Institutional Stack

The institutional stack is expected, based on public documentation, to support strong identifier linkage through CRSP permanent identifiers, Compustat company identifiers, and CCM link history.

However, no actual local link table, field list, sample record, link start date, link end date, link type, or primary-link semantics were inspected.

Result:

`PARTIAL / UNVERIFIED`

## Accessible Commercial Stack

Sharadar/Nasdaq/QuantRocket may provide useful ticker and company tables, but no actual local sample was inspected. Ticker-only linkage is not acceptable as the primary historical linkage key for this program.

Result:

`FAILED / UNVERIFIED`

## Conclusion

Identifier linkage is not verified for any candidate stack in the current project environment.
""",
    )

    write_text(
        "dsa002_unresolved_gaps.md",
        """
# DSA-002 Unresolved Gaps

## Blocking Gaps

1. No real institutional stack access verified.
2. No real accessible commercial stack access verified.
3. No local data dictionary inspected.
4. No local sample schema inspected.
5. No survivorship sample case verified.
6. No point-in-time sample record verified.
7. No identifier linkage table inspected.
8. License rights remain unresolved.

## Blocked Research Programs

- BFL-002
- RVP-001
- BMR
- NOC
- PEAD-001 empirical work
- PROF-001 empirical work
- VAL-001 empirical work
- CSM x ISM bridge empirical work

## Required Gap Resolution

The project must acquire verified access to at least one candidate source stack and inspect sample schemas before controlled remediation can resume.
""",
    )

    write_text(
        "dsa002_final_decision.md",
        """
# DSA-002 Final Decision

## Overall Decision

`SOURCE_STACK_UNAVAILABLE`

## Rationale

DSA-001 identified credible source families. DSA-002 attempted to verify actual access and inspect local schemas.

No authenticated access, local data dictionary, local schema, or sample extract was available for either the institutional or accessible commercial stack.

Therefore no source stack can be technically or legally approved for remediation.

## Critical DBA Findings Technically Satisfiable

`0 / 2`

## Major DBA Findings Technically Satisfiable

`0 / 2`

## BFL-002

`NOT AUTHORIZED`

## Authorized Next Action

`RESEARCH SCOPE REVISION`

This may include:

- obtaining WRDS/CRSP/Compustat/I/B/E/S/GICS access,
- obtaining Sharadar/Nasdaq Data Link access,
- or explicitly revising the research scope to a verifiable period/source.

No alpha research is authorized.
""",
    )

    manifest = {
        "program": "DSA-002 Access Verification & Sample Schema Inspection",
        "status": "Completed",
        "generated_at_utc": generated_at,
        "institutional_stack_access": "UNAVAILABLE",
        "accessible_stack_access": "UNAVAILABLE",
        "critical_dba_findings_technically_satisfiable": "0 / 2",
        "major_dba_findings_technically_satisfiable": "0 / 2",
        "survivorship_capability": "FAILED",
        "point_in_time_capability": "FAILED",
        "identifier_linkage": "FAILED",
        "license_status": "UNRESOLVED",
        "performance_evaluation_performed": "NO",
        "alpha_logic_changed": "NO",
        "overall_decision": "SOURCE_STACK_UNAVAILABLE",
        "bfl002_authorized": "NO",
        "authorized_next_action": "RESEARCH SCOPE REVISION",
    }
    (OUT / "dsa002_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    write_text(
        "executive_summary.md",
        """
# Executive Summary

DSA-002 is complete.

Final decision:

`SOURCE_STACK_UNAVAILABLE`

No candidate source stack currently has verified access, inspected schema, inspected sample records, or resolved license status.

This does not mean acceptable data sources do not exist. It means the project does not currently have access sufficient to approve remediation.

BFL-002 remains blocked.

The authorized next action is:

`RESEARCH SCOPE REVISION`
""",
    )

    # Hash generated report artifacts after all writes.
    hash_rows = []
    for path in sorted(OUT.iterdir()):
        if not path.is_file() or path.name == "sample_artifact_hashes.csv":
            continue
        hash_rows.append(
            {
                "artifact": path.name,
                "path": str(path.relative_to(ROOT)),
                "sha256": sha256(path),
            }
        )
    write_csv("report_artifact_hashes.csv", hash_rows)


if __name__ == "__main__":
    main()
