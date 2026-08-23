# LIQ-001 / HV-001: Hypothesis Validation

## Purpose

Evaluate whether the mechanism hypotheses generated in MI-001 are empirically supported.

This stage evaluates explanatory validity only. No predictive, alpha, profitability, or economic utility claim is made.

## Overall Classification

**Partially supported**

## Results

hypothesis                                                           description                 feature expected_direction  high_count  low_count  high_mean  low_mean  difference    ci_low   ci_high  cohens_d  permutation_pvalue        classification
        H1 High LIQ-001 periods have higher contemporaneous realized volatility. realized_volatility_20d           positive         751        751   0.258229  0.088506    0.169723  0.160247  0.179368  1.762118             0.00025 Supported by evidence
        H2               High LIQ-001 periods have larger absolute market moves.          abs_spy_return           positive         751        751   0.013038  0.004538    0.008500  0.007509  0.009518  0.859126             0.00025 Supported by evidence
        H3                High LIQ-001 periods occur in deeper drawdown context.            spy_drawdown           negative         751        751  -0.101868 -0.020286   -0.081582 -0.086944 -0.076214 -1.533549             0.00025 Supported by evidence
        H4          High LIQ-001 periods overlap more with MR-001 STRESS states.     mr_stress_indicator           positive         751        751   0.780293  0.001332    0.778961  0.749667  0.808256  2.648579             0.00025 Supported by evidence
        H5                       LIQ-001 is not merely a data coverage artifact.          coverage_ratio          near_zero         751        751   0.955743  0.963732   -0.007989 -0.011849 -0.004017 -0.201179             0.00025   Partially supported

## Interpretation

The evidence supports the broad mechanism that high LIQ-001 periods represent aggregate price-impact liquidity stress associated with volatile, high-movement, drawdown-heavy market conditions and greater overlap with MR-001 STRESS states.

The evidence is not interpreted as prediction or economic utility.
