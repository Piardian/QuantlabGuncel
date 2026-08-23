# Timing Policy

PEAD-001 uses conservative event timing.

## Before Market Open

The construct state becomes available at the same trading day's open.

## During Market Hours

If intraday data exists, the construct state becomes available on the next trading bar after the announcement timestamp.

If intraday data does not exist, the construct state becomes available at the next trading day's open.

## After Market Close

The construct state becomes available at the next trading day's open.

## Unknown Time

The construct state becomes available at the next trading day's open.

## Forbidden Timing Assumption

After-close earnings must never be treated as tradable at the same day's close.
