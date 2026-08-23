# RSM-001 / LR-001 Literature Review

## Purpose

Synthesize the scientific literature on Residual Momentum as a risk-adjusted / idiosyncratic momentum construct.

This review does not define the frozen RSM-001 construct, choose a factor model, choose a regression window, implement code, backtest, optimize, or claim alpha.

## Primary Research Question

What does the current scientific literature collectively conclude about Residual Momentum as an independent momentum-related expected-return mechanism?

## High-Level Finding

Residual Momentum is a scientifically meaningful extension of cross-sectional momentum. Instead of ranking securities on raw prior returns, it ranks or scores securities using residual returns after removing common factor exposures.

The central claim in the literature is that conventional price momentum contains time-varying exposure to common factors, while residual momentum aims to isolate more idiosyncratic continuation.

## Canonical Literature Anchor

Blitz, Huij and Martens (2011) are the central literature anchor. Their work argues that ranking stocks on residual returns rather than total returns can reduce exposure to common factors and improve consistency relative to conventional momentum.

## Relationship To CSM-001

CSM-001:

- Uses raw cross-sectional prior return.
- Measures relative price leadership.
- Does not remove factor exposures.

RSM-001:

- Uses residual prior return after factor-model adjustment.
- Attempts to isolate idiosyncratic momentum.
- Requires a predefined risk model and regression design.

Residual Momentum is therefore not simply a parameter variant of CSM-001. It is a different measurement construct.

## Residual Return Concept

General form:

```text
asset_return_i,t = alpha_i + beta_i * factor_returns_t + residual_i,t
```

Residual momentum uses prior residual returns as the momentum input.

Key design choices:

- Factor model.
- Regression window.
- Return frequency.
- Formation window.
- Skip period.
- Residual aggregation method.
- Residual volatility standardization.

These choices must be frozen in CD-001.

## Theoretical Explanations

Potential mechanisms:

- Idiosyncratic underreaction: investors underreact to stock-specific information.
- Factor-exposure separation: raw momentum partly reflects common factor movement.
- Cleaner signal hypothesis: residual returns may reduce confounding from market, value, size or other factors.
- Risk-model dependence: apparent residual momentum may depend on omitted-factor specification.

## Empirical Evidence Summary

Strong evidence:

- Residual momentum is a recognized academic and practitioner construct.
- It has evidence suggesting lower common factor exposure than raw price momentum.
- It is naturally comparable to conventional momentum.

Moderate evidence:

- Some studies report more stable performance than raw momentum.
- International and follow-up studies suggest residual/idiosyncratic momentum can appear outside the original sample.

Conflicting or limited evidence:

- Results depend on chosen asset-pricing model.
- Residualization can introduce estimation error.
- Regression windows and residual volatility scaling affect measurement.
- Omitted factors can change the meaning of residuals.

## Data Requirements

RSM requires:

- Security return panel.
- Common factor return series.
- Risk-free rate if excess returns are used.
- Sufficient history per security for rolling regressions.
- Deterministic handling of missing data.

This is materially more feasible than PEAD-001 and PROF-001 because it does not require point-in-time earnings or accounting statement data.

## LR-001 Conclusion

Residual Momentum is scientifically mature enough to proceed to construct definition.

CD-001 must freeze a single residualization design. The factor model and regression window are not implementation details; they define the construct itself.

## Next Stage

Proceed to:

**RSM-001 / CD-001 Construct Definition**
