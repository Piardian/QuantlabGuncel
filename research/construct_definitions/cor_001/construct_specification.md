# Construct Specification

## Construct ID

`COR-001`

## Construct Name

US Equity Market Average Pairwise Correlation State

## Construct Family

Market Correlation

## Construct Class

Continuous market-level realized co-movement state construct.

## Measurement Family

Average pairwise realized correlation across a fixed US equity universe.

## Primary Question Answered

```text
What is the current realized co-movement state of the US equity market?
```

## Inputs

- Daily adjusted close or normalized close for every security in the fixed universe
- Fixed US equity research universe file

## Formula

For each security `i`:

```text
r_i,t = ln(close_i,t / close_i,t-1)
```

For each date `t`, construct a trailing 60-trading-day return matrix using eligible securities.

Compute the Pearson correlation matrix across eligible securities.

Let `rho_ij,t` be the pairwise correlation between securities `i` and `j` over the trailing 60-day window.

The raw COR-001 value is:

```text
cor001_avg_pairwise_corr_60d,t =
mean(rho_ij,t for all i < j among eligible securities)
```

Normalize over trailing 252 valid raw observations:

```text
cor001_zscore_252d,t =
(cor001_avg_pairwise_corr_60d,t - mean_252d) / std_252d
```

```text
cor001_percentile_252d,t =
percentile_rank(cor001_avg_pairwise_corr_60d,t within trailing 252 valid observations)
```

## Eligibility

A security is eligible on date `t` if it has valid daily log returns for the entire trailing 60-trading-day correlation window.

A date is eligible for raw COR-001 output if at least 50 securities are eligible.

## Core Output

```text
cor001_avg_pairwise_corr_60d
```

## State Outputs

```text
cor001_zscore_252d
cor001_percentile_252d
```

## Diagnostic Outputs

```text
cor001_eligible_security_count
cor001_pair_count
cor001_coverage_ratio
```

## Interpretation

Higher values indicate higher cross-sectional co-movement.

Lower values indicate lower cross-sectional co-movement.

No predictive, trading-performance, alpha, or economic interpretation is permitted at CD-001.

