# PEAD-001 / CD-001 Construct Definition

## Purpose

Freeze one precise, reproducible and point-in-time-safe PEAD construct definition based on LR-001.

No implementation, backtest, optimization, predictive validation or profitability claim was performed.

## Frozen Construct

Construct ID:

**PEAD-001**

Construct Name:

**Point-in-Time Analyst Surprise Post-Earnings Announcement Drift State**

Primary construct:

PEAD-001 measures the signed earnings-surprise state available immediately after a firm's public quarterly earnings announcement, using point-in-time analyst consensus expectations and actual reported EPS.

## Mathematical Specification

For firm `i` and earnings announcement event `e`:

```text
earnings_surprise_i,e = actual_eps_i,e - consensus_expected_eps_i,e

standardized_earnings_surprise_i,e =
    earnings_surprise_i,e / abs(price_reference_i,e)

pead_state_i,e =
    POSITIVE if standardized_earnings_surprise_i,e > 0
    NEGATIVE if standardized_earnings_surprise_i,e < 0
    NEUTRAL  if standardized_earnings_surprise_i,e = 0
```

The construct output is the signed event state. It does not include the future drift return.

## Required Point-In-Time Inputs

Each event must include:

- Ticker or permanent security identifier.
- Earnings announcement date.
- Earnings announcement timestamp or session classification.
- Fiscal period end date.
- Actual reported EPS available at announcement.
- Analyst consensus expected EPS as known before the announcement.
- Consensus timestamp or evidence that the consensus is pre-announcement.
- Split-adjusted price reference known before the announcement.
- Trading calendar.

## Timing Rule

The earnings surprise becomes observable only after the announcement is public.

First valid decision timestamp:

- Before-market-open announcement: same trading day's open.
- During-market announcement: next trading bar after announcement timestamp, if intraday data exists; otherwise next trading day's open.
- After-market-close announcement: next trading day's open.
- Unknown timestamp: next trading day's open.

This conservative rule is frozen to avoid same-close look-ahead bias.

## Exclusion Rules

Exclude events if:

- Announcement date is missing.
- Announcement timing cannot be assigned to a safe first tradable timestamp.
- Actual EPS is missing.
- Pre-announcement consensus expected EPS is missing.
- Consensus timestamp is unavailable or not provably before the announcement.
- Price reference is missing or non-positive.
- Security cannot be mapped to a tradable instrument at event time.

## Explicitly Excluded Variables

Excluded from PEAD-001:

- Future returns.
- Announcement-window return.
- Revenue surprise.
- Guidance surprise.
- Estimate revision after announcement.
- Volatility scaling.
- Liquidity filter.
- Momentum filter.
- Any optimized threshold.

These may be studied later only as separate preregistered constructs or conditioning variables.

## Final CD-001 Status

**Construct frozen**

PEAD-001 is now frozen as a point-in-time analyst-surprise event-state construct.

Progression to IM-001 requires obtaining or providing a dataset satisfying the required input specification.
