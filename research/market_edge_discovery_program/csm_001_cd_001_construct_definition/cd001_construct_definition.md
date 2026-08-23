# CSM-001 / CD-001 Construct Definition

## Purpose

Freeze one precise Cross-Sectional Momentum construct for the Market Edge Discovery Program.

CD-001 defines the construct only. It does not run empirical tests, compare profitability, optimize parameters, implement code, or recommend trading strategies.

## Selected Construct

**Construct ID:** CSM-001

**Construct Name:** Canonical 12-1 Cross-Sectional Momentum State

**Construct Family:** Cross-Sectional Momentum

**Primary Measurement Question:** Which securities are relative winners within a predefined universe based on medium-horizon prior adjusted-price performance, excluding the most recent month?

## Frozen Operational Definition

For each eligible security `i` on date `t`:

```text
return_12_1_i,t = adjusted_close_i,t-21 / adjusted_close_i,t-252 - 1
```

Eligible securities are ranked cross-sectionally by `return_12_1_i,t` on the same date `t`.

```text
csm001_momentum_score_i,t = percentile_rank(return_12_1_i,t among eligible securities on date t)
```

```text
csm001_top_decile_flag_i,t = 1 if csm001_momentum_score_i,t >= 0.90 else 0
```

## Frozen Parameters

| Parameter | Value | Status |
| --- | ---: | --- |
| Formation anchor | 252 trading days | Frozen |
| Skip period | 21 trading days | Frozen |
| Top-decile threshold | 0.90 | Frozen |
| Minimum eligible securities per date | 50 | Frozen implementation requirement |
| Ranking direction | Higher prior return receives higher score | Frozen |
| Rank tie method | Average rank | Frozen |

## Eligibility Rules

A security is eligible on date `t` only if:

- It belongs to the predefined universe for the study.
- It has a strictly positive adjusted close at `t`.
- It has a strictly positive adjusted close at `t-21`.
- It has a strictly positive adjusted close at `t-252`.
- Its computed `return_12_1_i,t` is finite.

A date is valid only if at least `50` eligible securities exist.

## Required Outputs

For every security-date pair, implementation must output:

- `date`
- `ticker`
- `adjusted_close`
- `price_t_minus_21`
- `price_t_minus_252`
- `return_12_1`
- `csm001_rank`
- `csm001_eligible_count`
- `csm001_momentum_score`
- `csm001_top_decile_flag`
- `csm001_valid_observation`

## Interpretation

`csm001_momentum_score` is a cross-sectional relative winner score. It does not represent absolute expected return, standalone alpha, trade entry quality, or production readiness.

`csm001_top_decile_flag` identifies the upper tail of the cross-sectional prior-return distribution under the frozen definition.

## Explicit Exclusions

CSM-001 does not define:

- Portfolio weights
- Entry or exit rules
- Rebalancing rules
- Risk management
- Transaction costs
- Position sizing
- Short portfolio construction
- Production deployment logic

## Rationale

The 12-1 structure is selected because LR-001 identified it as a canonical, literature-aligned cross-sectional momentum convention. The selection is based on scientific clarity, reproducibility and literature alignment, not expected profitability.

## Freeze Statement

After CD-001, the variables, formulas, parameters, outputs, assumptions and exclusions in this document are frozen. Any future change requires a new preregistered construct definition and cannot silently modify CSM-001.
