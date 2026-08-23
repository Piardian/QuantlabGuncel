# EXB-001 Missing Data Policy

## Frozen Policy

| Condition | Required Handling |
| --- | --- |
| Missing daily bar | Symbol is ineligible for that date. |
| Missing warm-up history | Symbol remains ineligible until sufficient usable history exists. |
| Duplicate symbol-date row | Fail the affected batch and record incident. |
| Invalid OHLC relationship | Exclude affected row/security/date and record incident. |
| Non-positive price | Exclude affected row/security/date and record incident. |
| Zero or negative volume | Symbol is ineligible for that date. |
| API failure | Retry using bounded deterministic retry policy; if unresolved, mark batch incomplete. |
| Corporate-action ambiguity | Do not repair silently; record limitation. |

## Forward Fill

Silent forward filling is forbidden.

## Performance Peeking

Missingness decisions must not depend on observed returns or strategy outcomes.
