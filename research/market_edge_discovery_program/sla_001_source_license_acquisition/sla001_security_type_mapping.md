# SLA-001 Security-Type Mapping

## Decision

`NOT FROZEN`

## Reason

SLA-001 could not inspect actual source taxonomies because no authenticated source stack is available.

PDC-001 must not freeze security-type rules against assumed vendor fields.

## Required Future Inspection

The selected source must distinguish, or support deterministic exclusion of:

- common stock
- REIT
- ADR
- ETF
- preferred stock
- closed-end fund
- warrant
- unit
- rights
- SPAC
- foreign ordinary
- multiple share classes

## Current Source-Level Evidence

| Vendor | Security-Type Mapping Status |
|---|---|
| Databento | `PUBLIC_DOCS_ONLY / NOT_INSPECTED` |
| Nasdaq Data Link / Sharadar | `PUBLIC_DOCS_ONLY / NOT_INSPECTED` |
| Norgate Data | `PUBLIC_DOCS_ONLY / NOT_INSPECTED` |
| Tiingo | `PUBLIC_DOCS_ONLY / NOT_INSPECTED` |
| Polygon / Massive | `PUBLIC_DOCS_ONLY / NOT_INSPECTED` |
| WRDS / CRSP / Compustat | `NO_LOCAL_ACCESS / NOT_INSPECTED` |

## Conclusion

Security-type policy remains blocked until actual source fields and taxonomy values are inspected.

