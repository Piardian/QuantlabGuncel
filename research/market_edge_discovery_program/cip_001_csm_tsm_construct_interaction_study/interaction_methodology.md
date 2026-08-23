# Interaction Methodology

CIP-001 evaluates the interaction between two frozen constructs only:

- CSM-001: cross-sectional relative leadership / intermediate-horizon winner-state construct.
- TSM-001: own-trend state construct.

The study uses the shared ticker-date panel where both constructs report valid observations. CSM state is represented by the frozen `csm001_top_decile_flag`. TSM state is represented by the frozen positive vs negative own-trend state.

Confirmatory analyses:

- Information overlap using Jaccard similarity, precision, recall, coverage and binary association.
- Interaction-state profiling across CSM_HIGH/CSM_NOT_HIGH and TSM_HIGH/TSM_LOW.
- Incremental information using descriptive linear R-squared comparisons for future returns at the already used 21, 63 and 126 trading-day horizons.
- Conditional predictive analysis comparing CSM spreads within TSM states and TSM spreads within CSM states.
- Agreement/disagreement and transition analysis.
- Yearly robustness checks.

Interpretation is limited to incremental scientific information and interaction behavior. The study does not redefine either construct, optimize thresholds, build a trading strategy, or recommend production deployment.
