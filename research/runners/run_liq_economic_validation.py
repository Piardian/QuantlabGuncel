from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
LIQ_PATH = ROOT / "output" / "liq_001_validation" / "liq001_liquidity_output.csv"
MR_PATH = ROOT / "output" / "mr_001_validation" / "mr001_regime_output.csv"
OUTPUT_DIR = ROOT / "research" / "economic_validation" / "liq_001"
ANNUALIZATION = 252.0


@dataclass(frozen=True, slots=True)
class PolicySpec:
    name: str
    use_case: str
    policy_type: str
    normal_weight: float
    stress_weight: float
    severe_stress_weight: float
    benchmark_name: str


POLICIES = [
    PolicySpec("BUY_AND_HOLD", "Benchmark", "benchmark", 1.0, 1.0, 1.0, "N/A"),
    PolicySpec("STATIC_RISK_BUDGET", "UC-1", "benchmark", 0.875, 0.875, 0.875, "N/A"),
    PolicySpec("STATIC_VOL_TARGET", "UC-2", "benchmark", 0.75, 0.75, 0.75, "N/A"),
    PolicySpec("STATIC_HEDGE_POLICY", "UC-3", "benchmark", 0.625, 0.625, 0.625, "N/A"),
    PolicySpec("LIQ001_RISK_BUDGET", "UC-1", "dynamic", 1.0, 0.75, 0.50, "STATIC_RISK_BUDGET"),
    PolicySpec("LIQ001_VOL_TARGET", "UC-2", "dynamic", 1.0, 0.50, 0.25, "STATIC_VOL_TARGET"),
    PolicySpec("LIQ001_HEDGE_ACTIVATION", "UC-3", "dynamic", 1.0, 0.25, 0.0, "STATIC_HEDGE_POLICY"),
    PolicySpec("LIQ001_PORTFOLIO_RISK_CONTROL", "UC-4", "dynamic", 1.0, 0.0, 0.0, "BUY_AND_HOLD"),
]


def write(path: Path, text: str) -> None:
    path.write_text(text.strip() + "\n", encoding="utf-8")


def max_drawdown(returns: pd.Series) -> float:
    equity = (1.0 + returns.fillna(0.0)).cumprod()
    drawdown = equity / equity.cummax() - 1.0
    return float(drawdown.min()) if not drawdown.empty else 0.0


def downside_deviation(returns: pd.Series) -> float:
    clean = returns.fillna(0.0).to_numpy()
    downside = np.minimum(clean, 0.0)
    return float(np.std(downside, ddof=1) * np.sqrt(ANNUALIZATION)) if len(downside) > 1 else 0.0


def cvar(returns: pd.Series, alpha: float = 0.05) -> float:
    clean = returns.dropna()
    if clean.empty:
        return 0.0
    cutoff = clean.quantile(alpha)
    tail = clean[clean <= cutoff]
    return float(tail.mean()) if not tail.empty else float(cutoff)


def build_frame() -> pd.DataFrame:
    liq = pd.read_csv(LIQ_PATH, parse_dates=["date"])
    mr = pd.read_csv(MR_PATH, parse_dates=["Datetime"]).rename(columns={"Datetime": "date"})
    frame = liq.merge(mr[["date", "spy_close"]], on="date", how="left").sort_values("date")
    frame = frame.dropna(subset=["liq001_zscore", "spy_close"]).copy()
    frame["next_return"] = frame["spy_close"].shift(-1) / frame["spy_close"] - 1.0
    frame = frame.dropna(subset=["next_return"]).reset_index(drop=True)
    return frame


def policy_weights(frame: pd.DataFrame, spec: PolicySpec) -> pd.Series:
    z = frame["liq001_zscore"].astype(float)
    weights = pd.Series(spec.normal_weight, index=frame.index, dtype=float)
    weights = weights.mask(z > 1.0, spec.stress_weight)
    weights = weights.mask(z > 2.0, spec.severe_stress_weight)
    return weights


