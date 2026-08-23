# BRD-001 / PV-001: Calibration Analysis

## Purpose

Evaluate binary risk-event discrimination using BRD-001 rank as a nonparametric score.

No fitted probability model was trained.

## AUC Results

| Hypothesis | Horizon | Event Rate | AUC | Rank-Probability Brier |
| --- | ---: | ---: | ---: | ---: |
| Future high volatility | 20d | 0.2001 | 0.8247 | 0.2295 |
| Future high volatility | 60d | 0.2001 | 0.7959 | 0.2387 |
| Future adverse drawdown | 20d | 0.2001 | 0.6296 | 0.2919 |
| Future adverse drawdown | 60d | 0.2001 | 0.6636 | 0.2811 |
| Future trend deterioration | 20d | 0.2781 | 0.9121 | 0.1679 |
| Future trend deterioration | 60d | 0.4248 | 0.8108 | 0.1815 |
| Future top-return event | 20d | 0.2001 | 0.2734 | 0.4059 |
| Future top-return event | 60d | 0.2001 | 0.2970 | 0.3984 |

## Assessment

BRD-001 discriminates future high-volatility and future trend-deterioration events.

Drawdown-event discrimination is weaker.

Return-event discrimination is not supported in the expected direction.

## Boundary

The rank-probability score is a diagnostic tool, not a calibrated production model.

