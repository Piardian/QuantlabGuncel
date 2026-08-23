# Correlation Stress Risk Control Analysis

## Use Case

UC-3 Correlation Stress Risk Control

## Policy

COR policy:

- HIGH_CORRELATION: 0.25 exposure
- LOW/MID_CORRELATION: 1.00 exposure

Benchmark:

```text
Static 0.75 exposure
```

## Result

Classification:

```text
Partially supported
```

## Evidence

| Metric | Delta |
| --- | ---: |
| CAGR | 0.0001 |
| Volatility | -0.0045 |
| Downside volatility | -0.0033 |
| Max drawdown | 0.0626 |
| Calmar | 0.1069 |

## Interpretation

Partially supported:

The full-sample results support risk-control utility, including shallower drawdown and lower volatility.

Limitation:

Cross-period robustness is weak. The policy improved at least two of three risk metrics in only one of four evaluated historical blocks.

