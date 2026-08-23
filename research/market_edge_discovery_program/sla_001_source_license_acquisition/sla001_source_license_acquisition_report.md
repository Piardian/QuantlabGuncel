# SLA-001 — Source & License Acquisition

## Program

Market Edge Discovery Program

## Purpose

SLA-001 evaluates whether the project currently has, or can verify, an actually usable source stack for prospective US equity capture.

This stage evaluates source access, schema inspectability, licensing, identity semantics, lifecycle coverage, corporate actions, market coverage and operational feasibility only.

It does not evaluate alpha, returns, Sharpe, drawdown, rankings, or strategy performance.

## Current State

| Item | State |
|---|---|
| PDC-001 | `PDC_SPECIFICATION_NOT_READY` |
| PDC-001 Remediation Cycle 1 | `REMEDIATION_INCOMPLETE` |
| Scientific T0 | `NOT_ESTABLISHED` |
| Alpha logic | `FROZEN` |
| Performance evaluation | `FORBIDDEN` |
| RVP | `NOT_AUTHORIZED` |
| Production | `NOT_AUTHORIZED` |

## Evidence Sources

| Evidence Type | Result |
|---|---|
| Local credential/environment inspection | No relevant vendor credential environment variables detected |
| Local data directory inspection | No approved vendor data directories detected |
| Repository credential/config scan | No usable vendor access configuration detected |
| Public vendor documentation review | Multiple plausible vendors identified, but public documentation is not sufficient for SLA acquisition |

## Candidate Sources Evaluated

| Source | Evidence Level | SLA Access Status |
|---|---|---|
| Databento | Public documentation only | `UNAVAILABLE` |
| Nasdaq Data Link / Sharadar | Public documentation only | `UNAVAILABLE` |
| Norgate Data | Public documentation only | `UNAVAILABLE` |
| Tiingo | Public documentation only | `UNAVAILABLE` |
| Polygon / Massive | Public documentation only | `UNAVAILABLE` |
| WRDS / CRSP / Compustat | Prior DSA evidence, no account evidence | `UNAVAILABLE` |

## Public Documentation Findings

Databento publicly documents corporate actions, security master/reference data, US exchange coverage, point-in-time corporate action format, and file/API export capabilities. This is strong source-candidate evidence, but not authenticated project access.

Sharadar publicly describes securities master, EOD stock prices, and corporate actions tables, including API and bulk download access. This is strong source-candidate evidence, but not authenticated project access.

Norgate publicly emphasizes survivorship-bias-free US equity data and delisted securities coverage. However, its access model and license must be inspected directly before approval.

Tiingo publicly documents broad EOD coverage, OHLCV, dividends, splits, raw and adjusted prices, and internal-use license tiers. However, project-specific access and license rights are not verified.

Polygon/Massive publicly documents financial market APIs and terms, but no authenticated project entitlement or SLA-compatible license evidence is available.

## Final Decision

`SOURCE_STACK_UNAVAILABLE`

## Rationale

SLA-001 requires actual usable access, not theoretical vendor suitability. No candidate source currently satisfies the required combination of:

- authenticated access
- actual sample retrieval
- schema inspection
- license approval
- security master verification
- corporate-action verification
- market data verification
- permanent identifier verification
- local immutable storage permission

Therefore no source stack can be acquired or approved at this time.

## Authorized Next Action

`DATA_STRATEGY_BUDGET_VENDOR_DECISION_REVIEW`

PDC-001 refreeze remains prohibited.

## Sources Used

- Databento corporate actions and reference data documentation: https://databento.com/corporate-actions
- Sharadar public product documentation: https://sharadar.com/
- Nasdaq Data Link Sharadar pages: https://data.nasdaq.com/databases/SEP and https://data.nasdaq.com/databases/SFA
- Norgate Data overview and data content pages: https://norgatedata.com/ and https://norgatedata.com/data-content-tables.php
- Tiingo EOD product and documentation pages: https://www.tiingo.com/products/end-of-day-stock-price-data and https://www.tiingo.com/documentation/end-of-day
- Tiingo terms of service: https://app.tiingo.com/tos/
- Massive/Polygon terms pages: https://massive.com/legal/terms

