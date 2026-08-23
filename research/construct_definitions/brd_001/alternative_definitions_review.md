# BRD-001 / CD-001: Alternative Definitions Review

## Purpose

This document explains which breadth alternatives were considered and why they were not selected for BRD-001.

No alternative was rejected because of performance.

## Alternative A: Advance / Decline Line

Description:

Cumulative net advancing issues minus declining issues.

Reason not selected:

The cumulative A/D line is sensitive to universe changes, listing history, and daily noise. It is useful, but less clean as the first BRD-001 state construct.

Status:

Rejected for BRD-001, not rejected as a future construct.

## Alternative B: Daily Advance Ratio

Description:

Percentage of securities closing above the prior close.

Reason not selected:

It measures one-day participation and can be noisy. BRD-001 is intended to capture more persistent market participation.

Status:

Rejected for BRD-001, not rejected as a future construct.

## Alternative C: Up-Volume / Down-Volume Breadth

Description:

Participation weighted by volume on advancing and declining securities.

Reason not selected:

Volume adds a useful dimension but introduces data-quality and concentration issues. CD-001 prioritizes close-only reproducibility for the first breadth construct.

Status:

Rejected for BRD-001, not rejected as a future construct.

## Alternative D: New High / New Low Breadth

Description:

Count or ratio of securities making new highs or new lows over a fixed lookback.

Reason not selected:

New high/new low measures capture extreme participation, but can be sparse and lookback-sensitive. BRD-001 prioritizes continuous participation coverage.

Status:

Rejected for BRD-001, not rejected as a future construct.

## Alternative E: Sector Breadth

Description:

Participation across sectors or industries.

Reason not selected:

Sector breadth requires reliable sector classifications and introduces an additional taxonomy layer. BRD-001 focuses first on security-level market-wide participation.

Status:

Rejected for BRD-001, not rejected as a future construct.

## Alternative F: Equal-Weighted Versus Cap-Weighted Confirmation

Description:

Difference between equal-weighted and capitalization-weighted market behavior.

Reason not selected:

This is conceptually valuable but mixes breadth with index construction and size exposure. BRD-001 keeps the first construct as a direct participation ratio.

Status:

Rejected for BRD-001, not rejected as a future construct.

## Selected Alternative

The selected definition is:

```text
Percent of eligible securities with close > SMA200
```

Selection rationale:

- Strong practitioner recognition
- Clear participation interpretation
- Close-only data requirement
- Deterministic calculation
- Bounded scale
- Directly reproducible from panel close data
- Lower daily noise than raw advance/decline breadth

