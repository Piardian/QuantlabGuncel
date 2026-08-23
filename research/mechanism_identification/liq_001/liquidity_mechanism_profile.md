# Liquidity Mechanism Profile

## Segment Profiles

                      segment  observations  liq_zscore_mean  liq_zscore_median  aggregate_illiquidity_median  spy_realized_volatility_20d_mean  spy_abs_return_mean  spy_return_mean  spy_drawdown_mean  spy_drawdown_min  mr_stress_share  coverage_ratio_mean
LOW_LIQUIDITY_STRESS_BOTTOM20           751        -1.448126          -1.377628                  3.784668e-11                          0.088506             0.004538         0.000256          -0.020286         -0.192167         0.001332             0.963732
                    MIDDLE_60          2251        -0.449329          -0.513933                  4.781429e-11                          0.122633             0.006142         0.000646          -0.029835         -0.211530         0.089738             0.952714
  HIGH_LIQUIDITY_STRESS_TOP20           751         1.873201           1.603791                  6.633000e-11                          0.258229             0.013038         0.000037          -0.101868         -0.341047         0.780293             0.955743

## Mechanism Interpretation

Supported by evidence:

- High LIQ-001 periods have higher realized volatility than low LIQ-001 periods.
- High LIQ-001 periods have higher absolute market movement than low LIQ-001 periods.
- High LIQ-001 periods occur in deeper drawdown contexts.

Partially supported:

- LIQ-001 overlaps with MR-001 stress regimes, but overlap is not perfect.

Not supported:

- A pure coverage artifact explanation. Coverage remains high in high-stress periods.
