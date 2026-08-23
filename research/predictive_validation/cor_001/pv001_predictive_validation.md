# COR-001 / PV-001: Predictive Validation

## Purpose

Evaluate whether COR-001 contains statistically significant predictive information about future market risk behavior.

This study evaluates predictive validity only.

It does not evaluate trading profitability, alpha, portfolio performance, Sharpe ratio, CAGR, or economic value.

## Construct

COR-001 measures average pairwise Pearson correlation of daily log returns across a fixed US equity universe over a trailing 60-trading-day window.

## Forecast Horizons

PV-001 evaluated:

- 20 trading days
- 60 trading days

## Future Outcomes

The predefined future outcomes were:

- future SPY realized volatility
- future SPY drawdown risk
- future market breadth deterioration
- future market correlation persistence

## Statistical Method

COR-001 was evaluated as a continuous predictor using:

- Pearson correlation
- rank correlation
- fixed-seed permutation test against a no-association null
- LOW_CORRELATION versus HIGH_CORRELATION mean differences
- bootstrap confidence intervals
- AUC for binary risk-event classification
- period-block stability
- calibration by COR-001 quintile

No model fitting, threshold optimization, trading strategy, or portfolio simulation was performed.

## Hypothesis Results

| Hypothesis | Target | Horizon | Rank Corr | Low Mean | High Mean | AUC | Classification |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| H1 | Future realized volatility | 20d | 0.3176 | 0.1186 | 0.2107 | 0.7370 | Supported by evidence |
| H1 | Future realized volatility | 60d | 0.2413 | 0.1387 | 0.1969 | 0.7222 | Supported by evidence |
| H2 | Future drawdown risk | 20d | -0.0483 | -0.0198 | -0.0315 | 0.5724 | Partially supported |
| H2 | Future drawdown risk | 60d | -0.0010 | -0.0421 | -0.0514 | 0.5368 | Partially supported |
| H3 | Future breadth deterioration | 20d | -0.4036 | 0.6543 | 0.3821 | 0.7611 | Supported by evidence |
| H3 | Future breadth deterioration | 60d | -0.2765 | 0.5490 | 0.3352 | 0.7273 | Supported by evidence |
| H4 | Future correlation persistence | 20d | 0.6864 | 0.2169 | 0.4487 | 0.8801 | Supported by evidence |
| H4 | Future correlation persistence | 60d | 0.5685 | 0.2377 | 0.4223 | 0.8109 | Supported by evidence |

## Main Findings

### Future Realized Volatility

COR-001 contains predictive information about future SPY realized volatility.

Higher correlation state is associated with higher future realized volatility at both 20-day and 60-day horizons.

Classification:

```text
Supported by evidence
```

### Future Breadth Deterioration

COR-001 contains predictive information about future market breadth deterioration.

Higher correlation state is associated with lower future minimum BRD-001 breadth at both horizons.

Classification:

```text
Supported by evidence
```

### Future Correlation Persistence

COR-001 contains predictive information about future correlation persistence.

Higher current correlation state is associated with higher future average COR-001 values at both horizons.

Classification:

```text
Supported by evidence
```

### Future Drawdown Risk

COR-001 contains weaker predictive information about future drawdown risk.

The pooled high-minus-low differences preserve the expected direction, but rank correlations are small and cross-period evidence is mixed.

Classification:

```text
Partially supported
```

## Overall PV-001 Conclusion

COR-001 predictive validity is classified as:

```text
Partially supported
```

The evidence supports COR-001 as a risk-state predictive construct for future realized volatility, future breadth deterioration, and future correlation persistence.

The evidence for future drawdown risk is weaker and classified as partially supported.

No economic, portfolio, alpha, profitability, or production-deployment conclusion is made.

