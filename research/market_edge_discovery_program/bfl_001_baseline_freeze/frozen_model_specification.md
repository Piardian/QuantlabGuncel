# Frozen Model Specification

## Baseline Name

`CSMxTSM_GROSS_RESEARCH_BASELINE_V1`

## Primary Workflow

CSM-001 x TSM-001

## CSM-001

Final status:

`Completed scientific construct`

Role:

Stock-level cross-sectional relative leadership.

Frozen high state:

`csm001_top_decile_flag == True`

## TSM-001

Final status:

`UNKNOWN`

Role:

Own-trend / positive state gate.

Frozen positive state:

`tsm001_positive_state == True`

## Workflow State

CSM x TSM selected state:

`csm001_top_decile_flag == True AND tsm001_positive_state == True`

## Portfolio Accounting Currently Frozen

WPC-002:

`Portfolio Construction Supported`

Policy:

- monthly rebalance
- equal-weight
- gross accounting only
- no costs
- no production execution

## Workflow Readiness

WRS-002:

`Research-Validated Portfolio Workflow, Not Production Ready`
