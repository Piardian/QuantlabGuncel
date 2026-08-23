# SIB-003: Stock-to-Industry Bridge Definition

## Purpose

Attempt to freeze one precise stock-to-industry bridge definition that could connect CSM-001 ticker-level observations to ISM-001 Ken French 49 industry-month states.

## Final Decision

**Bridge Definition Blocked**

## Reason

SIB-002 granted only a **CONDITIONAL GO**.

The required condition was the ability to specify a valid point-in-time historical stock-level industry classification source.

Repository inspection found:

- Ken French 49 industry portfolio returns are available.
- No point-in-time stock-level SIC/security master file is available.
- No CRSP/Compustat historical SIC file is available.
- No validated point-in-time GICS/SIC/NAICS mapping file is available.
- No frozen ticker-to-Ken-French-49 bridge exists.

## Why Definition Cannot Be Frozen

A valid bridge definition must specify:

- source data
- security identifier
- point-in-time classification field
- date alignment
- SIC-to-FF49 mapping rule
- missing-data policy
- delisting/symbol-change policy
- output schema

The source-data requirement is currently unsatisfied.

Freezing a bridge definition without a real source would create a pseudo-construct that cannot be independently reproduced.

## Evidence Classification

Supported by evidence:

- The repository contains `data/ism_001/ken_french_49_industry_value_weighted_monthly.csv`.
- The repository does not contain a usable point-in-time stock-level SIC/security master dataset.
- SIB-002 required such a source before bridge definition could proceed.

Not supported:

- A frozen bridge definition.
- Any ticker-to-industry assignment.
- Any CSM x ISM interaction analysis.

## Scientific Boundary

SIB-003 does not modify CSM-001 or ISM-001.

SIB-003 does not create a bridge.

SIB-003 does not authorize implementation.

## Conclusion

The bridge program is blocked until a valid point-in-time stock-level industry classification source is obtained and documented.
