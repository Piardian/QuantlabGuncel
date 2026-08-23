# OPT-001 / CV-001: Construct Validation

## Scope

This study evaluates construct validity only. It does not evaluate prediction, alpha, trading performance, economic value, or production suitability.

## Construct Under Review

```text
US Equity Index Option-Implied Volatility State
Source: VIXCLS
```

## Primary Findings

- The implementation faithfully represents the frozen CD-001 VIXCLS-based construct.
- Raw observations cover 9,239 valid VIX observations from 1990-01-02 to 2026-07-28.
- Normalized observations cover 8,988 OK observations after the 252-valid-observation warmup.
- Missing-data handling is explicit and deterministic; no official construct values are forward filled.
- Rolling z-score and percentile outputs are internally interpretable and reproducible.
- High VIX observations align descriptively with well-known market stress windows, which supports construct face validity without making predictive claims.

## Validation Classification

```text
Supported by evidence
```

## Rationale

OPT-001 is internally coherent, reproducible, and faithful to CD-001. The source series is a widely used options-implied volatility measure, the data-quality flags are explicit, and normalized outputs become available after the preregistered rolling 252-valid-observation window.

## No Forbidden Claims

No claim is made about predictive validity, alpha, trading returns, economic value, or production use.
