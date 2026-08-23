# FUND-001 / IM-001

# Verification Report

## Scope

This report verifies implementation fidelity only.

It does not evaluate prediction, alpha, profitability, trading performance, or economic utility.

## Verification Run

Command:

```powershell
.venv\Scripts\python.exe research\implementations\fund_001\validate_fund_001.py --config research\implementations\fund_001\config.yaml
```

## Verification Summary

- Construct ID: FUND-001
- Commercial paper series: DCPF3M
- Treasury bill series: DTB3
- Input source: FRED download
- Rows produced: 18,931
- Date range: 1954-01-04 to 2026-07-27
- Raw spread observations: 6,714
- 252-valid-observation z-score observations: 6,463
- 252-valid-observation percentile observations: 6,463
- OK flags: 6,463
- MISSING_INPUT flags: 12,217
- INSUFFICIENT_LOOKBACK flags: 251
- ZERO_ROLLING_STD flags: 0
- Repeated transform deterministic: True

## Hashes

- Input snapshot SHA256: `0ec7a4c07b51b530256e5805749db3c2a23675f37c24f25b1c5fc7ed6a607542`
- Output SHA256: `5654a7badb524fb91a2922c6c2714910aa63054c9d54a3e39b586c1398e3698e`

## Result

FUND-001 implementation is structurally complete and deterministic.

The implementation faithfully produces the CD-001 output schema from the frozen formula:

```text
DCPF3M - DTB3
```

