# CRD-001 / MI-001: Mechanism Identification

## Purpose

Identify observable market mechanisms associated with CRD-001 low, mid, and high credit-stress states.

This study is explanatory and descriptive only. It does not evaluate predictive validity, trading performance, alpha generation, profitability, economic value, or production deployment.

## Construct

CRD-001:

```text
US High-Yield Credit Spread Stress
```

Primary value:

```text
crd001_hy_oas
```

## State Definition Used For MI-001 Profiling

State buckets were defined using CRD-001's own trailing 252-day percentile:

| State | Rule |
| --- | --- |
| LOW_CREDIT_STRESS | `crd001_percentile_252d <= 0.20` |
| MID_CREDIT_STRESS | `0.20 < crd001_percentile_252d < 0.80` |
| HIGH_CREDIT_STRESS | `crd001_percentile_252d >= 0.80` |

These buckets are descriptive profiling groups only. They are not trading rules and are not optimized thresholds.

## Data Used

- CRD-001 output: `output/crd_001_validation/crd001_credit_stress_output.csv`
- Valid normalized rows analyzed: 530
- Date range: 2024-07-16 to 2026-07-27

## State Profile Summary

| State | Observations | Mean HY OAS | Median HY OAS | Mean Z | Mean Percentile |
| --- | ---: | ---: | ---: | ---: | ---: |
| LOW_CREDIT_STRESS | 183 | 2.7726 | 2.7300 | -1.4292 | 0.0785 |
| MID_CREDIT_STRESS | 292 | 2.9998 | 2.9500 | -0.3053 | 0.4575 |
| HIGH_CREDIT_STRESS | 55 | 3.6431 | 3.5300 | 1.6966 | 0.9081 |

## Main Mechanism Finding

Partially supported by evidence:

High CRD-001 states represent wider high-yield corporate spreads relative to the construct's own recent history. This is consistent with a speculative-grade credit stress mechanism: investors require greater compensation for holding below-investment-grade corporate credit risk.

Supported by evidence within the available sample:

Low CRD-001 states represent tighter high-yield corporate spreads relative to recent history, consistent with lower observed high-yield credit stress.

## Mechanism Interpretation

The evidence is consistent with the following descriptive mechanism:

```text
High CRD-001
        ->
Wider high-yield option-adjusted spreads
        ->
Elevated observed compensation for speculative-grade corporate credit risk
        ->
Credit stress state
```

This is an explanatory profile, not a predictive or economic claim.

## Final MI-001 Conclusion

The primary mechanism represented by CRD-001 is classified as:

```text
High-yield credit spread stress / speculative-grade credit risk compensation state
```

Evidence classification:

```text
Partially supported by evidence
```

The classification is partial because the available sample is too short to characterize the mechanism across multiple credit cycles.
