# FUND-001 / CD-001: Funding Stress Construct Definition

## Study Identity

- Research program: Market Signal Discovery Program v3.0
- Construct ID: FUND-001
- Construct family: Funding Stress
- Stage: CD-001 Construct Definition

## Selected Construct

FUND-001 is defined as:

```text
US Financial Commercial Paper Funding Spread Stress
```

The construct measures stress in short-term private financial-sector funding markets using the spread between 90-day AA financial commercial paper rates and 3-month US Treasury bill rates.

## Construct Class

Market-level short-term funding stress construct.

## Primary Question Answered

```text
What is the current stress level in short-term US financial-sector funding markets relative to Treasury bill funding conditions?
```

## Theoretical Mechanism

FUND-001 represents the cost premium required for highly rated financial commercial paper issuers to obtain short-term unsecured funding relative to short-term US Treasury bills.

The selected observable is intended to capture stress in private short-term financial funding markets. Higher values indicate a larger premium for private financial funding relative to Treasury bills.

This stage does not attempt to decompose the spread into liquidity risk, counterparty credit risk, monetary policy expectations, safe-asset demand, or market technicals.

## Why This Definition Was Selected

The financial commercial paper funding spread definition was selected because it offers:

- direct connection to short-term private funding markets
- stronger post-LIBOR continuity than LIBOR-OIS or TED-style definitions
- public data availability through FRED
- daily source frequency
- operational simplicity
- interpretable spread construction
- conceptual distinction from high-yield credit spreads, equity liquidity, realized volatility, breadth, correlation, and broad market regime constructs

The selection is based on construct clarity and reproducibility, not expected predictive or economic performance.

## Frozen Operational Definition

For each date `t`:

```text
fund001_cp_rate_t = DCPF3M_t
```

where `DCPF3M_t` is the 90-Day AA Financial Commercial Paper Interest Rate from FRED.

```text
fund001_tbill_rate_t = DTB3_t
```

where `DTB3_t` is the 3-Month Treasury Bill Secondary Market Rate, Discount Basis from FRED.

The raw funding spread is:

```text
fund001_cp_tbill_spread_t = fund001_cp_rate_t - fund001_tbill_rate_t
```

All raw rates are expressed in percentage points.

The normalized stress score is:

```text
fund001_zscore_252d_t =
    (fund001_cp_tbill_spread_t - mean(fund001_cp_tbill_spread over trailing 252 valid observations))
    /
    std(fund001_cp_tbill_spread over trailing 252 valid observations)
```

The percentile state is:

```text
fund001_percentile_252d_t =
    percentile_rank(fund001_cp_tbill_spread_t within trailing 252 valid observations)
```

Higher values indicate higher funding stress.

## Inputs

- `DCPF3M`: 90-Day AA Financial Commercial Paper Interest Rate
- `DTB3`: 3-Month Treasury Bill Secondary Market Rate, Discount Basis

## Outputs

- `fund001_cp_rate`
- `fund001_tbill_rate`
- `fund001_cp_tbill_spread`
- `fund001_zscore_252d`
- `fund001_percentile_252d`
- `fund001_valid_observation_count_252d`
- `fund001_data_quality_flag`

## Valid Observation Rule

A date is a valid raw FUND-001 observation only when both `DCPF3M` and `DTB3` are available on that date.

No forward filling is part of the frozen construct definition.

Implementation may separately report missing-data diagnostics, but must not manufacture construct values for missing dates.

## Normalization Rule

The 252-observation z-score and percentile are computed only when at least 252 valid historical spread observations are available.

If fewer than 252 valid spread observations exist, normalized outputs must be missing and the data quality flag must identify insufficient lookback history.

## Excluded Variables

The following are intentionally excluded from FUND-001:

- LIBOR-OIS spread
- TED spread
- SOFR-OIS alternatives
- repo spread measures
- haircut or margin requirement measures
- dealer leverage or balance-sheet measures
- central-bank liquidity operation variables
- OFR Financial Stress Index funding category
- Chicago Fed NFCI components
- high-yield credit spreads
- equity liquidity measures
- equity volatility measures
- breadth measures
- correlation measures
- macroeconomic variables

These may be valid constructs or future variants, but they are not part of frozen FUND-001.

## Frozen Status

After CD-001, FUND-001 is frozen.

Any change to source series, spread formula, normalization windows, missing-data handling, eligibility rules, output schema, or interpretation requires restarting from CD-001 under a new preregistered definition.

## Stage Boundary

No claims are made regarding predictive validity, trading performance, alpha generation, economic value, production suitability, or portfolio usefulness.

