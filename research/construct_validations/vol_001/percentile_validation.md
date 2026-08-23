# Percentile Validation

## Bucket Distribution

bucket  count      pct
  0-20    944 0.251532
 20-40    738 0.196643
 40-60    713 0.189981
 60-80    646 0.172129
80-100    712 0.189715

## Bounds

- Minimum percentile: 0.003968
- Maximum percentile: 1.000000
- Observations outside [0, 1]: 0

## Assessment

VOL-001 percentile values are bounded between 0 and 1 and use deterministic tie handling from CD-001.

Because the percentile uses a trailing 252-day rolling window, exact long-run uniformity is not required, but bucket counts should be broadly interpretable.
