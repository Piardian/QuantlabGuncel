# Roadmap Update: Research Workflow To Production-Grade Portfolio System

Date: 2026-08-04

## Purpose

This roadmap update incorporates the latest external-style project critique into the Market Edge Discovery Program.

It does not modify any construct, strategy, parameter, threshold, portfolio rule, or production system.

## Current Project Classification

The project is best classified as:

**Research-validated momentum leadership workflow + risk construct library**

It is not yet:

**Production-ready trading bot**

## Current Core Model

| Layer | Current project method | Role | Status |
|---|---|---|---|
| Primary return construct | CSM-001 | Stock-level cross-sectional leadership | Supported |
| Secondary / gating construct | TSM-001 | Own-trend / positive trend state | Supported |
| Best validated workflow | CSM-001 x TSM-001 | Select CSM leaders inside TSM-positive names | Research-validated portfolio workflow |
| Industry leadership | ISM-001 | Industry-level leadership | Supported at industry level, blocked for stock-level integration |
| Residual momentum | RSM-001 | Factor-residual stock momentum | Mostly redundant vs CSM in CIP-003 |
| Risk sensor library | MR/VOL/LIQ/COR/BRD/CRD/FUND/OPT | Market and risk-state measurement | Scientific sensor library exists |
| Portfolio construction | Monthly equal-weight gross workflow | Research portfolio accounting | Supported gross only |
| Production execution | None | Broker/live/monitoring/kill-switch | Not supported |

## Main Roadmap Change

The next phase should slow down new alpha-construct expansion and prioritize:

1. Bias and data audit.
2. Net-of-cost validation.
3. Benchmark race.
4. Production sizing and exposure policy.
5. Execution realism and shadow trading.
6. Only then additional alpha layers such as PROF, PEAD, or stock-level ISM integration.

## Why

The project has already produced meaningful scientific construct work.

The main unresolved question is no longer:

Which new indicator should be added?

The main unresolved question is:

Can the validated gross research workflow become a net-of-cost, executable, risk-controlled portfolio process?

## Updated Priority Order

| Priority | Program | Purpose | Status |
|---:|---|---|---|
| 1 | DBA-001 Data & Bias Audit | Audit survivorship, point-in-time assumptions, delisting gaps, execution timing and data integrity | New required gate |
| 2 | NOC-001 Net-of-Cost Validation Protocol | Define commissions, spread, slippage, impact and turnover assumptions | New required gate |
| 3 | NOC-002 Net-of-Cost Workflow Evaluation | Test CSM x TSM workflow net of predefined costs | New required gate |
| 4 | BMR-001 Benchmark Race Protocol | Compare index, equal-weight universe, simple 12-1 momentum, CSM, TSM, CSM x TSM, CSM x TSM + risk | New required gate |
| 5 | PCM-001 Portfolio Construction Model Protocol | Define equal-weight, inverse-vol, capped equal-weight, exposure and concentration policies | New required gate |
| 6 | PCM-002 Portfolio Construction Evaluation | Evaluate sizing policies without optimization | New required gate |
| 7 | ERS-001 Execution Realism Simulation | Define executable prices, spread limits, participation limits and order timing | New required gate |
| 8 | SHD-001 Shadow Portfolio Protocol | Define paper/shadow trading evidence requirements | New required gate |
| 9 | ISM Bridge Restart | Resume only if valid point-in-time stock-to-industry data exists | Blocked |
| 10 | PROF-001 Completion | Complete quality/profitability lifecycle before PEAD/ML/order flow | Pending |
| 11 | PEAD-001 Completion | Requires strict point-in-time earnings and announcement timing | Later |
| 12 | Multi-Asset Expansion | Only after equity workflow survives net-cost and shadow stages | Later |
| 13 | ML / Order Flow | Use only for slippage, liquidity, anomaly or execution support | Later |

## New Roadmap Gates

### DBA-001: Data & Bias Audit

Goal:

Determine whether the current research dataset is sufficiently clean for net-of-cost and production-readiness evaluation.

Must evaluate:

- survivorship bias
- delisted security absence
- point-in-time universe limitations
- signal/execution timing
- adjusted price handling
- missing data
- liquidity gaps
- repeated testing / research degrees of freedom

### NOC-001 / NOC-002: Net-of-Cost Validation

Goal:

Move from gross research portfolio evidence to net-of-cost evidence.

Must include:

- commissions
- bid/ask spread
- slippage
- market impact proxy
- turnover
- stress cost scenarios

No production claim is allowed unless net-of-cost evidence is favorable and stable.

### BMR-001: Benchmark Race

Goal:

Answer whether the added workflow complexity contributes beyond simple alternatives.

Required comparators:

- index buy-and-hold
- equal-weight universe
- simple 12-1 momentum
- CSM-001
- TSM-001
- CSM x TSM
- CSM x TSM + risk policy, if a frozen risk policy exists

### PCM-001 / PCM-002: Portfolio Construction Model

Goal:

Evaluate simple production-plausible sizing rules before advanced optimization.

Allowed fixed candidates:

- equal-weight
- capped equal-weight
- inverse-vol
- inverse-vol with max position cap
- sector/cluster/concentration caps if valid mapping exists

Forbidden:

- optimizer fit to historical performance
- post-hoc best rule selection

### ERS-001: Execution Realism Simulation

Goal:

Define whether signals could be realistically executed.

Must define:

- signal timestamp
- tradeable timestamp
- market-on-open / next-open / next-close policy
- spread limit
- participation cap
- missing quote behavior
- rejected order behavior

### SHD-001: Shadow Portfolio

Goal:

Run the system without real capital and compare observed executable prices against research assumptions.

Required evidence:

- signal log
- intended orders
- executable reference prices
- missing data events
- spread/slippage observations
- backtest-vs-shadow drift

## Deferred Items

The following are not priority now:

- Carry
- Full risk parity
- ML alpha models
- Order-flow alpha
- Multi-asset expansion

These may become relevant only after net-cost and execution realism gates.

## Current Scientific Decision

Do not abandon the project.

Do not pivot away from CSM x TSM as the best validated workflow.

Do not keep adding new alpha constructs before proving the gross workflow can survive realistic cost, sizing and execution assumptions.

## Next Recommended Goal

Begin:

**DBA-001: Data & Bias Audit**

This should be the next gate before additional interaction or alpha expansion.
