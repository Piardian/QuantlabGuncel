# CPP-000.5

# Classification Rules

| relationship | classification_rule |
| --- | --- |
| Redundant | Absolute Spearman >= 0.80 AND absolute Pearson >= 0.70 AND stable sign in >=75% robustness windows AND conditional relationship adds negligible information. |
| Partially redundant | Absolute Spearman >= 0.60 OR absolute Pearson >= 0.60, but stability or conditional evidence is incomplete. |
| Orthogonal | Absolute Spearman <= 0.20 AND absolute Pearson <= 0.20 AND nonlinear dependence not supported after correction. |
| Complementary | Pairwise dependence not redundant AND multivariate/incremental information gain is supported after correction and robustness. |
| Dominated / downstream candidate | Construct loses incremental information after conditioning on another construct and exhibits consistent lagging temporal association. |
| Upstream candidate | Construct shows stable lead-lag association before another construct without causal claim and retains incremental information. |
| Inconclusive | Minimum sample, correction, stability, or robustness criteria not met. |

## Evidence Labels

Every relationship conclusion must use one of:

- Supported by evidence
- Partially supported
- Not supported
- Inconclusive

## Boundary

Redundancy does not invalidate a construct. Orthogonality does not imply economic usefulness. Complementarity does not imply trading edge.
