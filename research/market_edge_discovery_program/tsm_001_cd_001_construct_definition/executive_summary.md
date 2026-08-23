# Executive Summary

TSM-001 / CD-001 freezes the construct as:

**Raw 12-1 Time-Series Momentum State**.

For each eligible instrument, TSM-001 computes prior adjusted-price return from `t-252` to `t-21` and assigns a positive, negative or neutral own-history momentum state.

Volatility scaling is explicitly excluded to avoid confusing raw TSM signal behavior with risk allocation effects.

This is a construct state only. It is not a trading strategy, alpha claim, profitability claim or production recommendation.

The next stage is IM-001, whose only purpose is faithful deterministic implementation.
