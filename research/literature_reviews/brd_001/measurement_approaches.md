# BRD-001 / LR-001: Measurement Approaches

## Purpose

This document reviews common ways Market Breadth is operationalized.

No final construct is selected in LR-001.

## Advance / Decline Measures

Required data:

- Daily close or daily return for each security
- Fixed or historically accurate universe

Common definitions:

- Advancing security: close greater than prior close
- Declining security: close less than prior close
- Net advances: advancing count minus declining count
- Advance ratio: advancing count divided by total valid securities
- A/D line: cumulative net advances

Strengths:

- Simple
- Interpretable
- Directly measures daily participation

Limitations:

- Sensitive to universe definition
- Cumulative series affected by listing history
- Equal-weights all securities

## Moving-Average Breadth

Required data:

- Daily close for each security
- Moving-average lookback

Common definitions:

- Percent of securities above 50-day moving average
- Percent of securities above 200-day moving average
- Percent of securities with short MA above long MA

Strengths:

- Interpretable
- Captures trend participation
- Less noisy than one-day advance/decline measures

Limitations:

- Depends on moving-average horizon
- Overlaps conceptually with trend constructs
- Warmup requirements matter

## New High / New Low Breadth

Required data:

- Daily high/close for each security
- Lookback window such as 52 weeks

Common definitions:

- Count of new highs
- Count of new lows
- New highs minus new lows
- New high ratio

Strengths:

- Captures extreme participation
- Useful for identifying broad strength or deterioration

Limitations:

- Sparse in some periods
- Lookback selection matters
- Sensitive to IPOs and short histories

## Up-Volume / Down-Volume Breadth

Required data:

- Daily volume
- Daily price direction

Common definitions:

- Up-volume divided by total volume
- Up-volume divided by down-volume
- Volume-weighted advancing participation

Strengths:

- Adds participation intensity
- Can distinguish low-volume advances from high-volume advances

Limitations:

- Requires reliable volume
- Volume behavior differs across time and securities
- Strongly affected by mega-cap volume concentration

## Breadth Momentum / Breadth Thrust

Required data:

- Breadth base series such as advances minus declines
- Smoothing or acceleration definition

Common definitions:

- Short EMA minus long EMA of net advances
- Rapid change in advance ratio
- Threshold-based breadth thrust

Strengths:

- Captures rapid participation shifts
- May identify market-internal transitions

Limitations:

- More parameter-dependent
- Harder to define without threshold choices
- Risk of overfitting if not preregistered

## Equal-Weighted Versus Cap-Weighted Confirmation

Required data:

- Equal-weighted market return proxy
- Cap-weighted index return proxy

Common definitions:

- Equal-weighted return minus cap-weighted return
- Equal-weighted trend confirmation
- Average constituent return relative to index return

Strengths:

- Directly addresses concentration
- Useful for cap-weighted index interpretation

Limitations:

- Requires clean constituent universe
- Rebalancing assumptions can matter
- Can overlap with size exposure

## Measurement Conclusion

Market Breadth can be implemented reproducibly, but CD-001 must freeze:

- Universe definition
- Security inclusion rules
- Data source
- Breadth family
- Exact formula
- Warmup handling
- Missing-data policy
- Output variables

