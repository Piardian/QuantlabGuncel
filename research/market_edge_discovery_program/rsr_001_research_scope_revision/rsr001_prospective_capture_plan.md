# Prospective Capture Plan

## Scope ID

`RSR-D`

## T0

`2026-08-11`

## Required Daily / Periodic Security Universe Snapshot

- security ID if available
- ticker
- exchange
- security type
- active status
- listing date if available
- delisting status
- sector / industry if used
- source timestamp
- ingestion timestamp

## Required Market Data Snapshot

- timestamp
- open
- high
- low
- close
- adjusted close or adjustment state
- volume
- source timestamp
- ingestion timestamp

## Required Corporate Actions

- event type
- announcement date
- effective date
- old identifier
- new identifier
- adjustment factor

## Auditability

Generate:

- ingestion logs
- daily hashes
- schema versions
- transformation versions
- immutable raw snapshots

## Important Limitation

This program creates future PIT evidence only. It does not repair historical V1 evidence.
