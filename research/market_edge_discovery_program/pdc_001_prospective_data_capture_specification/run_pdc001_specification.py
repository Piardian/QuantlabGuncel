from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
DRY_RUN = OUT / "non_formal_test_capture"

SPEC_ID = "NONE"
SCHEMA_VERSION = "PDC_SCHEMA_V1_DRAFT"
FINAL_DECISION = "PDC_SPECIFICATION_NOT_READY"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_text(name: str, content: str) -> None:
    (OUT / name).write_text(content.strip() + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict]) -> None:
    fieldnames = list(rows[0].keys()) if rows else ["empty"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def create_non_formal_dry_run() -> dict:
    DRY_RUN.mkdir(exist_ok=True)
    rows = [
        {
            "capture_label": "NON_FORMAL_TEST_CAPTURE",
            "security_id": "TESTSRC:NYSE:TEST:COMMON:2026-08-11",
            "ticker": "TEST",
            "exchange": "NYSE",
            "security_type": "COMMON_STOCK",
            "active_status": "ACTIVE",
            "source_timestamp_utc": "2026-08-11T21:30:00Z",
            "ingestion_timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "schema_version": SCHEMA_VERSION,
        }
    ]
    sample_path = DRY_RUN / "security_master_sample.csv"
    write_csv(sample_path, rows)
    manifest = {
        "capture_label": "NON_FORMAL_TEST_CAPTURE",
        "formal_t0": False,
        "schema_version": SCHEMA_VERSION,
        "file_inventory": [
            {
                "file": "security_master_sample.csv",
                "sha256": sha256(sample_path),
                "row_count": len(rows),
            }
        ],
        "status": "SUCCESS_NON_FORMAL",
        "warning": "Dry run validates local file/hash/manifest mechanics only. It is not source access validation.",
    }
    manifest_path = DRY_RUN / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return {
        "dry_run_status": "PARTIAL",
        "sample_path": str(sample_path.relative_to(ROOT)),
        "sample_sha256": sha256(sample_path),
        "manifest_path": str(manifest_path.relative_to(ROOT)),
        "manifest_sha256": sha256(manifest_path),
    }


def main() -> None:
    generated_at = datetime.now(timezone.utc).isoformat()
    dry_run = create_non_formal_dry_run()

    security_type_rows = [
        {"security_type": "US common stocks", "decision": "INCLUDE", "rationale": "Comparable operating-company equity instrument; primary target for CSM x TSM."},
        {"security_type": "REITs", "decision": "CONDITIONAL", "rationale": "Equity-like but structurally distinct; include only if source tags reliably and policy accepts REIT comparability before launch."},
        {"security_type": "Foreign ordinary shares", "decision": "EXCLUDE", "rationale": "May introduce country, currency, and listing structure differences not required for initial US equity capture."},
        {"security_type": "ADRs", "decision": "EXCLUDE", "rationale": "Different issuer/listing structure; avoid complexity in initial prospective scope."},
        {"security_type": "ETFs", "decision": "EXCLUDE", "rationale": "Funds are not operating-company equities."},
        {"security_type": "Closed-end funds", "decision": "EXCLUDE", "rationale": "Funds are not comparable to operating-company equities."},
        {"security_type": "Preferred stocks", "decision": "EXCLUDE", "rationale": "Hybrid security; not comparable to common equity."},
        {"security_type": "Units", "decision": "EXCLUDE", "rationale": "Composite/temporary structures create lifecycle ambiguity."},
        {"security_type": "Warrants", "decision": "EXCLUDE", "rationale": "Derivative-like instrument."},
        {"security_type": "SPACs", "decision": "EXCLUDE", "rationale": "Pre-combination shell structure differs from ordinary operating companies."},
        {"security_type": "Rights", "decision": "EXCLUDE", "rationale": "Temporary corporate-action instrument."},
        {"security_type": "Limited partnerships", "decision": "EXCLUDE", "rationale": "Different legal/economic structure."},
        {"security_type": "Tracking stocks", "decision": "EXCLUDE", "rationale": "Non-standard claim on business segment."},
        {"security_type": "Multiple share classes", "decision": "CONDITIONAL", "rationale": "Allowed only if each share class has stable security ID and is not merged by ticker/company alone."},
    ]
    write_csv(OUT / "pdc001_security_type_policy.csv", security_type_rows)

    write_text(
        "pdc001_specification_and_freeze_report.md",
        f"""
# PDC-001 Prospective Data Capture Specification & Freeze

## Final Decision

`{FINAL_DECISION}`

## Reason

The prospective capture architecture is specified as a draft, but Critical launch requirements remain unresolved:

- real raw market data source access is not verified
- real security-master source access is not verified
- real corporate-action source access is not verified
- license status is unresolved
- source-backed lifecycle and identifier fields are not verified

Therefore the specification cannot be frozen as `US_EQUITY_PROSPECTIVE_CAPTURE_SPEC_V1`.

## Scientific T0

`NOT_ESTABLISHED`

PDC-001 does not establish T0. T0 can only be set by PDC-002 after a successful formal capture launch.

## Alpha Control

- Alpha logic changed: `NO`
- Performance evaluation performed: `NO`
- Performance peeking detected: `NO`

## Authorized Next Action

`PDC-001 REMEDIATION`
""",
    )

    write_text(
        "pdc001_market_exchange_scope.md",
        """
# Market And Exchange Scope

## Market

`US Equities`

## Included Exchanges

- NYSE
- Nasdaq
- NYSE American

## Excluded Venues

- OTC markets
- Pink sheets
- Non-US primary listings
- Crypto venues
- Futures/options venues
- Non-US exchanges

## Exchange Transfers

Exchange changes must be captured as lifecycle events with effective date and source timestamp.

Historical snapshots must retain the exchange known at the time of capture.

## Blocker

The source used to determine exchange membership is unresolved.
""",
    )

    write_text(
        "pdc001_security_type_policy.md",
        """
# Security-Type Policy

The initial prospective scope prioritizes deterministic, comparable US operating-company equity instruments.

See `pdc001_security_type_policy.csv` for the frozen draft decision table.

Critical blocker:

The source fields required to identify security type and share class are unresolved.
""",
    )

    write_text(
        "pdc001_security_identifier_policy.md",
        """
# Security Identifier Policy

## Preferred Hierarchy

```text
source_permanent_security_id
  -> ticker
  -> source_company_id
  -> exchange
```

Ticker must not be the primary historical identity key.

## Internal ID Fallback

If no external immutable security ID is available, generate:

```text
internal_security_id = SHA256(source_name | first_seen_exchange | first_seen_ticker | first_seen_company_name | security_type | share_class | first_seen_timestamp)
```

This fallback is partial and must not merge separate share classes, ticker reuse cases, relistings or successor securities.

## Blocker

No source permanent security ID is currently verified.
""",
    )

    write_text(
        "pdc001_universe_definition.md",
        """
# Universe Definition

## Draft Deterministic Rule

A security is eligible at date T if, using only records captured at or before T:

- exchange is NYSE, Nasdaq or NYSE American
- security type is included or conditionally included under the security-type policy
- active/tradable status is active
- listing status is listed
- security has enough captured history for frozen CSM/TSM lookback requirements before signal eligibility
- security is not suspended, halted for prolonged period, stale, missing required price data or delisted as of T

## IPOs

IPOs enter the security master when first observed by the selected source and become signal-eligible only after frozen lookback requirements are satisfied.

## No Alpha Filters

No liquidity, sector, volatility or performance filter is introduced here.

## Blocker

The source fields for active/tradable/listing status are not verified.
""",
    )

    write_text(
        "pdc001_universe_snapshot_policy.md",
        """
# Universe Snapshot Policy

## Frequency

Capture universe/security-master state once per US equity trading day after official close/final source publication.

## Timezone

Store timestamps in UTC. Preserve source timezone where provided.

## Snapshot Timing

Draft target:

`Post-close after end-of-day data finalization`

## Retry Behavior

Failed or partial snapshots produce a failure manifest and may be retried. Retry artifacts must not overwrite original failed artifacts.

## Blocker

The exact source finalization time is unresolved because source access is unresolved.
""",
    )

    write_text(
        "pdc001_security_lifecycle_policy.md",
        """
# Security Lifecycle Policy

Required lifecycle events:

- IPO / initial listing
- normal listing
- suspension
- ticker change
- exchange change
- share-class change
- merger
- acquisition
- bankruptcy
- delisting
- relisting
- inactive status
- corporate reorganization

Historical records must not be deleted after a security disappears.

Blocker:

No verified lifecycle source exists yet.
""",
    )

    write_text(
        "pdc001_ipo_delisting_suspension_policy.md",
        """
# IPO, Delisting, Suspension And Halt Policy

## IPOs

Do not add a security to any snapshot before its listing or first observed active status.

## Delistings

Preserve all prior records. Record delisting event, effective date, last tradable date and reason/status if available.

## Suspensions And Halts

Suspended or halted securities remain in historical records but receive status flags. They must not be represented as normally tradable.

## Stale/Zero Volume

Flag stale or zero-volume observations; do not delete silently.

## Blocker

Event source for IPO/delisting/suspension is unresolved.
""",
    )

    write_text(
        "pdc001_corporate_action_policy.md",
        """
# Corporate Action Policy

Corporate actions must be stored as events, not only embedded into adjusted prices.

Required event fields:

- event_id
- security_id
- event_type
- announcement_date where available
- ex_date
- record_date where available
- effective_date
- payment_date where applicable
- adjustment_factor where applicable
- source_timestamp
- ingestion_timestamp
- source

Events covered:

- stock splits
- reverse splits
- cash dividends
- stock dividends
- rights issues
- spin-offs
- mergers
- acquisitions
- symbol changes
- share-class changes

Blocker:

Corporate-action source is unresolved.
""",
    )

    write_text(
        "pdc001_market_data_schema.md",
        """
# Market Data Schema

Minimum fields:

- trade_date
- security_id
- ticker
- exchange
- raw_open
- raw_high
- raw_low
- raw_close
- raw_volume
- vendor_adjusted_close if available
- source_timestamp
- ingestion_timestamp
- schema_version
- freshness_status
- capture_provenance

Optional fields:

- VWAP
- trade_count
- bid
- ask
- shares_outstanding

Blocker:

Raw market data source is unresolved.
""",
    )

    write_text(
        "pdc001_raw_adjusted_price_policy.md",
        """
# Raw Vs Adjusted Price Policy

Raw market data must be stored independently from adjustment metadata.

Do not overwrite raw prices with adjusted values.

Store where available:

- raw OHLCV
- vendor adjusted close
- split adjustment factor
- dividend adjustment factor
- internally derived adjusted series version, if later authorized

Vendor adjusted data may be used only with source documentation and retained metadata.
""",
    )

    write_text(
        "pdc001_timestamp_policy.md",
        """
# Timestamp Policy

All system timestamps are stored in UTC.

Where available, distinguish:

- event_time
- source_time
- available_to_system_time
- ingestion_time

The system must answer separately:

```text
When did the event occur?
```

and:

```text
When could the research system first know it?
```

Late data must be marked and must not silently revise previous snapshots.
""",
    )

    write_text(
        "pdc001_missing_stale_data_policy.md",
        """
# Missing And Stale Data Policy

Allowed statuses:

- FRESH
- DELAYED
- STALE
- MISSING
- INVALID

Forbidden by default:

- forward-filling tradable prices
- interpolation
- substituting future values
- deleting stale observations silently

Any non-price metadata carry-forward must be explicitly versioned and traceable.
""",
    )

    write_text(
        "pdc001_data_revision_policy.md",
        """
# Data Revision Policy

Never silently overwrite original captured data.

For revised records preserve:

- first_seen_value
- latest_value
- revision_timestamp
- source_version if available
- prior artifact hash
- revised artifact hash

Formal PIT research should use first historically knowable state unless a later gate authorizes a different research question.
""",
    )

    write_text(
        "pdc001_storage_architecture.md",
        """
# Storage Architecture

Draft root:

`data/prospective/us_equities/`

Layout:

```text
raw/
normalized/
derived/
manifests/
schemas/
logs/
quarantine/
```

Raw files must be immutable. Corrected source deliveries create new versions rather than replacing prior files.

Blocker:

Write-once enforcement is not implemented yet.
""",
    )

    write_text(
        "pdc001_hash_manifest_policy.md",
        """
# Hash And Manifest Policy

Hash algorithm:

`SHA256`

Hash:

- raw snapshot files
- security-master files
- corporate-action files
- normalized formal evidence files
- schemas
- manifests

Each capture batch manifest must include:

- capture_id
- capture_date
- capture_timestamp
- source
- schema_version
- file inventory
- file hashes
- row counts
- security counts
- earliest source timestamp
- latest source timestamp
- missing components
- warnings
- capture status
- code/config version
""",
    )

    write_text(
        "pdc001_schema_version_policy.md",
        f"""
# Schema Version Policy

Draft schema version:

`{SCHEMA_VERSION}`

Any field addition, removal or type change requires:

- new schema version
- effective date
- change reason
- backward compatibility statement
- migration policy if required

Status:

`DRAFT_NOT_FROZEN`
""",
    )

    write_text(
        "pdc001_transformation_version_policy.md",
        """
# Transformation Version Policy

Each raw-to-normalized transformation must record:

- transformation_id
- code hash or commit hash
- configuration version
- input hashes
- output hashes
- execution timestamp
- warnings/errors

Same raw input and same transformation version must produce deterministic output.
""",
    )

    write_text(
        "pdc001_data_lineage.md",
        """
# Data Lineage

Required lineage:

```text
source
  -> raw artifact
  -> normalized artifact
  -> security master
  -> universe snapshot
  -> future alpha input
```

Current status:

`PARTIAL`

Reason:

The architecture is documented, but source access is unresolved.
""",
    )

    write_text(
        "pdc001_capture_frequency_policy.md",
        """
# Capture Frequency Policy

## Security Master

Daily after official close/finalization, plus event-driven if source supports it.

## Universe Snapshot

Every US equity trading day.

## OHLCV

Daily after official close/finalization.

## Corporate Actions

Daily or event-driven where supported.

## Industry Metadata

Periodic/event-driven only if later used.

Blocker:

Exact source finalization cadence is unresolved.
""",
    )

    write_text(
        "pdc001_trading_calendar_policy.md",
        """
# Trading Calendar Policy

Authoritative calendar:

`NYSE/Nasdaq US equity trading calendar`

Capture must distinguish:

- trading days
- weekends
- holidays
- half-days
- exceptional closures

Missing data on market holidays must not be classified as capture failure.

Blocker:

The concrete calendar library/source has not been frozen.
""",
    )

    write_text(
        "pdc001_failure_recovery_policy.md",
        """
# Failure, Recovery And Replay Policy

Capture states:

- SUCCESS
- PARTIAL_SUCCESS
- FAILED
- RETRY_PENDING
- MANUAL_REVIEW

Recovery provenance:

- LIVE_CAPTURE
- VERIFIED_REPLAY
- LATE_RETRIEVAL
- UNVERIFIED_BACKFILL

`UNVERIFIED_BACKFILL` must not enter the formal prospective research dataset.

Failed manifests must be preserved and never replaced.
""",
    )

    write_text(
        "pdc001_license_assessment.md",
        """
# License Assessment

License status:

`UNRESOLVED`

Required rights before PDC-002:

- local storage
- research use
- automated retrieval
- derived dataset creation
- internal commercial research if relevant
- live-trading support if eventually needed
- retention
- backups
- server/cloud deployment

Critical blocker:

`LICENSE_BLOCKER = YES`
""",
    )

    write_text(
        "pdc001_csm_tsm_data_compatibility.md",
        """
# CSM x TSM Data Compatibility

Structural compatibility:

`PARTIAL`

The proposed capture architecture can eventually support frozen CSM x TSM if it captures:

- adjusted close or auditable equivalent
- enough lookback history for CSM and TSM
- deterministic eligible universe
- monthly trading/rebalance calendar
- stable security identifiers
- delisting/lifecycle representation
- missing-data flags

Compatibility blocker:

No verified source currently guarantees these fields.

No performance was evaluated.
""",
    )

    write_text(
        "pdc001_minimum_observation_requirement.md",
        """
# Minimum Observation Requirement

Minimum before any formal alpha evaluation may be considered:

- At least 252 trading days of prospective captured lookback before first signal eligibility.
- At least 24 monthly rebalance observations after first eligible signal date.
- Preferably more than one volatility/regime environment before strong inference.

This rule is based on frozen lookback requirements and minimum observation logic, not expected profitability.

Early operational health checks may inspect data quality only.
""",
    )

    write_text(
        "pdc001_dry_run_report.md",
        f"""
# Dry Run Report

Dry-run type:

`NON_FORMAL_TEST_CAPTURE`

Result:

`PARTIAL`

Validated:

- local artifact creation
- CSV schema writing
- SHA256 hashing
- manifest generation

Not validated:

- real source access
- real security master schema
- real corporate action feed
- real market data feed
- license rights

Sample artifact:

`{dry_run['sample_path']}`

Sample SHA256:

`{dry_run['sample_sha256']}`

Manifest:

`{dry_run['manifest_path']}`

Manifest SHA256:

`{dry_run['manifest_sha256']}`

This dry run does not establish scientific T0.
""",
    )

    blockers = [
        "Raw market data source unresolved",
        "Security-master source unresolved",
        "Corporate-action source unresolved",
        "License unresolved",
        "Immutable/write-once enforcement not implemented",
        "Calendar source not frozen",
        "Source finalization timestamps unresolved",
    ]

    checklist_rows = [
        {"criterion": "exchange scope frozen", "status": "PASS", "evidence": "NYSE, Nasdaq, NYSE American included; OTC/non-US excluded."},
        {"criterion": "security type scope frozen", "status": "PARTIAL", "evidence": "Policy drafted, source tags unverified."},
        {"criterion": "universe rules frozen", "status": "PARTIAL", "evidence": "Rule drafted, active/tradable/listing fields unverified."},
        {"criterion": "identifier policy frozen", "status": "PARTIAL", "evidence": "Hierarchy/fallback drafted, source permanent ID unverified."},
        {"criterion": "lifecycle handling frozen", "status": "PARTIAL", "evidence": "Policy drafted, source unresolved."},
        {"criterion": "corporate-action handling frozen", "status": "PARTIAL", "evidence": "Event schema drafted, source unresolved."},
        {"criterion": "raw/adjusted data policy frozen", "status": "PASS", "evidence": "Raw and adjusted storage policy separated."},
        {"criterion": "timestamp policy frozen", "status": "PARTIAL", "evidence": "UTC/source/ingestion semantics drafted, source semantics unresolved."},
        {"criterion": "snapshot cadence frozen", "status": "PARTIAL", "evidence": "Daily post-close cadence drafted, source finalization unresolved."},
        {"criterion": "missing/stale rules frozen", "status": "PASS", "evidence": "Freshness statuses and no silent fill policy defined."},
        {"criterion": "immutable storage design frozen", "status": "PARTIAL", "evidence": "Layout drafted, write-once enforcement not implemented."},
        {"criterion": "hash policy operational", "status": "PASS", "evidence": "Dry-run SHA256 hash generated."},
        {"criterion": "manifest policy operational", "status": "PASS", "evidence": "Dry-run manifest generated."},
        {"criterion": "schema version frozen", "status": "NO", "evidence": "Draft schema exists but source schemas unresolved."},
        {"criterion": "source access real", "status": "FAIL", "evidence": "No real source access verified."},
        {"criterion": "licensing sufficient", "status": "FAIL", "evidence": "License unresolved."},
        {"criterion": "reproducibility dry-run succeeds", "status": "PARTIAL", "evidence": "Local mechanics only; no real source."},
    ]
    write_csv(OUT / "pdc001_acceptance_checklist.csv", checklist_rows)

    write_text(
        "pdc001_acceptance_checklist.md",
        "\n".join(
            [
                "# Acceptance Checklist",
                "",
                "| Criterion | Status | Evidence |",
                "| --- | --- | --- |",
                *[f"| {r['criterion']} | {r['status']} | {r['evidence']} |" for r in checklist_rows],
            ]
        ),
    )

    write_text(
        "pdc001_protocol_incidents.md",
        """
# Protocol Incidents

Performance peeking:

`NONE DETECTED`

Alpha logic changes:

`NONE DETECTED`

Formal capture launched:

`NO`

Scientific T0 established:

`NO`
""",
    )

    write_text(
        "pdc001_final_decision.md",
        f"""
# PDC-001 Final Decision

## Overall Decision

`{FINAL_DECISION}`

## Specification ID

`{SPEC_ID}`

## Critical Blockers

{chr(10).join(f"- {b}" for b in blockers)}

## Scientific T0

`NOT_ESTABLISHED`

## PDC-002

`NOT AUTHORIZED`

## Authorized Next Action

`PDC-001 REMEDIATION`

No alpha research, formal capture, RVP, benchmark race, net-of-cost evaluation or production work is authorized.
""",
    )

    # Hash policy artifacts.
    policy_files = [
        "pdc001_specification_and_freeze_report.md",
        "pdc001_market_exchange_scope.md",
        "pdc001_security_type_policy.md",
        "pdc001_security_type_policy.csv",
        "pdc001_security_identifier_policy.md",
        "pdc001_universe_definition.md",
        "pdc001_universe_snapshot_policy.md",
        "pdc001_security_lifecycle_policy.md",
        "pdc001_ipo_delisting_suspension_policy.md",
        "pdc001_corporate_action_policy.md",
        "pdc001_market_data_schema.md",
        "pdc001_raw_adjusted_price_policy.md",
        "pdc001_timestamp_policy.md",
        "pdc001_missing_stale_data_policy.md",
        "pdc001_data_revision_policy.md",
        "pdc001_storage_architecture.md",
        "pdc001_hash_manifest_policy.md",
        "pdc001_schema_version_policy.md",
        "pdc001_transformation_version_policy.md",
        "pdc001_data_lineage.md",
        "pdc001_capture_frequency_policy.md",
        "pdc001_trading_calendar_policy.md",
        "pdc001_failure_recovery_policy.md",
        "pdc001_license_assessment.md",
        "pdc001_csm_tsm_data_compatibility.md",
        "pdc001_minimum_observation_requirement.md",
        "pdc001_dry_run_report.md",
        "pdc001_acceptance_checklist.md",
        "pdc001_acceptance_checklist.csv",
        "pdc001_protocol_incidents.md",
        "pdc001_final_decision.md",
    ]
    hash_rows = [
        {"artifact": name, "path": str((OUT / name).relative_to(ROOT)), "sha256": sha256(OUT / name)}
        for name in policy_files
    ]
    write_csv(OUT / "pdc001_artifact_hashes.csv", hash_rows)

    manifest = {
        "program_id": "PDC-001",
        "program_name": "Prospective Data Capture Specification & Freeze",
        "parent_scope": "RSR-D",
        "creation_date_utc": generated_at,
        "specification_id": SPEC_ID,
        "schema_version": SCHEMA_VERSION,
        "scientific_t0_status": "NOT_ESTABLISHED",
        "market": "US equities",
        "exchange_scope": "NYSE, Nasdaq, NYSE American",
        "security_type_scope": "Draft: include US common stocks; conditionally REITs and multiple share classes; exclude funds, derivatives, ADRs and non-common structures",
        "universe_rule": "Draft deterministic active/tradable listed security rule using records captured at or before T",
        "selected_sources": {
            "raw_market_data_source": "UNRESOLVED",
            "security_master_source": "UNRESOLVED",
            "corporate_action_source": "UNRESOLVED",
        },
        "timestamp_standard": "UTC storage with event/source/available/ingestion distinction where available",
        "capture_cadence": "Draft daily post-close by domain; exact source finalization unresolved",
        "identifier_policy": "Partial hierarchy plus internal fallback; source permanent ID unresolved",
        "license_state": "UNRESOLVED",
        "alpha_logic_changed": "NO",
        "performance_evaluation_performed": "NO",
        "performance_peeking_detected": "NO",
        "critical_blockers": len(blockers),
        "unresolved_blockers": blockers,
        "dry_run_result": "PARTIAL",
        "artifact_hashes": "pdc001_artifact_hashes.csv",
        "final_decision": FINAL_DECISION,
        "pdc002_authorized": "NO",
        "rvp_authorized": "NO",
        "production_authorized": "NO",
        "authorized_next_action": "PDC-001 REMEDIATION",
    }
    (OUT / "pdc001_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
