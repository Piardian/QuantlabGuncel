# FUND-001 / HV-001

# Executive Summary

## Overall Result

```text
Partially supported
```

## Hypothesis Classifications

| hypothesis | classification | primary_metric | difference | ci_95_low | ci_95_high | cohens_d | rationale |
| --- | --- | --- | --- | --- | --- | --- | --- |
| H1 | Supported by evidence | high_vs_normal_mean_spread_difference | 0.253816 | 0.230555 | 0.276713 | 0.828933 | High states have materially wider raw spreads and bootstrap CI is positive. |
| H2 | Partially supported | high_vs_normal_cp_deviation_difference | 0.362223 | 0.325429 | 0.399970 | 0.443154 | High states show higher CP deviations on average, but MI showed this is not the sole driver. |
| H3 | Partially supported | episode_windows_with_positive_tbill_contribution | -0.075189 | -0.116437 | -0.034087 | -0.093903 | Some predefined stress windows show positive Treasury-bill contribution, but it is not universal. |
| H4 | Supported by evidence | largest_high_state_mechanism_share |  |  |  |  | High states are distributed across multiple mechanism labels rather than one pure CP-only channel. |

## Main Scientific Conclusion

FUND-001's explanatory mechanism is validated as a mixed short-term funding spread mechanism.

It is supported as a CP-Tbill spread stress construct, partially supported as a commercial-paper funding pressure construct, and not supported as a pure funding-liquidity sensor.

## Next Stage

After human approval, FUND-001 may proceed to:

```text
PV-001 Predictive Validation
```

No predictive, trading, alpha, or economic claim is made.
