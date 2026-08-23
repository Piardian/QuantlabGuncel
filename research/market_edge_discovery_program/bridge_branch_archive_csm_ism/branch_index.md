# CSM-001 x ISM-001 Bridge Branch Archive

## Purpose

This archive summarizes the CSM-001 x ISM-001 interaction attempt and the follow-up stock-to-industry bridge program.

It introduces no new empirical evidence and performs no implementation.

## Final Branch Status

**Blocked: valid point-in-time stock-to-industry data unavailable**

## Triggering Study

CIP-002 attempted to evaluate whether company-level leadership and industry-level leadership provide overlapping, incremental or complementary information.

Final CIP-002 conclusion:

**Inconclusive**

Reason:

CSM-001 is ticker-date level while ISM-001 is Ken French industry-month level. No frozen ticker-to-industry mapping exists.

## Bridge Follow-Up

| Stage | Folder | Result |
|---|---|---|
| CIP-002 | `cip_002_csm_ism_construct_interaction_study` | Inconclusive |
| SIB-001 | `sib_001_stock_industry_bridge_protocol` | Bridge Protocol Registered |
| SIB-002 | `sib_002_stock_industry_bridge_data_source_review` | Conditional GO |
| SIB-003 | `sib_003_stock_industry_bridge_definition` | Bridge Definition Blocked |

## Supported By Evidence

- CSM-001 and ISM-001 do not share a common observation unit.
- ISM-001 does not assign industries to individual stocks.
- ISM-001 stock-level applicability is not supported.
- A valid interaction study requires point-in-time stock-to-industry mapping.
- The repository does not currently contain the required point-in-time SIC/security master data.

## Not Supported

- CSM x ISM complementarity.
- CSM x ISM redundancy.
- CSM x ISM incremental information.
- A hierarchical leadership workflow.
- Any stock-level application of ISM-001.

## Required To Resume

The branch can resume only after acquiring and documenting one of:

- CRSP/Compustat historical SIC/security master data.
- Another validated point-in-time stock-level SIC source.
- Point-in-time GICS History plus a separately validated translation to Ken French 49.

## Stop Condition

No further code or statistical analysis is authorized until valid source data exists.
