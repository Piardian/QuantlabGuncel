# MR-001 Implementation Specification

## Frozen Construct

MR-001 is a two-state latent market regime inferred from:

- SPY daily close
- daily log return
- 20-day realized volatility

## Implementation Method

The construct is implemented as a deterministic two-state Gaussian Hidden Markov Model.

## Outputs

- posterior state probability for each state
- latent state assignment
- regime label

## Determinism Rules

- No random initialization
- No stochastic sampling
- Fixed two-state structure
- Fixed feature set
- Fixed realized-volatility window

## Reproducibility Rules

The same input data and configuration must produce identical outputs.

