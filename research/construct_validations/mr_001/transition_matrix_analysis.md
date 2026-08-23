# Transition Matrix Analysis

The fitted MR-001 implementation produces a strongly persistent two-state regime process.

## Transition Matrix

from_state  to_state  transition_probability
 EXPANSION EXPANSION                0.959254
 EXPANSION    STRESS                0.040746
    STRESS EXPANSION                0.014975
    STRESS    STRESS                0.985025

## Interpretation

- Expansion persistence is high at 0.9593.
- Stress persistence is high at 0.9850.
- Cross-state switching is relatively rare, which is consistent with a persistent latent regime model.

## Conclusion

The transition dynamics are internally coherent and interpretable for a two-state regime specification.
