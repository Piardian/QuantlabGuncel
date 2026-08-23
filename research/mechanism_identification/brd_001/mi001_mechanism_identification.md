# BRD-001 / MI-001: Mechanism Identification

## Purpose

Identify the observable market mechanisms represented by BRD-001.

This stage is explanatory and descriptive.

It does not evaluate predictive validity, trading performance, alpha, profitability, or economic value.

## Construct

BRD-001 measures the percentage of eligible securities in `sp500_current_universe.csv` whose adjusted close is above their own 200-day simple moving average.

## Descriptive State Method

For mechanism profiling only, valid BRD-001 observations were divided into descriptive breadth states:

- `LOW_BREADTH`: bottom 20% of observed breadth values
- `MID_BREADTH`: middle 60% of observed breadth values
- `HIGH_BREADTH`: top 20% of observed breadth values

These are descriptive analysis buckets, not trading thresholds.

Observed cutoffs:

- low-breadth cutoff: 0.5265
- high-breadth cutoff: 0.8172

## Market Variables Used

Only same-day or trailing observable market variables were used:

- SPY 20-day return
- SPY 60-day return
- SPY above SMA200
- SPY distance from SMA200
- SPY 20-day realized volatility
- SPY drawdown from 52-week high
- SPY SMA50/SMA200 trend spread

No future outcome variables were used.

## Main Findings

### Broad Participation Mechanism

HIGH_BREADTH periods show substantially broader participation:

- average BRD-001 value: 0.8708
- SPY above SMA200: 100.00% of observations
- average SPY distance from SMA200: +10.12%
- average 20-day realized volatility: 10.78%
- average 52-week drawdown: -0.68%

Classification:

```text
Supported by evidence
```

### Narrow Participation / Market Stress Mechanism

LOW_BREADTH periods show weak participation and stress-like market conditions:

- average BRD-001 value: 0.3647
- SPY above SMA200: 20.50% of observations
- average SPY distance from SMA200: -4.11%
- average 20-day realized volatility: 26.07%
- average 52-week drawdown: -11.37%

Classification:

```text
Supported by evidence
```

### Internal Confirmation Mechanism

BRD-001 is strongly associated with contemporaneous SPY trend condition:

- correlation with SPY distance from SMA200: 0.8804
- correlation with SPY SMA50/SMA200 trend spread: 0.7165
- correlation with SPY 60-day return: 0.6727

Classification:

```text
Supported by evidence
```

### Volatility and Drawdown Environment Mechanism

BRD-001 is negatively associated with contemporaneous realized volatility and positively associated with shallower drawdown state:

- correlation with SPY 20-day realized volatility: -0.6825
- correlation with SPY drawdown from 52-week high: 0.8306

Classification:

```text
Supported by evidence
```

## Mechanism Interpretation

BRD-001 primarily appears to represent:

```text
Long-term trend participation and internal market confirmation.
```

Secondarily, low BRD-001 values are associated with:

```text
Market stress, elevated realized volatility, and deeper contemporaneous drawdown.
```

## Historical Event Alignment

Low breadth aligned descriptively with several known broad-market stress periods:

- 2011 US debt downgrade / euro stress period
- Q4 2018 selloff
- COVID crash low
- 2022 bear-market stress

This is descriptive historical alignment, not predictive validation.

## Final MI-001 Conclusion

BRD-001 mechanism identification is classified as:

```text
Supported by evidence
```

The identified mechanism is:

```text
BRD-001 represents long-term cross-sectional trend participation and internal market confirmation, with low values corresponding to narrow participation and stress-like market conditions.
```

This conclusion is explanatory only.

No predictive, economic, trading, profitability, alpha, or production-deployment claim is made.

