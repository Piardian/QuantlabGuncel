# RSM-001 / RP-001 Research Prioritization

## Purpose

Determine whether Residual Momentum should be accepted as an independent scientific edge construct worthy of full investigation within the Market Edge Discovery Program.

This stage does not define the construct, choose a risk model, implement code, backtest, optimize, or claim alpha.

## Primary Research Question

Should Residual Momentum be accepted as an independent scientific construct worthy of full investigation?

## Decision

**GO**

## Rationale

Residual Momentum is a natural next construct after CSM-001 and TSM-001 because it remains within the momentum family while asking a distinct scientific question:

Does momentum remain meaningful after removing common factor exposures?

The literature, led by Blitz, Huij and Martens, argues that ranking securities by residual returns can reduce time-varying exposure to common factors and produce a more idiosyncratic momentum signal than raw total-return momentum.

The GO decision is based on scientific relevance, conceptual distinctiveness, expected incremental value and strong compatibility with the existing price-return infrastructure.

The decision is not based on expected profitability or production suitability.

## Critical Qualification

RSM-001 requires strict preregistration of the residualization model.

Before CD-001 freezes the construct, the program must explicitly resolve:

- Which common factor model is used.
- Which regression window is used.
- Whether returns are daily or monthly.
- Whether residual momentum is ranked cross-sectionally or classified as a state.
- Whether residuals are volatility-standardized.
- How missing data and low-observation windows are handled.
- Whether factor data is public and reproducible.

## Evidence Classification

Supported by evidence:

- Residual Momentum is a recognized momentum variant.
- It is conceptually distinct from raw cross-sectional momentum.
- It is constructable using price returns plus predefined factor returns.
- It has high expected information value after CSM-001 and TSM-001.

Partially supported:

- Implementation feasibility is strong if factor data and regression design are frozen.

Not supported at RP stage:

- Any claim of predictive validity in this repository.
- Any claim that RSM is superior to CSM.
- Any production readiness conclusion.

## Final RP-001 Conclusion

RSM-001 receives a **GO** decision for literature review.

The next stage is:

**RSM-001 / LR-001**
