# Market Condition Summary

## Correlations With Observable Market Conditions

                    feature  correlation_with_liq_zscore
spy_realized_volatility_20d                     0.797622
   abs_spy_daily_log_return                     0.456832
               spy_drawdown                    -0.605343
             coverage_ratio                    -0.052057

## MR-001 Overlap

         liq_bucket regime_label  observations  share_within_bucket
  HIGH_STRESS_TOP20    EXPANSION           165             0.219707
  HIGH_STRESS_TOP20       STRESS           586             0.780293
LOW_STRESS_BOTTOM20    EXPANSION           750             0.998668
LOW_STRESS_BOTTOM20       STRESS             1             0.001332
          MIDDLE_60    EXPANSION          2049             0.910262
          MIDDLE_60       STRESS           202             0.089738

## Interpretation

LIQ-001 is positively associated with realized volatility and absolute market movement, and negatively associated with SPY drawdown level because more severe drawdowns are represented by more negative values.

This supports interpreting LIQ-001 as a liquidity-stress / price-impact condition rather than a standalone trend or return construct.
