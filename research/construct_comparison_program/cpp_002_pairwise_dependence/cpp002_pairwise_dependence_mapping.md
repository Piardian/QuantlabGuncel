# CPP-002 Pairwise Dependence Mapping

## Purpose

CPP-002 maps pairwise statistical dependence among the eight frozen validated constructs using CPP-001 frozen alignment columns.

This stage measures statistical association only. It does not classify redundancy, orthogonality, complementarity, hierarchy, causality, predictive value, or economic utility.

## Inputs

- Alignment registry: `../cpp_001_data_inventory/construct_output_registry.csv`
- Sample rule: pairwise exact-date observations with `N >= 252`
- Multiple testing policy: Benjamini-Hochberg FDR at `q = 0.05` within metric families where p-values are available.

## Methods Executed

- Pearson correlation with Fisher z normal approximation p-values.
- Spearman rank correlation with Fisher z normal approximation p-values.
- Kendall tau-b with large-sample normal approximation p-values.
- Quantile-discretized normalized mutual information as descriptive nonlinear association magnitude.
- Distance correlation as descriptive nonlinear association magnitude.

## Descriptive Highest Absolute Associations by Metric Family

The table below is a navigation aid only. It is not a redundancy, hierarchy, complementarity, or causal classification.

| metric_family | construct_a | construct_b | n | statistic | bh_fdr_reject |
| --- | --- | --- | --- | --- | --- |
| kendall | LIQ-001 | VOL-001 | 3753 | 0.577062 | True |
| kendall | VOL-001 | OPT-001 | 3753 | 0.534118 | True |
| kendall | VOL-001 | COR-001 | 3712 | 0.49036 | True |
| kendall | BRD-001 | OPT-001 | 3573 | -0.481523 | True |
| kendall | LIQ-001 | COR-001 | 3712 | 0.457387 | True |
| pearson | LIQ-001 | VOL-001 | 3753 | 0.79826 | True |
| pearson | VOL-001 | OPT-001 | 3753 | 0.76631 | True |
| pearson | LIQ-001 | COR-001 | 3712 | 0.722439 | True |
| pearson | BRD-001 | OPT-001 | 3573 | -0.720749 | True |
| pearson | VOL-001 | COR-001 | 3712 | 0.717688 | True |
| spearman | LIQ-001 | VOL-001 | 3753 | 0.768428 | True |
| spearman | VOL-001 | OPT-001 | 3753 | 0.715522 | True |
| spearman | VOL-001 | COR-001 | 3712 | 0.669404 | True |
| spearman | BRD-001 | OPT-001 | 3573 | -0.662514 | True |
| spearman | LIQ-001 | COR-001 | 3712 | 0.634464 | True |

## Boundary

Statistically high or low pairwise association in CPP-002 does not establish construct redundancy or independence. Those classifications are reserved for later preregistered CPP stages.
