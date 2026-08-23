# BRD-001 / CV-001: Limitations

## Survivorship Limitation

BRD-001 uses `sp500_current_universe.csv`.

This is a fixed current universe and not a survivorship-free historical constituent universe.

## Data Vendor Limitation

Yahoo Finance reported missing or invalid data for:

- `BRK.B`
- `HONA`
- `BF.B`
- `FDXF`

These symbols were handled through eligibility and coverage diagnostics.

## Adjustment Limitation

The pipeline uses the configured Yahoo close field.

Any future interpretation must account for the chosen adjustment basis.

## Scope Limitation

CV-001 validates construct behavior only.

It does not test:

- future returns
- future volatility
- drawdown prediction
- alpha
- trading performance
- economic value
- production deployment

## Construct Scope Limitation

BRD-001 measures 200-day moving-average breadth.

It does not measure:

- daily advance/decline breadth
- up/down volume breadth
- new high/new low breadth
- sector breadth
- breadth thrust

Those would require separate constructs or a restart from CD-001.

