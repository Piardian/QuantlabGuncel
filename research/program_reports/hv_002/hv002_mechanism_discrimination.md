# HV-002 Mechanism Discrimination Study

## Purpose
This study evaluates whether the completed v2.0 evidence can meaningfully distinguish between two competing explanatory mechanisms:

- **H1:** the observable behavior of the Production Relative Strength Gate is more consistent with a **Composite Trend** construct.
- **H2:** the observable behavior of the Production Relative Strength Gate is equally or better explained by a **Trend Strength** construct.

No new backtest, optimization, threshold tuning, or return analysis was performed.

## Evidence basis
- `LR-001` ruled out equivalence with canonical cross-sectional momentum.
- `CV-001` showed low overlap with the preregistered 12-1 comparator.
- `CI-001` identified the Trend family as the highest-overlap family.
- `TCM-001` identified `COMPOSITE_TREND_SCORE` as the highest-overlap comparator inside Trend.
- `HV-001` found the mechanism is trend-like, but not uniquely isolated.

## Discrimination result
The available evidence does **not** reliably distinguish Composite Trend from Trend Strength as competing explanations.

### Why
- Composite Trend has the highest Jaccard overlap in the Trend family.
- Trend Strength is extremely close behind in Jaccard overlap.
- Trend Strength has a higher mean daily Spearman agreement with the production gate than Composite Trend.
- Both candidates are stable across years and consistently positive in the yearly slices evaluated in TCM-001.

## Conclusion
**Current evidence cannot distinguish between the two mechanisms.**

That conclusion is supported by:
- the very small gap in descriptive overlap,
- the split across different descriptive metrics,
- and the strong year-by-year stability of both candidates.

It is not supported by any evidence that one mechanism is uniquely established.

