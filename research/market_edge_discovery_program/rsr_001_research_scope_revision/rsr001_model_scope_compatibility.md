# Model Scope Compatibility

## Frozen Model

`CSM-001 x TSM-001`

## Historical Local Scope

Compatibility:

`PARTIAL`

The model can technically compute on the existing price panel, but the scope is not scientifically valid for production-quality historical claims.

## Prospective Scope

Compatibility:

`PARTIAL`

The frozen model can operate prospectively if the capture program provides:

- sufficient lookback history after warmup
- adjusted close or frozen equivalent price field
- deterministic eligible universe
- monthly rebalance dates
- missing-data policy
- stable identifiers

No alpha logic change is required, but evidence cannot begin until enough lookback history has accumulated.
