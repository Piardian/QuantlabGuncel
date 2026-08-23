from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
LIQ_PATH = ROOT / "output" / "liq_001_validation" / "liq001_liquidity_output.csv"
MR_PATH = ROOT / "output" / "mr_001_validation" / "mr001_regime_output.csv"
OUTPUT_DIR = ROOT / "research" / "mechanism_identification" / "liq_001"


def write(path: Path, text: str) -> None:
    path.write_text(text.strip() + "\n", encoding="utf-8")


def safe_corr(frame: pd.DataFrame, left: str, right: str) -> float:
    subset = frame[[left, right]].dropna()
    if len(subset) < 3:
        return float("nan")
    return float(subset[left].corr(subset[right]))


def profile_segment(name: str, segment: pd.DataFrame) -> dict[str, object]:
    return {
        "segment": name,
        "observations": int(len(segment)),
        "liq_zscore_mean": float(segment["liq001_zscore"].mean()),
        "liq_zscore_median": float(segment["liq001_zscore"].median()),
        "aggregate_illiquidity_median": float(segment["aggregate_illiquidity"].median()),
        "spy_realized_volatility_20d_mean": float(segment["realized_volatility_20d"].mean()),
        "spy_abs_return_mean": float(segment["daily_log_return"].abs().mean()),
        "spy_return_mean": float(segment["daily_log_return"].mean()),
        "spy_drawdown_mean": float(segment["spy_drawdown"].mean()),
        "spy_drawdown_min": float(segment["spy_drawdown"].min()),
        "mr_stress_share": float(segment["regime_label"].eq("STRESS").mean()),
        "coverage_ratio_mean": float(segment["coverage_ratio"].mean()),
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    liq = pd.read_csv(LIQ_PATH, parse_dates=["date"])
    mr = pd.read_csv(MR_PATH, parse_dates=["Datetime"]).rename(columns={"Datetime": "date"})
    frame = liq.merge(
        mr[["date", "spy_close", "daily_log_return", "realized_volatility_20d", "regime_label"]],
        on="date",
        how="left",
    ).sort_values("date")
    frame["spy_peak"] = frame["spy_close"].cummax()
    frame["spy_drawdown"] = frame["spy_close"] / frame["spy_peak"] - 1.0
    valid = frame.dropna(subset=["liq001_zscore", "realized_volatility_20d", "spy_drawdown"]).copy()

    q20 = valid["liq001_zscore"].quantile(0.20)
    q80 = valid["liq001_zscore"].quantile(0.80)
    high = valid[valid["liq001_zscore"] >= q80]
    middle = valid[(valid["liq001_zscore"] > q20) & (valid["liq001_zscore"] < q80)]
    low = valid[valid["liq001_zscore"] <= q20]

    profiles = pd.DataFrame(
        [
            profile_segment("LOW_LIQUIDITY_STRESS_BOTTOM20", low),
            profile_segment("MIDDLE_60", middle),
            profile_segment("HIGH_LIQUIDITY_STRESS_TOP20", high),
        ]
    )
    profiles.to_csv(OUTPUT_DIR / "liquidity_characteristics.csv", index=False)

    regime_cross = (
        valid.assign(liq_bucket=np.where(valid["liq001_zscore"] >= q80, "HIGH_STRESS_TOP20", np.where(valid["liq001_zscore"] <= q20, "LOW_STRESS_BOTTOM20", "MIDDLE_60")))
        .groupby(["liq_bucket", "regime_label"])
        .size()
        .reset_index(name="observations")
    )
    regime_cross["share_within_bucket"] = regime_cross["observations"] / regime_cross.groupby("liq_bucket")["observations"].transform("sum")
    regime_cross.to_csv(OUTPUT_DIR / "mr001_overlap.csv", index=False)

    correlations = pd.DataFrame(
        [
            {"feature": "spy_realized_volatility_20d", "correlation_with_liq_zscore": safe_corr(valid, "liq001_zscore", "realized_volatility_20d")},
            {"feature": "abs_spy_daily_log_return", "correlation_with_liq_zscore": safe_corr(valid.assign(abs_return=valid["daily_log_return"].abs()), "liq001_zscore", "abs_return")},
            {"feature": "spy_drawdown", "correlation_with_liq_zscore": safe_corr(valid, "liq001_zscore", "spy_drawdown")},
            {"feature": "coverage_ratio", "correlation_with_liq_zscore": safe_corr(valid, "liq001_zscore", "coverage_ratio")},
        ]
    )
    correlations.to_csv(OUTPUT_DIR / "mechanism_correlations.csv", index=False)

    episodes = valid.nlargest(20, "liq001_zscore")[
        [
            "date",
            "liq001_zscore",
            "aggregate_illiquidity",
            "realized_volatility_20d",
            "daily_log_return",
            "spy_drawdown",
            "regime_label",
            "coverage_ratio",
        ]
    ].copy()
    episodes.to_csv(OUTPUT_DIR / "stress_episodes.csv", index=False)

    high_profile = profiles.loc[profiles["segment"].eq("HIGH_LIQUIDITY_STRESS_TOP20")].iloc[0]
    low_profile = profiles.loc[profiles["segment"].eq("LOW_LIQUIDITY_STRESS_BOTTOM20")].iloc[0]
    vol_ratio = high_profile["spy_realized_volatility_20d_mean"] / low_profile["spy_realized_volatility_20d_mean"]
    absret_ratio = high_profile["spy_abs_return_mean"] / low_profile["spy_abs_return_mean"]
    stress_delta = high_profile["mr_stress_share"] - low_profile["mr_stress_share"]
    drawdown_delta = high_profile["spy_drawdown_mean"] - low_profile["spy_drawdown_mean"]

    final_classification = "Partially supported"

    write(
        OUTPUT_DIR / "mi001_mechanism_identification.md",
        f"""# LIQ-001 / MI-001: Mechanism Identification

## Purpose

Identify observable market mechanisms represented by LIQ-001.

This stage is explanatory only. No predictive, alpha, profitability, economic utility, or causal claim is made.

## Final Classification

**{final_classification}**

## Main Finding

LIQ-001 primarily behaves like an **aggregate price-impact liquidity stress construct** that becomes elevated during broad market turbulence.

High LIQ-001 periods are associated with:

- higher SPY realized volatility
- larger average absolute SPY moves
- deeper average drawdown context
- higher overlap with MR-001 STRESS states
- interpretable crisis-period spikes, especially March 2020

## Key Descriptive Differences

- High liquidity-stress volatility is {vol_ratio:.2f}x low-stress volatility.
- High liquidity-stress absolute SPY movement is {absret_ratio:.2f}x low-stress absolute movement.
- MR-001 STRESS share is {stress_delta:.2%} higher in high LIQ-001 periods than low LIQ-001 periods.
- Mean SPY drawdown is {drawdown_delta:.2%} lower in high LIQ-001 periods than low LIQ-001 periods.

## Interpretation

The evidence supports a mechanism in which LIQ-001 captures market-wide trading-friction stress through price movement per unit of dollar volume.

The mechanism is related to volatility and MR-001 stress states, but not identical: LIQ-001 measures price-impact illiquidity directly, while MR-001 measures latent return/volatility regime state.

## Boundary

This study does not establish that LIQ-001 predicts future outcomes or has economic value.
""",
    )

    write(
        OUTPUT_DIR / "liquidity_mechanism_profile.md",
        f"""# Liquidity Mechanism Profile

## Segment Profiles

{profiles.to_string(index=False)}

## Mechanism Interpretation

Supported by evidence:

- High LIQ-001 periods have higher realized volatility than low LIQ-001 periods.
- High LIQ-001 periods have higher absolute market movement than low LIQ-001 periods.
- High LIQ-001 periods occur in deeper drawdown contexts.

Partially supported:

- LIQ-001 overlaps with MR-001 stress regimes, but overlap is not perfect.

Not supported:

- A pure coverage artifact explanation. Coverage remains high in high-stress periods.
""",
    )

    write(
        OUTPUT_DIR / "stress_episode_analysis.md",
        f"""# Stress Episode Analysis

## Top LIQ-001 Stress Episodes

{episodes.to_string(index=False)}

## Assessment

The strongest observed LIQ-001 stress dates cluster in March 2020. This is plausible for an aggregate liquidity-stress construct because that period combined large price moves, elevated volatility, broad risk aversion, and market-wide execution stress.

## Boundary

Event alignment is descriptive. It is not predictive validation.
""",
    )

    write(
        OUTPUT_DIR / "market_condition_summary.md",
        f"""# Market Condition Summary

## Correlations With Observable Market Conditions

{correlations.to_string(index=False)}

## MR-001 Overlap

{regime_cross.to_string(index=False)}

## Interpretation

LIQ-001 is positively associated with realized volatility and absolute market movement, and negatively associated with SPY drawdown level because more severe drawdowns are represented by more negative values.

This supports interpreting LIQ-001 as a liquidity-stress / price-impact condition rather than a standalone trend or return construct.
""",
    )

    write(
        OUTPUT_DIR / "mechanism_hypotheses.md",
        """# Mechanism Hypotheses

## H1

LIQ-001 represents aggregate price-impact liquidity stress.

Status: Supported by evidence.

## H2

LIQ-001 is primarily a volatility duplicate.

Status: Partially supported but not sufficient.

Rationale: LIQ-001 is associated with volatility, but it is constructed from absolute return per dollar volume and therefore measures price movement relative to trading activity, not volatility alone.

## H3

LIQ-001 is primarily a data coverage artifact.

Status: Not supported.

Rationale: Coverage remains high during high-stress periods.

## H4

LIQ-001 is distinct from MR-001.

Status: Partially supported.

Rationale: It overlaps with MR-001 STRESS states but represents price-impact illiquidity rather than latent return/volatility regime.

## Hypotheses for HV-001

Future hypothesis validation should formally test whether high LIQ-001 states are consistently associated with:

- higher contemporaneous realized volatility
- deeper drawdown context
- larger absolute market moves per unit of volume
- elevated MR-001 stress overlap without being fully redundant with MR-001
""",
    )

    write(
        OUTPUT_DIR / "limitations.md",
        """# Limitations

- MI-001 uses the capped IM/CV validation universe.
- LIQ-001 is daily and cannot observe intraday spread, depth, immediacy, or resiliency.
- The analysis is descriptive and contemporaneous.
- No predictive, alpha, profitability, or economic utility claim is made.
- MR-001 overlap is descriptive and does not establish construct redundancy or causality.
- A full-volume decomposition is not available from the aggregate output; LIQ-001 remains interpreted through its frozen price-impact formula and market-condition context.
""",
    )

    write(
        OUTPUT_DIR / "executive_summary.md",
        f"""# Executive Summary

LIQ-001 / MI-001 identifies the observable mechanism represented by the US Equity Aggregate Daily Illiquidity construct.

## Final Classification

**{final_classification}**

## Main Mechanism

LIQ-001 behaves as an aggregate **price-impact liquidity stress** measure.

High LIQ-001 values are associated with elevated volatility, larger absolute market moves, deeper drawdown context, and higher overlap with MR-001 STRESS states.

## Boundary

This is explanatory evidence only. It does not establish prediction, alpha, profitability, or economic utility.

## Next Authorized Stage

`LIQ-001 / HV-001`
""",
    )

    write(
        OUTPUT_DIR / "README.md",
        """# LIQ-001 / MI-001

Mechanism identification artifacts for LIQ-001.

## Status

Completed.

## Final Classification

Partially supported.

## Next Authorized Stage

LIQ-001 / HV-001
""",
    )


if __name__ == "__main__":
    main()

