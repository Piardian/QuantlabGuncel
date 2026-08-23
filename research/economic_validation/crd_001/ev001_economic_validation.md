# CRD-001 / EV-001: Economic Validation

## Purpose

Evaluate whether CRD-001 provides measurable economic utility inside predefined credit-stress risk-management workflows.

This study evaluates economic utility. It does not evaluate alpha discovery or universal production superiority.

## Construct

CRD-001 measures US High-Yield Credit Spread Stress using FRED series `BAMLH0A0HYM2`.

## No-Lookahead Rule

All CRD-based policies use one-day-lagged CRD state.

The CRD state observed at day `t-1` determines exposure on day `t`.

## Predefined CRD States

The state definitions from MI/HV/PV were preserved:

- `LOW_CREDIT_STRESS`: bottom 20% of CRD-001 percentile values
- `MID_CREDIT_STRESS`: middle 60%
- `HIGH_CREDIT_STRESS`: top 20%

No thresholds were optimized.

## Predefined Use Cases

| Use Case | CRD Policy | Benchmark |
| --- | --- | --- |
| UC-1 Credit-stress risk budgeting | LOW 1.00, MID 0.75, HIGH 0.50 exposure | Static 0.75 exposure |
| UC-2 Volatility-aware de-risking support | HIGH target 8%, MID target 10%, LOW target 12%, cap 1.00 | Static 10% vol target, cap 1.00 |
| UC-3 Drawdown-risk warning support | LOW 1.00, MID 0.75, HIGH 0.25 exposure | Static 0.75 exposure |
| UC-4 Credit-spread stress monitoring for portfolio risk control | LOW 1.00, MID 0.85, HIGH 0.50 exposure | Buy-and-hold |

These policies are fixed, simple, and non-optimized.

## Main Results

| Use Case | Classification | Delta Ann Return | Delta Vol | Delta Max DD | Delta Downside Vol |
| --- | ---: | ---: | ---: | ---: | ---: |
| UC-1 | Supported by evidence | -0.0243 | -0.0067 | 0.0106 | -0.0056 |
| UC-2 | Supported by evidence | 0.0001 | -0.0007 | 0.0080 | -0.0015 |
| UC-3 | Supported by evidence | -0.0405 | -0.0175 | 0.0261 | -0.0128 |
| UC-4 | Partially supported | -0.0508 | -0.0427 | 0.0443 | -0.0349 |

Positive max-drawdown delta means the CRD policy had a shallower drawdown.

## Overall EV-001 Conclusion

CRD-001 / EV-001 is classified as:

```text
Partially supported
```

This classification is limited to the predefined risk-management workflows tested in EV-001 and the available sample.
