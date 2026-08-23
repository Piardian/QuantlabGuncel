# Confidence Interval Report

## Bootstrap Confidence Intervals

Bootstrap method: resampling high and low LIQ-001 buckets independently.

Iterations: 4000

hypothesis                 feature  difference    ci_low   ci_high        classification
        H1 realized_volatility_20d    0.169723  0.160247  0.179368 Supported by evidence
        H2          abs_spy_return    0.008500  0.007509  0.009518 Supported by evidence
        H3            spy_drawdown   -0.081582 -0.086944 -0.076214 Supported by evidence
        H4     mr_stress_indicator    0.778961  0.749667  0.808256 Supported by evidence
        H5          coverage_ratio   -0.007989 -0.011849 -0.004017   Partially supported

## Boundary

Confidence intervals describe uncertainty in the observed historical sample. They do not establish causality.