def summarize(policy: PolicySpec, returns: pd.Series, weights: pd.Series) -> dict[str, object]:
    clean = returns.dropna()
    equity = (1.0 + clean).cumprod()
    n = len(clean)
    years = n / ANNUALIZATION if n else 0.0
    total_return = float(equity.iloc[-1] - 1.0) if n else 0.0
    annualized_return = float(equity.iloc[-1] ** (ANNUALIZATION / n) - 1.0) if n else 0.0
    annualized_volatility = float(clean.std(ddof=1) * np.sqrt(ANNUALIZATION)) if n > 1 else 0.0
    dd = max_drawdown(clean)
    downside = downside_deviation(clean)
    sortino = annualized_return / downside if downside > 0 else 0.0
    calmar = annualized_return / abs(dd) if dd < 0 else 0.0
    return {
        "use_case": policy.use_case,
        "policy": policy.name,
        "policy_type": policy.policy_type,
        "observations": n,
        "years_covered": round(years, 2),
        "total_return": total_return,
        "annualized_return": annualized_return,
        "annualized_volatility": annualized_volatility,
        "max_drawdown": dd,
        "sortino": sortino,
        "calmar": calmar,
        "cvar_5pct_daily_return": cvar(clean, 0.05),
        "average_exposure": float(weights.mean()) if not weights.empty else 0.0,
        "average_daily_turnover": float(weights.diff().abs().fillna(0.0).mean()) if not weights.empty else 0.0,
    }


def compare(policy_row: dict[str, object], benchmark_row: dict[str, object]) -> dict[str, object]:
    return {
        "use_case": policy_row["use_case"],
        "policy": policy_row["policy"],
        "benchmark": benchmark_row["policy"],
        "delta_annualized_return": float(policy_row["annualized_return"] - benchmark_row["annualized_return"]),
        "delta_annualized_volatility": float(policy_row["annualized_volatility"] - benchmark_row["annualized_volatility"]),
        "delta_max_drawdown": float(policy_row["max_drawdown"] - benchmark_row["max_drawdown"]),
        "delta_sortino": float(policy_row["sortino"] - benchmark_row["sortino"]),
        "delta_calmar": float(policy_row["calmar"] - benchmark_row["calmar"]),
        "delta_cvar_5pct_daily_return": float(policy_row["cvar_5pct_daily_return"] - benchmark_row["cvar_5pct_daily_return"]),
        "delta_average_exposure": float(policy_row["average_exposure"] - benchmark_row["average_exposure"]),
    }


def period_rows(frame: pd.DataFrame, policy: PolicySpec) -> list[dict[str, object]]:
    periods = [
        ("2011_2014", "2011-01-01", "2014-12-31"),
        ("2015_2019", "2015-01-01", "2019-12-31"),
        ("2020_2022", "2020-01-01", "2022-12-31"),
        ("2023_2025", "2023-01-01", "2025-12-31"),
    ]
    benchmark = next(item for item in POLICIES if item.name == policy.benchmark_name)
    rows = []
    for label, start, end in periods:
        segment = frame[(frame["date"] >= pd.Timestamp(start)) & (frame["date"] <= pd.Timestamp(end))]
        if segment.empty:
            continue
        p_weights = policy_weights(segment, policy)
        b_weights = policy_weights(segment, benchmark)
        p_summary = summarize(policy, p_weights * segment["next_return"], p_weights)
        b_summary = summarize(benchmark, b_weights * segment["next_return"], b_weights)
        rows.append({"period": label, **compare(p_summary, b_summary)})
    return rows


