# DBA-002 Remediated Baseline Audit Protocol

## Purpose

DBA-002 must evaluate whether the BFL-002 remediated baseline resolves DBA-001 material findings without introducing new material data/bias issues.

No performance evaluation is allowed during DBA-002.

## Required Re-Audit Domains

1. Universe integrity
2. Survivorship and delisting integrity
3. Point-in-time integrity
4. Corporate actions
5. Signal timing
6. Liquidity and tradability
7. Data integrity
8. Baseline reproducibility

## Required Finding Closure Checks

| DBA-001 Finding | Required DBA-002 Question |
| --- | --- |
| DBA-001-F001 | Does V2 avoid applying a current-style universe backward through history? |
| DBA-001-F002 | Does V2 include or explicitly account for delisted/failed securities? |
| DBA-001-F003 | Does V2 evaluate eligibility using only information available at each historical date? |
| DBA-001-F004 | Does V2 preserve no same-close/future-return leakage in timing? |
| DBA-001-F005 | Does V2 document and verify corporate action adjustment integrity? |
| DBA-001-F006 | Are liquidity/capacity limitations preserved and not overstated? |
| DBA-001-F007 | Does V2 pass deterministic data integrity checks? |

## Authorization Rules

| DBA-002 Result | Decision |
| --- | --- |
| Critical findings = 0 and material major findings = 0 | RVP-001 authorized |
| Critical findings = 0 and remaining major findings are explicitly limited | Conditional progression may be considered |
| Critical findings > 0 | RVP-001 blocked |
| Survivorship remains FAIL | Production claim blocked |
| Point-in-time remains materially unresolved | Fundamental/event alpha validation blocked |

## Required Output

DBA-002 must produce a new findings register using the same schema as DBA-001:

```text
finding_id,audit_domain,artifact,severity,description,evidence,affected_period,affected_symbols,potential_bias_direction,baseline_impact,remediation_required,baseline_revision_required,status
```
