# Correlation-Aware Volatility Targeting Analysis

## Use Case

UC-2 Correlation-Aware Volatility Targeting

## Policy

COR policy:

- HIGH_CORRELATION: 8% volatility target
- LOW/MID_CORRELATION: 12% volatility target
- exposure capped at 1.00

Benchmark:

```text
Static 12% volatility target, cap 1.00
```

## Result

Classification:

```text
Supported by evidence
```

## Evidence

| Metric | Delta |
| --- | ---: |
| CAGR | -0.0066 |
| Volatility | -0.0070 |
| Downside volatility | -0.0039 |
| Max drawdown | 0.0139 |
| Calmar | 0.0113 |

## Interpretation

Supported by evidence:

COR-001 improves volatility management when used to lower the volatility target during high-correlation states.

Limitation:

This is a predefined simple workflow. It does not prove universal superiority over all possible volatility-targeting designs.

