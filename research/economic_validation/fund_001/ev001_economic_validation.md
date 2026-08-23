# FUND-001 / EV-001: Economic Validation

## Purpose

Evaluate whether FUND-001 provides measurable economic utility inside predefined funding-stress-aware risk-management workflows.

This stage evaluates economic utility only. It does not claim alpha discovery or universal superiority.

## Construct

```text
FUND-001 = DCPF3M - DTB3
```

## No-Lookahead Rule

All FUND-based policies use one-day-lagged FUND state.

The FUND state observed at day `t-1` determines exposure on day `t`.

## Predefined FUND States

- `NORMAL_OR_LOW`: trailing percentile <= 50%
- `ELEVATED`: 50% < trailing percentile <= 80%
- `HIGH_STRESS`: trailing percentile > 80%

These state cutoffs are fixed descriptive state buckets. They are not optimized.

## Predefined Use Cases

| Use Case | FUND Policy | Benchmark |
| --- | --- | --- |
| UC-1 Funding-stress-aware risk budgeting | NORMAL 1.00, ELEVATED 0.75, HIGH 0.50 exposure | Static 0.75 exposure |
| UC-2 Funding-stress-aware volatility targeting | NORMAL 0.90, ELEVATED 0.75, HIGH 0.55 exposure | Static 0.75 exposure |
| UC-3 Funding-stress-aware hedge activation | NORMAL 1.00, ELEVATED 0.85, HIGH 0.50 exposure | Static 0.75 exposure |
| UC-4 Funding-stress-aware portfolio risk control | NORMAL 1.00, ELEVATED 0.80, HIGH 0.45 exposure | Buy-and-hold |

## Overall Classification

```text
Not supported
```

## Benchmark Comparison

| use_case | policy | benchmark | delta_annualized_return | delta_annualized_volatility | delta_downside_volatility | delta_max_drawdown | delta_cvar_5pct_daily_return | delta_average_exposure | classification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| UC-1 | UC1_FUND_RISK_BUDGET | STATIC_RISK_BUDGET_075 | 0.027782 | -0.000272 | -0.003132 | -0.063247 | 0.000001 | 0.056583 | Not supported |
| UC-2 | UC2_FUND_VOL_TARGET | STATIC_VOL_TARGET_075 | 0.017480 | -0.004550 | -0.006738 | -0.033602 | 0.000721 | 0.021352 | Not supported |
| UC-3 | UC3_FUND_HEDGE_ACTIVATION | STATIC_HEDGE_POLICY_075 | 0.034746 | 0.003804 | -0.000731 | -0.066685 | -0.000531 | 0.083557 | Not supported |
| UC-4 | UC4_FUND_PORTFOLIO_RISK_CONTROL | BUY_AND_HOLD | -0.004738 | -0.043528 | -0.039136 | -0.000905 | 0.006631 | -0.192528 | Not supported |

## Use-Case Classifications

| use_case | policy | benchmark | risk_metrics_improved_count | classification |
| --- | --- | --- | --- | --- |
| UC-1 | UC1_FUND_RISK_BUDGET | STATIC_RISK_BUDGET_075 | 1 | Not supported |
| UC-2 | UC2_FUND_VOL_TARGET | STATIC_VOL_TARGET_075 | 1 | Not supported |
| UC-3 | UC3_FUND_HEDGE_ACTIVATION | STATIC_HEDGE_POLICY_075 | 1 | Not supported |
| UC-4 | UC4_FUND_PORTFOLIO_RISK_CONTROL | BUY_AND_HOLD | 1 | Not supported |

## Interpretation

FUND-001 does not provide sufficient evidence of economic utility inside the four predefined risk-management workflows.

Several dynamic policies improved annualized return or volatility, but the predefined success standard required risk-management utility across volatility, downside risk, drawdown, and left-tail loss metrics. The FUND-aware policies did not consistently improve drawdown versus the static benchmarks.

This is not an alpha claim. It is an economic utility assessment for predefined risk-management workflows only.
