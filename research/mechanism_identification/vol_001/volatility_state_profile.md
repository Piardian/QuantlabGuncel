# Volatility State Profile

## State Profiles

         segment  observations  volatility_mean  volatility_median  zscore_mean  percentile_mean  abs_daily_return_mean  daily_return_mean  overnight_abs_mean  open_to_close_abs_mean  rs_component_mean  drawdown_mean  drawdown_min  positive_return_share
LOW_VOL_BOTTOM20           751         0.093370           0.089667    -1.271223         0.074747               0.004599           0.000609            0.002593                0.003756           0.000025      -0.022953     -0.180231               0.573901
       MIDDLE_60          2251         0.131712           0.119277    -0.295456         0.455905               0.006239           0.000606            0.003698                0.004937           0.000048      -0.027767     -0.243651               0.550422
  HIGH_VOL_TOP20           751         0.255682           0.231055     2.146849         0.910173               0.012529           0.000161            0.007783                0.009130           0.000198      -0.084960     -0.337172               0.536618

## Supported by Evidence

- High VOL-001 states have higher realized volatility than low states.
- High VOL-001 states have larger absolute daily moves than low states.
- High VOL-001 states occur in deeper drawdown contexts.

## Interpretation

VOL-001 state separation is internally coherent: the high-volatility bucket behaves like a market turbulence state, while the low-volatility bucket behaves like a calmer realized-variation state.
