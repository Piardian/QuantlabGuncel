# BRD-001 / EV-001: Trend Deterioration Risk Control Analysis

## Use Case

UC-3 Trend Deterioration Risk Control.

## Policy

BRD policy:

- LOW_BREADTH: 0.25 exposure
- MID_BREADTH: 1.00 exposure
- HIGH_BREADTH: 1.00 exposure

Benchmark:

- Static 0.75 exposure

## Results

| Metric | BRD Policy | Benchmark | Delta |
| --- | ---: | ---: | ---: |
| CAGR | 0.1009 | 0.0939 | +0.0070 |
| Annualized volatility | 0.1157 | 0.1287 | -0.0130 |
| Max drawdown | -0.1523 | -0.2644 | +0.1121 |
| Downside volatility | 0.0915 | 0.1050 | -0.0134 |
| Average exposure | 0.8497 | 0.7500 | +0.0997 |

## Assessment

This is the strongest predefined EV-001 use case.

BRD-001 reduced exposure during low-breadth states while allowing full exposure during mid/high breadth states.

The policy improved CAGR, volatility, downside volatility and max drawdown relative to the static risk-control benchmark.

Classification:

```text
Supported by evidence
```

