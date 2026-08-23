# Executive Summary

COR-001 / CD-001 selected and froze the official Market Correlation construct.

Frozen construct:

```text
US Equity Market Average Pairwise Correlation State
```

The construct measures the average pairwise Pearson correlation of daily log returns across a fixed US equity universe over a trailing 60-trading-day window.

It produces:

- raw 60-day average pairwise correlation
- trailing 252-day z-score
- trailing 252-day percentile
- eligibility and coverage diagnostics

This definition was selected because it is simple, transparent, reproducible, literature-supported, and directly measures broad equity-market co-movement.

Rejected alternatives include implied correlation, DCC-GARCH correlation, PCA concentration, cross-asset correlation, tail dependence, sector correlation, and SPY-relative correlation. These remain valid possible future constructs, but they answer different questions or require more complex data/modeling assumptions.

No predictive, trading, alpha, profitability, or economic value claim is made in CD-001.

COR-001 is now frozen and ready for IM-001 after human approval.

