# Forecast Horizon Analysis

## Fixed Horizons

The preregistered horizons are 5, 20, and 60 trading days.

## Results

 horizon                    target      metric  estimate   ci_low  ci_high  baseline
       5    future_realized_vol_5d spearman_ic  0.372777 0.342047 0.400942       0.0
       5        future_abs_move_5d spearman_ic  0.408317 0.380329 0.437200       0.0
       5  future_drawdown_depth_5d spearman_ic  0.062915 0.028854 0.096230       0.0
       5   future_mr_stress_any_5d         auc  0.920719 0.910233 0.930749       0.5
      20   future_realized_vol_20d spearman_ic  0.390661 0.361437 0.418920       0.0
      20       future_abs_move_20d spearman_ic  0.405855 0.376950 0.434632       0.0
      20 future_drawdown_depth_20d spearman_ic  0.106704 0.073701 0.139180       0.0
      20  future_mr_stress_any_20d         auc  0.877461 0.864720 0.889820       0.5
      60   future_realized_vol_60d spearman_ic  0.391344 0.362805 0.419703       0.0
      60       future_abs_move_60d spearman_ic  0.392669 0.364569 0.420330       0.0
      60 future_drawdown_depth_60d spearman_ic  0.107389 0.076046 0.139954       0.0
      60  future_mr_stress_any_60d         auc  0.796905 0.781974 0.811115       0.5

## Reading

Positive Spearman IC means higher LIQ-001 is associated with higher future risk-target values. AUC above 0.50 means higher LIQ-001 ranks future MR-001 STRESS occurrence better than random ordering.
