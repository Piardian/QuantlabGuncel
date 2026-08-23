# OPT-001 / LR-001

# Limitations

## Construct Family Is Broad

Options-implied market information is not one construct. It includes volatility level, variance premium, skew, tail risk, correlation, parity deviations, and flow.

## Risk-Neutral vs Physical Interpretation

Option prices imply risk-neutral pricing. They do not directly reveal true physical probabilities.

## Data Quality

Security-level option data requires careful control for:

- bid-ask spreads,
- stale quotes,
- low open interest,
- maturity selection,
- moneyness selection,
- early exercise,
- dividends,
- borrow constraints,
- corporate actions.

## Public Data Constraints

Public index-level series are easier to reproduce than full option surfaces. This may bias early OPT constructs toward VIX-style definitions.

## Measurement Sensitivity

Variance risk premium, skewness, and implied tail measures depend heavily on interpolation, extrapolation, and realized variance estimation choices.

## Practitioner vs Academic Evidence

Some widely used practitioner indicators have weaker theoretical or peer-reviewed support than formal risk-neutral pricing constructs.

## No Independent Testing

LR-001 does not independently test predictive validity or economic utility.

