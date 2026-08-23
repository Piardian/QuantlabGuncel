# VOL-001 / PV-001: Predictive Validation

## Purpose

Evaluate whether VOL-001 contains predictive information about future market risk variables.

This is predictive validation only. No alpha, trading-performance, profitability, Sharpe, CAGR, portfolio, or economic utility claim is made.

## Overall Classification

**Supported by evidence**

## Hypothesis Classifications

hypothesis                                  target        classification
        H1              future realized volatility Supported by evidence
        H2         future absolute market movement Supported by evidence
        H3                    future drawdown risk          Inconclusive
        H4 future high-volatility state occurrence Supported by evidence

## Predictive Metrics

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

## Interpretation

VOL-001 shows predictive information for future volatility-state behavior and future realized risk variables. The clearest evidence is expected to come from future high-volatility occurrence and future realized volatility because volatility is persistent by construction and by documented literature mechanisms.

The evidence should be interpreted as risk-state predictive information, not as a trading signal or alpha source.
