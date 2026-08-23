# BRD-001 / CD-001: Construct Specification

## Construct Name

US Equity 200-Day Moving-Average Breadth State

## Construct ID

BRD-001

## Scientific Category

Market Breadth / Market Internals / Participation

## Observable Question

What percentage of eligible securities in the fixed broad US equity universe are participating in a long-term positive trend state?

## Formal Definition

For each eligible security:

```text
above_sma200_i,t = 1 if close_i,t > mean(close_i,t-199 ... close_i,t) else 0
```

For the market:

```text
brd001_pct_above_sma200_t =
    mean(above_sma200_i,t across eligible securities)
```

## Scale

The primary value is continuous and bounded:

```text
0 to 1
```

## Interpretation

Higher values indicate broad participation above long-term trend.

Lower values indicate weak or narrow participation.

## Primary Output

```text
brd001_pct_above_sma200
```

## Secondary Outputs

```text
brd001_zscore
brd001_percentile
coverage diagnostics
```

## Fixed Parameters

| Parameter | Value | Rationale |
| --- | ---: | --- |
| Moving-average length | 200 trading days | Widely used long-term trend participation horizon. |
| Normalization window | 252 valid observations | Approximately one trading year. |
| Minimum eligible securities | 50 | Prevents market-level output from very sparse coverage. |

## Frozen Status

All parameters are frozen after CD-001.

