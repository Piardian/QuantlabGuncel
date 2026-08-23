# Baseline Comparison

## future_return
 horizon_days  avg_rmse_improvement  avg_mae_improvement    avg_r2    avg_ic  avg_auc  avg_brier
            5             -0.000053             0.000002 -0.028043 -0.109896      NaN        NaN
           20             -0.000396            -0.000201 -0.134709 -0.216698      NaN        NaN
           60             -0.001364            -0.001198 -0.754677 -0.364221      NaN        NaN

## future_realized_vol
 horizon_days  avg_rmse_improvement  avg_mae_improvement     avg_r2    avg_ic  avg_auc  avg_brier
            5              0.015799             0.016817  -0.511703 -0.267603 0.328738   0.744827
           20              0.015884             0.018806  -2.173182 -0.219970 0.361123   0.769069
           60              0.009466             0.013889 -11.695766 -0.056130 0.363309   0.744112

## future_drawdown
 horizon_days  avg_rmse_improvement  avg_mae_improvement    avg_r2    avg_ic  avg_auc  avg_brier
            5              0.000528             0.000833 -0.168495  0.018221 0.442370   0.746550
           20              0.001252             0.001653 -0.588764 -0.041370 0.521971   0.742385
           60              0.000540             0.001677 -2.703505 -0.192722 0.570108   0.737916