# TSM-001 / EV-001 Economic Validation

## Purpose

Evaluate whether TSM-001 predictive risk-state information provides measurable economic utility under fixed, preregistered risk-management workflows.

This is economic validation only. It is not alpha discovery, not construct modification, and not a recommendation for production deployment.

## Fixed Workflows

- Benchmark: static equal-weight available universe.
- UC-1: positive-only exposure with cash remainder.
- UC-2: positive-breadth-scaled risk control.
- UC-3: defensive equal-weight scaling when positive breadth is below 60%.

No threshold optimization or parameter tuning was performed. The 60% defensive threshold was fixed before execution as a simple majority-breadth rule.

## Evidence Base

- Source state file: `output/tsm_001_cv001/tsm001_construct_state.csv`
- Daily observations: 3,770
- Date range: 2011-01-03 to 2025-12-29

## Results

- static_equal_weight: classification Benchmark, ann return 0.1756, ann vol 0.1806, max drawdown -0.3837, return/vol 0.9725
- positive_only_cash_remainder: classification Partially supported, ann return 0.1113, ann vol 0.1255, max drawdown -0.3151, return/vol 0.8869
- risk_control_positive_breadth_scaled: classification Partially supported, ann return 0.1113, ann vol 0.1255, max drawdown -0.3151, return/vol 0.8869
- defensive_breadth_scaled_equal_weight: classification Partially supported, ann return 0.1416, ann vol 0.1592, max drawdown -0.3837, return/vol 0.8891

## EV-001 Classification

**Partially supported**

The conclusion is limited to the fixed workflows evaluated here. No universal economic superiority, trading alpha or production readiness is inferred.
