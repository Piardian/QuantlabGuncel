# COR-001 / EV-001: Economic Validation

## Purpose

Evaluate whether COR-001 provides measurable economic utility inside predefined risk-management workflows.

This study evaluates economic utility.

It does not evaluate alpha discovery or universal production superiority.

## Construct

COR-001 measures average pairwise Pearson correlation of daily log returns across a fixed US equity universe over a trailing 60-trading-day window.

PV-001 classified COR-001 as a risk-state predictive construct for future realized volatility, future breadth deterioration, and future correlation persistence.

## No-Lookahead Rule

All COR-based policies use one-day-lagged COR state.

The COR state observed at day `t-1` determines exposure on day `t`.

## Predefined COR States

The state definitions from MI/HV/PV were preserved:

- `LOW_CORRELATION`: bottom 20% of COR-001 percentile values
- `MID_CORRELATION`: middle 60%
- `HIGH_CORRELATION`: top 20%

No thresholds were optimized.

## Predefined Use Cases

| Use Case | COR Policy | Benchmark |
| --- | --- | --- |
| UC-1 Diversification Risk Budgeting | LOW 1.00, MID 0.75, HIGH 0.50 exposure | Static 0.75 exposure |
| UC-2 Correlation-Aware Volatility Targeting | HIGH target 8%, LOW/MID target 12%, cap 1.00 | Static 12% vol target, cap 1.00 |
| UC-3 Correlation Stress Risk Control | HIGH 0.25, LOW/MID 1.00 exposure | Static 0.75 exposure |
| UC-4 Regime-Aware Portfolio De-Risking Support | LOW 1.00, MID 0.85, HIGH 0.50 exposure | Buy-and-hold |

These policies are fixed, simple, and non-optimized.

## Main Results

| Use Case | Classification | Delta CAGR | Delta Vol | Delta Max DD | Delta Downside Vol |
| --- | --- | ---: | ---: | ---: | ---: |
| UC-1 Diversification Risk Budgeting | Supported by evidence | -0.0060 | -0.0129 | 0.0468 | -0.0131 |
| UC-2 Correlation-Aware Volatility Targeting | Supported by evidence | -0.0066 | -0.0070 | 0.0139 | -0.0039 |
| UC-3 Correlation Stress Risk Control | Partially supported | 0.0001 | -0.0045 | 0.0626 | -0.0033 |
| UC-4 Regime-Aware Portfolio De-Risking Support | Partially supported | -0.0272 | -0.0487 | 0.1171 | -0.0424 |

Positive max-drawdown delta means the COR policy had a shallower drawdown.

## Interpretation

COR-001 provides measurable economic utility primarily through risk control:

- lower realized volatility
- lower downside volatility
- shallower maximum drawdown
- reduced exposure during high-correlation states

The strongest supported use cases were:

```text
UC-1 Diversification Risk Budgeting
UC-2 Correlation-Aware Volatility Targeting
```

UC-3 produced favorable full-sample metrics but weak cross-period robustness, so it is classified as partially supported.

UC-4 materially reduced risk but imposed a larger CAGR penalty versus buy-and-hold, so it is classified as partially supported.

## What Is Not Supported

EV-001 does not support COR-001 as an alpha or return-enhancement construct.

The economic utility is risk-management utility, not directional return prediction.

## Overall EV-001 Conclusion

COR-001 / EV-001 is classified as:

```text
Supported by evidence
```

This classification is limited to the predefined risk-management workflows tested in EV-001.

