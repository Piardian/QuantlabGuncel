# Baseline Comparison

## Null Baselines

- Continuous targets: zero rank correlation.
- Future high-volatility occurrence: AUC 0.50 and unconditional-event-rate Brier score.

## Metrics

 horizon                    target      metric  estimate   ci_low  ci_high  observations  baseline
       5    future_realized_vol_5d spearman_ic  0.359559 0.329435 0.387319          3752       0.0
       5        future_abs_move_5d spearman_ic  0.399261 0.369481 0.427507          3752       0.0
       5  future_drawdown_depth_5d spearman_ic  0.057376 0.023745 0.090486          3752       0.0
       5    future_high_vol_any_5d         auc  0.983895 0.979446 0.987888          3752       0.5
      20   future_realized_vol_20d spearman_ic  0.331844 0.302173 0.360818          3752       0.0
      20       future_abs_move_20d spearman_ic  0.351946 0.321360 0.380931          3752       0.0
      20 future_drawdown_depth_20d spearman_ic  0.072984 0.040207 0.106642          3752       0.0
      20   future_high_vol_any_20d         auc  0.882541 0.867925 0.896365          3752       0.5
      60   future_realized_vol_60d spearman_ic  0.346912 0.319565 0.375419          3752       0.0
      60       future_abs_move_60d spearman_ic  0.337913 0.308919 0.366186          3752       0.0
      60 future_drawdown_depth_60d spearman_ic  0.061960 0.030689 0.092968          3752       0.0
      60   future_high_vol_any_60d         auc  0.770025 0.754156 0.784976          3752       0.5

## Calibration Metrics

 horizon                  target  unconditional_event_rate  rank_score_brier  null_brier  brier_delta_vs_null
       5  future_high_vol_any_5d                  0.227079          0.163545    0.175514            -0.011969
      20 future_high_vol_any_20d                  0.311567          0.169279    0.214493            -0.045214
      60 future_high_vol_any_60d                  0.468017          0.198882    0.248977            -0.050095

## Boundary

The rank-score Brier comparison is descriptive. It does not transform VOL-001 into a calibrated probability model.
