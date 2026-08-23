# Distribution Analysis

## Volatility Statistics

                  metric  count  missing_pct      mean    median      std       min       p01       p05       p25      p75      p95      p99      max      skew
  vol001_yz_variance_20d   4004     0.004970  0.000123  0.000062 0.000256  0.000008  0.000014  0.000020  0.000038 0.000125 0.000331 0.000812 0.003460  9.368765
vol001_yz_volatility_20d   4004     0.004970  0.150822  0.124681 0.091012  0.043784  0.059437  0.070715  0.097949 0.177680 0.288617 0.452287 0.933719  3.706500
           vol001_zscore   3753     0.067346 -0.001992 -0.369089 1.349802 -2.367823 -1.828441 -1.458115 -0.811390 0.419897 2.558545 5.152959 7.630532  1.952575
       vol001_percentile   3753     0.067346  0.470535  0.448413 0.308172  0.003968  0.003968  0.015873  0.198413 0.734127 0.984127 1.000000 1.000000  0.142098
        overnight_return   4023     0.000249  0.000328  0.000574 0.006933 -0.110357 -0.019486 -0.009681 -0.002237 0.003339 0.009566 0.017185 0.058624 -1.887751
    open_to_close_return   4023     0.000249  0.000189  0.000584 0.008178 -0.058277 -0.023859 -0.013736 -0.003323 0.004293 0.011303 0.020495 0.106005  0.114738
            rs_component   4023     0.000249  0.000076  0.000030 0.000239  0.000000  0.000002  0.000005  0.000014 0.000067 0.000241 0.000664 0.007650 15.901066

## Assessment

VOL-001 annualized volatility is positive, right-skewed, and heavy-tailed. This is plausible for an equity-market volatility-state construct because volatility tends to spike during stress episodes and compress during calm periods.

## Boundary

Distribution shape supports construct interpretability only. It does not imply predictive value or economic utility.
