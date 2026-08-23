# Construct Specification

## Construct ID

`CRD-001`

## Construct Name

US High-Yield Credit Spread Stress

## Construct Family

Credit Stress

## Construct Class

Continuous market-level credit spread stress construct.

## Measurement Family

High-yield corporate option-adjusted spread.

## Primary Question Answered

```text
What is the current stress level in US high-yield corporate credit markets?
```

## Input Series

```text
FRED series: BAMLH0A0HYM2
Series name: ICE BofA US High Yield Option-Adjusted Spread
Frequency: Daily
Units: Percent
```

## Raw Formula

For each valid date `t`:

```text
crd001_hy_oas,t = BAMLH0A0HYM2,t
```

## Normalized Outputs

Trailing 252 valid observations are used for normalization.

```text
crd001_zscore_252d,t =
(crd001_hy_oas,t - mean_252d) / std_252d
```

```text
crd001_percentile_252d,t =
rank_percentile(crd001_hy_oas,t within trailing 252 valid observations)
```

## Observation Eligibility

A date is eligible for raw CRD-001 output when:

- `BAMLH0A0HYM2` is available for that date, or
- the value can be forward-filled from the most recent valid observation within a maximum of 5 calendar days.

A date is eligible for normalized output when:

- raw CRD-001 is available, and
- at least 252 valid historical observations exist in the trailing normalization window, and
- trailing standard deviation is greater than zero.

## Missing Data Rule

Forward-fill is allowed for gaps of up to 5 calendar days to handle holidays and publication gaps.

Gaps longer than 5 calendar days must be marked invalid and not silently filled.

## Core Output

```text
crd001_hy_oas
```

## State Outputs

```text
crd001_zscore_252d
crd001_percentile_252d
```

## Diagnostic Outputs

```text
crd001_valid_observation_count_252d
crd001_days_since_last_observation
crd001_data_quality_flag
```

## Interpretation

Higher values indicate wider high-yield credit spreads and higher observed high-yield credit stress.

Lower values indicate tighter high-yield credit spreads and lower observed high-yield credit stress.

No predictive, trading-performance, alpha, or economic interpretation is permitted at CD-001.

