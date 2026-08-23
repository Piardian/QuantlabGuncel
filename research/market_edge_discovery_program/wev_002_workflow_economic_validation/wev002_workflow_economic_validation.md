# WEV-002: Workflow Economic Validation

## Purpose

Evaluate whether the CSM-001 x TSM-001 nested composite workflow provides measurable economic utility relative to predefined benchmark workflows.

## Final Conclusion

**Economic Utility Partially Supported**

## Evidence Summary

Supported by evidence:

- Fixed equal-weight workflow metrics were generated for 21, 63 and 126 trading-day horizons.
- Reference and OOS samples were evaluated separately.
- UC-1 and UC-2 are effectively unchanged from CSM standalone when CSM_HIGH remains nested inside TSM_HIGH.
- UC-3 directly compares the CSM leadership subset inside TSM_HIGH against the broader TSM_HIGH non-CSM region.

Not supported:

- Any production deployment recommendation.
- Any optimized trading strategy.
- Any claim beyond the evaluated fixed workflow definitions.

## Outputs

- `use_case_results.csv`
- `benchmark_comparison.csv`
- `horizon_analysis.csv`
- `risk_downside_analysis.csv`
- `turnover_proxy_analysis.csv`
- `yearly_stability.csv`
- `oos_economic_check.csv`
