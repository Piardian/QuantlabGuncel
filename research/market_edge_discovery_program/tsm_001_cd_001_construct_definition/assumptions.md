# Construct Assumptions

- Adjusted close is the required price input.
- Trading-day offsets are row-based within the supplied daily price panel.
- The universe is predefined before validation.
- The construct is time-series, not cross-sectional.
- The construct measures own-history directional state, not peer-relative strength.
- The one-month skip period is represented as 21 trading days.
- The twelve-month formation anchor is represented as 252 trading days.
- Volatility scaling is excluded.
- Missing or non-positive prices make an instrument ineligible for that date.
- TSM-001 does not include breadth, regime, volatility, liquidity, fundamentals or cross-sectional ranking inputs.
