# Robustness Analysis

Yearly agreement results are saved as `agreement_by_year.csv`. Horizon-level conditional interaction robustness results are saved as `robustness_analysis.csv`.

| Metric | Value |
|---|---:|
| Years evaluated | 15 |
| Minimum yearly Jaccard | 0.113069 |
| Median yearly Jaccard | 0.134045 |
| Maximum yearly Jaccard | 0.197079 |
| Years with P(TSM_HIGH given CSM_HIGH) = 1.0 | 15 |

Supported by evidence:

- The nesting relationship is stable across evaluated years.
- Jaccard similarity remains low-to-moderate because TSM_HIGH remains much broader than CSM_HIGH.

Inconclusive:

- Robustness outside the frozen historical sample.
