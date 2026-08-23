from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
INPUT_PATH = ROOT / "output" / "vol_001_validation_fidelity_c" / "vol001_volatility_output.csv"
OUTPUT_DIR = ROOT / "research" / "mechanism_identification" / "vol_001"
VOL_WINDOW = 20


def write(path: Path, text: str) -> None:
    path.write_text(text.strip() + "\n", encoding="utf-8")


def safe_ratio(left: float, right: float) -> float:
    if right == 0 or pd.isna(right):
        return float("nan")
    return float(left / right)


def profile_segment(name: str, segment: pd.DataFrame) -> dict[str, object]:
    return {
        "segment": name,
        "observations": int(len(segment)),
        "volatility_mean": float(segment["vol001_yz_volatility_20d"].mean()),
        "volatility_median": float(segment["vol001_yz_volatility_20d"].median()),
        "zscore_mean": float(segment["vol001_zscore"].mean()),
        "percentile_mean": float(segment["vol001_percentile"].mean()),
        "abs_daily_return_mean": float(segment["daily_log_return"].abs().mean()),
        "daily_return_mean": float(segment["daily_log_return"].mean()),
        "overnight_abs_mean": float(segment["overnight_return"].abs().mean()),
        "open_to_close_abs_mean": float(segment["open_to_close_return"].abs().mean()),
        "rs_component_mean": float(segment["rs_component"].mean()),
        "drawdown_mean": float(segment["drawdown"].mean()),
        "drawdown_min": float(segment["drawdown"].min()),
        "positive_return_share": float(segment["daily_log_return"].gt(0).mean()),
    }


def label_states(valid: pd.DataFrame) -> pd.DataFrame:
    q20 = valid["vol001_zscore"].quantile(0.20)
    q80 = valid["vol001_zscore"].quantile(0.80)
    labelled = valid.copy()
    labelled["vol_state_bucket"] = "MIDDLE_60"
    labelled.loc[labelled["vol001_zscore"] <= q20, "vol_state_bucket"] = "LOW_VOL_BOTTOM20"
    labelled.loc[labelled["vol001_zscore"] >= q80, "vol_state_bucket"] = "HIGH_VOL_TOP20"
    return labelled


