# TSM-001 / CD-001 Construct Definition

## Purpose

Freeze one precise Time-Series Momentum construct definition.

CD-001 defines the construct only. It does not run empirical tests, optimize parameters, implement code, evaluate profitability, or recommend trading strategies.

## Selected Construct

**Construct ID:** TSM-001

**Construct Name:** Raw 12-1 Time-Series Momentum State

**Construct Family:** Time-Series Momentum / Own-History Directional Persistence

**Primary Measurement Question:** Is each instrument in a positive, negative or neutral own-history momentum state based on medium-horizon prior adjusted-price performance, excluding the most recent month?

## Core Definition

For each eligible instrument `i` on date `t`:

```text
tsm_return_12_1_i,t = adjusted_close_i,t-21 / adjusted_close_i,t-252 - 1
```

State assignment:

```text
tsm001_state_i,t = POSITIVE if tsm_return_12_1_i,t > 0
tsm001_state_i,t = NEGATIVE if tsm_return_12_1_i,t < 0
tsm001_state_i,t = NEUTRAL  if tsm_return_12_1_i,t = 0
```

Directional score:

```text
tsm001_direction_score_i,t = sign(tsm_return_12_1_i,t)
```

Where:

```text
POSITIVE = +1
NEUTRAL  = 0
NEGATIVE = -1
```

## Frozen Parameters

| Parameter | Value | Status |
| --- | ---: | --- |
| Formation anchor | 252 trading days | Frozen |
| Skip period | 21 trading days | Frozen |
| Price input | Adjusted close | Frozen |
| Volatility scaling | Excluded | Frozen |
| Direction threshold | 0.0 prior return | Frozen |
| Neutral condition | exactly zero prior return | Frozen |

## Universe

The construct is universe-agnostic at CD-001. Any empirical study must predefine its universe before execution.

The construct may be applied to any instrument with valid adjusted-close history, including equities, ETFs, futures proxies or indices, but the universe must be frozen before validation.

## Eligibility Rules

An instrument is eligible on date `t` only if:

- It belongs to the predefined universe for the study.
- It has strictly positive adjusted close at `t`.
- It has strictly positive adjusted close at `t-21`.
- It has strictly positive adjusted close at `t-252`.
- `tsm_return_12_1_i,t` is finite.

## Required Outputs

For every instrument-date pair, implementation must output:

- `date`
- `ticker`
- `adjusted_close`
- `price_t_minus_21`
- `price_t_minus_252`
- `tsm_return_12_1`
- `tsm001_direction_score`
- `tsm001_state`
- `tsm001_positive_state`
- `tsm001_negative_state`
- `tsm001_valid_observation`

## Volatility Scaling Decision

Volatility scaling is explicitly excluded from TSM-001.

Rationale: LR-001 identified volatility scaling as a major interpretive confound. The first TSM construct must isolate raw own-history directional persistence before later research evaluates risk scaling or economic workflows.

## Explicit Exclusions

TSM-001 does not define:

- Portfolio weights
- Long/short position sizes
- Volatility targeting
- Risk parity
- Rebalancing schedule
- Transaction costs
- Entry or exit rules
- Production deployment logic

## Freeze Statement

After CD-001, the variables, formula, parameters, outputs, assumptions and exclusions in this document are frozen. Any future change requires a new preregistered construct definition.
