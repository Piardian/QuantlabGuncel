# Confidence Interval Report

## Method

Confidence intervals are computed from observation-level bootstrap resampling.

Iterations: 4000

## Results

 horizon                    target      metric  estimate   ci_low  ci_high
       5    future_realized_vol_5d spearman_ic  0.359559 0.329435 0.387319
       5        future_abs_move_5d spearman_ic  0.399261 0.369481 0.427507
       5  future_drawdown_depth_5d spearman_ic  0.057376 0.023745 0.090486
       5    future_high_vol_any_5d         auc  0.983895 0.979446 0.987888
      20   future_realized_vol_20d spearman_ic  0.331844 0.302173 0.360818
      20       future_abs_move_20d spearman_ic  0.351946 0.321360 0.380931
      20 future_drawdown_depth_20d spearman_ic  0.072984 0.040207 0.106642
      20   future_high_vol_any_20d         auc  0.882541 0.867925 0.896365
      60   future_realized_vol_60d spearman_ic  0.346912 0.319565 0.375419
      60       future_abs_move_60d spearman_ic  0.337913 0.308919 0.366186
      60 future_drawdown_depth_60d spearman_ic  0.061960 0.030689 0.092968
      60   future_high_vol_any_60d         auc  0.770025 0.754156 0.784976

## Boundary

These intervals describe historical uncertainty only and do not establish causality.
