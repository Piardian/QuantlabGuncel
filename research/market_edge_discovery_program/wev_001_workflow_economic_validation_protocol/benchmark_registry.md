# Benchmark Registry

## Benchmark A: CSM-001 Standalone

Frozen state:

`csm001_top_decile_flag == True`

No TSM condition.

## Benchmark B: TSM-001 Standalone

Frozen state:

`tsm001_positive_state == True`

No CSM condition.

## Benchmark C: Equal-Weight Eligible Universe

All ticker-date observations where both CSM-001 and TSM-001 are valid.

## Benchmark D: Static CSM Top-Decile

Same as Benchmark A. Included as a named reference because CSM top-decile is the principal standalone edge workflow comparator.

## Benchmark Rules

- No benchmark may be optimized.
- No benchmark may use future information.
- No benchmark may change construct thresholds.
- No benchmark may be modified after results are observed.
