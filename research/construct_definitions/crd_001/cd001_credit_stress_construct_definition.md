# CRD-001 / CD-001: Credit Stress Construct Definition

## Study Identity

- Research program: Market Signal Discovery Program v3.0
- Construct ID: CRD-001
- Construct family: Credit Stress
- Stage: CD-001 Construct Definition

## Selected Construct

CRD-001 is defined as:

```text
US High-Yield Credit Spread Stress
```

The construct measures the current state of US speculative-grade corporate credit stress using the ICE BofA US High Yield Option-Adjusted Spread, publicly available through FRED as:

```text
BAMLH0A0HYM2
```

## Construct Class

Market-level credit spread stress construct.

## Primary Question Answered

```text
What is the current stress level in US high-yield corporate credit markets?
```

## Theoretical Mechanism

CRD-001 represents market compensation demanded for holding below-investment-grade corporate credit risk relative to comparable-risk-free rates after option adjustment. The selected observable can reflect expected default risk, non-default credit risk premium, credit-market liquidity stress, and broad risk appetite.

This stage does not attempt to decompose those components.

## Why This Definition Was Selected

The high-yield option-adjusted spread definition was selected because it offers:

- strong literature relevance for credit stress monitoring
- direct connection to below-investment-grade corporate credit conditions
- high stress sensitivity
- public data availability
- reproducibility through a stable FRED series
- operational simplicity
- conceptual separation from equity volatility, breadth, correlation, and liquidity constructs already researched

The selection is based on construct clarity and reproducibility, not expected predictive or economic performance.

## Frozen Operational Definition

For each valid date `t`:

```text
crd001_hy_oas,t = BAMLH0A0HYM2,t
```

where `BAMLH0A0HYM2,t` is the ICE BofA US High Yield Option-Adjusted Spread observed on date `t`.

The raw spread is expressed in percentage points.

Normalized state outputs are defined as:

```text
crd001_zscore_252d,t =
(crd001_hy_oas,t - mean(crd001_hy_oas over trailing 252 valid observations))
/
std(crd001_hy_oas over trailing 252 valid observations)
```

```text
crd001_percentile_252d,t =
percentile_rank(crd001_hy_oas,t within trailing 252 valid observations)
```

These normalized outputs are descriptive state measures only. They are not thresholds, trading rules, or performance filters.

## Inputs

- `BAMLH0A0HYM2`: ICE BofA US High Yield Option-Adjusted Spread

## Outputs

- `crd001_hy_oas`
- `crd001_zscore_252d`
- `crd001_percentile_252d`
- `crd001_valid_observation_count_252d`
- `crd001_data_quality_flag`

## Excluded Variables

The following are intentionally excluded from CRD-001:

- investment-grade OAS
- Baa-Treasury spread
- Baa-Aaa spread
- CDS spreads
- excess bond premium
- default rates
- credit ETF prices
- financial stress index composites
- equity-market volatility
- equity-market breadth
- market liquidity indicators
- macroeconomic variables

These may be valid constructs, but they are not part of frozen CRD-001.

## Frozen Status

After CD-001, CRD-001 is frozen. Any change to the input series, formula, normalization windows, missing-data handling, or output schema requires restarting from CD-001 under a new preregistered definition.

## Stage Boundary

No claims are made regarding predictive validity, trading performance, alpha generation, economic value, or production suitability.

