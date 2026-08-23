# Baseline V1 To V2 Delta Template

## Purpose

This document defines the required delta disclosure for BFL-002.

V1 must remain preserved. V2 must be created as a new baseline with explicit parentage and documented remediation reason.

## Required BFL-002 Manifest Fields

```text
baseline_id: CSMxTSM_GROSS_RESEARCH_BASELINE_V2_BIAS_REMEDIATED
parent_baseline: CSMxTSM_GROSS_RESEARCH_BASELINE_V1
revision_reason: DBA-001 critical and major data/bias findings
alpha_logic_change: NONE
data_policy_change: YES
alpha_status: UNEVALUATED_AFTER_REMEDIATION
data_status: PENDING_DBA_002
production_status: NOT_AUTHORIZED
```

## Required Delta Table

| Field | V1 | V2 | Reason | DBA Finding |
| --- | --- | --- | --- | --- |
| Universe | Current-style broad universe | To be defined by remediation | Universe integrity | DBA-001-F001 |
| Survivorship / delisting | Not demonstrably survivorship-free | To be defined by remediation | Survivorship integrity | DBA-001-F002 |
| Point-in-time membership | Partial / absent in frozen artifacts | To be defined by remediation | PIT integrity | DBA-001-F003 |
| Corporate actions | Adjusted prices used, independent audit not frozen | To be defined by remediation | Corporate action auditability | DBA-001-F005 |
| CSM logic | Frozen | Unchanged | Alpha logic must not change | N/A |
| TSM logic | Frozen | Unchanged | Alpha logic must not change | N/A |
| CSM x TSM workflow | Frozen | Unchanged | Workflow logic must not change | N/A |
| Rebalance | Frozen | Unchanged | Timing policy must not change | N/A |
| Portfolio accounting | Frozen | Unchanged | Accounting policy must not change | N/A |

## Required Hash Policy

BFL-002 must produce a new artifact hash registry.

The BFL-002 registry must include:

- V2 artifact path
- V2 SHA256
- parent V1 artifact path where applicable
- parent V1 SHA256 where applicable
- DBA finding ID that justified the change
- whether logic changed

Logic-change value must be `NO` for all alpha/workflow logic artifacts.
