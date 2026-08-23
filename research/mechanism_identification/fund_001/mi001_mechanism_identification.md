# FUND-001 / MI-001: Mechanism Identification

## Scope

This stage identifies observable mechanisms represented by FUND-001. It does not evaluate prediction, trading returns, alpha, economic value, or production suitability.

## Construct

```text
FUND-001 = DCPF3M - DTB3
```

## Primary Mechanism Finding

FUND-001 primarily represents stress in short-term private financial funding relative to Treasury bill rates.

High FUND-001 readings can arise through two observable channels:

1. Commercial paper rates rising relative to their trailing context.
2. Treasury bill rates falling relative to their trailing context.

The empirical decomposition shows that elevated readings are not always a pure commercial-paper funding-cost phenomenon; Treasury bill safe-asset demand and policy-rate context can materially influence the spread.

## Evidence Classification

- Supported by evidence: FUND-001 measures the spread between financial commercial paper funding cost and Treasury bill rates.
- Supported by evidence: high readings often coincide with known funding-stress or liquidity-stress windows.
- Partially supported: high readings represent funding stress specifically, because the spread can include credit, counterparty, safe-asset, and policy-rate components.
- Not supported: FUND-001 as a pure funding-liquidity measure.
- Speculation: the exact institutional cause of any individual spike without additional market microstructure or balance-sheet data.

## State Profiles

| state_bucket | observations | start | end | mean_cp_rate | mean_tbill_rate | mean_spread | median_spread | mean_zscore | median_zscore | max_zscore | mean_percentile |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| normal_or_low | 3089 | 1998-01-05 | 2026-07-27 | 2.269123 | 2.090890 | 0.178232 | 0.110000 | -0.785470 | -0.715090 | 0.136472 | 0.228267 |
| elevated | 1691 | 1998-01-08 | 2026-06-26 | 2.309243 | 2.028551 | 0.280692 | 0.170000 | 0.250391 | 0.249733 | 0.979473 | 0.656840 |
| high_stress | 1026 | 1998-04-28 | 2026-07-02 | 2.423197 | 2.013879 | 0.409318 | 0.280000 | 1.225313 | 1.185669 | 2.581618 | 0.877150 |
| extreme_stress | 657 | 1998-06-01 | 2026-07-16 | 2.232557 | 1.672161 | 0.560396 | 0.360000 | 2.779526 | 2.504315 | 12.706966 | 0.980153 |

## Mechanism Labels

| mechanism_label | observations | mean_spread_deviation | mean_cp_contribution | mean_tbill_contribution | max_spread_deviation | pct_observations |
| --- | --- | --- | --- | --- | --- | --- |
| CP_UP_AND_TBILL_DOWN | 380 | 0.191639 | 0.058054 | 0.133585 | 2.462698 | 0.058796 |
| CP_UP_DOMINANT | 2641 | 0.011096 | 0.628325 | -0.617229 | 0.971468 | 0.408634 |
| INSUFFICIENT_OR_NEUTRAL | 2 | -0.000000 | 0.461448 | -0.461448 | 0.000000 | 0.000309 |
| OTHER_OFFSETTING | 424 | -0.064981 | -0.034432 | -0.030548 | -0.001905 | 0.065604 |
| TBILL_DOWN_DOMINANT | 3016 | -0.041378 | -0.620927 | 0.579549 | 1.747460 | 0.466656 |

## Overall Conclusion

FUND-001 is best interpreted as a short-term private financial funding spread stress sensor, not as a pure funding-liquidity construct.
