# Non-Definition Rationale

## Why A Definition Was Not Forced

Forcing a bridge definition would require inventing or assuming a data source.

That would violate:

- SIB-001 point-in-time requirement.
- SIB-002 conditional GO requirement.
- ISM-001 taxonomy limitations.
- CIP-002 frozen input boundary.

## Rejected Alternatives

Current metadata:

- Rejected because it can leak current classifications into historical observations.

Manual mapping:

- Rejected because it is discretionary and non-reproducible.

GICS without source access:

- Rejected because the actual point-in-time dataset is not present.

Ken French returns alone:

- Rejected because they are industry portfolio returns, not stock membership records.

## Scientific Interpretation

The correct conclusion is:

SIB-003 is blocked by missing source data, not by a failure of the bridge concept.
