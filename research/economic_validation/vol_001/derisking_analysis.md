# Dynamic De-Risking Analysis

UC-3 compares `VOL001_DERISKING` against `STATIC_DERISKING_POLICY`.

## Metrics

use_case                  policy policy_type  observations  years_covered  total_return  annualized_return  annualized_volatility  max_drawdown  sortino   calmar  cvar_5pct_daily_return  average_exposure  average_daily_turnover
    UC-3 STATIC_DERISKING_POLICY   benchmark          3752          14.89      2.531081           0.088428               0.107476     -0.221164 1.281300 0.399830               -0.016417          0.625000                0.000000
    UC-3        VOL001_DERISKING     dynamic          3752          14.89      4.698063           0.123978               0.123284     -0.234750 1.575581 0.528127               -0.019305          0.860008                0.013859

## Comparison

use_case           policy               benchmark  delta_annualized_return  delta_annualized_volatility  delta_max_drawdown  delta_sortino  delta_calmar  delta_cvar_5pct_daily_return  delta_average_exposure
    UC-3 VOL001_DERISKING STATIC_DERISKING_POLICY                  0.03555                     0.015808           -0.013586        0.29428      0.128297                     -0.002888                0.235008
