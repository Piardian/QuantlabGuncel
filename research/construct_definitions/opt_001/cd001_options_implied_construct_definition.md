# OPT-001 / CD-001: Options-Implied Construct Definition

## Study Identity

- Research program: Market Signal Discovery Program v3.0
- Construct ID: OPT-001
- Construct family: Options-Implied Market Information
- Stage: CD-001 Construct Definition

## Selected Construct

OPT-001 is defined as:

```text
US Equity Index Option-Implied Volatility State
```

The construct measures the current state of option-implied volatility for the US equity market using the Cboe Volatility Index, publicly available through FRED as:

```text
VIXCLS
```

## Construct Class

Market-level option-implied volatility state construct.

## Primary Question Answered

```text
What is the current level of option-implied near-term volatility priced in the US equity index options market?
```

## Theoretical Mechanism

OPT-001 represents option-market pricing of expected near-term S&P 500 volatility.

The selected observable is derived from SPX option prices. It reflects risk-neutral, options-implied volatility information rather than realized volatility.

This stage does not attempt to separate physical volatility expectations, variance risk premium, hedging demand, investor risk aversion, or tail-risk compensation.

## Why This Definition Was Selected

The VIX-based implied volatility state definition was selected because it offers:

- strong academic and practitioner recognition,
- official index methodology,
- public daily data availability through FRED and Cboe,
- direct link to SPX options prices,
- minimal option microstructure handling inside the local framework,
- operational simplicity,
- clear distinction from realized volatility constructs such as VOL-001.

The selection is based on construct clarity and reproducibility, not expected predictive or economic performance.

## Frozen Operational Definition

For each valid date `t`:

```text
opt001_vix_close_t = VIXCLS_t
```

where `VIXCLS_t` is the Cboe Volatility Index daily close observed on date `t`.

The raw value is expressed in VIX index points.

The normalized state score is:

```text
opt001_zscore_252d_t =
    (opt001_vix_close_t - mean(opt001_vix_close over trailing 252 valid observations))
    /
    std(opt001_vix_close over trailing 252 valid observations)
```

The percentile state is:

```text
opt001_percentile_252d_t =
    percentile_rank(opt001_vix_close_t within trailing 252 valid observations)
```

Higher values indicate higher option-implied volatility state.

## Inputs

- `VIXCLS`: Cboe Volatility Index: VIX

## Outputs

- `opt001_vix_close`
- `opt001_zscore_252d`
- `opt001_percentile_252d`
- `opt001_valid_observation_count_252d`
- `opt001_data_quality_flag`

## Valid Observation Rule

A date is a valid raw OPT-001 observation only when `VIXCLS` is available and positive.

No forward filling is part of the frozen construct definition.

## Normalization Rule

The 252-observation z-score and percentile are computed only when at least 252 valid historical `VIXCLS` observations are available.

If fewer than 252 valid observations exist, normalized outputs must be missing and the data quality flag must identify insufficient lookback history.

## Excluded Variables

The following are intentionally excluded from OPT-001:

- VIX futures term structure
- VIX9D, VIX3M, VIX6M, or other volatility tenor indexes
- variance risk premium
- realized volatility
- risk-neutral skewness
- implied tail risk
- volatility smirk or smile slope
- implied correlation
- put-call parity deviations
- put-call ratios
- option volume and open interest
- dealer gamma or positioning estimates
- individual equity option surfaces

These may be valid future constructs, but they are not part of frozen OPT-001.

## Frozen Status

After CD-001, OPT-001 is frozen.

Any change to source series, formula, normalization windows, missing-data handling, output schema, or interpretation requires restarting from CD-001 under a new preregistered definition.

## Stage Boundary

No claims are made regarding predictive validity, trading performance, alpha generation, economic value, production suitability, or portfolio usefulness.

