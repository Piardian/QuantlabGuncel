# BRD-001 / EV-001: Portfolio Risk Control Analysis

## Use Case

UC-4 Regime-Aware Portfolio Risk Control.

## Policy

BRD policy:

- LOW_BREADTH: 0.50 exposure
- MID_BREADTH: 0.85 exposure
- HIGH_BREADTH: 1.00 exposure

Benchmark:

- Buy-and-hold

## Results

| Metric | BRD Policy | Buy-and-Hold | Delta |
| --- | ---: | ---: | ---: |
| CAGR | 0.0976 | 0.1230 | -0.0254 |
| Annualized volatility | 0.1175 | 0.1716 | -0.0541 |
| Max drawdown | -0.2055 | -0.3410 | +0.1356 |
| Downside volatility | 0.0911 | 0.1399 | -0.0489 |
| Average exposure | 0.8099 | 1.0000 | -0.1901 |

## Assessment

BRD-001 materially improved portfolio risk control relative to buy-and-hold.

However, the CAGR penalty was larger than the EV-001 support threshold.

Classification:

```text
Partially supported
```

