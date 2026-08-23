# BRD-001 / PV-001: Baseline Comparison

## Purpose

Compare BRD-001 predictive associations against a predefined no-association null model.

## Null Model

The null model is:

```text
No association between BRD-001 and the future outcome.
```

This was evaluated using fixed-seed permutation of the future outcome series.

## Results

All tested associations were statistically non-null against the permutation null.

However, statistical non-null does not imply support for the hypothesis unless the direction matches the preregistered expectation.

## Supported Against Null

- Future realized volatility: supported in expected direction.
- Future trend deterioration risk: supported in expected direction.

## Partially Supported Against Null

- Future drawdown risk: expected pooled direction, but weak rank correlation and mixed cross-period evidence.

## Not Supported Against Null

- Future returns: statistically non-null, but direction is opposite the preregistered hypothesis.

## Boundary

This analysis does not evaluate profitability, alpha, or economic value.

