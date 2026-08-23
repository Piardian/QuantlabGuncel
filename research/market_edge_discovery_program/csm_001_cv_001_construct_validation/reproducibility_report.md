# Reproducibility Report

## Procedure

The same cached adjusted-close panel was transformed twice by the frozen CSM-001 implementation. The resulting construct-state frames were hashed after deterministic ordering.

## Result

- First run hash: `d10f21273efbf676a33224ff365174434b78e5ba86fd48c7dac9495aad86e26c`
- Second run hash: `d10f21273efbf676a33224ff365174434b78e5ba86fd48c7dac9495aad86e26c`
- Reproducibility status: **PASSED**

No random seed is required because the implementation contains no stochastic component.
