# CRD-001 / PV-001: Predictive Validation

## Purpose

Evaluate whether CRD-001 contains statistically significant predictive information beyond predefined null models.

This study evaluates predictive validity only. It does not evaluate trading profitability, alpha generation, portfolio performance, Sharpe ratio, CAGR, economic value, or production deployment.

## Construct

CRD-001 measures US High-Yield Credit Spread Stress using FRED series `BAMLH0A0HYM2`.

## Forecast Horizons

PV-001 evaluated:

- 5 trading days
- 20 trading days
- 60 trading days

## Future Outcomes

The predefined future outcomes were:

- future SPY realized volatility
- future SPY drawdown magnitude
- future CRD-001 credit spread change
- future SPY log return

## Statistical Method

CRD-001 was evaluated as a continuous predictor using:

- Pearson correlation
- rank correlation
- fixed-seed permutation test against a no-association null
- LOW_CREDIT_STRESS versus HIGH_CREDIT_STRESS mean differences
- bootstrap confidence intervals
- AUC for top-quartile risk/event classification
- period-block stability
- calibration by CRD-001 percentile quintile

No model fitting, threshold optimization, trading strategy, or portfolio simulation was performed.

## Hypothesis Results

| Hypothesis | 5d Spearman / AUC | 20d Spearman / AUC | 60d Spearman / AUC | Classification |
| --- | ---: | ---: | ---: | --- |
| H1 Future realized volatility | 0.2372 / AUC 0.6295 | 0.1081 / AUC 0.6426 | -0.2809 / AUC 0.4377 | Partially supported |
| H2 Future drawdown risk | -0.0403 / AUC 0.5033 | -0.1077 / AUC 0.5494 | -0.2957 / AUC 0.4021 | Not supported |
| H3 Future credit spread widening | -0.2558 / AUC 0.4707 | -0.3690 / AUC 0.4247 | -0.6304 / AUC 0.3000 | Not supported |
| H4 Future equity market returns | 0.1964 / AUC 0.4730 | 0.3389 / AUC 0.4229 | 0.6872 / AUC 0.2570 | Supported by evidence |

## Main Findings

### Future Realized Volatility

Classification: Partially supported.

Evidence is positive at 5-day and 20-day horizons but reverses at 60 days. This supports short-horizon volatility information but not stable horizon-wide predictive validity.

### Future Drawdown Risk

Classification: Not supported.

### Future Credit Spread Widening

Classification: Not supported.

The observed association is negative across horizons, so the preregistered widening hypothesis is not supported. This may indicate spread normalization within the available sample, but that is not tested here and is not promoted to a new conclusion.

### Future Equity Market Returns

Classification: Supported by evidence.

This means only that CRD-001 showed statistical association with future SPY log returns in the available sample. It does not imply alpha, tradability, profitability, or economic value.

## Overall PV-001 Conclusion

CRD-001 predictive validity is classified as:

```text
Partially supported
```

This conclusion is limited to predictive validity over the available sample. No economic, portfolio, alpha, profitability, or production-deployment conclusion is made.
