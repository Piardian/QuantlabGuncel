# BRD-001 / CV-001: Normalization Analysis

## Purpose

Evaluate whether BRD-001 normalization outputs behave consistently with CD-001.

## Normalization Outputs

BRD-001 produced:

- 3,573 normalized observations
- first normalized date: `2011-10-14`
- z-score mean: -0.1292
- z-score median: 0.1872
- z-score standard deviation: 1.3120
- percentile mean: 0.4915
- percentile median: 0.4921
- percentile minimum: 0.0040
- percentile maximum: 1.0000

## Warmup Behavior

The implementation produced 251 missing z-score and percentile values during the expected 252-observation normalization warmup.

This behavior is consistent with CD-001 because the rolling 252-day window includes the current day and requires 252 valid raw breadth observations.

## Percentile Bounds

All percentile values remained within:

```text
0 <= brd001_percentile <= 1
```

Conclusion classification:

```text
Supported by evidence
```

## Boundary

Normalization outputs are descriptive state transforms.

They are not trading thresholds or optimized decision rules.

