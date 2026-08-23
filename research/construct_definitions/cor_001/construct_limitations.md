# Construct Limitations

## Linear Dependence

Pearson correlation captures linear co-movement. It may miss nonlinear dependence and tail dependence.

## Window Sensitivity

The 60-day window balances responsiveness and stability, but any fixed window can smooth fast changes or amplify recent events.

## Volatility Interaction

Correlation estimates can be affected by volatility changes. COR-001 intentionally measures realized co-movement without correcting for heteroskedasticity.

## Universe Dependence

Average pairwise correlation depends on the selected universe. A different universe may produce different values.

## Survivorship Risk

If the fixed universe uses current constituents, historical results may contain survivorship bias.

## Missing Data

Securities without complete return history in the trailing window are excluded for that date. Coverage diagnostics are required.

## Outlier Sensitivity

Extreme returns can affect Pearson correlations.

## Not Forward-Looking

COR-001 is a realized historical construct. It is not implied correlation and does not use option-market expectations.

## Not A Tail-Risk Construct

COR-001 may rise during stress, but it is not designed to specifically measure tail dependence.

## CD-001 Boundary

These limitations are acknowledged before implementation. They do not invalidate the construct, but they constrain future interpretation.

