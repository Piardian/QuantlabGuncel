# DVB-001 — Data Vendor & Budget Decision Review

## Program

Market Edge Discovery Program

## Purpose

DVB-001 converts the `SLA-001 = SOURCE_STACK_UNAVAILABLE` result into an explicit owner-level vendor and budget decision gate.

This is not a research gate. It is a procurement, budget and access authorization gate.

## Trigger

SLA-001 concluded that no real source stack is currently available:

- verified access: `0`
- sample/schema inspection: `0`
- selected market data source: `NONE`
- selected security master source: `NONE`
- selected corporate-action source: `NONE`
- license status: `UNRESOLVED`

## Scientific State

| Item | State |
|---|---|
| Alpha hypothesis | `ACTIVE / FROZEN` |
| Historical evidence | `NON_PRODUCTION_VALID` |
| Prospective design | `PARTIALLY_DESIGNED` |
| Actual source access | `NONE` |
| License evidence | `NONE` |
| Scientific T0 | `NOT_ESTABLISHED` |
| PDC refreeze | `BLOCKED` |
| PDC-002 | `BLOCKED` |
| RVP | `BLOCKED` |
| Production | `BLOCKED` |

## Core Decision

The project owner must decide whether to fund and obtain a real, license-compatible US equity data stack.

The agent cannot complete this step alone because it requires external owner actions:

```text
open account
select plan
approve budget
accept or negotiate license
create entitlement
generate credential
provide credential securely
authorize sample access verification
```

## Non-Negotiable Constraint

Vendor selection must not use strategy performance.

Forbidden during DVB-001:

- no CSM run
- no TSM run
- no CSM x TSM run
- no historical return comparison
- no Sharpe/CAGR/drawdown/PnL
- no vendor chosen because alpha looks better

## Decision Options

| Option | Meaning | Next Gate |
|---|---|---|
| `APPROVE_VENDOR_BUDGET` | Owner approves a vendor/product stack and budget for acquisition. | `OWNER_ACTION_REQUIRED` |
| `APPROVE_EXPLORATORY_LOW_COST_STACK` | Owner approves a lower-cost stack for non-formal validation only. | `SLA-002_LIMITED_VERIFICATION` |
| `DEFER_VENDOR_DECISION` | Owner delays acquisition. | `PROGRAM_PAUSED` |
| `REJECT_VENDOR_SPEND` | Owner declines data spend. | `FORMAL_PROSPECTIVE_PROGRAM_BLOCKED` |

## Recommended Decision Structure

DVB-001 should not force one vendor as scientifically superior. It should define acceptable budget tiers and require the owner to choose the practical path.

The technically preferred path is the cheapest stack that can pass the SLA/PDC minimum standard without relaxing scientific controls.

