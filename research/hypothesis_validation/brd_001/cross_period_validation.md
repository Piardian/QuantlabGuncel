# BRD-001 / HV-001: Cross-Period Validation

## Purpose

Evaluate whether the explanatory mechanism remains directionally consistent across historical periods.

## Period Blocks

| Period | Low N | High N | SPY Distance Diff | Vol Diff | Drawdown Diff | SPY Above Diff |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2010-2013 | 108 | 371 | 0.1478 | -0.1951 | 0.1048 | 0.9444 |
| 2014-2017 | 129 | 159 | 0.1114 | -0.1229 | 0.0710 | 0.9147 |
| 2018-2021 | 170 | 221 | 0.1746 | -0.2247 | 0.1221 | 0.7941 |
| 2022-2025 | 359 | 14 | 0.1638 | -0.1169 | 0.1180 | 0.7075 |

## Directional Stability

All four period blocks support the expected direction:

- HIGH_BREADTH had stronger SPY trend condition.
- HIGH_BREADTH had lower realized volatility.
- HIGH_BREADTH had shallower drawdown.
- HIGH_BREADTH had higher SPY-above-SMA200 frequency.

## Limitation

The 2022-2025 block contains only 14 HIGH_BREADTH observations.

This creates period imbalance and limits the strength of cross-period claims.

## Classification

```text
Partially supported
```

Reason:

Direction is stable, but period sample balance is imperfect.

