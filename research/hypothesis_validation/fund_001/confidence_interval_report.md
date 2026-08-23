# FUND-001 / HV-001

# Confidence Interval Report

Bootstrap confidence intervals compare high FUND-001 states against normal/non-high states using 2,000 deterministic bootstrap draws with fixed seed 12345.

| hypothesis | classification | primary_metric | difference | ci_95_low | ci_95_high | cohens_d | rationale |
| --- | --- | --- | --- | --- | --- | --- | --- |
| H1 | Supported by evidence | high_vs_normal_mean_spread_difference | 0.253816 | 0.230555 | 0.276713 | 0.828933 | High states have materially wider raw spreads and bootstrap CI is positive. |
| H2 | Partially supported | high_vs_normal_cp_deviation_difference | 0.362223 | 0.325429 | 0.399970 | 0.443154 | High states show higher CP deviations on average, but MI showed this is not the sole driver. |
| H3 | Partially supported | episode_windows_with_positive_tbill_contribution | -0.075189 | -0.116437 | -0.034087 | -0.093903 | Some predefined stress windows show positive Treasury-bill contribution, but it is not universal. |
| H4 | Supported by evidence | largest_high_state_mechanism_share |  |  |  |  | High states are distributed across multiple mechanism labels rather than one pure CP-only channel. |

## Boundary

Confidence intervals are descriptive uncertainty estimates for explanatory validation only. They are not strategy-performance confidence intervals.
