# WLC-001: Workflow Liquidity and Capacity Protocol

## Background

WER-002 concluded:

**Execution Realism Partially Supported**

The reason full support was not assigned:

Selected-name volume and dollar-volume data were unavailable, so liquidity and capacity could not be validated.

## Purpose

WLC-001 registers the protocol for evaluating liquidity and capacity of the UC-3 CSM-001 x TSM-001 workflow.

No empirical liquidity or capacity analysis is performed in this stage.

## Primary Research Question

Does the UC-3 workflow have sufficient selected-name liquidity and capacity under predefined account-size and participation assumptions?

## Scope

Evaluate only:

**UC-3: CSM leadership subset inside TSM_HIGH versus broader TSM-positive non-CSM region**

No other use case is authorized.

## Required Data

WLC-002 must obtain or construct a ticker-date panel containing:

- adjusted close
- close
- volume
- dollar volume
- average dollar volume over 20 trading days
- average dollar volume over 60 trading days

If reliable volume data cannot be obtained, WLC-002 must conclude:

**Inconclusive: Liquidity Data Unavailable**

## Frozen Inputs

Use only frozen:

- CSM-001 state definitions
- TSM-001 state definitions
- WEV-002 UC-3 workflow definition
- WER-002 cost/slippage findings

No construct definition, threshold or parameter may be modified.

## Predefined Capacity Assumptions

Account sizes:

- $100,000
- $1,000,000
- $10,000,000

Participation limits:

- 1% of average daily dollar volume
- 5% of average daily dollar volume

Liquidity thresholds:

- $10 million average dollar volume
- $50 million average dollar volume
- $100 million average dollar volume

## Forbidden

Do NOT:

- optimize universe membership
- exclude names after seeing liquidity results
- tune capacity thresholds
- change CSM-001
- change TSM-001
- modify UC-3 definition
- recommend production deployment
- claim live readiness

## Authorized Next Stage

**WLC-002: Workflow Liquidity and Capacity Audit**
