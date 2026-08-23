# Accounting Policy

## Return Measurement

For each monthly holding period:

```text
holding_return = adjusted_close_exit / adjusted_close_entry - 1
```

Entry price:

- next trading day adjusted close after rebalance signal date

Exit price:

- adjusted close on the trading day before the next portfolio entry date, or the next rebalance close where implementation is simpler and deterministic

The chosen implementation detail must be documented in WPC-002 and applied consistently.

## Portfolio Return

Portfolio return for each holding period:

```text
portfolio_return = mean(holding_return of selected holdings)
```

If there are no selected holdings:

```text
portfolio_return = 0
```

## Benchmark Return

Benchmark return uses the same accounting rule and same rebalance dates.

Benchmark holdings:

```text
CSM_NOT_HIGH x TSM_HIGH
```

## Costs

WPC-002 must first validate gross accounting.

Cost-adjusted accounting is reserved for a later protocol unless explicitly authorized.

## Required Accounting Checks

WPC-002 must verify:

- no look-ahead dates
- entry date is after signal date
- exit date is after entry date
- holdings exist in price panel
- missing prices are reported
- cash periods are recorded
- benchmark uses identical timing
