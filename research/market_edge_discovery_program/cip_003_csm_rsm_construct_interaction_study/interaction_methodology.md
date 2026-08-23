# Interaction Methodology

## Frozen Inputs

- CSM-001 state file: `output/csm_001_cv001/csm001_construct_state.csv`
- RSM-001 state file: `output/rsm_001/rsm001_residual_momentum_state.csv`

## Common Panel

RSM-001 is ticker-month level.

CSM-001 is ticker-date level.

For each ticker-month, the last available CSM-001 state date inside the month is used to align with the RSM-001 month-end state.

## High-State Definitions

- CSM_HIGH: frozen `csm001_top_decile_flag == True`
- RSM_HIGH: frozen `rsm_state == TOP_DECILE`

## Outcome Used For Conditional Predictive Analysis

Future one-month security return is calculated from the frozen RSM monthly return panel using a one-month forward shift by ticker.

No trading strategy or portfolio accounting is performed.
