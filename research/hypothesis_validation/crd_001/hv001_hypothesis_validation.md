# CRD-001 / HV-001: Hypothesis Validation

## Purpose

Evaluate whether the explanatory mechanism identified in MI-001 is empirically supported.

This study evaluates explanatory validity only. It does not evaluate prediction, trading performance, alpha generation, profitability, economic value, or production deployment.

## Construct

CRD-001 measures US High-Yield Credit Spread Stress using FRED series `BAMLH0A0HYM2`.

## State Definitions

The MI-001 descriptive state definitions were preserved:

- `LOW_CREDIT_STRESS`: `crd001_percentile_252d <= 0.20`
- `MID_CREDIT_STRESS`: `0.20 < crd001_percentile_252d < 0.80`
- `HIGH_CREDIT_STRESS`: `crd001_percentile_252d >= 0.80`

These are explanatory analysis buckets, not trading thresholds.

## Statistical Method

For each preregistered hypothesis, HV-001 used:

- mean difference
- bootstrap confidence interval with fixed seed
- Cohen's d
- fixed-seed permutation test for mean difference
- cross-period direction review where data allowed
- trimmed-extreme robustness

Only same-day or trailing observable variables were used.

## Hypothesis Results

| Hypothesis | Variable | Comparison | Difference | Cohen's d | Permutation p | Classification |
| --- | --- | --- | ---: | ---: | ---: | --- |
| H1 | crd001_hy_oas | High - Low | 0.8705 | 3.7827 | 0.0002 | Supported by evidence |
| H2 | spread_change_20d | High - Low | 0.5026 | 1.5654 | 0.0002 | Supported by evidence |
| H3 | crd001_zscore_252d | High - Not High | 2.4349 | 3.1723 | 0.0002 | Supported by evidence |
| H4 | crd001_hy_oas | Low - Not Low | -0.3291 | -1.1667 | 0.0002 | Supported by evidence |

## Interpretation

The evidence supports the internal separation of CRD-001 high and low spread states within the available sample.

The evidence partially supports the MI-001 mechanism:

```text
CRD-001 represents high-yield credit spread stress / speculative-grade credit risk compensation state.
```

The classification remains partial because the available sample is short and the main high/low comparisons are based on CRD-001's own percentile-defined state groups.

## Final HV-001 Conclusion

CRD-001 / HV-001 is classified as:

```text
Partially supported
```

This conclusion is limited to explanatory validity. No predictive, economic, trading, profitability, alpha, or production-deployment conclusion is made.
