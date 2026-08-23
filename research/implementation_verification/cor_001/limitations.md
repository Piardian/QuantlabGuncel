# IM-001 Limitations

## Synthetic Verification

IM-001 uses deterministic synthetic data to verify implementation fidelity.

It does not validate full historical behavior.

## Data Availability

The implementation supports Yahoo Finance download and CSV close-panel input. Data-source quality is not validated until CV-001.

## Performance

Average pairwise correlation across large universes can be computationally heavier than single-index constructs. This is an engineering consideration, not a construct-definition change.

## Missing Data

The implementation excludes securities without complete trailing 60-day return windows on each date.

## Methodological Boundary

IM-001 does not evaluate:

- predictive validity
- trading performance
- alpha generation
- economic utility
- production suitability

