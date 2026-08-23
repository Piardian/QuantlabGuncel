# BRD-001 / HV-001: Confidence Interval Report

## Purpose

Report uncertainty estimates for LOW_BREADTH versus HIGH_BREADTH differences.

## Bootstrap Confidence Intervals

| Hypothesis | Variable | High - Low | 95% CI Low | 95% CI High |
| --- | --- | ---: | ---: | ---: |
| H1 | BRD-001 breadth | 0.5061 | 0.4972 | 0.5146 |
| H2 | SPY distance from SMA200 | 0.1423 | 0.1381 | 0.1464 |
| H3 | SPY 20d realized volatility | -0.1529 | -0.1631 | -0.1432 |
| H4 | SPY 52w drawdown | 0.1069 | 0.1028 | 0.1111 |
| H5 | SPY above SMA200 | 0.7950 | 0.7676 | 0.8238 |

## Assessment

All preregistered confidence intervals exclude zero in the expected direction.

Classification:

```text
Supported by evidence
```

## Statistical Test Note

SciPy was not available in the local environment.

HV-001 therefore used a deterministic fixed-seed permutation test for mean difference rather than Mann-Whitney.

This substitution preserves the explanatory validation objective and avoids adding new variables or tuning choices.

