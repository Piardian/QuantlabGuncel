# ISM-001 / EV-001 Economic Validation

## Purpose

Evaluate whether ISM-001 predictive information provides measurable economic utility under fixed, preregistered industry-level workflows.

This is economic validation only. It is not construct modification, not alpha discovery, not stock-level signal assignment and not a recommendation for production deployment.

## Fixed Workflows

- Benchmark: `STATIC_EQUAL_WEIGHT`, equal-weight all valid Ken French 49 industry portfolios.
- UC-1: `UC1_TOP_DECILE_LONG_ONLY`, equal-weight TOP_DECILE industries.
- UC-2: `UC2_TOP_MINUS_BOTTOM_DOLLAR_NEUTRAL`, equal-weight TOP_DECILE long and BOTTOM_DECILE short research spread.
- UC-3: `UC3_50_50_BENCHMARK_TOP_TILT`, 50% equal-weight benchmark plus 50% equal-weight TOP_DECILE tilt.

## Fixed Assumptions

- Rebalance frequency: monthly.
- Signal timing: state observed at month `t`, realized return measured during month `t+1`.
- Transaction cost: 10.0 bps per dollar of turnover.
- No threshold optimization, no parameter tuning, no workflow redesign after observing results.

## Results

- STATIC_EQUAL_WEIGHT: classification Benchmark, ann return 0.1103, ann vol 0.2038, max drawdown -0.8514, return/vol 0.5412
- UC1_TOP_DECILE_LONG_ONLY: classification Partially supported, ann return 0.1513, ann vol 0.2275, max drawdown -0.7738, return/vol 0.6653
- UC2_TOP_MINUS_BOTTOM_DOLLAR_NEUTRAL: classification Supported by evidence, ann return 0.0607, ann vol 0.2265, max drawdown -0.9666, return/vol 0.2682
- UC3_50_50_BENCHMARK_TOP_TILT: classification Supported by evidence, ann return 0.1325, ann vol 0.2078, max drawdown -0.8146, return/vol 0.6376

## EV-001 Classification

**Supported by evidence**

This result is limited to the fixed industry-level workflows and assumptions evaluated here. It does not imply production readiness, universal economic superiority or individual-stock applicability.
