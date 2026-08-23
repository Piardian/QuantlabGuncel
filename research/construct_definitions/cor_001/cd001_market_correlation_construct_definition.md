# COR-001 / CD-001: Market Correlation Construct Definition

## Purpose

Define the official COR-001 construct for the remainder of the Market Signal Discovery Program lifecycle.

This stage freezes the construct definition. It does not implement the construct, evaluate predictive validity, evaluate economic utility, or recommend production use.

## Frozen Construct

Construct ID: COR-001

Construct Name: US Equity Market Average Pairwise Correlation State

Construct Family: Market Correlation

Construct Class: Continuous market-level realized co-movement state construct

## Primary Question Answered

What is the current realized co-movement state of the US equity market?

## Selected Definition

COR-001 measures the average pairwise Pearson correlation of daily log returns across a fixed US equity universe over a trailing 60-trading-day window.

The construct is normalized using a trailing 252-trading-day z-score and percentile.

## Official Output Names

Primary raw output:

```text
cor001_avg_pairwise_corr_60d
```

Normalized outputs:

```text
cor001_zscore_252d
cor001_percentile_252d
```

Diagnostic outputs:

```text
cor001_eligible_security_count
cor001_pair_count
cor001_coverage_ratio
```

## Inputs

- Daily adjusted close or normalized close for each security in the fixed research universe
- Fixed US equity universe file
- Trading calendar derived from available daily price data

## Derived Variables

- Daily log return for each eligible security
- Rolling 60-day return matrix
- Pairwise Pearson correlation matrix
- Average off-diagonal pairwise correlation
- Rolling 252-day z-score of raw correlation
- Rolling 252-day percentile of raw correlation

## Parameters

These parameters are frozen:

| Parameter | Value | Rationale |
|---|---:|---|
| return type | daily log return | Standard for return co-movement measurement |
| correlation estimator | Pearson correlation | Transparent, reproducible, widely used |
| correlation window | 60 trading days | Balances current-state responsiveness and estimation stability |
| normalization window | 252 trading days | Approximate one trading year |
| aggregation | mean off-diagonal pairwise correlation | Direct market-wide synchronization measure |
| minimum eligible securities | 50 | Prevents unstable market-level estimates from very small panels |
| universe | fixed US equity research universe | Reproducibility and alignment with existing construct library |

## Interpretation

Higher COR-001 values indicate higher realized market-wide co-movement among securities.

Lower COR-001 values indicate lower realized market-wide co-movement and more security-specific dispersion.

No return prediction, alpha, profitability, or economic interpretation is permitted at CD-001.

## Construct Freeze

After CD-001, the following are frozen:

- selected construct family
- return type
- estimator type
- rolling correlation window
- aggregation method
- normalization method
- required diagnostic outputs
- inclusion and exclusion rules

Any future change requires restarting from CD-001.

