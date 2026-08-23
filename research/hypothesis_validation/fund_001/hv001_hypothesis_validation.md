# FUND-001 / HV-001: Hypothesis Validation

## Scope

This stage validates explanatory mechanism hypotheses only. It does not evaluate prediction, alpha, trading returns, economic value, or production suitability.

## Construct

```text
FUND-001 = DCPF3M - DTB3
```

## Overall Classification

```text
Partially supported
```

## Hypothesis Results

| hypothesis | classification | primary_metric | difference | ci_95_low | ci_95_high | cohens_d | rationale |
| --- | --- | --- | --- | --- | --- | --- | --- |
| H1 | Supported by evidence | high_vs_normal_mean_spread_difference | 0.253816 | 0.230555 | 0.276713 | 0.828933 | High states have materially wider raw spreads and bootstrap CI is positive. |
| H2 | Partially supported | high_vs_normal_cp_deviation_difference | 0.362223 | 0.325429 | 0.399970 | 0.443154 | High states show higher CP deviations on average, but MI showed this is not the sole driver. |
| H3 | Partially supported | episode_windows_with_positive_tbill_contribution | -0.075189 | -0.116437 | -0.034087 | -0.093903 | Some predefined stress windows show positive Treasury-bill contribution, but it is not universal. |
| H4 | Supported by evidence | largest_high_state_mechanism_share |  |  |  |  | High states are distributed across multiple mechanism labels rather than one pure CP-only channel. |

## Interpretation

H1 is strongly supported because high FUND-001 states mechanically and empirically correspond to wider CP-Tbill spreads.

H2 is partially supported because CP elevation contributes to high states, but it is not the only mechanism.

H3 is partially supported because Treasury bill decline contributes in some periods and stress windows, but not universally.

H4 is supported because high states are not explained by a single pure commercial-paper funding-cost mechanism.

## Boundary

No predictive, economic, alpha, or trading conclusion is made.
