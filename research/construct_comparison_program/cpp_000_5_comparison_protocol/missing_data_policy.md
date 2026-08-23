# CPP-000.5

# Missing Data Policy

## Primary Policy

CPP-001 must create two sample definitions:

1. Common Sample: dates where all eligible construct outputs are available.
2. Pairwise Maximum Sample: dates where a given construct pair has valid observations.

## Usage Rules

- Common Sample is primary for multivariate, incremental, redundancy, and architecture analysis.
- Pairwise Maximum Sample is allowed for pairwise dependence only and must be clearly labeled.
- No forward filling may be introduced during CPP unless the original frozen construct output already contains such processing.
- Missing observations must remain missing.
- If aligned observations fall below minimum sample thresholds, the result is classified as Inconclusive.

## Excluded Periods

No period is excluded at CPP-000.5. Any exclusion must be justified in CPP-001 as a data-quality issue and cannot be based on results.
