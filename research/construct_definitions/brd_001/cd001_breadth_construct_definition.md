# BRD-001 / CD-001: Market Breadth Construct Definition

## Purpose

Define the exact Market Breadth construct that will be investigated throughout the remaining V3.0 lifecycle.

This stage freezes the construct. It does not test prediction, profitability, alpha, trading performance, or economic utility.

## Selected Construct

**US Equity 200-Day Moving-Average Breadth State**

## Construct Type

Continuous market-level participation construct.

## Definition

BRD-001 measures the percentage of eligible securities in a fixed broad US equity universe whose adjusted close is above their own trailing 200-day simple moving average.

The construct is designed to represent long-term trend participation across securities.

Higher values indicate broader market participation above long-term trend.

Lower values indicate narrower participation or broad deterioration below long-term trend.

## Market Universe

The US equity market participation universe is represented by the fixed repository universe:

```text
sp500_current_universe.csv
```

This is a fixed current-constituent universe, not a survivorship-free historical constituent universe.

This limitation is intentional and must be reported in every BRD-001 study until a separate construct revision changes it.

## Required Inputs

For each security `i` and trading day `t`:

- adjusted or normalized close

The close series must be adjusted on a consistent basis across all securities.

## Core Security-Level Measure

For each eligible security `i` on day `t`, compute:

```text
sma200_i,t = mean(close_i,t-199 ... close_i,t)
```

Then compute:

```text
above_sma200_i,t = 1 if close_i,t > sma200_i,t else 0
```

Equality is treated as not above:

```text
close_i,t == sma200_i,t -> above_sma200_i,t = 0
```

## Market-Level Breadth

Let `N_t` be the number of eligible securities on day `t`.

```text
brd001_pct_above_sma200_t =
    sum(above_sma200_i,t across eligible securities) / N_t
```

The value is bounded:

```text
0 <= brd001_pct_above_sma200_t <= 1
```

## Normalized Breadth State

The normalized breadth z-score is:

```text
brd001_zscore_t =
    (brd001_pct_above_sma200_t - rolling_mean(brd001_pct_above_sma200_t, 252))
    / rolling_std(brd001_pct_above_sma200_t, 252)
```

The percentile state is:

```text
brd001_percentile_t =
    count(values <= brd001_pct_above_sma200_t within trailing 252 valid values)
    / 252
```

The rolling 252-day window includes the current day and requires 252 valid market-level breadth observations.

## Coverage Diagnostics

For each day `t`, compute:

```text
brd001_eligible_count_t = N_t
brd001_total_universe_count_t = number of tickers in sp500_current_universe.csv
brd001_coverage_ratio_t = brd001_eligible_count_t / brd001_total_universe_count_t
brd001_count_above_sma200_t = sum(above_sma200_i,t)
brd001_count_not_above_sma200_t = N_t - brd001_count_above_sma200_t
```

## Eligibility Rules

A security-day is eligible if:

- current close is positive
- current close is finite
- at least 200 valid closes are available for that security in the trailing 200 trading-day window ending at `t`
- all 200 closes used in the SMA calculation are positive and finite

A market-day receives a raw BRD-001 value only if:

```text
brd001_eligible_count_t >= 50
```

A market-day receives `brd001_zscore` and `brd001_percentile` only if 252 valid raw `brd001_pct_above_sma200` observations are available.

## Outputs

Each valid market day receives:

- `date`
- `brd001_pct_above_sma200`
- `brd001_zscore`
- `brd001_percentile`
- `brd001_count_above_sma200`
- `brd001_count_not_above_sma200`
- `brd001_eligible_count`
- `brd001_total_universe_count`
- `brd001_coverage_ratio`
- `brd001_valid_observation`

## Primary Breadth Dimension

BRD-001 primarily represents:

- market participation
- long-term trend participation
- internal market confirmation across securities
- breadth of securities trading above long-term moving average

## Non-Goals

BRD-001 does not attempt to:

- measure daily advance / decline breadth
- measure up-volume / down-volume breadth
- measure new high / new low breadth
- measure sector breadth
- measure liquidity
- measure realized volatility
- measure market regime
- forecast returns
- maximize trading performance
- produce buy/sell signals
- optimize thresholds

## Final CD-001 Status

The BRD-001 construct is now frozen.

Any future change to universe, input fields, moving-average length, eligibility rules, normalization window, formula, or outputs requires restarting from CD-001.

