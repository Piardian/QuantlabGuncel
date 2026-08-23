# CV-001 Limitations

## Universe Limitation

The construct uses a fixed current US equity universe from `sp500_current_universe.csv`.

This may introduce survivorship bias in historical observations.

## Data Source Limitation

Yahoo Finance reported missing or invalid data for several symbols.

The construct handled this through eligibility and coverage diagnostics, but data-source limitations remain.

## Linear Correlation Limitation

COR-001 uses Pearson correlation and therefore measures linear co-movement.

It does not measure nonlinear dependence or tail dependence.

## Window Limitation

The 60-day correlation window and 252-day normalization window are frozen by CD-001.

CV-001 does not test alternative windows.

## Construct Independence Limitation

CV-001 does not evaluate whether COR-001 is independent from MR-001, VOL-001, LIQ-001, or BRD-001.

## Predictive And Economic Boundary

CV-001 does not evaluate:

- future returns
- future volatility
- future drawdown
- trading performance
- alpha
- economic value
- production suitability

