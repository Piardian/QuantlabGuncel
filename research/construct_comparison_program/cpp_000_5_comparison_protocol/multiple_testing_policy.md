# CPP-000.5

# Multiple Testing Policy

## Primary Correction

Benjamini-Hochberg false discovery rate correction at:

```text
q = 0.05
```

## Application Families

Correction is applied within predefined families:

- Pairwise Pearson tests.
- Pairwise Spearman tests.
- Nonlinear dependence tests.
- Incremental information tests by target family.
- Lead-lag tests by construct-pair lag family.

## Reporting

Reports may include raw p-values, but confirmatory interpretation must rely on corrected significance.

If no p-value based test is applicable, confidence intervals and stability criteria must be reported instead.
