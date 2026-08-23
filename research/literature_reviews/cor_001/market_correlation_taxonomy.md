# Market Correlation Taxonomy

## Purpose

This taxonomy organizes major market-correlation construct families identified in the literature.

No official COR-001 definition is selected in LR-001.

## Taxonomy Table

| Family | What It Measures | Typical Inputs | Strengths | Key Limitations |
|---|---|---|---|---|
| Pairwise realized correlation | Co-movement between two return series | Daily or intraday returns | Simple and interpretable | Narrow, pair-specific, window-sensitive |
| Average pairwise correlation | Broad synchronization across a universe | Panel returns | Direct market-wide co-movement measure | Sensitive to universe and missing data |
| Correlation matrix state | Full dependence structure | Multi-asset return matrix | Portfolio-risk relevance | High dimensional and noisy |
| EWMA correlation | Recent-weighted correlation | Return matrix | Responsive to recent changes | Decay choice affects behavior |
| Shrinkage covariance/correlation | Noise-reduced matrix estimate | Return matrix | Addresses finite-sample instability | Requires estimator assumptions |
| Dynamic conditional correlation | Model-based time-varying correlation | Return series | Formal econometric framework | Model complexity and assumptions |
| Implied correlation | Option-market expected co-movement | Index and constituent options | Forward-looking market-implied measure | Requires options data and methodology choices |
| Cross-asset correlation | Co-movement between asset classes | Asset-class returns | Diversification relevance | Asset-class definitions matter |
| Sector correlation | Common movement within or across sectors | Sector returns or constituents | Captures market structure | Sector taxonomy dependence |
| PCA/eigenvalue concentration | Common-factor dominance | Correlation/covariance matrix | Systemic-risk relevance | Interpretation depends on universe |
| Tail dependence | Extreme co-movement | Tail observations or copula inputs | Crisis-relevant | More complex and data hungry |
| Network correlation | Connectivity and clustering | Correlation graph | Structure-rich systemic view | Methodology-sensitive |

## Key Taxonomy Decision For CD-001

The most important CD-001 decision is whether COR-001 should represent:

- broad equity-market synchronization
- cross-asset diversification failure
- systemic common-factor concentration
- forward-looking implied co-movement
- extreme-tail co-movement

These are related but not identical constructs.

