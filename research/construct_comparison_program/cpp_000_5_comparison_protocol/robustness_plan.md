# CPP-000.5

# Robustness and Sensitivity Plan

## Required Robustness Checks

- Common Sample vs Pairwise Maximum Sample comparison where applicable.
- Rolling windows: 252, 756, and 1260 observations where available.
- Calendar-year stability where sample permits.
- Crisis/calm segmentation only after CPP-001 defines objective state labels from frozen constructs or existing calendar periods.
- Bootstrap confidence intervals for key dependence and incremental-information estimates.
- Leave-one-construct-out multivariate sensitivity.

## Stability Requirement

A relationship is stable only if direction and broad magnitude class remain consistent in at least 75 percent of eligible robustness windows.

## Failure Rule

If a conclusion depends on one period, one sample definition, or one extreme window, classify as Partially supported or Inconclusive depending on severity.
