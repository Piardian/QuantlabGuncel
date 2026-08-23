# FUND-001 / MI-001

# Stress Mechanism Summary

## Component Decomposition Method

For every valid observation with at least 252 prior valid observations, FUND-001 decomposes spread deviation from trailing context as:

```text
spread_deviation = cp_deviation - tbill_deviation
```

where:

```text
cp_deviation = DCPF3M - trailing_252_valid_mean(DCPF3M)
tbill_deviation = DTB3 - trailing_252_valid_mean(DTB3)
```

Therefore:

```text
cp_contribution = cp_deviation
tbill_contribution = -tbill_deviation
```

## Mechanism Summary

| mechanism_label | observations | mean_spread_deviation | mean_cp_contribution | mean_tbill_contribution | max_spread_deviation | pct_observations |
| --- | --- | --- | --- | --- | --- | --- |
| CP_UP_AND_TBILL_DOWN | 380 | 0.191639 | 0.058054 | 0.133585 | 2.462698 | 0.058796 |
| CP_UP_DOMINANT | 2641 | 0.011096 | 0.628325 | -0.617229 | 0.971468 | 0.408634 |
| INSUFFICIENT_OR_NEUTRAL | 2 | -0.000000 | 0.461448 | -0.461448 | 0.000000 | 0.000309 |
| OTHER_OFFSETTING | 424 | -0.064981 | -0.034432 | -0.030548 | -0.001905 | 0.065604 |
| TBILL_DOWN_DOMINANT | 3016 | -0.041378 | -0.620927 | 0.579549 | 1.747460 | 0.466656 |

## Episode Decomposition

| episode | start | end | observations | mean_spread | max_spread | mean_spread_deviation | mean_cp_deviation | mean_tbill_deviation | mean_cp_contribution | mean_tbill_contribution | dominant_mechanism_label |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dot_com_aftershock_2001 | 2001-01-01 | 2001-12-31 | 247 | 0.246559 | 0.840000 | -0.165182 | -1.748285 | -1.583103 | -1.748285 | 1.583103 | TBILL_DOWN_DOMINANT |
| global_financial_crisis_2007_2009 | 2007-07-01 | 2009-06-30 | 457 | 1.019125 | 3.730000 | 0.086948 | -1.116195 | -1.203143 | -1.116195 | 1.203143 | TBILL_DOWN_DOMINANT |
| eurozone_us_downgrade_2011 | 2011-07-01 | 2011-12-31 | 124 | 0.182581 | 0.350000 | 0.043174 | -0.022030 | -0.065204 | -0.022030 | 0.065204 | TBILL_DOWN_DOMINANT |
| covid_liquidity_shock_2020 | 2020-02-15 | 2020-04-30 | 26 | 0.678077 | 2.570000 | 0.532120 | -0.633927 | -1.166047 | -0.633927 | 1.166047 | TBILL_DOWN_DOMINANT |
| rate_hiking_stress_2022 | 2022-01-01 | 2022-12-31 | 197 | 0.205330 | 1.110000 | 0.083810 | 1.622903 | 1.539093 | 1.622903 | -1.539093 | CP_UP_DOMINANT |
| regional_bank_stress_2023 | 2023-03-01 | 2023-05-31 | 21 | 0.151905 | 0.410000 | -0.033819 | 2.597012 | 2.630831 | 2.597012 | -2.630831 | CP_UP_DOMINANT |

## Interpretation

FUND-001 captures a funding-spread mechanism rather than a single pure driver. Some stress windows are dominated by rising commercial paper rates; others include a large Treasury bill decline component consistent with flight-to-quality or policy-rate context.
