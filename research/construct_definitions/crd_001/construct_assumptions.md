# Construct Assumptions

## Assumption 1: High-Yield Spreads Are a Valid Credit Stress Observable

CRD-001 assumes that high-yield option-adjusted spreads are a valid market-level observable for speculative-grade US corporate credit stress.

Evidence status: Supported by literature.

## Assumption 2: Wider Spreads Represent Higher Credit Stress

The construct assumes a monotonic interpretation:

```text
higher high-yield OAS = higher observed high-yield credit stress
```

Evidence status: Supported by literature.

## Assumption 3: Option-Adjusted Spread Is Preferable to Simple Yield Spread for This Construct

The selected source uses an option-adjusted spread convention, which is intended to make spread measurement more comparable across bonds with embedded options.

Evidence status: Supported for measurement clarity; vendor methodology remains a limitation.

## Assumption 4: A Single Public Source Is Preferred for Reproducibility

CRD-001 assumes that a single public FRED series is preferable to a multi-source composite at this stage because it improves deterministic reproducibility.

Evidence status: Methodological design choice.

## Assumption 5: 252 Valid Observations Are Appropriate for State Normalization

The construct uses trailing 252 valid observations for z-score and percentile outputs. This is a descriptive normalization convention approximating one trading year.

Evidence status: Operational assumption; not selected for expected performance.

## Assumption 6: CRD-001 Does Not Decompose Spread Components

CRD-001 assumes the total high-yield OAS is the observable construct, without separating expected default risk, liquidity premium, and excess risk premium.

Evidence status: Known simplification.

