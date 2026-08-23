# Reproducibility Report

CRD-001 uses deterministic formulas only. With identical source data, configuration, and preprocessing, output values are reproducible.

The validation summary records SHA256 hashes for both the input snapshot and primary output CSV.

## Independent Snapshot Reproduction

The validator was rerun using the frozen input snapshot:

```text
output/crd_001_validation/crd001_input_series.csv
```

The primary output hash matched exactly:

```text
572b37694f289dd35c665ae31c84711e6e8dbf7c038cbd91e4612cc8a851b8ba
```

Conclusion: reproducibility is verified for identical input data and configuration.
