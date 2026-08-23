# DSA-001 Decision Tree

```text
Start
  |
  v
Can a source provide PIT universe membership?
  |-- NO --> SOURCE_UNAVAILABLE or PARTIAL_SOURCE_APPROVED if narrower scope exists
  |
  v
Can a source provide survivorship/delisted securities?
  |-- NO --> SOURCE_UNAVAILABLE or PARTIAL_SOURCE_APPROVED if narrower scope exists
  |
  v
Can security lifecycle be reconstructed deterministically?
  |-- NO --> PARTIAL_SOURCE_APPROVED or SOURCE_UNAVAILABLE
  |
  v
Can corporate actions be audited/reproduced?
  |-- NO --> PARTIAL_SOURCE_APPROVED if documented as limitation
  |
  v
Can source be licensed, retained, and reproduced?
  |-- NO --> SOURCE_UNAVAILABLE
  |
  v
SOURCE_APPROVED
```

## Partial Approval Examples

`PARTIAL_SOURCE_APPROVED` is appropriate when:

- PIT data begins later than the desired research period.
- Delisted coverage is reliable only after a specific date.
- Universe membership exists only for one index or one investable scope.
- Corporate-action coverage is acceptable but not complete for older periods.

In this case the future baseline must explicitly narrow its scope before BFL-002.

## Rejection Examples

`SOURCE_UNAVAILABLE` is appropriate when:

- Only current constituents are available.
- Delisted securities cannot be represented.
- Membership effective dates cannot be reconstructed.
- Licensing prevents reproducible research use.
- Data cannot be archived or regenerated.
