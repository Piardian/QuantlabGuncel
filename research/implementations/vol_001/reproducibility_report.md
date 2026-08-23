# Reproducibility Report

## Deterministic Formula

VOL-001 uses deterministic formulas only:

- OHLC normalization
- log return components
- Rogers-Satchell component
- 20-day Yang-Zhang variance
- annualization
- 252-day z-score
- 252-day percentile

## Frozen Input Test

The implementation was executed twice using the same frozen input file:

```text
output/vol_001_validation_fidelity_a/vol001_input_ohlc.csv
```

Both executions produced the same primary output hash:

```text
6d282bc54967f813b34def31d606c155b711cf168fa5a189c616e461796454c2
```

## Reproducibility Boundary

Determinism requires identical input data.

Live Yahoo Finance downloads can differ across runs due vendor updates or data revisions. For scientific reproduction, raw input snapshots should be archived with validation outputs.

## Conclusion

VOL-001 is reproducible from identical input data and configuration.

