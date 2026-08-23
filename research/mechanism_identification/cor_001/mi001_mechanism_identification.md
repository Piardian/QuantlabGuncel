# COR-001 / MI-001: Mechanism Identification

## Purpose

Identify observable market mechanisms associated with COR-001 high and low correlation states.

This study is explanatory and descriptive only.

It does not evaluate predictive validity, trading performance, alpha, profitability, or economic value.

## Construct

COR-001:

```text
US Equity Market Average Pairwise Correlation State
```

Primary value:

```text
cor001_avg_pairwise_corr_60d
```

## State Definition Used For MI-001 Profiling

State buckets were defined using COR-001's own trailing 252-day percentile:

| State | Rule |
| --- | --- |
| LOW_CORRELATION | `cor001_percentile_252d <= 0.20` |
| MID_CORRELATION | `0.20 < cor001_percentile_252d < 0.80` |
| HIGH_CORRELATION | `cor001_percentile_252d >= 0.80` |

These buckets are descriptive profiling groups only.

They are not trading rules.

## Data Used

- COR-001 output: `output/cor001_correlation_state.csv`
- BRD-001 output: `output/brd001_breadth_state.csv`
- SPY contemporaneous daily market profile

Rows analyzed:

```text
3,712
```

## State Profile Summary

| State | Observations | Mean COR | Mean SPY 20d Vol | Mean SPY 52w Drawdown | Mean Breadth |
| --- | ---: | ---: | ---: | ---: | ---: |
| HIGH_CORRELATION | 702 | 0.4511 | 0.2540 | -0.0971 | 0.4586 |
| MID_CORRELATION | 2,025 | 0.3038 | 0.1323 | -0.0306 | 0.6907 |
| LOW_CORRELATION | 985 | 0.2113 | 0.1001 | -0.0163 | 0.7401 |

## Main Mechanism Finding

Supported by evidence:

High COR-001 states represent market-wide synchronization associated with elevated realized volatility, deeper contemporaneous drawdowns, weaker SPY trend position, and lower market breadth.

Supported by evidence:

Low COR-001 states represent lower market-wide synchronization associated with lower realized volatility, shallower contemporaneous drawdowns, stronger SPY trend position, and broader market participation.

## Contemporaneous Associations

COR-001 raw values showed the following contemporaneous associations:

| Feature | Pearson | Spearman |
| --- | ---: | ---: |
| SPY 20d realized volatility | 0.6673 | 0.6268 |
| SPY distance from SMA200 | -0.6385 | -0.5781 |
| SPY 52w drawdown | -0.6514 | -0.5716 |
| BRD-001 breadth | -0.5700 | -0.4088 |
| SPY absolute return | 0.3463 | 0.2509 |

## Mechanism Interpretation

The evidence is consistent with the following descriptive mechanism:

```text
High COR-001
        ->
Market-wide co-movement / synchronization
        ->
Common-factor dominance and stress-like internal market behavior
        ->
Higher contemporaneous volatility, weaker breadth, and deeper drawdown profile
```

This is an explanatory profile, not a predictive claim.

## Final MI-001 Conclusion

The primary mechanism represented by COR-001 is classified as:

```text
Market-wide synchronization / common co-movement stress
```

Evidence classification:

```text
Supported by evidence
```

No predictive, economic, alpha, profitability, trading-performance, or production-deployment conclusion is made.

