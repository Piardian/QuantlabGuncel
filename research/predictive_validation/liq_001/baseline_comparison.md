# Baseline Comparison

## Null Baselines

- Continuous targets: zero rank correlation.
- Future MR-STRESS occurrence: AUC 0.50 and unconditional-event-rate Brier score.

## Metrics

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

## Calibration Metrics

 horizon                   target  unconditional_event_rate  rank_score_brier  null_brier  brier_delta_vs_null
       5  future_mr_stress_any_5d                  0.229478          0.184624    0.176818             0.007807
      20 future_mr_stress_any_20d                  0.289979          0.177958    0.205891            -0.027933
      60 future_mr_stress_any_60d                  0.421375          0.188572    0.243818            -0.055246

## Boundary

The rank-score Brier comparison is descriptive. It does not transform LIQ-001 into a calibrated probability model.
