# BRD-001 / CD-001: Construct Assumptions

## Assumption 1: Fixed Universe Is Acceptable for Initial Construct Research

BRD-001 uses `sp500_current_universe.csv` as a fixed broad US equity universe.

This assumes a fixed-universe participation construct is scientifically useful despite survivorship limitations.

## Assumption 2: Closing Prices Are Sufficient for Long-Term Participation

The construct assumes adjusted or normalized closing prices are sufficient to measure whether each security participates in a long-term positive trend state.

## Assumption 3: 200-Day SMA Represents Long-Term Trend Participation

The construct assumes the 200-day simple moving average is an established and interpretable long-term trend reference.

This is not a profitability assumption.

## Assumption 4: Equal Security Weighting Represents Breadth

Each eligible security contributes equally to the breadth measure.

This assumes breadth should measure participation count rather than capitalization-weighted contribution.

## Assumption 5: Missing Securities Should Be Excluded Per Date

Securities without sufficient valid history on a given date are excluded from that day's eligible universe.

Coverage diagnostics must always be reported.

## Assumption 6: Normalization Is Descriptive

The 252-day z-score and percentile are descriptive state transformations.

They are not trading thresholds and must not be interpreted as optimized decision rules.