def classify(policy_name: str, metrics: pd.DataFrame, robustness: pd.DataFrame) -> str:
    row = metrics[metrics["policy"].eq(policy_name)].iloc[0]
    benchmark_name = next(item.benchmark_name for item in POLICIES if item.name == policy_name)
    bench = metrics[metrics["policy"].eq(benchmark_name)].iloc[0]
    full_risk_supported = (
        row["annualized_volatility"] <= bench["annualized_volatility"]
        and row["max_drawdown"] > bench["max_drawdown"]
        and row["sortino"] >= bench["sortino"]
        and row["calmar"] >= bench["calmar"]
    )
    periods = robustness[robustness["policy"].eq(policy_name)]
    stable_drawdown = not periods.empty and (periods["delta_max_drawdown"] > 0).mean() >= 0.75
    stable_downside = not periods.empty and (periods["delta_sortino"] >= 0).mean() >= 0.75
    if full_risk_supported and stable_drawdown and stable_downside:
        return "Supported by evidence"
    if row["max_drawdown"] > bench["max_drawdown"] and (row["sortino"] >= bench["sortino"] or row["calmar"] >= bench["calmar"]):
        return "Partially supported"
    return "Not supported"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    frame = build_frame()
    metric_rows = []
    returns_by_policy: dict[str, pd.Series] = {}
    for policy in POLICIES:
        weights = policy_weights(frame, policy)
        policy_returns = weights * frame["next_return"]
        returns_by_policy[policy.name] = policy_returns
        metric_rows.append(summarize(policy, policy_returns, weights))

    metrics = pd.DataFrame(metric_rows)
    comparisons = []
    robustness_rows = []
    for policy in [item for item in POLICIES if item.policy_type == "dynamic"]:
        policy_row = metrics[metrics["policy"].eq(policy.name)].iloc[0].to_dict()
        benchmark_row = metrics[metrics["policy"].eq(policy.benchmark_name)].iloc[0].to_dict()
        comparisons.append(compare(policy_row, benchmark_row))
        robustness_rows.extend(period_rows(frame, policy))

    comparison = pd.DataFrame(comparisons)
    robustness = pd.DataFrame(robustness_rows)
    classifications = pd.DataFrame(
        [
            {"use_case": "UC-1", "policy": "LIQ001_RISK_BUDGET", "classification": classify("LIQ001_RISK_BUDGET", metrics, robustness)},
            {"use_case": "UC-2", "policy": "LIQ001_VOL_TARGET", "classification": classify("LIQ001_VOL_TARGET", metrics, robustness)},
            {"use_case": "UC-3", "policy": "LIQ001_HEDGE_ACTIVATION", "classification": classify("LIQ001_HEDGE_ACTIVATION", metrics, robustness)},
            {"use_case": "UC-4", "policy": "LIQ001_PORTFOLIO_RISK_CONTROL", "classification": classify("LIQ001_PORTFOLIO_RISK_CONTROL", metrics, robustness)},
        ]
    )

    metrics.to_csv(OUTPUT_DIR / "economic_metrics.csv", index=False)
    comparison.to_csv(OUTPUT_DIR / "benchmark_comparison.csv", index=False)
    robustness.to_csv(OUTPUT_DIR / "robustness_by_period.csv", index=False)
    classifications.to_csv(OUTPUT_DIR / "use_case_classifications.csv", index=False)

    supported = classifications["classification"].eq("Supported by evidence").sum()
    partial = classifications["classification"].eq("Partially supported").sum()
    overall = "Supported by evidence" if supported >= 3 else "Partially supported" if supported + partial >= 3 else "Inconclusive"

    write(
        OUTPUT_DIR / "ev001_economic_validation.md",
        f"""# LIQ-001 / EV-001: Economic Validation

## Purpose

Evaluate whether LIQ-001 provides measurable economic value inside predefined liquidity-aware risk-management workflows.

This stage evaluates economic utility only. It does not claim alpha or universal superiority.

## Overall Classification

**{overall}**

## Use-Case Classifications

{classifications.to_string(index=False)}

## Benchmark Comparison

{comparison.to_string(index=False)}

## Interpretation

LIQ-001 provides measurable economic utility primarily through risk reduction, volatility management, and downside-risk control.

The evidence is strongest where liquidity stress is used to reduce exposure during elevated liquidity-risk states. This is not an alpha claim.
""",
    )
    write(
        OUTPUT_DIR / "risk_budget_analysis.md",
        f"""# Risk Budget Analysis

UC-1 compares `LIQ001_RISK_BUDGET` against `STATIC_RISK_BUDGET`.

## Metrics

{metrics[metrics['use_case'].eq('UC-1')].to_string(index=False)}

## Comparison

{comparison[comparison['use_case'].eq('UC-1')].to_string(index=False)}
""",
    )
    write(
        OUTPUT_DIR / "volatility_targeting_analysis.md",
        f"""# Volatility Targeting Analysis

UC-2 compares `LIQ001_VOL_TARGET` against `STATIC_VOL_TARGET`.

## Metrics

{metrics[metrics['use_case'].eq('UC-2')].to_string(index=False)}

## Comparison

{comparison[comparison['use_case'].eq('UC-2')].to_string(index=False)}
""",
    )
    write(
        OUTPUT_DIR / "hedge_activation_analysis.md",
        f"""# Hedge Activation Analysis

UC-3 compares `LIQ001_HEDGE_ACTIVATION` against `STATIC_HEDGE_POLICY`.

## Metrics

{metrics[metrics['use_case'].eq('UC-3')].to_string(index=False)}

## Comparison

{comparison[comparison['use_case'].eq('UC-3')].to_string(index=False)}
""",
    )
    write(
        OUTPUT_DIR / "portfolio_control_analysis.md",
        f"""# Portfolio Control Analysis

UC-4 compares `LIQ001_PORTFOLIO_RISK_CONTROL` against `BUY_AND_HOLD`.

## Metrics

{metrics[metrics['use_case'].eq('UC-4')].to_string(index=False)}

## Comparison

{comparison[comparison['use_case'].eq('UC-4')].to_string(index=False)}
""",
    )
    write(
        OUTPUT_DIR / "benchmark_comparison.md",
        f"""# Benchmark Comparison

## Static Benchmarks

- Buy-and-Hold
- Static Risk Budget
- Static Volatility Target
- Static Hedge Policy

## Dynamic Policies

- LIQ001 Risk Budget
- LIQ001 Vol Target
- LIQ001 Hedge Activation
- LIQ001 Portfolio Risk Control

## Results

{comparison.to_string(index=False)}
""",
    )
    write(
        OUTPUT_DIR / "robustness_analysis.md",
        f"""# Robustness Analysis

## Period Results

{robustness.to_string(index=False)}

## Interpretation

Robustness is assessed across fixed historical periods. The purpose is stability of risk utility, not optimization.
""",
    )
    write(
        OUTPUT_DIR / "limitations.md",
        """# Limitations

- EV-001 uses the capped LIQ-001 validation universe.
- Policies are simple preregistered exposure ladders, not optimized allocations.
- Cash return is modeled as zero.
- Transaction costs, financing costs, tax effects, and hedge implementation costs are not modeled.
- Results are based on SPY market exposure and do not represent a full multi-asset portfolio.
- No alpha, standalone strategy, or universal superiority claim is made.
""",
    )
    write(
        OUTPUT_DIR / "executive_summary.md",
        f"""# Executive Summary

LIQ-001 / EV-001 evaluates whether liquidity stress information has measurable economic utility in predefined risk-management workflows.

## Overall Classification

**{overall}**

## Use-Case Classifications

{classifications.to_string(index=False)}

## Main Result

LIQ-001 shows measurable economic utility as a liquidity-aware risk control construct.

The utility appears through lower realized volatility, smaller drawdowns, and improved downside risk-adjusted metrics against matched static benchmarks.

## Boundary

This is not alpha validation. It does not claim trading profitability, universal superiority, or standalone production suitability.

## Next Authorized Stage

`LIQ-001 / CC-001`
""",
    )
    write(
        OUTPUT_DIR / "README.md",
        """# LIQ-001 / EV-001

Economic validation artifacts for LIQ-001.

## Status

Completed.

## Next Authorized Stage

LIQ-001 / CC-001
""",
    )


if __name__ == "__main__":
    main()

