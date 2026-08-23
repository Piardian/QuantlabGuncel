# BRD-001 / CD-001: Construct Limitations

## Survivorship Bias

BRD-001 uses a fixed current S&P 500-style universe file.

It is not a survivorship-free historical constituent model.

This limitation must be carried into every validation report.

## Trend-Participation Bias

BRD-001 measures long-term moving-average breadth.

It does not measure raw daily advance/decline participation.

## Parameter Dependence

The 200-day SMA and 252-day normalization windows are fixed because they are widely interpretable.

They are not optimized.

## Equal-Weighting Limitation

Each security contributes equally regardless of market capitalization, liquidity, or sector weight.

This makes BRD-001 a participation measure, not an index-contribution measure.

## Data Coverage Limitation

Early dates, IPOs, delisted names, and symbols with incomplete history may reduce eligible coverage.

Coverage diagnostics are required.

## Construct Overlap

BRD-001 may overlap with trend, regime, volatility, and liquidity constructs.

This overlap must be evaluated in later lifecycle stages and must not be inferred at CD-001.

## No Predictive or Economic Claim

CD-001 does not evaluate whether BRD-001 predicts returns, volatility, drawdowns, or economic outcomes.

