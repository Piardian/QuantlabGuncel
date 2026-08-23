# CSM-001 / EV-001 Economic Validation

## Purpose

Evaluate whether CSM-001 predictive information provides measurable economic utility under a fixed, preregistered portfolio workflow.

## Fixed Workflow

- Portfolio: equal-weight CSM-001 top-decile securities.
- Benchmark: equal-weight eligible universe on the same rebalance dates.
- Rebalance interval: 21 trading days.
- Execution assumption: signal observed at close, return measured from next close-to-close interval.
- Transaction cost: 10.0 bps per dollar traded.
- No threshold optimization, no parameter tuning, no strategy redesign.

## Results

- Top-decile net annualized return: 0.2298
- Benchmark net annualized return: 0.1651
- Annualized return delta: 0.0646
- Top-decile return-to-volatility: 1.0021
- Benchmark return-to-volatility: 0.9687
- Active positive year rate: 0.6667
- Top-decile max drawdown: -0.3853
- Benchmark max drawdown: -0.3701

## EV-001 Classification

**Partially supported**

This result is limited to the fixed workflow, current-constituent universe and cost assumption evaluated here. It does not imply production readiness or universal economic superiority.
