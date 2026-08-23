# EXB-001 Model Data Compatibility

## Scope

This document evaluates structural data compatibility only. It does not evaluate predictive power or performance.

## Frozen Workflow Dependency

The planned exploratory workflow depends on CSM/TSM style daily close-based calculations and cross-sectional comparison.

## Compatibility Assessment

| Requirement | EXB-001 Status | Notes |
| --- | --- | --- |
| Daily close availability | PASS | Alpaca daily bars include close. |
| Daily OHLC availability | PASS | Alpaca daily bars include open/high/low/close. |
| Volume availability | PARTIAL | Volume exists, but zero-volume rows were observed. |
| Multi-symbol retrieval | PASS | 100 symbols returned rows. |
| Trading calendar | PASS | Alpaca calendar endpoint accessible. |
| Corporate actions | NOT SUPPORTED | Corporate action access was not available in ALP-002. |
| Point-in-time universe | NOT SUPPORTED | Current-active universe only. |
| Delisting lifecycle | NOT SUPPORTED | Delisted history not available in free stack. |

## Conclusion

The data is structurally compatible with a non-formal exploratory CSM/TSM preparation workflow, but it is not compatible with formal survivorship-aware alpha validation.
