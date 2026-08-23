# LIQ-001 / PV-001: Predictive Validation

## Purpose

Evaluate whether LIQ-001 contains predictive information about future market behavior.

This is predictive validation only. No alpha, profitability, economic utility, Sharpe, CAGR, or portfolio claim is made.

## Overall Classification

**Supported by evidence**

## Hypothesis Classifications

hypothesis                          target        classification
        H1      future realized volatility Supported by evidence
        H2 future absolute market movement Supported by evidence
        H3            future drawdown risk   Partially supported
        H4 future MR-001 STRESS occurrence Supported by evidence

## Predictive Metrics

 horizon                    target      metric  estimate   ci_low  ci_high  observations  baseline
       5    future_realized_vol_5d spearman_ic  0.372777 0.342047 0.400942          3752       0.0
       5        future_abs_move_5d spearman_ic  0.408317 0.380329 0.437200          3752       0.0
       5  future_drawdown_depth_5d spearman_ic  0.062915 0.028854 0.096230          3752       0.0
       5   future_mr_stress_any_5d         auc  0.920719 0.910233 0.930749          3752       0.5
      20   future_realized_vol_20d spearman_ic  0.390661 0.361437 0.418920          3752       0.0
      20       future_abs_move_20d spearman_ic  0.405855 0.376950 0.434632          3752       0.0
      20 future_drawdown_depth_20d spearman_ic  0.106704 0.073701 0.139180          3752       0.0
      20  future_mr_stress_any_20d         auc  0.877461 0.864720 0.889820          3752       0.5
      60   future_realized_vol_60d spearman_ic  0.391344 0.362805 0.419703          3752       0.0
      60       future_abs_move_60d spearman_ic  0.392669 0.364569 0.420330          3752       0.0
      60 future_drawdown_depth_60d spearman_ic  0.107389 0.076046 0.139954          3752       0.0
      60  future_mr_stress_any_60d         auc  0.796905 0.781974 0.811115          3752       0.5

## Interpretation

LIQ-001 shows strongest predictive evidence for future MR-001 STRESS occurrence and directionally positive evidence for future volatility, absolute movement, and drawdown risk.

The evidence should be interpreted as risk-state predictive information, not as a trading signal or alpha source.
