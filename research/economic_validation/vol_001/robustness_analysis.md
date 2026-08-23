# Robustness Analysis

## Period Results

   period use_case                        policy               benchmark  delta_annualized_return  delta_annualized_volatility  delta_max_drawdown  delta_sortino  delta_calmar  delta_cvar_5pct_daily_return  delta_average_exposure
2011_2014     UC-1            VOL001_RISK_BUDGET      STATIC_RISK_BUDGET                 0.000907                     0.000505            0.002589       0.043047      0.018665                      0.000186                0.078901
2015_2019     UC-1            VOL001_RISK_BUDGET      STATIC_RISK_BUDGET                 0.007549                     0.000245           -0.002885       0.092228      0.033359                      0.000142                0.066176
2020_2022     UC-1            VOL001_RISK_BUDGET      STATIC_RISK_BUDGET                 0.021954                    -0.029805            0.053021       0.269568      0.136079                      0.005051                0.038360
2023_2025     UC-1            VOL001_RISK_BUDGET      STATIC_RISK_BUDGET                 0.012518                    -0.004654            0.019777       0.251476      0.251008                      0.000426                0.076731
2011_2014     UC-2             VOL001_VOL_TARGET       STATIC_VOL_TARGET                 0.008599                     0.011814           -0.001263       0.014850      0.053455                     -0.001245                0.172492
2015_2019     UC-2             VOL001_VOL_TARGET       STATIC_VOL_TARGET                 0.021947                     0.008998            0.006537       0.183761      0.182937                     -0.001211                0.149642
2020_2022     UC-2             VOL001_VOL_TARGET       STATIC_VOL_TARGET                 0.032314                    -0.023127            0.020997       0.386349      0.154356                      0.003717                0.102183
2023_2025     UC-2             VOL001_VOL_TARGET       STATIC_VOL_TARGET                 0.034868                     0.006307            0.023143       0.358409      0.521035                     -0.001205                0.171771
2011_2014     UC-3              VOL001_DERISKING STATIC_DERISKING_POLICY                 0.015886                     0.027118           -0.027243      -0.093063     -0.042130                     -0.003850                0.266084
2015_2019     UC-3              VOL001_DERISKING STATIC_DERISKING_POLICY                 0.035962                     0.021460           -0.020366       0.214291      0.164104                     -0.003691                0.233108
2020_2022     UC-3              VOL001_DERISKING STATIC_DERISKING_POLICY                 0.040962                    -0.003573           -0.013586       0.413209      0.160949                     -0.000521                0.166005
2023_2025     UC-3              VOL001_DERISKING STATIC_DERISKING_POLICY                 0.056212                     0.021994            0.020870       0.328262      0.810763                     -0.003477                0.266811
2011_2014     UC-4 VOL001_PORTFOLIO_RISK_CONTROL            BUY_AND_HOLD                -0.043669                    -0.031587            0.043028      -0.128367     -0.061637                      0.004967               -0.125633
2015_2019     UC-4 VOL001_PORTFOLIO_RISK_CONTROL            BUY_AND_HOLD                -0.000522                    -0.030072            0.050250       0.330739      0.210300                      0.004423               -0.166137
2020_2022     UC-4 VOL001_PORTFOLIO_RISK_CONTROL            BUY_AND_HOLD                 0.017983                    -0.099270            0.116057       0.447503      0.192386                      0.013948               -0.244709
2023_2025     UC-4 VOL001_PORTFOLIO_RISK_CONTROL            BUY_AND_HOLD                -0.029431                    -0.036091            0.087809       0.344667      0.794527                      0.004437               -0.119840

## Interpretation

Robustness is assessed across fixed historical periods. The purpose is stability of risk utility, not optimization.
