# EXB-001 Historical Access Report

## Access Summary

Data source: Alpaca Market Data API  
Feed: IEX  
Timeframe: 1Day  
Adjustment: raw  
Access mode: read-only  
Raw market data stored: no  
Metadata and quality summaries stored: yes

## Verification Results

| Check | Result |
| --- | --- |
| Account access dependency | PASS via ALP-001 |
| Read-only integration dependency | PASS via ALP-002 |
| Broker mutation safety dependency | PASS via ALP-003 |
| Assets endpoint | PASS |
| Calendar endpoint | PASS |
| Historical bars endpoint | PASS |
| Single-symbol historical probe | PASS |
| Multi-symbol historical retrieval | PASS |
| Broker/order mutation calls | 0 |

## Observed Historical Coverage

| Metric | Value |
| --- | --- |
| Earliest verified bar date | 2020-07-27 |
| Latest verified bar date | 2026-08-11 |
| Verified history span | 6.04 years |
| EXB-001 dataset request start | 2021-01-01T00:00:00Z |
| EXB-001 dataset request end | 2026-08-11T23:59:59Z |
| Requested symbol count | 100 |
| Symbols with rows | 100 |
| Row count | 91,986 |

## Request Limits

EXB-001 verified paginated multi-symbol retrieval using Alpaca next-page tokens. This report does not certify vendor-level maximum entitlement, full SIP access, or production-grade historical completeness.

## Interpretation

Historical access is sufficient to prepare a reduced non-formal exploratory dataset. It is not sufficient for formal survivorship-aware historical validation.
