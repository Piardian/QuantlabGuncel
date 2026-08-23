# FUND-001 / CV-001: Construct Validation

## Scope

This study evaluates construct validity only. It does not evaluate prediction, alpha, trading performance, economic value, or production suitability.

## Construct Under Review

```text
US Financial Commercial Paper Funding Spread Stress
FUND-001 = DCPF3M - DTB3
```

## Primary Findings

- The implementation faithfully represents the frozen CD-001 formula.
- Raw observations begin in 1997-01-02 because DCPF3M begins later than DTB3.
- Normalized OK observations begin in 1998-01-05 after 252 valid spread observations.
- The construct produces interpretable spikes around known funding-stress windows, especially the global financial crisis and March 2020 liquidity shock.
- Missing-data behavior is explicit and deterministic.

## Validation Classification

```text
Partially supported
```

## Rationale

FUND-001 is internally coherent, reproducible, and faithful to CD-001 over the period where both source series are available. However, the long pre-1997 section contains missing input because the commercial paper source series does not cover the full Treasury bill history. The construct is therefore valid for the available commercial-paper era but not a continuous 1954-present funding stress history.

## No Forbidden Claims

No claim is made about predictive validity, alpha, trading returns, economic value, or production use.
