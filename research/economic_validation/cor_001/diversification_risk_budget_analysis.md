# Diversification Risk Budget Analysis

## Use Case

UC-1 Diversification Risk Budgeting

## Policy

COR policy:

- LOW_CORRELATION: 1.00 exposure
- MID_CORRELATION: 0.75 exposure
- HIGH_CORRELATION: 0.50 exposure

Benchmark:

```text
Static 0.75 exposure
```

## Result

Classification:

```text
Supported by evidence
```

## Evidence

| Metric | Delta |
| --- | ---: |
| CAGR | -0.0060 |
| Volatility | -0.0129 |
| Downside volatility | -0.0131 |
| Max drawdown | 0.0468 |
| Calmar | 0.0464 |

## Interpretation

Supported by evidence:

COR-001 improves diversification-risk budgeting by reducing exposure during high-correlation states and increasing exposure during low-correlation states.

Limitation:

The improvement is primarily risk-control utility, not return enhancement.

