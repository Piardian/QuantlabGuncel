# Methodology Comparison

## Purpose

Compare major methodologies used to measure market correlation.

No methodology is selected in LR-001.

## Methodology Table

| Method | Description | Advantages | Limitations | CD-001 Suitability |
|---|---|---|---|---|
| Rolling Pearson correlation | Correlation over fixed rolling windows | Simple, transparent, reproducible | Window-sensitive, assumes linear dependence | High for simple construct |
| Average pairwise correlation | Mean of pairwise correlations across a universe | Market-wide synchronization view | Requires universe and missing-data rules | High |
| Rolling covariance matrix | Full covariance estimate | Portfolio-risk relevance | Noisy in high dimensions | Medium |
| EWMA covariance/correlation | Exponentially weighted recent observations | Responsive and common in risk systems | Decay parameter must be frozen | Medium |
| Ledoit-Wolf shrinkage | Noise-reduced covariance estimator | Addresses sample noise | More complex and estimator-dependent | Medium |
| CCC-GARCH | Conditional variance with constant conditional correlation | Formal econometric structure | Correlation is fixed by design | Low-Medium |
| DCC-GARCH | Dynamic conditional correlation model | Models time-varying correlation | Complex, estimation-sensitive | Medium |
| PCA/eigenvalue concentration | Share of variance explained by dominant components | Systemic common-factor view | Less direct as "correlation" | Medium-High |
| Implied correlation | Derived from index and constituent options | Forward-looking | Requires options data | Medium |
| Copula/tail dependence | Nonlinear and extreme co-movement | Crisis-state relevance | Complex and data hungry | Medium |
| Correlation network | Graph representation of dependence | Structural and systemic interpretation | Methodological degrees of freedom | Medium |

## Main Methodological Warning

Simple correlation is not wrong, but it is not neutral. It embeds assumptions about linear dependence, sample window, stationarity, and volatility conditions.

## Recommended LR-001 Interpretation

The literature supports multiple legitimate measurement families. CD-001 must choose one based on scientific objective, not expected performance.

