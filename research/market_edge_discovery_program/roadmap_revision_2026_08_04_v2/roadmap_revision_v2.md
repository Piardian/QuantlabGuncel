# Roadmap Revision v2: Investment-System Development Gates

Date: 2026-08-04

## Purpose

This revision incorporates the second external-style review of the roadmap.

It supersedes the ordering in `roadmap_update_2026_08_04` without modifying any construct, workflow, parameter, strategy rule or prior result.

## Classification Language Update

Previous wording:

**Research-validated momentum leadership workflow + risk construct library**

Updated wording:

**Provisionally research-supported momentum leadership workflow + risk construct library**

Reason:

The workflow has supportive evidence under current data and backtest assumptions, but DBA-001 may reveal survivorship, point-in-time, delisting, or signal/execution timing issues that weaken prior conclusions.

## Core Decision

Do not abandon the project.

Do not pivot away from the CSM-001 x TSM-001 core.

Do not continue adding new alpha constructs before validation infrastructure catches up.

The next program phase should convert the current gross research workflow into an audited, net-of-cost, executable portfolio system candidate.

## Revised Priority Order

| Priority | Gate | Purpose | Status |
|---:|---|---|---|
| 1 | BFL-001 Baseline Freeze & Research Ledger | Freeze current model, data, universe, assumptions and prior research ledger before further validation | New mandatory gate |
| 2 | DBA-001 Data & Bias Audit | Audit data quality, survivorship, point-in-time limits, delisting gaps and timing assumptions | New mandatory gate |
| 3 | RVP-001 Robustness & OOS Validation | Test whether evidence survives OOS, subperiods, parameter neighborhoods and research-degree adjustment | New mandatory gate |
| 4 | NOC-001 Cost Model Protocol | Freeze cost model assumptions before net testing | New mandatory gate |
| 5 | NOC-002 Net-of-Cost Evaluation | Evaluate workflow under predefined cost assumptions | New mandatory gate |
| 6 | BMR-001 Gross and Net Benchmark Race | Compare against fair benchmarks under identical assumptions | New mandatory gate |
| 7 | CAP-001 Capacity & Scalability Analysis | Estimate capital limits, ADV participation, liquidation time and break-even AUM | New mandatory gate |
| 8 | PCM-001 Portfolio Construction Protocol | Freeze sizing candidates such as EW, capped EW and inverse-vol | New mandatory gate |
| 9 | PCM-002 Portfolio Construction Evaluation | Evaluate frozen sizing candidates without optimization | New mandatory gate |
| 10 | ERS-001 Execution Realism Simulation | Test tradeability under executable timestamp, spread and participation rules | New mandatory gate |
| 11 | SHD-001 Shadow Portfolio | Run live-like paper/shadow logging and compare with research assumptions | New mandatory gate |
| 12 | OPS-001 Operational Readiness | Validate data freshness, logging, reconciliation, restart, override and rollback controls | New mandatory gate |
| 13 | PRM-001 Production Risk Management | Define kill-switches, exposure limits, loss limits and escalation rules | New mandatory gate |
| 14 | LVP-001 Limited-Capital Live Pilot | Test system with small capital for operational correctness, not profit maximization | Later gate |
| 15 | SCL-001 Controlled Scaling | Define conditions for scaling after sufficient live evidence | Later gate |

## New Gate: BFL-001

Baseline Freeze must occur before DBA-001.

It must freeze:

- data set and version
- universe construction rule
- CSM formula
- TSM formula
- lookback windows
- ranking method
- selected stock fraction
- rebalance frequency
- signal timestamp
- default execution timestamp
- position weighting
- current result metrics
- all previously attempted variations if available
- code/version/release tag if available

Purpose:

Prevent accidental model changes after validation begins.

## New Gate: RVP-001

RVP-001 must occur after DBA-001 and before NOC-001.

It must test:

- untouched OOS period if available
- walk-forward stability
- subperiod stability
- market-regime stability
- parameter-neighborhood robustness
- universe perturbation
- bootstrap uncertainty
- model-selection / research-degree risk
- Deflated Sharpe Ratio or related overfitting adjustment if feasible
- failed-test ledger

Purpose:

Determine whether the observed evidence is robust or mainly the result of research degrees of freedom.

## NOC And CAP Separation

NOC answers:

Does the workflow survive realistic trading costs?

CAP answers:

At what capital size does the workflow stop being feasible?

These are separate gates.

CAP-001 must evaluate:

- ADV participation
- liquidation horizon
- market-impact proxy by AUM
- micro-cap / low-liquidity contribution
- break-even fund size
- max capital per name
- forced liquidation stress

## Benchmark Race Rules

BMR-001 must produce both:

1. Gross benchmark race.
2. Net-of-cost benchmark race.

All benchmark candidates must use identical:

- point-in-time universe
- date range
- rebalance timing
- execution delay
- position limits
- cost model
- liquidity rules
- long-only or long-short convention
- corporate-action handling

Decision emphasis:

The net-of-cost benchmark race is the primary decision table.

## PCM Rules

Portfolio construction candidates must be frozen before results.

Initial allowed candidates:

- equal-weight
- capped equal-weight
- inverse-vol
- inverse-vol with max position cap
- sector/cluster cap only if valid mapping exists

Forbidden:

- generating new sizing variants after observing results
- optimizer fit to historical performance

## SHD Pass/Fail Criteria

SHD-001 must define pass/fail metrics such as:

- percent of signals generated on time
- intended order vs shadow fill drift
- realized slippage vs NOC assumptions
- missing-data event count
- portfolio weight drift
- explainability of backtest-vs-shadow drift

## Production Gates

OPS-001 must cover:

- data freshness checks
- duplicate order protection
- stale-price checks
- broker/internal reconciliation
- daily P&L reconciliation
- logging and model versioning
- error notifications
- restart recovery
- manual override
- rollback procedure
- data-provider outage policy

PRM-001 must cover:

- max position limit
- max sector or cluster exposure
- max ADV participation
- gross and net exposure limits
- drawdown escalation
- daily loss limit
- volatility de-risking
- kill switch
- conditions for stopping new orders
- manual approval points

## Deferred Research

Do not prioritize until the above gates are passed:

- new alpha constructs
- ML alpha
- order-flow alpha
- carry
- full risk parity
- multi-asset expansion

## Final Roadmap Principle

Freeze first.

Audit data second.

Try to falsify robustness third.

Only then test costs, benchmarks, capacity, sizing, execution and live-readiness.

## Recommended Immediate Next Stage

Begin:

**BFL-001: Baseline Freeze & Research Ledger**

DBA-001 should start only after BFL-001 is complete.
