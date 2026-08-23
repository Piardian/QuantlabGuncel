# V1 To V2 Remediation Delta

## Purpose

This file is the required audit trail for all differences between:

`CSMxTSM_GROSS_RESEARCH_BASELINE_V1`

and the future:

`CSMxTSM_GROSS_RESEARCH_BASELINE_V2_BIAS_REMEDIATED`

Every change must be mechanical, evidence-backed, and linked to a DBA-001 finding.

No change may be justified by performance.

## Required Entry Format

```text
DBA finding ID:
V1 defect:
Remediation:
Affected artifacts:
Alpha logic changed:
Expected bias direction:
Verification test:
Status:
```

## DBA-001-F001

DBA finding ID:

`DBA-001-F001`

V1 defect:

Current-style broad equity universe was applied historically without frozen point-in-time membership fields.

Remediation:

To be completed during controlled remediation.

Affected artifacts:

- `adjusted_close_panel.csv`
- `csm001_construct_state.csv`
- `tsm001_construct_state.csv`
- downstream CSM x TSM workflow artifacts

Alpha logic changed:

`NO`

Expected bias direction:

`UPWARD`

Verification test:

For each historical date, verify every eligible security was known/listed/eligible as of that date.

Status:

`OPEN`

## DBA-001-F002

DBA finding ID:

`DBA-001-F002`

V1 defect:

Delisted and failed securities were not demonstrably represented in the frozen V1 universe and price history.

Remediation:

To be completed during controlled remediation.

Affected artifacts:

- price panel
- universe membership data
- construct state files
- workflow selected security files

Alpha logic changed:

`NO`

Expected bias direction:

`UPWARD`

Verification test:

Verify delisted securities are included during their valid trading lifetime and excluded after delisting, with delisting treatment documented.

Status:

`OPEN`

## DBA-001-F003

DBA finding ID:

`DBA-001-F003`

V1 defect:

Point-in-time security eligibility metadata was absent or incomplete.

Remediation:

To be completed during controlled remediation.

Affected artifacts:

- PIT eligibility table
- universe membership table
- construct state generation inputs

Alpha logic changed:

`NO`

Expected bias direction:

`UPWARD`

Verification test:

Confirm all eligibility decisions use only information available at or before the decision date.

Status:

`OPEN`

## DBA-001-F004

DBA finding ID:

`DBA-001-F004`

V1 defect:

No material defect identified. Signal timing passed DBA-001 as informational.

Remediation:

Carry timing policy forward unchanged.

Affected artifacts:

- workflow accounting protocol
- workflow selected state files

Alpha logic changed:

`NO`

Expected bias direction:

`NEUTRAL`

Verification test:

Confirm V2 preserves signal formation at rebalance close and return measurement from the next trading day.

Status:

`CLOSED / CARRY FORWARD`

## DBA-001-F005

DBA finding ID:

`DBA-001-F005`

V1 defect:

Adjusted prices were used, but independent corporate action verification was not frozen.

Remediation:

To be completed during controlled remediation.

Affected artifacts:

- adjusted price data
- corporate action documentation
- data quality report

Alpha logic changed:

`NO`

Expected bias direction:

`UNKNOWN`

Verification test:

Run split/dividend adjustment sanity checks and document the adjustment source.

Status:

`OPEN`

## DBA-001-F006

DBA finding ID:

`DBA-001-F006`

V1 defect:

Liquidity/capacity was partially supported but not sufficient for production authorization.

Remediation:

Carry limitation forward. Do not introduce new liquidity rules during BFL-002.

Affected artifacts:

- liquidity/capacity documentation
- future capacity gate references

Alpha logic changed:

`NO`

Expected bias direction:

`UNKNOWN`

Verification test:

Confirm limitation is preserved and not overstated as production readiness.

Status:

`KNOWN LIMITATION`

## DBA-001-F007

DBA finding ID:

`DBA-001-F007`

V1 defect:

General data integrity requires revalidation after any rebuilt V2 artifacts.

Remediation:

To be completed after V2 data artifacts are generated.

Affected artifacts:

- all V2 data artifacts

Alpha logic changed:

`NO`

Expected bias direction:

`UNKNOWN`

Verification test:

Run duplicate, missingness, coverage, timestamp, and consistency checks.

Status:

`OPEN`
