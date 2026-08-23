# OPT-001 / CD-001

# Construct Limitations

## Not A Complete Options Surface Construct

OPT-001 uses VIXCLS only. It does not reconstruct the full SPX option surface.

## Not A Pure Expected Volatility Forecast

VIX is risk-neutral and options-implied. It can include variance risk premium, hedging demand, risk aversion, and tail-risk pricing.

## Not A Variance Risk Premium Construct

OPT-001 does not subtract realized or expected physical variance. Therefore it is not a volatility risk premium or variance risk premium measure.

## Not A Skew Or Tail-Risk Construct

OPT-001 does not separately measure downside skew, put-wing steepness, or risk-neutral tail loss.

## Not A Cross-Sectional Options Construct

OPT-001 does not use individual equity option data and cannot measure stock-level option information.

## Source Methodology Dependence

OPT-001 relies on Cboe VIX methodology and FRED-distributed daily close values. Methodological changes or data revisions may affect future reproduction unless input snapshots are archived.

## Overlap With VOL-001

OPT-001 may overlap empirically with VOL-001 because implied volatility and realized volatility are related. The constructs remain conceptually distinct.

## Stage Boundary

CD-001 does not test whether OPT-001 predicts future volatility, improves decisions, or has economic utility.

