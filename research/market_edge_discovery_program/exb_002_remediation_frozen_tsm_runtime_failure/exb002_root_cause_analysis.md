# EXB-002 Root Cause Analysis

## Root Cause Classification

Root cause:

```text
DEPENDENCY/API_CHANGE
IMPLEMENTATION_BUG
```

## Explanation

The frozen TSM calculation generated a valid numeric `direction_score` DataFrame using the frozen formula:

```text
sign(close_t-21 / close_t-252 - 1)
```

The failure occurred only when converting numeric direction scores into textual state labels using `DataFrame.replace`.

This indicates a technical state-label serialization failure rather than a frozen model definition failure.

## Root Cause Identified

ROOT_CAUSE_IDENTIFIED = YES

## Not Root Cause

- Not insufficient history.
- Not missing-data policy ambiguity.
- Not universe selection.
- Not threshold ambiguity.
- Not look-ahead timing.
- Not portfolio accounting.
