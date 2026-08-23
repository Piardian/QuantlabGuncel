# Robustness Analysis

## Persistence Validation

 observed_episode_count  observed_median_duration  observed_max_duration  observed_lag1_continuation  null_median_duration_mean  null_median_duration_ci_low  null_median_duration_ci_high  null_lag1_continuation_mean  null_lag1_continuation_ci_low  null_lag1_continuation_ci_high  median_duration_pvalue  lag1_continuation_pvalue        classification
                     29                      24.0                     82                    0.961385                        1.0                          1.0                           1.0                     0.199796                       0.174434                        0.225033                 0.00025                   0.00025 Supported by evidence

## Preregistered Robustness Checks

- High/low states use fixed 20th and 80th percentile descriptive partitions from MI-001.
- Bootstrap intervals use a fixed random seed and fixed iteration count.
- Permutation p-values are descriptive, not causal.
- H6 compares observed high-state persistence against random reshuffles of the same high-state frequency.

## Robustness Summary

hypothesis        classification
        H1 Supported by evidence
        H2 Supported by evidence
        H3 Supported by evidence
        H4 Supported by evidence
        H5 Supported by evidence
        H6 Supported by evidence
