# OPT-001 / CV-001

# Implementation Validation

## CD-001 Fidelity

The implementation matches the frozen CD-001 specification:

- Source series: `VIXCLS`
- Raw construct output: `opt001_vix_close`
- Rolling normalization window: 252 valid observations
- Z-score output: `opt001_zscore_252d`
- Percentile output: `opt001_percentile_252d`
- Quality flag output: `opt001_data_quality_flag`
- No forward fill of official construct values

## Reproducibility

- Deterministic repeated transform: True
- Input snapshot SHA256: `06997d13a21f489e7cb2ed8cc874c7e1ce1fa4b14ae2e2e87e57da9a6948247b`
- Output SHA256: `c5b093c3f0cbcf4b3af7d51361da979e7470ebb7629e25b3402d7345a518aac1`

## Verification Result

The implementation faithfully represents CD-001 and produces reproducible outputs from the archived input snapshot and configuration.
