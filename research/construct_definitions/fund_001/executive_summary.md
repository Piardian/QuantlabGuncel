# FUND-001 / CD-001

# Executive Summary

## Selected Construct

FUND-001 is frozen as:

```text
US Financial Commercial Paper Funding Spread Stress
```

## Formula

```text
FUND-001 = DCPF3M - DTB3
```

where:

- `DCPF3M` = 90-Day AA Financial Commercial Paper Interest Rate
- `DTB3` = 3-Month Treasury Bill Secondary Market Rate, Discount Basis

## Interpretation

Higher values indicate higher short-term private financial funding stress relative to Treasury bill rates.

## Why Selected

This definition is:

- narrow,
- public,
- reproducible,
- interpretable,
- non-LIBOR-based,
- directly related to short-term financial funding costs.

## Main Limitation

The spread is not a pure funding-liquidity measure. It can include credit risk, liquidity risk, counterparty concern, safe-asset demand, and policy-rate effects.

## Stage Result

CD-001 successfully defines and freezes FUND-001.

Next authorized stage after human approval:

```text
FUND-001 / IM-001
```

## Boundary

No claims are made regarding predictive validity, alpha, profitability, trading performance, economic value, or production readiness.

