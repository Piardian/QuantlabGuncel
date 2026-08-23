# Canonical Definitions

## Core TSM Idea

Time-Series Momentum measures whether an asset's own past return is positive or negative and uses that own-history information as the construct state.

## Common Academic Form

A common academic form evaluates prior return over a formation window and assigns a positive state when the prior return is positive and a negative state when the prior return is negative.

## Common Horizons

Literature often examines continuation over 1 to 12 month horizons and potential reversal over longer horizons.

## Volatility Scaling

Many TSM implementations scale positions by volatility. This is not merely a measurement detail; it can materially affect empirical conclusions.

## LR-001 Boundary

No horizon, volatility scaling method, asset universe or position mapping is frozen in LR-001. CD-001 must make those choices explicitly.
