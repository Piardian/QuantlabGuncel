# OPT-001 / CD-001

# Construct Specification

## Official Name

US Equity Index Option-Implied Volatility State

## Construct Intent

OPT-001 measures the current option-implied volatility state of the US equity market using daily VIX close values.

## Observable Dimension

Primary observable dimension:

```text
option-implied near-term S&P 500 volatility
```

## Financial Interpretation

Higher VIX values indicate that SPX option prices imply a higher near-term volatility state.

OPT-001 records this state without decomposing it into expected physical volatility, risk premium, hedging demand, or investor risk aversion.

## Mathematical Definition

```text
opt001_vix_close_t = VIXCLS_t
```

```text
opt001_zscore_252d_t =
    (opt001_vix_close_t - rolling_mean_252_valid(opt001_vix_close))
    /
    rolling_std_252_valid(opt001_vix_close)
```

```text
opt001_percentile_252d_t =
    percentile_rank(opt001_vix_close_t, trailing_252_valid_vix_values)
```

## Frequency

Daily close, subject to source availability.

## Data Provider

FRED / Federal Reserve Bank of St. Louis.

Underlying source: Chicago Board Options Exchange.

## Required Series

- `VIXCLS`

## Output Direction

Higher raw value, z-score, and percentile indicate higher option-implied volatility state.

## Minimum History

Raw VIX state:

- valid when source value is available and positive.

Normalized outputs:

- valid only after 252 valid VIX observations.

## Data Quality Flags

Required flags:

- `OK`
- `MISSING_INPUT`
- `INSUFFICIENT_LOOKBACK`
- `ZERO_ROLLING_STD`
- `INVALID_NON_POSITIVE`

