# SIB-001: Stock-to-Industry Bridge Protocol

## Purpose

Define the scientific requirements for a future bridge that can connect stock-level constructs such as CSM-001 with industry-level constructs such as ISM-001.

This stage is a protocol registration only.

No mapping is selected, implemented or validated in SIB-001.

## Background

CIP-002 concluded **Inconclusive** because CSM-001 and ISM-001 do not share a common observation unit.

CSM-001 operates at:

- ticker-date level

ISM-001 operates at:

- Ken French 49 industry-month level

ISM-001 explicitly does not assign industry states to individual securities.

## Primary Research Question

What scientific requirements must a stock-to-industry bridge satisfy before CSM-001 x ISM-001 interaction analysis can be validly performed?

## Required Bridge Properties

A valid future bridge must be:

- point-in-time
- reproducible
- deterministic
- auditable
- documented
- compatible with CSM-001 ticker observations
- compatible with ISM-001 Ken French 49 industry-month states
- free of current-classification look-ahead bias
- stable enough for historical analysis

## Explicitly Forbidden Shortcuts

The following may not be used without a separate preregistered validation:

- current Yahoo industry classifications
- current GICS labels
- current SIC labels
- current NAICS labels
- manually assigned ticker labels
- post-hoc taxonomy selection
- result-driven mapping changes

## Candidate Data Sources To Review Later

SIB-001 does not select any source, but future research may evaluate:

- CRSP/SIC historical membership if available
- Compustat historical industry classification if available
- point-in-time GICS if licensed and timestamped
- Ken French portfolio assignment files if available
- other fully documented point-in-time classification sources

## Required Future Lifecycle

A bridge may not be used in CIP research until it completes:

1. SIB-002 Literature / Data Source Review
2. SIB-003 Bridge Definition
3. SIB-004 Implementation
4. SIB-005 Validation
5. SIB-006 Final Bridge Readiness Review

## Success Criteria

SIB-001 is successful if it clearly defines the minimum scientific standard required before stock-level and industry-level constructs can be compared.

## Non-Goals

SIB-001 does not:

- create a bridge
- select a data provider
- map tickers to industries
- revalidate CSM-001
- revalidate ISM-001
- run interaction statistics
- evaluate performance
- recommend production usage

## Authorized Next Stage

If approved by the human reviewer:

**SIB-002: Stock-to-Industry Bridge Data Source Review**
