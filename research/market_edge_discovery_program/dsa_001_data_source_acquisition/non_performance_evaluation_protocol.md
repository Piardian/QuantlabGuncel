# Non-Performance Evaluation Protocol

## Purpose

DSA-001 evaluates data sources only by data quality, bias control, reproducibility, access, and implementation feasibility.

## Prohibited Evidence

The following must not be calculated, inspected, stored, or used:

- Strategy return
- CAGR
- Sharpe
- Sortino
- Drawdown
- Alpha
- Hit rate
- Win rate
- Profit factor
- CSM return spread
- TSM return spread
- Benchmark outperformance
- Equity curve

## Permitted Evidence

- Field availability
- Sample schema
- Identifier continuity
- Listing/delisting coverage
- PIT membership effective dates
- Corporate-action event coverage
- Daily price/volume coverage
- Missingness
- Duplicate records
- Re-download/versioning reproducibility
- Licensing documentation
- Cost/access practicality

## Protocol Incident Rule

If performance is accidentally exposed, create a protocol incident record before continuing.

The incident must include:

- timestamp
- source
- metric exposed
- how exposure occurred
- whether the source selection process was contaminated
- remediation action
