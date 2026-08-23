# PROF-001 / CD-001 Construct Definition

## Purpose

Freeze one precise, reproducible Profitability / Quality construct definition based on LR-001.

No implementation, backtesting, optimization, predictive validation, economic validation or profitability claim was performed.

## Frozen Construct

Construct ID:

**PROF-001**

Construct Name:

**Conservative-Lag Gross Profitability State**

Primary construct:

PROF-001 measures firm-level gross profitability using gross profits scaled by total assets, with conservative accounting publication lag to reduce look-ahead risk.

## Construct Family Decision

PROF-001 is defined as **narrow profitability**, not broad quality.

Rationale:

- Gross profitability is simple and interpretable.
- It is strongly connected to the Novy-Marx gross profitability literature.
- It avoids arbitrary multidimensional quality weighting.
- It preserves construct purity for later validation.

## Mathematical Specification

For firm `i` and fiscal period `t`:

```text
gross_profit_i,t = revenue_i,t - cost_of_goods_sold_i,t

gross_profitability_i,t =
    gross_profit_i,t / total_assets_i,t
```

State assignment:

```text
PROFITABLE     if gross_profitability_i,t > 0
UNPROFITABLE   if gross_profitability_i,t < 0
NEUTRAL        if gross_profitability_i,t = 0
INVALID        if required accounting fields are missing or invalid
```

## Publication Lag Policy

If exact filing date is available:

The observation becomes available on the first trading day after the filing date.

If exact filing date is unavailable:

The observation becomes available 180 calendar days after fiscal period end.

This conservative lag is frozen before implementation and is intended to reduce look-ahead risk when point-in-time filing data is unavailable.

## Required Inputs

- Permanent security identifier.
- Ticker.
- Fiscal period end date.
- Report date or filing date, if available.
- Revenue.
- Cost of goods sold.
- Total assets.
- Trading calendar.
- Security identifier mapping.

## Exclusion Rules

Exclude observations if:

- Revenue is missing.
- Cost of goods sold is missing.
- Total assets is missing.
- Total assets is less than or equal to zero.
- Fiscal period end date is missing.
- Security cannot be mapped to a tradable instrument.
- Accounting data availability date cannot be assigned.

## Explicitly Excluded Variables

Excluded from PROF-001:

- Operating profitability.
- Return on equity.
- Return on assets.
- Cash-flow profitability.
- Growth.
- Safety.
- Payout.
- Quality composite scores.
- Value metrics.
- Momentum metrics.
- Future returns.
- Sector adjustments.
- Optimized thresholds.

These may be studied later only as separate preregistered constructs or conditioning variables.

## Final CD-001 Status

**Construct frozen**

PROF-001 is now frozen as a Conservative-Lag Gross Profitability State.

Progression to IM-001 requires accounting data satisfying the required input specification.
