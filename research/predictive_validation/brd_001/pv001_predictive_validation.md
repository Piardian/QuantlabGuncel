# BRD-001 / PV-001: Predictive Validation

## Purpose

Evaluate whether BRD-001 contains statistically significant predictive information about future SPY market behavior.

This study evaluates predictive validity only.

It does not evaluate trading profitability, alpha, portfolio performance, Sharpe ratio, CAGR, or economic value.

## Construct

BRD-001 measures the percentage of eligible securities in `sp500_current_universe.csv` whose adjusted close is above its own 200-day simple moving average.

## Forecast Horizons

PV-001 evaluated:

- 20 trading days
- 60 trading days

## Future Outcomes

The predefined future outcomes were:

- future SPY realized volatility
- future SPY drawdown risk
- future SPY trend deterioration risk
- future SPY returns

## Statistical Method

BRD-001 was evaluated as a continuous predictor using:

- Pearson correlation
- rank correlation
- fixed-seed permutation test against a no-association null
- LOW_BREADTH versus HIGH_BREADTH mean differences
- bootstrap confidence intervals
- AUC for binary risk-event classification
- period-block stability

No model fitting, threshold optimization, trading strategy, or portfolio simulation was performed.

## Hypothesis Results

| Hypothesis | Target | Horizon | Rank Corr | Low Mean | High Mean | AUC | Classification |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| H1 | Future realized volatility | 20d | -0.4158 | 0.2331 | 0.1169 | 0.8247 | Supported by evidence |
| H1 | Future realized volatility | 60d | -0.3633 | 0.2061 | 0.1319 | 0.7959 | Supported by evidence |
| H2 | Future drawdown risk | 20d | 0.0712 | -0.0359 | -0.0190 | 0.6296 | Partially supported |
| H2 | Future drawdown risk | 60d | 0.0728 | -0.0547 | -0.0363 | 0.6636 | Partially supported |
| H3 | Future trend deterioration | 20d | -0.6396 | 0.8851 | 0.0039 | 0.9121 | Supported by evidence |
| H3 | Future trend deterioration | 60d | -0.5322 | 0.8901 | 0.1216 | 0.8108 | Supported by evidence |
| H4 | Future returns | 20d | -0.1667 | 0.0184 | 0.0070 | 0.2734 | Not supported |
| H4 | Future returns | 60d | -0.1973 | 0.0534 | 0.0208 | 0.2970 | Not supported |

## Main Findings

### Future Realized Volatility

BRD-001 contains predictive information about future SPY realized volatility.

Lower breadth is associated with higher future realized volatility at both 20-day and 60-day horizons.

Classification:

```text
Supported by evidence
```

### Future Trend Deterioration

BRD-001 contains predictive information about future SPY trend deterioration risk.

Lower breadth is associated with materially higher probability of SPY being below SMA200 during the future horizon.

Classification:

```text
Supported by evidence
```

### Future Drawdown Risk

BRD-001 contains weaker predictive information about future drawdown risk.

The pooled direction is favorable, but cross-period evidence is mixed and the rank correlations are small.

Classification:

```text
Partially supported
```

### Future Returns

BRD-001 does not support the hypothesis that higher breadth predicts higher future SPY returns.

Observed associations were statistically non-null but in the opposite direction from the preregistered return hypothesis.

Classification:

```text
Not supported
```

## Overall PV-001 Conclusion

BRD-001 predictive validity is classified as:

```text
Partially supported
```

The evidence supports BRD-001 as a risk-state predictive construct for future volatility and future trend deterioration.

The evidence does not support BRD-001 as a return-prediction construct.

No economic, portfolio, alpha, profitability, or production-deployment conclusion is made.

