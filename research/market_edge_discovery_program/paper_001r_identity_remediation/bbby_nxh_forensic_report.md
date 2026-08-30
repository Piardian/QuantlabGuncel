# BBBY -> NXH Forensic Continuity Investigation Report

## 1. Executive Summary
During the prospective execution precheck of PAPER-002 Stage A, universe member `BBBY` (Selection Order 94, source asset ID `34479ce5-4d55-4d85-8ff4-25d08f908979`) failed data freshness and lookback criteria:
- Alpaca daily bars under symbol `BBBY` stopped at `2026-08-14`.
- Querying Alpaca for `BBBY` returned HTTP 404.
- Querying Alpaca for asset ID `34479ce5-4d55-4d85-8ff4-25d08f908979` returned HTTP 404.

A forensic investigation was conducted across regulatory filings, exchange notices, and broker endpoints to establish authoritative corporate action continuity.

## 2. Regulatory & Exchange Evidence
1. **Corporate Name Change & Rebranding**:
   - Entity: *Bed Bath & Beyond, Inc.* (SEC Filer CIK: 0001130713, SEC Accession: 0001628280-26-052552).
   - Action: Filed Certificate of Amendment to Certificate of Incorporation with the State of New York on August 14, 2026, officially changing its corporate name to *Neighborhood Intelligence, Inc.*
2. **Exchange Listing Transfer**:
   - Previous Listing: New York Stock Exchange (NYSE: `BBBY`).
   - New Listing: The Nasdaq Stock Market LLC (Nasdaq: `NXH`, Nasdaq Trader Notice: `DTN2026-17`).
   - CUSIP Continuity: CUSIP `690370101` continuing unchanged.
   - Last NYSE Trading Session: Friday, August 14, 2026 (Close: $4.355).
   - First Nasdaq Trading Session: Monday, August 17, 2026 (Open: $4.480, Close: $4.325).
3. **Common Stock Lineage & Capital Structure**:
   - Capital continuity: 1:1 continuing common security.
   - Corporate action adjustments required: None (no split, reverse split, or recapitalization occurred during the exchange transfer).

## 3. Broker Data Characterization
- **Alpaca Old Symbol (`BBBY`)**: Contains 241 daily bars spanning `2025-03-21` to `2026-08-14`. Asset status set to inactive post-delisting from NYSE.
- **Alpaca New Symbol (`NXH`)**: Assigned a new broker platform asset UUID (`96a49f53-6ed9-4900-b92a-44814b21cf92`). Daily bars begin on `2026-08-17` (6 bars through `2026-08-24`).
- **Broker UUID Discontinuity**: Alpaca mints distinct asset UUIDs when creating a newly listed ticker symbol and does not automatically backfill pre-transition historical bars under the new ticker.
- **Conclusion**: Broker asset UUID is an internal platform identifier and does not indicate economic or legal discontinuity.

## 4. Stitching Validation
Logical series reconstruction:
- Sub-series 1: `BBBY` bars for dates <= 2026-08-14 (241 bars).
- Sub-series 2: `NXH` bars for dates >= 2026-08-17 (6 bars as of 2026-08-24).
- Overlap check: 0 duplicate dates.
- Monotonicity check: Strictly monotonic calendar chronology.
- Combined length: 247 bars as of 2026-08-24.

## 5. Formal Verdict
The relationship between `BBBY` and `NXH` is classified as `VERIFIED_CONTINUITY`.