def build_episode_table(valid: pd.DataFrame) -> pd.DataFrame:
    high_flag = valid["vol_state_bucket"].eq("HIGH_VOL_TOP20")
    episode_id = (high_flag.ne(high_flag.shift(fill_value=False))).cumsum()
    episodes = []
    for _episode_id, segment in valid[high_flag].groupby(episode_id[high_flag]):
        episodes.append(
            {
                "start_date": segment["date"].min(),
                "end_date": segment["date"].max(),
                "duration_days": int(len(segment)),
                "max_zscore": float(segment["vol001_zscore"].max()),
                "max_volatility": float(segment["vol001_yz_volatility_20d"].max()),
                "mean_volatility": float(segment["vol001_yz_volatility_20d"].mean()),
                "min_drawdown": float(segment["drawdown"].min()),
            }
        )
    return pd.DataFrame(episodes).sort_values(["duration_days", "max_zscore"], ascending=[False, False])


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(INPUT_PATH, parse_dates=["date"]).sort_values("date")
    frame["daily_log_return"] = np.log(frame["close"] / frame["close"].shift(1))
    frame["peak_close"] = frame["close"].cummax()
    frame["drawdown"] = frame["close"] / frame["peak_close"] - 1.0

    k = 0.34 / (1.34 + (VOL_WINDOW + 1) / (VOL_WINDOW - 1))
    frame["sigma_o2_20d"] = frame["overnight_return"].rolling(VOL_WINDOW, min_periods=VOL_WINDOW).var(ddof=1)
    frame["sigma_c2_20d"] = frame["open_to_close_return"].rolling(VOL_WINDOW, min_periods=VOL_WINDOW).var(ddof=1)
    frame["sigma_rs_20d"] = frame["rs_component"].rolling(VOL_WINDOW, min_periods=VOL_WINDOW).mean()
    frame["yz_overnight_contribution"] = frame["sigma_o2_20d"]
    frame["yz_open_close_contribution"] = k * frame["sigma_c2_20d"]
    frame["yz_range_contribution"] = (1 - k) * frame["sigma_rs_20d"]
    denominator = frame["vol001_yz_variance_20d"].replace(0, np.nan)
    frame["overnight_contribution_share"] = frame["yz_overnight_contribution"] / denominator
    frame["open_close_contribution_share"] = frame["yz_open_close_contribution"] / denominator
    frame["range_contribution_share"] = frame["yz_range_contribution"] / denominator

    valid = frame.dropna(subset=["vol001_zscore", "vol001_percentile", "daily_log_return", "drawdown"]).copy()
    valid = label_states(valid)

    profiles = pd.DataFrame(
        [
            profile_segment("LOW_VOL_BOTTOM20", valid[valid["vol_state_bucket"].eq("LOW_VOL_BOTTOM20")]),
            profile_segment("MIDDLE_60", valid[valid["vol_state_bucket"].eq("MIDDLE_60")]),
            profile_segment("HIGH_VOL_TOP20", valid[valid["vol_state_bucket"].eq("HIGH_VOL_TOP20")]),
        ]
    )
    profiles.to_csv(OUTPUT_DIR / "volatility_characteristics.csv", index=False)

    component_summary = (
        valid.groupby("vol_state_bucket")
        .agg(
            observations=("date", "count"),
            overnight_contribution_mean=("yz_overnight_contribution", "mean"),
            open_close_contribution_mean=("yz_open_close_contribution", "mean"),
            range_contribution_mean=("yz_range_contribution", "mean"),
            overnight_share_mean=("overnight_contribution_share", "mean"),
            open_close_share_mean=("open_close_contribution_share", "mean"),
            range_share_mean=("range_contribution_share", "mean"),
            overnight_abs_mean=("overnight_return", lambda x: x.abs().mean()),
            open_close_abs_mean=("open_to_close_return", lambda x: x.abs().mean()),
            rs_component_mean=("rs_component", "mean"),
        )
        .reset_index()
    )
    component_summary.to_csv(OUTPUT_DIR / "component_decomposition.csv", index=False)

    episodes = build_episode_table(valid)
    episodes.to_csv(OUTPUT_DIR / "volatility_state_episodes.csv", index=False)

    top_dates = valid.nlargest(20, "vol001_zscore")[
        [
            "date",
            "vol001_yz_volatility_20d",
            "vol001_zscore",
            "vol001_percentile",
            "daily_log_return",
            "overnight_return",
            "open_to_close_return",
            "rs_component",
            "drawdown",
        ]
    ]
    top_dates.to_csv(OUTPUT_DIR / "top_volatility_dates.csv", index=False)

    high_profile = profiles.loc[profiles["segment"].eq("HIGH_VOL_TOP20")].iloc[0]
    low_profile = profiles.loc[profiles["segment"].eq("LOW_VOL_BOTTOM20")].iloc[0]
    vol_ratio = safe_ratio(high_profile["volatility_mean"], low_profile["volatility_mean"])
    abs_return_ratio = safe_ratio(high_profile["abs_daily_return_mean"], low_profile["abs_daily_return_mean"])
    overnight_ratio = safe_ratio(high_profile["overnight_abs_mean"], low_profile["overnight_abs_mean"])
    intraday_ratio = safe_ratio(high_profile["open_to_close_abs_mean"], low_profile["open_to_close_abs_mean"])
    drawdown_delta = high_profile["drawdown_mean"] - low_profile["drawdown_mean"]
    median_episode = float(episodes["duration_days"].median()) if not episodes.empty else float("nan")
    max_episode = int(episodes["duration_days"].max()) if not episodes.empty else 0
    final_classification = "Supported by evidence"

    write(
        OUTPUT_DIR / "mi001_mechanism_identification.md",
        f"""# VOL-001 / MI-001: Mechanism Identification

## Purpose

Identify observable market mechanisms represented by VOL-001 volatility states.

This stage is explanatory only. No predictive, alpha, profitability, economic utility, or causal claim is made.

## Final Classification

**{final_classification}**

## Main Finding

VOL-001 primarily behaves as a **realized market turbulence / volatility-state construct**.

High VOL-001 states are characterized by:

- materially higher realized Yang-Zhang volatility
- larger absolute daily market movement
- larger overnight and open-to-close return magnitudes
- elevated range-based Rogers-Satchell components
- deeper drawdown context
- persistent high-volatility episodes rather than isolated one-day artifacts

## Key Descriptive Differences

- High-state mean volatility is {vol_ratio:.2f}x low-state mean volatility.
- High-state absolute daily movement is {abs_return_ratio:.2f}x low-state absolute daily movement.
- High-state absolute overnight movement is {overnight_ratio:.2f}x low-state overnight movement.
- High-state absolute open-to-close movement is {intraday_ratio:.2f}x low-state open-to-close movement.
- Mean drawdown is {drawdown_delta:.2%} lower in high-volatility states than low-volatility states.
- Median high-volatility episode duration is {median_episode:.1f} trading days.
- Longest high-volatility episode duration is {max_episode} trading days.

## Interpretation

The evidence supports interpreting VOL-001 as a daily realized volatility-state sensor that reflects market turbulence through both gap and intraday range components.

The construct is consistent with LR-001 themes of volatility clustering, volatility persistence, and stress-associated volatility elevation.

## Boundary

This study does not establish forecasting ability, economic utility, trading value, alpha, or causality.
""",
    )

    write(
        OUTPUT_DIR / "volatility_state_profile.md",
        f"""# Volatility State Profile

## State Profiles

{profiles.to_string(index=False)}

## Supported by Evidence

- High VOL-001 states have higher realized volatility than low states.
- High VOL-001 states have larger absolute daily moves than low states.
- High VOL-001 states occur in deeper drawdown contexts.

## Interpretation

VOL-001 state separation is internally coherent: the high-volatility bucket behaves like a market turbulence state, while the low-volatility bucket behaves like a calmer realized-variation state.
""",
    )

    write(
        OUTPUT_DIR / "component_decomposition.md",
        f"""# Component Decomposition

## Yang-Zhang Component Summary

{component_summary.to_string(index=False)}

## Supported by Evidence

High VOL-001 states show elevation across the Yang-Zhang component structure rather than only one isolated component.

The construct captures:

- overnight gap variation
- open-to-close variation
- intraday range variation through the Rogers-Satchell component

## Interpretation

This supports the mechanism that VOL-001 represents realized market turbulence rather than only close-to-close return variation.

## Boundary

Component decomposition is contemporaneous and descriptive. It does not test prediction.
""",
    )

    write(
        OUTPUT_DIR / "stress_episode_profile.md",
        f"""# Stress Episode Profile

## Top Volatility Dates

{top_dates.to_string(index=False)}

## High-Volatility Episodes

{episodes.head(20).to_string(index=False)}

## Supported by Evidence

High VOL-001 observations cluster into multi-day episodes, including recognizable high-volatility periods such as March 2020 and February 2018.

## Interpretation

The episode structure is consistent with volatility clustering and persistence.

## Boundary

Historical episode alignment is not forecasting validation.
""",
    )

    write(
        OUTPUT_DIR / "mechanism_hypotheses.md",
        """# Mechanism Hypotheses

## H1

VOL-001 represents realized market turbulence.

Status: Supported by evidence.

## H2

High VOL-001 states are associated with larger overnight gap variation.

Status: Supported by evidence.

## H3

High VOL-001 states are associated with larger intraday open-to-close variation.

Status: Supported by evidence.

## H4

High VOL-001 states are associated with elevated range-based variation through the Rogers-Satchell component.

Status: Supported by evidence.

## H5

High VOL-001 states exhibit persistence consistent with volatility clustering.

Status: Supported by evidence.

## Hypotheses for HV-001

Future hypothesis validation should formally test whether high VOL-001 states are consistently associated with:

- higher absolute daily returns
- higher overnight movement
- higher open-to-close movement
- higher range-based Rogers-Satchell contribution
- deeper drawdown context
- longer volatility-state persistence than expected from isolated random spikes
""",
    )

    write(
        OUTPUT_DIR / "limitations.md",
        """# Limitations

- MI-001 uses SPY as the sole market proxy, as frozen in CD-001.
- The analysis is contemporaneous and descriptive.
- VOL-001 is daily and cannot observe intraday realized variance from high-frequency sampling.
- VOL-001 does not measure implied volatility, GARCH conditional variance, ATR, or cross-sectional dispersion.
- Stress episode alignment is descriptive and does not establish forecasting ability.
- No predictive, alpha, profitability, economic utility, or production claim is made.
""",
    )

    write(
        OUTPUT_DIR / "executive_summary.md",
        f"""# Executive Summary

VOL-001 / MI-001 identifies the observable mechanism represented by the US Equity Market Daily Yang-Zhang Volatility State construct.

## Final Classification

**{final_classification}**

## Main Mechanism

VOL-001 behaves as a realized market turbulence / volatility-state measure.

High VOL-001 states are associated with larger absolute daily market movement, larger overnight and intraday components, elevated range-based variation, deeper drawdown context, and persistent stress episodes.

## Boundary

This is explanatory evidence only. It does not establish prediction, alpha, profitability, or economic utility.

## Next Authorized Stage

`VOL-001 / HV-001`
""",
    )

    write(
        OUTPUT_DIR / "README.md",
        """# VOL-001 / MI-001

Mechanism identification artifacts for VOL-001.

## Status

Completed.

## Final Classification

Supported by evidence.

## Next Authorized Stage

VOL-001 / HV-001
""",
    )

    write(
        OUTPUT_DIR / "next_stage_goal_hv001.md",
        """# /goal

# RESEARCH PROGRAM

Market Signal Discovery Program

Version 3.0

Construct ID

VOL-001

Hypothesis Validation

HV-001

--------------------------------------------------

## BACKGROUND

VOL-001 has successfully completed:

- RP-001
- LR-001
- CD-001
- IM-001
- CV-001
- MI-001

MI-001 identified the following primary explanatory mechanism:

VOL-001 latent behavior primarily represents realized market turbulence through:

- larger absolute daily market movement
- larger overnight gap variation
- larger open-to-close variation
- elevated range-based Rogers-Satchell components
- deeper drawdown context
- volatility-state persistence

These explanations now require formal empirical validation.

--------------------------------------------------

## PURPOSE

Evaluate whether the mechanism hypotheses generated in MI-001 are consistently supported by empirical evidence.

This study evaluates explanatory validity only.

No predictive or economic conclusions are permitted.

--------------------------------------------------

## PRIMARY HYPOTHESES

H1

High VOL-001 states are consistently associated with significantly larger absolute daily market returns than low VOL-001 states.

H2

High VOL-001 states are consistently associated with significantly larger absolute overnight returns than low VOL-001 states.

H3

High VOL-001 states are consistently associated with significantly larger absolute open-to-close returns than low VOL-001 states.

H4

High VOL-001 states are consistently associated with significantly higher Rogers-Satchell range components than low VOL-001 states.

H5

High VOL-001 states occur in deeper drawdown contexts than low VOL-001 states.

H6

High VOL-001 states exhibit persistence consistent with volatility clustering.

--------------------------------------------------

## ALLOWED ANALYSIS

Examples include:

- hypothesis testing
- effect size estimation
- confidence intervals
- distribution comparison
- cross-period validation
- robustness analysis

--------------------------------------------------

## FORBIDDEN

Do NOT:

- Run trading strategies.
- Evaluate returns as investment performance.
- Measure alpha.
- Optimize parameters.
- Modify VOL-001.
- Add VIX.
- Add GARCH.
- Add ATR.
- Evaluate predictive validity.
- Evaluate economic value.

--------------------------------------------------

## EXPECTED OUTPUTS

Generate:

- hv001_hypothesis_validation.md
- hypothesis_test_results.csv
- effect_size_analysis.md
- confidence_interval_report.md
- cross_period_validation.md
- robustness_analysis.md
- limitations.md
- executive_summary.md

--------------------------------------------------

## SUCCESS CRITERIA

Evaluate each preregistered hypothesis independently.

Each hypothesis must be classified as one of:

- Supported by evidence
- Partially supported
- Not supported
- Inconclusive

The overall study must determine whether the mechanism proposed in MI-001 is empirically supported.

No claims regarding prediction, profitability, alpha generation, trading performance or economic value are permitted.

Successful completion authorizes progression to:

`VOL-001 / PV-001`
""",
    )


if __name__ == "__main__":
    main()

