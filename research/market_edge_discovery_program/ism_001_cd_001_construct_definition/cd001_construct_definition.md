# ISM-001 / CD-001 Construct Definition

## Purpose

Freeze one precise, reproducible Industry Momentum construct definition based on LR-001.

No implementation, backtesting, optimization, predictive validation, economic validation, alpha claim or production recommendation was performed.

## Frozen Construct

Construct ID:

**ISM-001**

Construct Name:

**Ken French 49 Industry Portfolio 12-1 Cross-Sectional Momentum Rank**

Primary construct:

ISM-001 measures cross-sectional industry momentum by ranking industry portfolios according to intermediate-horizon prior industry returns.

## Data Source

Frozen data source:

**Ken French 49 Industry Portfolios monthly returns**

Return type:

**Value-weighted industry portfolio returns**

The construct is industry-level. It does not require individual stock industry membership inside this repository.

## Return Frequency

Frozen return frequency:

**Monthly**

## Industry Universe

Frozen industry universe:

**49 Ken French industry portfolios**

An industry-month is valid only if the required monthly return history exists and the computed score is finite.

## Formation Window

Frozen formation:

**12-1**

Definition:

Use compounded industry portfolio returns from months `t-12` through `t-2`, excluding the most recent month `t-1`.

For industry `j` at month `t`:

```text
industry_return_12_1_j,t =
    product(1 + industry_return_j,t-12 ... 1 + industry_return_j,t-2) - 1
```

## Cross-Sectional Ranking

For every valid month:

```text
ism_score_j,t =
    percentile_rank(industry_return_12_1_j,t within valid industries at month t)
```

Higher prior 12-1 industry return receives higher percentile rank.

Rank tie method:

**Average rank**

## State Labels

```text
TOP_DECILE      if ism_score >= 0.90
BOTTOM_DECILE   if ism_score <= 0.10
MIDDLE          otherwise
INVALID         if required data is unavailable
```

## Minimum Cross-Section

A month is valid only if at least:

```text
30 valid industries
```

exist for that month.

## Required Outputs

For every industry-month pair, implementation must output:

- `month`
- `industry_id`
- `industry_name`
- `industry_return`
- `industry_return_12_1`
- `ism_rank`
- `ism_eligible_count`
- `ism_score`
- `ism_state`
- `ism_valid_observation`

## Explicit Exclusions

ISM-001 does not define:

- Individual-stock industry membership.
- Stock-level signal assignment.
- Portfolio construction.
- Long-short strategy construction.
- Rebalancing rules.
- Transaction costs.
- Economic value.
- Production deployment logic.
- Alternative taxonomies such as GICS, SIC, NAICS or Yahoo sectors.
- Equal-weighted industry returns.
- Daily industry returns.
- Optimized thresholds.

These may be studied only as separate preregistered constructs or comparators.

## Rationale

The Ken French 49 industry portfolio definition is selected because it is public, reproducible, widely used in academic asset-pricing research and avoids point-in-time stock-industry membership ambiguity at this stage.

The 12-1 formation is selected because it aligns with canonical intermediate-horizon momentum conventions and excludes the most recent month.

The selection is based on scientific clarity, literature alignment and reproducibility, not expected performance.

## Freeze Statement

After CD-001, the variables, formulas, data source, frequency, ranking rules, state labels, assumptions and exclusions in this document are frozen.

Any future change requires a new preregistered construct definition and cannot silently modify ISM-001.

