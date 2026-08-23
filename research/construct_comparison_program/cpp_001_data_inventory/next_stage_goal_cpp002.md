# /goal

# RESEARCH PROGRAM

Construct Comparison Program (CPP)

CPP-002

Pairwise Dependence Mapping

--------------------------------------------------

## BACKGROUND

CPP-000 established the Program Charter and Frozen Evidence Registry.

CPP-000.5 preregistered the comparison protocol.

CPP-001 completed the Data Inventory & Alignment Audit and confirmed that frozen construct outputs are available and sample-size eligible for pairwise comparison.

--------------------------------------------------

## PURPOSE

Map pairwise statistical dependence among the frozen validated constructs using only preregistered methods.

This stage measures statistical association only.

It does NOT classify redundancy, complementarity, hierarchy, causality, predictive value, or economic utility.

--------------------------------------------------

## REQUIRED ANALYSES

Use only CPP-001 frozen alignment columns and sample rules.

For every construct pair compute preregistered pairwise dependence metrics from CPP-000.5, including where applicable:

- Pearson correlation
- Spearman correlation
- Kendall correlation
- Mutual information
- Distance correlation
- Missingness-adjusted sample count
- Multiple-testing adjusted significance flags

--------------------------------------------------

## FORBIDDEN

Do NOT:

- modify construct outputs,
- change alignment columns,
- tune thresholds,
- classify redundancy,
- infer causality,
- infer hierarchy,
- infer economic value,
- recommend production usage.

--------------------------------------------------

## EXPECTED OUTPUTS

Generate:

- `cpp002_pairwise_dependence_mapping.md`
- `pairwise_pearson_matrix.csv`
- `pairwise_spearman_matrix.csv`
- `pairwise_kendall_matrix.csv`
- `pairwise_mutual_information.csv`
- `pairwise_distance_correlation.csv`
- `pairwise_sample_counts.csv`
- `multiple_testing_adjustment.csv`
- `limitations.md`
- `executive_summary.md`

--------------------------------------------------

## SUCCESS CRITERIA

CPP-002 succeeds if it produces a preregistered pairwise dependence map without making redundancy, complementarity, hierarchy, causal, predictive, or economic claims.
