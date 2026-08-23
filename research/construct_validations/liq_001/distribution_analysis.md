# Distribution Analysis

## Aggregate Illiquidity

               metric  count  missing_pct         mean       median          std          min          p01          p05          p25          p75          p95          p99          max     skew
aggregate_illiquidity   4023          0.0 6.147225e-11 5.015894e-11 4.254483e-11 6.863863e-12 1.518637e-11 2.168523e-11 3.482227e-11 7.253260e-11 1.433004e-10 2.390207e-10 4.129394e-10 2.546352

## Smoothed Illiquidity

                metric  count  missing_pct         mean       median          std          min          p01          p05          p25          p75          p95          p99          max     skew
liq001_illiquidity_20d   4004     0.004723 6.151826e-11 5.648230e-11 2.943299e-11 1.919307e-11 2.344893e-11 2.750041e-11 3.988103e-11 7.553592e-11 1.190691e-10 1.666859e-10 2.032486e-10 1.477444

## Liquidity Z-Score

       metric  count  missing_pct      mean    median      std       min       p01       p05       p25      p75     p95      p99      max     skew
liq001_zscore   3753     0.067114 -0.184441 -0.513933 1.249208 -2.376896 -1.997277 -1.602324 -1.014494 0.276036 2.45806 3.443727 7.118486 1.467231

## Assessment

The distribution is right-skewed and heavy-tailed, which is consistent with a liquidity-stress proxy. Extreme values exist but do not appear structurally invalid.
