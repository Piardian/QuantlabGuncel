# CD-001: Market Regime Construct Definition

## Selected Construct

**Official research construct:**  
**US Equity Market Regime = a two-state latent state process inferred from daily SPY market returns and realized volatility.**

This construct belongs to the **latent state / Markov-switching** family identified in LR-001.

## Why This Definition Was Selected

This definition was selected because it best satisfies the CD-001 selection criteria:

- **Strong literature support:** latent regime-switching models are one of the most established regime frameworks in finance.
- **Theoretical clarity:** regimes are modeled as persistent hidden states rather than ad hoc labels.
- **Operational simplicity:** the construct can be implemented with a small number of observable inputs.
- **Reproducibility:** two independent researchers can fit the same specification from the same data.
- **Measurement reliability:** the inputs are standard, liquid, and easy to compute from daily market data.

## Theoretical Framework

The construct is grounded in **latent-state regime-switching theory**, especially the Markov-switching tradition associated with Hamilton-style models and later finance applications.

The selected construct intentionally uses **observable market return behavior and realized volatility** as the state-defining inputs. This is consistent with the literature reviewed in LR-001, which repeatedly identifies returns and volatility as the most common starting point for regime inference.

## Exact Construct Definition

Let:

- `SPY_t` be the daily close of SPY on trading day `t`
- `r_t = ln(SPY_t / SPY_{t-1})` be the daily log return
- `RV20_t` be the 20-trading-day realized volatility of `r_t`, annualized

Define a **two-state hidden Markov model** over the joint observation vector:

`X_t = [r_t, RV20_t]`

The model has:

- **2 latent states**
- **first-order Markov transitions**
- **Gaussian emissions**
- **state-specific means and variances**

The regime at time `t` is the state with the highest posterior probability:

`Regime_t = argmax_k P(S_t = k | X_1...X_t)`

After estimation, the two states are labeled ex post as:

- **Expansion / Risk-On:** higher mean return and lower realized volatility
- **Stress / Risk-Off:** lower mean return and higher realized volatility

## Why Other Definitions Were Not Selected

Alternative regime definitions were rejected for this construct because they were less suitable for preregistered research:

- **Rule-based bull/bear rules** are transparent but rely on arbitrary threshold choices.
- **Volatility-only regimes** are simpler but ignore the return side of the market state.
- **Macro-heavy regime composites** are broader but less reproducible and more data-intensive.
- **Multi-state or highly granular taxonomies** are potentially informative but less parsimonious and harder to standardize.

## Intended Scope

This construct is intended to represent the **broad state of the US equity market**.
It is not intended to capture every possible regime concept in the literature.
It is intentionally narrow enough to be reproducible and broad enough to remain conceptually consistent with the literature.

