# FUND-001 / CD-001

# Construct Specification

## Official Name

US Financial Commercial Paper Funding Spread Stress

## Construct Intent

FUND-001 measures short-term US financial-sector funding stress through the premium of AA financial commercial paper funding rates over 3-month Treasury bill rates.

## Observable Dimension

Primary observable dimension:

```text
private financial short-term funding cost premium
```

## Financial Interpretation

When the spread rises, financial commercial paper issuers face a higher short-term funding cost relative to Treasury bill rates.

This may reflect funding stress, liquidity preference, counterparty risk, credit concern, or safe-asset demand. FUND-001 records the spread without decomposing those drivers.

## Mathematical Definition

```text
spread_t = DCPF3M_t - DTB3_t
```

```text
zscore_252d_t = (spread_t - rolling_mean_252_valid(spread)) / rolling_std_252_valid(spread)
```

```text
percentile_252d_t = percentile_rank(spread_t, trailing_252_valid_spreads)
```

## Frequency

Daily source frequency, subject to source availability.

## Data Provider

FRED / Federal Reserve Bank of St. Louis.

Underlying source: Board of Governors of the Federal Reserve System.

## Required Series

- `DCPF3M`
- `DTB3`

## Output Direction

Higher raw spread, higher z-score, and higher percentile indicate higher funding stress.

## Minimum History

Raw spread:

- valid when both source series are present.

Normalized outputs:

- valid only after 252 valid spread observations.

## Data Quality Flags

Required flags:

- `OK`
- `MISSING_INPUT`
- `INSUFFICIENT_LOOKBACK`
- `ZERO_ROLLING_STD`

