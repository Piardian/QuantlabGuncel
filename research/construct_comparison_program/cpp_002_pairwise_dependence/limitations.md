# CPP-002 Limitations

- CPP-002 uses only CPP-001 frozen alignment columns and exact-date pairwise intersections.
- Pearson, Spearman, and Kendall p-values use asymptotic approximations because `scipy` is not installed in the project virtual environment.
- Mutual information is estimated using deterministic quantile discretization and is reported as descriptive magnitude only.
- Distance correlation is exact for pairwise samples up to 2,000 observations; larger pairs use deterministic evenly spaced subsampling to 2,000 observations and are flagged in `pairwise_distance_correlation.csv`.
- No nonlinear p-values are reported.
- No redundancy, orthogonality, complementarity, hierarchy, causality, predictive, alpha, or economic interpretation is permitted from this stage.
