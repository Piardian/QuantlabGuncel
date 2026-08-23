# Construct Validation Summary

## Construct

COR-001: US Equity Market Average Pairwise Correlation State

## CV-001 Result

```text
Supported by evidence
```

## Evidence Summary

Supported by evidence:

- Output schema matches CD-001.
- Raw correlation values are bounded within [-1, 1].
- Percentile values are bounded within [0, 1].
- Valid raw observations are available across the full sample after warmup.
- Coverage is sufficient for construct validation.
- Pair counts are large enough for broad market-level estimation.
- Raw correlation values vary meaningfully across historical periods.
- Normalized state values are produced after the 252-observation warmup.

Partially supported:

- Coverage is sufficient but affected by fixed current-universe and Yahoo availability limitations.

Not supported:

- No construct-validity failure was identified in CV-001.

Inconclusive:

- Whether COR-001 captures tail dependence.
- Whether COR-001 is independent from VOL-001, MR-001, LIQ-001, or BRD-001.
- Whether COR-001 contains predictive or economic information.

## Final Boundary

CV-001 supports COR-001 as a valid implementation of the preregistered Market Correlation construct.

It does not support any claim about prediction, profitability, alpha, economic utility, or production deployment.

