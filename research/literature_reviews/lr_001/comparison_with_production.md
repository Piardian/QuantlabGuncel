# LR-001 Comparison With Production Implementation

## Current Implementation

```text
RS60 > 5%
AND StockReturn60 > SPYReturn60
AND (RS20 > 0 OR RS120 > 10%)

RSx = StockReturnx - SPYReturnx
```

## Similarities To Literature

- It uses prior price-return information over multiple horizons.
- It expresses performance relative to a benchmark, which resembles benchmark-relative return constructions.
- It has a medium-horizon component (60 trading days) and short/long persistence checks (20 and 120 days).

## Differences From Canonical Academic Cross-Sectional Momentum

- It does not rank stocks against a cross-sectional universe.
- It does not select top deciles, quintiles, or percentiles and does not form a winner-minus-loser portfolio.
- It is long-only and compares each stock only with SPY.
- It uses fixed thresholds and a logical `OR`; canonical studies commonly use continuous ranks and portfolio sorting.
- It does not use the common 12-1 specification explicitly.
- It is not sector-neutral, industry-relative, or risk-adjusted.

## Differences From Time-Series Momentum

Time-series momentum usually conditions on an asset's own prior excess-return sign. The production filter requires benchmark-relative outperformance, so it is not a pure time-series momentum implementation.

## Comparison With Practitioner Methodology

MSCI Momentum methodology combines 6-month and 12-month risk-adjusted price momentum scores, selects high-scoring constituents from a parent index, and includes implementation controls such as weighting, caps, buffers, and rebalancing. The production filter shares only the broad multi-horizon price-momentum intuition; it is not equivalent to that methodology.

## Boundary

Similarity to a literature family does not validate the production operationalization. This document neither endorses nor rejects the implementation.
