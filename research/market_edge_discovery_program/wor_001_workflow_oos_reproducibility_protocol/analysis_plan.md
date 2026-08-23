# Analysis Plan

## Study Name

WOR-002: Workflow Out-of-Sample Reproducibility Audit

## Required OOS Inputs

The OOS execution stage must regenerate or load frozen CSM-001 and TSM-001 outputs for a non-overlapping period after 2025-12-30.

Required fields:

- date
- ticker
- csm001_top_decile_flag
- csm001_momentum_score
- csm001_valid_observation
- tsm001_positive_state
- tsm001_direction_score
- tsm001_valid_observation

## Registered State Definitions

CSM state:

- CSM_HIGH: `csm001_top_decile_flag == True`
- CSM_NOT_HIGH: `csm001_top_decile_flag == False`

TSM state:

- TSM_HIGH: `tsm001_positive_state == True`
- TSM_LOW: `tsm001_positive_state == False`

Workflow states:

- CSM_HIGH x TSM_HIGH
- CSM_HIGH x TSM_LOW
- CSM_NOT_HIGH x TSM_HIGH
- CSM_NOT_HIGH x TSM_LOW

## Required Analyses

1. OOS data availability check
2. Non-overlap verification
3. Frozen implementation verification
4. Common OOS sample reconstruction
5. OOS workflow state matrix
6. OOS nested-state analysis
7. OOS agreement metrics
8. OOS time stability analysis
9. OOS symbol coverage analysis
10. Reproducibility classification versus CWS-001

## Registered Metrics

- Observation count
- Ticker count
- Date coverage
- Jaccard similarity
- P(TSM_HIGH | CSM_HIGH)
- P(CSM_HIGH | TSM_HIGH)
- CSM_HIGH x TSM_LOW count
- State coverage
- Year or month stability, depending on available OOS length

## Reproducibility Criteria

Reproduced:

- OOS period is non-overlapping.
- Sufficient OOS observations exist.
- P(TSM_HIGH | CSM_HIGH) remains very high.
- TSM_HIGH remains materially broader than CSM_HIGH.
- CSM_HIGH x TSM_LOW remains rare.

Partially Reproduced:

- The nesting relationship mostly remains, but one or more stability metrics weaken.

Not Reproduced:

- CSM_HIGH frequently appears outside TSM_HIGH.
- TSM_HIGH is no longer materially broader than CSM_HIGH.

Inconclusive:

- OOS sample is too small.
- OOS data are unavailable.
- Required frozen fields cannot be regenerated.
