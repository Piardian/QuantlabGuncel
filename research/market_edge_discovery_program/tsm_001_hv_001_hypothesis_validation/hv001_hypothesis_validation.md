# TSM-001 / HV-001 Hypothesis Validation

## Purpose

Formally validate the MI-001 mechanism hypotheses for the frozen TSM-001 Raw 12-1 Time-Series Momentum State.

No future returns, alpha, trading performance, backtests, volatility scaling or economic value were evaluated.

## Evidence Base

- Source state file: `output/tsm_001_cv001/tsm001_construct_state.csv`
- Valid observations: 1,768,840
- Unique tickers: 499
- Date range: 2011-01-03 to 2025-12-30

## Hypothesis Results

### H1

POSITIVE states represent positive intermediate-horizon own-trend behavior.

- Classification: **Supported by evidence**
- Positive return consistency: 1.000000
- Positive years with positive median: 15/15
- Mean POSITIVE 12-1 return: 0.293499
- 95% bootstrap CI for mean: [0.292916, 0.294055]

### H2

NEGATIVE states represent negative intermediate-horizon own-trend behavior.

- Classification: **Supported by evidence**
- Negative return consistency: 1.000000
- Negative years with negative median: 15/15
- Mean NEGATIVE 12-1 return: -0.152260
- 95% bootstrap CI for mean: [-0.152622, -0.151882]

### H3

Aggregate positive breadth represents market-wide prevalence of positive own-trend states.

- Classification: **Supported by evidence**
- Zero accounting-error date rate: 1.000000
- Mean positive breadth: 0.725449
- 2.5% to 97.5% historical positive breadth range: [0.336203, 0.950617]

### H4

State transitions represent sign changes in intermediate-horizon own-trend rather than short-horizon price reversals.

- Classification: **Supported by evidence**
- Transition zero-crossing rate: 1.000000
- Directional transition count: 45534
- Median absolute 12-1 return at transition-period observations: 0.011615

## Persistence Evidence

- POSITIVE median duration: 4.0 trading days
- POSITIVE p90 duration: 169.0 trading days
- NEGATIVE median duration: 3.0 trading days
- NEGATIVE p90 duration: 51.0 trading days

## Overall HV-001 Conclusion

**Supported by evidence**

The evidence supports the MI-001 mechanism interpretation that TSM-001 is a signed intermediate-horizon own-trend state construct. This validation is explanatory only and does not evaluate forecasting ability or economic value.
