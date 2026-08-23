# FUND-001 / IM-001

# Reproducibility Report

## Determinism

The implementation uses deterministic formulas only.

Given identical input CSVs, configuration, and code, FUND-001 produces identical outputs.

## Repeated Transform Check

Repeated execution on identical in-memory input produced identical data frames.

Result:

```text
deterministic_repeated_transform = true
```

## Hash-Based Reproducibility

The validation run recorded:

- input snapshot hash,
- primary output hash.

These hashes allow future reruns to verify whether input revisions or code changes altered the output.

## External Data Note

Live FRED downloads can change if source data are revised. Full reproducibility requires archiving the input snapshot:

```text
output/fund_001_validation/fund001_input_series.csv
```

