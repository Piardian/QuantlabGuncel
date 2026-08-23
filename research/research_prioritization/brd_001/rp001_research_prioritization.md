# BRD-001 / RP-001: Research Prioritization

## Purpose

Determine whether **Market Breadth** should become a standalone construct in the Market Signal Discovery Program v3.0.

This stage evaluates research priority only. It does not define the final construct, choose a breadth indicator, run empirical tests, evaluate prediction, or assess economic utility.

## Primary Decision

**GO**

BRD-001 should proceed to `BRD-001 / LR-001`.

## Evidence Summary

Market Breadth is a recognized market-internals construct describing the degree to which market movement is broadly shared across securities rather than concentrated in a small number of index constituents.

The literature and practitioner tradition support multiple breadth measurement families, including advance/decline measures, new-high/new-low measures, percentage of stocks above moving averages, up/down volume, participation ratios, and cross-sectional participation measures.

BRD-001 is scientifically distinct from completed constructs:

- MR-001 models latent market regime from index-level returns and volatility.
- LIQ-001 measures aggregate price-impact liquidity stress.
- VOL-001 measures realized volatility state from SPY daily OHLC.
- BRD-001 would measure market participation and internal confirmation across many securities.

This distinction matters because a capitalization-weighted index can rise or fall while participation narrows or broadens beneath the surface.

## Evaluation Dimensions

| Dimension | Assessment | Rationale |
| --- | --- | --- |
| Scientific relevance | High | Breadth measures market participation and internal strength, a concept widely used in market-internals analysis. |
| Theoretical foundation | Medium to High | Breadth is linked to participation, dispersion, concentration, confirmation, and internal market health. |
| Construct independence | High | Breadth is related to trend, volatility and regime but conceptually distinct because it measures how many securities participate. |
| Literature maturity | Medium | Practitioner literature is mature; academic evidence exists but is less standardized than volatility or liquidity. |
| Data availability | Medium to High | Daily panel OHLC data can support reproducible breadth proxies, though historical constituent data quality matters. |
| Measurability | High | Several deterministic measures can be computed from daily security panels. |
| Practical importance | High | Breadth can identify concentration, participation deterioration, broad-risk confirmation, and market-internal weakness. |
| Expected research contribution | High | BRD-001 may provide information not captured by index-level regime, liquidity, or volatility constructs. |

## Candidate Measurement Families for LR-001

The next stage should review at least:

- Advance / decline line
- Advance / decline ratio
- Net advancing issues
- Up-volume / down-volume
- New highs / new lows
- Percentage of stocks above moving averages
- Breadth thrust indicators
- Cross-sectional participation ratios
- Equal-weighted versus cap-weighted confirmation
- Sector breadth
- Concentration-adjusted breadth

This list is not a final construct definition. It is a literature-review scope.

## Supported Claims at RP Stage

- Market Breadth is a recognized market-internals construct.
- Breadth is conceptually distinct from index-level return, volatility, liquidity and regime.
- Breadth can be operationalized reproducibly from panel market data.
- A dedicated BRD-001 research program is scientifically justified.

## Not Supported at RP Stage

- Any specific breadth indicator is superior.
- Breadth predicts future returns.
- Breadth improves trading performance.
- Breadth has economic value in this project.
- BRD-001 should modify any production strategy.

## Decision

BRD-001 receives a **GO** decision for the next stage.

The next authorized stage is:

`BRD-001 / LR-001: Market Breadth Literature Review`

