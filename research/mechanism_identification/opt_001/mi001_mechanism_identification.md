# OPT-001 / MI-001: Mechanism Identification

## Purpose

Identify observable market mechanisms represented by OPT-001 options-implied volatility states.

This study is explanatory and descriptive only. It does not evaluate predictive validity, alpha, profitability, economic utility, trading performance, or causality.

## Construct

OPT-001:

```text
US Equity Index Option-Implied Volatility State
Source: VIXCLS
```

## State Definition Used For MI-001 Profiling

State buckets were defined using OPT-001's own trailing 252-valid-observation percentile:

| State | Rule |
| --- | --- |
| LOW_OPT_IMPLIED_VOL | `opt001_percentile_252d <= 0.20` |
| MID_OPT_IMPLIED_VOL | `0.20 < opt001_percentile_252d < 0.80` |
| HIGH_OPT_IMPLIED_VOL | `opt001_percentile_252d >= 0.80` |

These buckets are descriptive profiling groups only. They are not trading rules and are not optimized thresholds.

## Data Used

- OPT-001 output: `output/opt_001_validation/opt001_options_implied_output.csv`
- Market profile input: cached SPY OHLCV series
- Valid merged observations analyzed: 4,529
- Date range analyzed: 2008-01-02 to 2025-12-31

## Main Mechanism Finding

Supported by evidence:

OPT-001 primarily behaves as an **index option-implied market uncertainty / expected volatility state construct**.

High OPT-001 states are characterized by:

- materially higher VIX levels relative to recent history,
- higher contemporaneous absolute SPY movement,
- higher trailing realized SPY volatility,
- wider intraday SPY ranges,
- deeper contemporaneous 252-day drawdown context,
- episodic clustering around recognizable market stress windows.

## Key Descriptive Differences

- High-state mean absolute SPY movement is 3.35x low-state mean absolute SPY movement.
- High-state mean 20-day realized SPY volatility is 2.52x low-state mean realized volatility.
- High-state mean SPY daily range is 3.06x low-state mean daily range.
- High-state mean SPY volume ratio is 1.27x low-state mean volume ratio.
- High-state mean 252-day drawdown is -8.93% lower than low-state mean drawdown.

## Mechanism Interpretation

The evidence is consistent with the following descriptive mechanism:

```text
High OPT-001
        ->
Elevated index option-implied volatility
        ->
Higher observed market uncertainty / fear / expected volatility pricing
        ->
Higher contemporaneous realized turbulence and deeper drawdown context
```

This is an explanatory profile, not a predictive or economic claim.

## Final MI-001 Conclusion

The primary mechanism represented by OPT-001 is classified as:

```text
Index option-implied uncertainty / expected volatility state
```

Evidence classification:

```text
Supported by evidence
```
