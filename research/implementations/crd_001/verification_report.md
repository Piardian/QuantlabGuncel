# CRD-001 Verification Report

## Scope

This validation run checks implementation fidelity only. It does not evaluate prediction, alpha, profitability, trading performance, or economic utility.

## Verification Summary

- Source series: BAMLH0A0HYM2
- Input source: fred_download
- Input snapshot SHA256: `6132fd84cdd0220586642775694cb2b1423c66a1f051b1733f8c1433a11c1dda`
- Rows produced: 781
- Date range: 2023-07-31 00:00:00 to 2026-07-27 00:00:00
- Raw observations: 781
- 252-day z-score observations: 530
- 252-day percentile observations: 530
- VALID flags: 530
- SOURCE_MISSING flags: 0
- Repeated transform deterministic: True
- Output SHA256: `572b37694f289dd35c665ae31c84711e6e8dbf7c038cbd91e4612cc8a851b8ba`

## Verdict

The implementation is structurally complete. The output CSV contains the frozen CD-001 columns and repeated execution with identical inputs produces identical outputs.

## IM-001 Conclusion

Successfully implemented.
