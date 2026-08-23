# OPT-001 / CD-001

# Construct Assumptions

## Assumption 1: VIX Represents Option-Implied Equity Index Volatility

OPT-001 assumes that VIXCLS is an appropriate public observable for near-term option-implied volatility in the US equity index options market.

Evidence status: Supported by official methodology and literature.

## Assumption 2: VIX Is Distinct From Realized Volatility

OPT-001 assumes that options-implied volatility is conceptually distinct from realized volatility measured by VOL-001.

Evidence status: Supported by literature.

## Assumption 3: Daily Close Is Sufficient For State Measurement

OPT-001 uses daily close values. It assumes close-to-close VIX state is sufficient for a daily research construct.

Evidence status: Operational assumption.

## Assumption 4: VIX Level Can Be Used Without Decomposition

OPT-001 assumes the VIX level can be measured as an option-implied state even though it may reflect expected volatility, variance risk premium, hedging demand, risk aversion, and tail-risk compensation.

Evidence status: Partially supported.

## Assumption 5: Rolling 252 Valid Observations Are Suitable For Normalization

The construct assumes that trailing 252 valid observations provide a reproducible one-year normalization context.

Evidence status: Operational convention; not a predictive claim.

## Assumption 6: Missing Values Should Not Be Forward Filled

The construct assumes missing source observations should remain missing rather than be manufactured.

Evidence status: Methodological assumption for reproducibility.

