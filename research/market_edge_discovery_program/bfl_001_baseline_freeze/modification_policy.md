# Modification Policy

## Frozen Baseline Policy

After BFL-001, no validation stage may modify:

- CSM-001 definition
- TSM-001 definition
- CSM x TSM workflow rule
- lookback windows
- ranking method
- high-state thresholds
- rebalance frequency
- WPC-002 gross accounting policy

## If A Change Is Required

Any change requires a new baseline release.

The modified workflow must not be mixed with `CSMxTSM_GROSS_RESEARCH_BASELINE_V1` evidence.

## Allowed During Later Stages

Later stages may audit, evaluate, stress test or reject the baseline.

They may not silently improve it.
