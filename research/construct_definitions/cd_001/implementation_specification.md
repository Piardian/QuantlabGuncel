# Implementation Specification

## Required Input Data

- SPY daily adjusted close prices
- Trading calendar with no missing business days beyond standard market holidays

## Step-by-Step Construction

1. Compute daily close-to-close log returns:
   `r_t = ln(SPY_t / SPY_{t-1})`
2. Compute 20-day realized volatility from daily returns and annualize it.
3. Build the daily observation vector:
   `X_t = [r_t, RV20_t]`
4. Fit a two-state Gaussian Hidden Markov Model to the observation sequence.
5. Compute posterior state probabilities for each day.
6. Assign the daily regime label as the state with the highest posterior probability.
7. Order states after fitting:
   - higher mean return / lower volatility = Expansion / Risk-On
   - lower mean return / higher volatility = Stress / Risk-Off

## Reproducibility Rules

- Use the same SPY series for every researcher.
- Use the same return definition.
- Use the same 20-day volatility window.
- Use the same two-state HMM structure.
- Use the same state-ordering rule.

## Output Schema

Each date should include:

- `date`
- `regime_label`
- `state_probability_expansion`
- `state_probability_stress`
- `state_mean_return`
- `state_realized_volatility`

