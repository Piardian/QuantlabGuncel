# Regime-Aware Portfolio De-Risking Support Analysis

## Use Case

UC-4 Regime-Aware Portfolio De-Risking Support

## Policy

COR policy:

- LOW_CORRELATION: 1.00 exposure
- MID_CORRELATION: 0.85 exposure
- HIGH_CORRELATION: 0.50 exposure

Benchmark:

```text
Buy-and-hold
```

## Result

Classification:

```text
Partially supported
```

## Evidence

| Metric | Delta |
| --- | ---: |
| CAGR | -0.0272 |
| Volatility | -0.0487 |
| Downside volatility | -0.0424 |
| Max drawdown | 0.1171 |
| Calmar | 0.0602 |

## Interpretation

Partially supported:

The policy materially reduces realized volatility, downside volatility, and maximum drawdown.

Limitation:

The risk reduction comes with a material CAGR penalty versus buy-and-hold.

