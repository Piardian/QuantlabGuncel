# Universe Definition

## Draft Deterministic Rule

A security is eligible at date T if, using only records captured at or before T:

- exchange is NYSE, Nasdaq or NYSE American
- security type is included or conditionally included under the security-type policy
- active/tradable status is active
- listing status is listed
- security has enough captured history for frozen CSM/TSM lookback requirements before signal eligibility
- security is not suspended, halted for prolonged period, stale, missing required price data or delisted as of T

## IPOs

IPOs enter the security master when first observed by the selected source and become signal-eligible only after frozen lookback requirements are satisfied.

## No Alpha Filters

No liquidity, sector, volatility or performance filter is introduced here.

## Blocker

The source fields for active/tradable/listing status are not verified.
