# Missing And Stale Data Policy

Allowed statuses:

- FRESH
- DELAYED
- STALE
- MISSING
- INVALID

Forbidden by default:

- forward-filling tradable prices
- interpolation
- substituting future values
- deleting stale observations silently

Any non-price metadata carry-forward must be explicitly versioned and traceable.
