# BRD-001 / PV-001: Forecast Horizon Analysis

## Purpose

Compare predictive evidence across 20-day and 60-day horizons.

## 20-Day Horizon

| Target | Rank Corr | AUC | Classification |
| --- | ---: | ---: | --- |
| Future realized volatility | -0.4158 | 0.8247 | Supported by evidence |
| Future drawdown risk | 0.0712 | 0.6296 | Partially supported |
| Future trend deterioration | -0.6396 | 0.9121 | Supported by evidence |
| Future returns | -0.1667 | 0.2734 | Not supported |

## 60-Day Horizon

| Target | Rank Corr | AUC | Classification |
| --- | ---: | ---: | --- |
| Future realized volatility | -0.3633 | 0.7959 | Supported by evidence |
| Future drawdown risk | 0.0728 | 0.6636 | Partially supported |
| Future trend deterioration | -0.5322 | 0.8108 | Supported by evidence |
| Future returns | -0.1973 | 0.2970 | Not supported |

## Assessment

Predictive evidence is strongest for:

- future realized volatility
- future trend deterioration risk

Predictive evidence is weaker for:

- future drawdown risk

Predictive evidence is not supported for:

- future returns

## Boundary

This is not a trading horizon analysis and does not evaluate economic outcomes.

