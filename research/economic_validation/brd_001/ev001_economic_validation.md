# BRD-001 / EV-001: Economic Validation

## Purpose

Evaluate whether BRD-001 provides measurable economic utility inside predefined risk-management workflows.

This study evaluates economic utility.

It does not evaluate alpha discovery or universal production superiority.

## Construct

BRD-001 measures the percentage of eligible securities above their own 200-day simple moving average.

PV-001 classified BRD-001 as a risk-state predictive construct rather than a return-prediction construct.

## No-Lookahead Rule

All BRD-based policies use one-day-lagged breadth state.

The breadth state observed at day `t-1` determines exposure on day `t`.

## Predefined Breadth States

The state definitions from MI/HV/PV were preserved:

- `LOW_BREADTH`: bottom 20% of BRD-001 values
- `MID_BREADTH`: middle 60%
- `HIGH_BREADTH`: top 20%

No thresholds were optimized.

## Predefined Use Cases

| Use Case | BRD Policy | Benchmark |
| --- | --- | --- |
| UC-1 Risk Budgeting | LOW 0.50, MID 0.75, HIGH 1.00 exposure | Static 0.75 exposure |
| UC-2 Volatility Targeting | LOW target 8%, MID/HIGH target 12%, cap 1.00 | Static 12% vol target, cap 1.00 |
| UC-3 Trend Deterioration Risk Control | LOW 0.25, MID/HIGH 1.00 exposure | Static 0.75 exposure |
| UC-4 Portfolio Risk Control | LOW 0.50, MID 0.85, HIGH 1.00 exposure | Buy-and-hold |

These policies are fixed, simple and non-optimized.

## Main Results

| Use Case | Classification | Delta CAGR | Delta Vol | Delta Max DD | Delta Downside Vol |
| --- | --- | ---: | ---: | ---: | ---: |
| UC-1 Risk Budgeting | Supported by evidence | -0.0043 | -0.0182 | +0.0656 | -0.0190 |
| UC-2 Volatility Targeting | Supported by evidence | -0.0055 | -0.0092 | +0.0246 | -0.0065 |
| UC-3 Trend Deterioration Risk Control | Supported by evidence | +0.0070 | -0.0130 | +0.1121 | -0.0134 |
| UC-4 Portfolio Risk Control | Partially supported | -0.0254 | -0.0541 | +0.1356 | -0.0489 |

Positive max-drawdown delta means the BRD policy had a shallower drawdown.

## Interpretation

BRD-001 provides measurable economic utility primarily through risk control:

- lower realized volatility
- lower downside volatility
- shallower maximum drawdown
- reduced exposure during low-breadth states

The strongest use case was:

```text
UC-3 Trend Deterioration Risk Control
```

UC-3 improved CAGR versus the static benchmark while reducing volatility, downside volatility and max drawdown.

## What Is Not Supported

EV-001 does not support BRD-001 as an alpha or return-enhancement construct.

The economic utility is risk-management utility, not directional return prediction.

## Overall EV-001 Conclusion

BRD-001 / EV-001 is classified as:

```text
Supported by evidence
```

This classification is limited to the predefined risk-management workflows tested in EV-001.

