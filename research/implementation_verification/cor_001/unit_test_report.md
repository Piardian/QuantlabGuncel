# Unit Test Report

## Test Command

```powershell
.\.venv\Scripts\python.exe research\constructs\cor_001\verify_cor001.py
```

## Result

PASS

## Tested Behaviors

- Output schema matches CD-001.
- Repeated execution is deterministic.
- Minimum eligible count is enforced.
- Rolling-window eligibility behaves as expected.
- Pair count calculation matches `n * (n - 1) / 2`.
- Implementation pairwise-correlation aggregation matches an independent manual pandas calculation.
- Raw correlation remains within the valid correlation range.
- 252-day normalization becomes available after warmup.

## Not Tested In IM-001

- Full Yahoo Finance data availability.
- Historical universe survivorship impact.
- Predictive validity.
- Economic value.
- Production suitability.

