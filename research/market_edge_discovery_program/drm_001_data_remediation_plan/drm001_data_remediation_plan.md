# DRM-001 Data Remediation Plan

## Program

Market Edge Discovery Program

## Baseline Context

Parent baseline:

`CSMxTSM_GROSS_RESEARCH_BASELINE_V1`

BFL-001 status:

`PASS - Baseline Frozen`

DBA-001 status:

`Audit Failed`

## Purpose

DRM-001 defines the permitted remediation scope required after DBA-001.

This is not a performance study.

This is not a strategy redesign.

This is not a parameter optimization exercise.

The objective is to determine what data and bias issues must be remediated before a new baseline can be frozen as BFL-002.

## Scientific Interpretation

DBA-001 did not reject the CSM x TSM strategy logic.

DBA-001 rejected the evidentiary reliability of V1 historical performance as a production-quality scientific claim because critical data/bias findings remain unresolved.

V1 must be preserved as an archived research artifact. It must not be silently edited.

## Remediation Principle

The alpha model remains frozen.

The following must remain unchanged unless a new research program is explicitly opened:

- CSM construct definition
- TSM construct definition
- CSM x TSM selection logic
- Momentum lookbacks
- Ranking thresholds
- Rebalance schedule
- Portfolio accounting rules
- Workflow logic

Permitted changes are limited to data integrity and bias remediation required by DBA-001.

## Required Remediation Domains

1. Universe integrity
2. Survivorship and delisting integrity
3. Point-in-time integrity
4. Corporate action auditability
5. Data integrity verification
6. Liquidity/tradability carry-forward documentation

## Required Sequence

```text
BFL-001
  -> DBA-001 FAIL
  -> DRM-001 remediation scope freeze
  -> data/bias remediation implementation
  -> BFL-002 baseline V2 freeze
  -> DBA-002 remediated baseline audit
  -> RVP-001 only if DBA-002 authorizes progression
```

## Forbidden During DRM-001

- Do not inspect V2 performance.
- Do not calculate CAGR, Sharpe, drawdown, alpha, or portfolio profitability.
- Do not tune parameters.
- Do not change strategy logic.
- Do not change construct definitions.
- Do not reclassify prior evidence as valid for V2.
- Do not claim production readiness.

## Allowed During DRM-001

- Data source evaluation
- Point-in-time universe design
- Delisting coverage assessment
- Listing lifecycle reconstruction
- Corporate action verification design
- Missing data policy definition
- Symbol mapping policy definition
- Baseline revision documentation

## Completion Criteria

DRM-001 is complete when:

- Every DBA-001 finding has a documented remediation plan.
- No alpha logic change is required.
- V1 remains preserved.
- BFL-002 requirements are fully specified.
- DBA-002 audit requirements are preregistered.

## Current Status

`Remediation Plan Registered`

The next engineering/research action is controlled data remediation followed by BFL-002.
