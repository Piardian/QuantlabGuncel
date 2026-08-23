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
