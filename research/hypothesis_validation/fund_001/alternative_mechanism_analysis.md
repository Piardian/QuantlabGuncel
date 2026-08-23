# FUND-001 / HV-001

# Alternative Mechanism Analysis

## High-State Mechanism Mix

| mechanism_label | count | pct_high_state |
| --- | --- | --- |
| CP_UP_DOMINANT | 832 | 0.494355 |
| TBILL_DOWN_DOMINANT | 529 | 0.314320 |
| CP_UP_AND_TBILL_DOWN | 322 | 0.191325 |

## Episode Context

| episode | start | end | observations | mean_spread | max_spread | mean_spread_deviation | mean_cp_deviation | mean_tbill_deviation | mean_cp_contribution | mean_tbill_contribution | dominant_mechanism_label |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dot_com_aftershock_2001 | 2001-01-01 | 2001-12-31 | 247 | 0.246559 | 0.840000 | -0.165182 | -1.748285 | -1.583103 | -1.748285 | 1.583103 | TBILL_DOWN_DOMINANT |
| global_financial_crisis_2007_2009 | 2007-07-01 | 2009-06-30 | 457 | 1.019125 | 3.730000 | 0.086948 | -1.116195 | -1.203143 | -1.116195 | 1.203143 | TBILL_DOWN_DOMINANT |
| eurozone_us_downgrade_2011 | 2011-07-01 | 2011-12-31 | 124 | 0.182581 | 0.350000 | 0.043174 | -0.022030 | -0.065204 | -0.022030 | 0.065204 | TBILL_DOWN_DOMINANT |
| covid_liquidity_shock_2020 | 2020-02-15 | 2020-04-30 | 26 | 0.678077 | 2.570000 | 0.532120 | -0.633927 | -1.166047 | -0.633927 | 1.166047 | TBILL_DOWN_DOMINANT |
| rate_hiking_stress_2022 | 2022-01-01 | 2022-12-31 | 197 | 0.205330 | 1.110000 | 0.083810 | 1.622903 | 1.539093 | 1.622903 | -1.539093 | CP_UP_DOMINANT |
| regional_bank_stress_2023 | 2023-03-01 | 2023-05-31 | 21 | 0.151905 | 0.410000 | -0.033819 | 2.597012 | 2.630831 | 2.597012 | -2.630831 | CP_UP_DOMINANT |

## Supported Interpretation

FUND-001 is a spread stress construct with mixed observable drivers.

## Not Supported

The evidence does not support interpreting FUND-001 as a pure commercial-paper funding-cost sensor.

## Remaining Alternatives

- Counterparty credit concern.
- Treasury bill safe-asset demand.
- Policy-rate context.
- Commercial paper market technicals.
- Treasury bill supply-demand distortions.

These alternatives cannot be fully separated in HV-001 using only the frozen FUND-001 inputs.
