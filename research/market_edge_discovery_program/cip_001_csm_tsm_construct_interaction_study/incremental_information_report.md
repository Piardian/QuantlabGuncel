# Incremental Information Report

Incremental information was evaluated using descriptive R-squared comparisons on future returns. These statistics are not trading results and do not imply production value.

| horizon_days | observations | r2_csm_only | r2_tsm_only | r2_both | incremental_r2_tsm_beyond_csm | incremental_r2_csm_beyond_tsm | spearman_csm_future_return | spearman_tsm_future_return | spearman_csm_tsm |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 21 | 1.75836e+06 | 1.74169e-05 | 0.000854208 | 0.00183724 | 0.00181983 | 0.000983036 | 0.00544714 | -0.0226709 | 0.661622 |
| 63 | 1.7374e+06 | 8.05212e-05 | 0.00194293 | 0.00450493 | 0.0044244 | 0.002562 | 0.00281144 | -0.0412903 | 0.659569 |
| 126 | 1.70597e+06 | 0.000153979 | 0.00223229 | 0.00554778 | 0.0053938 | 0.00331549 | 0.00872849 | -0.0391808 | 0.656589 |

Supported by evidence:

- CSM and TSM are highly related because both are derived from intermediate-horizon price history.
- CSM retains incremental information beyond the broad TSM sign state across evaluated horizons.
- TSM also retains incremental state information beyond CSM across evaluated horizons.
- The TSM relationship is directionally different from CSM: prior TSM evidence classified it as a risk-state / own-trend construct rather than a standalone expected-return alpha construct.

Inconclusive:

- Whether the same interaction would remain under survivorship-free universe reconstruction and realistic investability constraints.
