# BFL-002 Acceptance Checklist

Before BFL-002 can be considered complete, all checklist items must be satisfied.

## Critical Findings

- [ ] All Critical DBA-001 findings have an implemented remediation.
- [ ] Every Critical remediation has evidence.
- [ ] Every Critical remediation maps to a DBA-001 finding ID.

## Major Findings

- [ ] Major findings are either closed or explicitly carried as justified limitations.
- [ ] Any open Major limitation has a documented reason.
- [ ] Any open Major limitation includes expected bias direction if knowable.

## Logic Freeze

- [ ] CSM construct logic is unchanged.
- [ ] TSM construct logic is unchanged.
- [ ] CSM x TSM workflow logic is unchanged.
- [ ] Rebalance logic is unchanged.
- [ ] Portfolio accounting logic is unchanged.
- [ ] Logic integrity is verified by spec/hash comparison where possible.

## V1 To V2 Delta

- [ ] `v1_to_v2_remediation_delta.md` is complete.
- [ ] V2 changes are limited to data, universe, PIT, corporate action, lifecycle, or integrity remediation.
- [ ] No V2 change is justified by performance.

## Data Quality

- [ ] Coverage checks completed.
- [ ] Symbol lifecycle checks completed.
- [ ] Missingness checks completed.
- [ ] Duplicate timestamp checks completed.
- [ ] Corporate-action sanity checks completed.
- [ ] Timestamp and decision-time checks completed.

## No Performance Peeking

- [ ] No CAGR inspected.
- [ ] No Sharpe inspected.
- [ ] No drawdown inspected.
- [ ] No equity curve inspected.
- [ ] No rank spread inspected.
- [ ] No benchmark comparison inspected.
- [ ] No "does it still work?" test performed.

## Freeze Artifacts

- [ ] V2 artifact inventory complete.
- [ ] V2 SHA256 hashes complete.
- [ ] Parent V1 hashes referenced where applicable.
- [ ] Manifest includes `parent_baseline = CSMxTSM_GROSS_RESEARCH_BASELINE_V1`.
- [ ] Manifest includes `revision_reason = DBA-001 findings`.
- [ ] Manifest includes `alpha_status = UNEVALUATED_AFTER_REMEDIATION`.
- [ ] Manifest includes `production_status = NOT_AUTHORIZED`.

## Post-Freeze Rule

- [ ] After BFL-002, all V2 artifacts are frozen.
- [ ] DBA-002 will run only on frozen V2 artifacts.
