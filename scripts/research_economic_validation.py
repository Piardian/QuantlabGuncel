"""EV-001 Economic Validation for MR-001.

This script evaluates predefined risk-management use cases driven by the
frozen MR-001 market regime construct. It does not modify the construct,
optimize thresholds, or estimate alpha.

Input:
    output/mr_001_validation/mr001_regime_output.csv

Outputs:
    research/program_reports/ev_001/
        economic_metrics.csv
        risk_budget_analysis.md
        volatility_targeting_analysis.md
        hedge_activation_analysis.md
        portfolio_control_analysis.md
        benchmark_comparison.md
        robustness_analysis.md
        limitations.md
        executive_summary.md
        ev001_economic_validation.md
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "output" / "mr_001_validation" / "mr001_regime_output.csv"
OUTPUT_DIR = ROOT / "research" / "program_reports" / "ev_001"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ANNUALIZATION = 252.0


@dataclass(frozen=True)
class PolicySpec:
    name: str
    kind: str
    expansion_weight: float
    stress_weight: float
    benchmark_name: str
    benchmark_weight: float
    use_case: str


POLICIES = [
    PolicySpec(
        name="BUY_AND_HOLD",
        kind="benchmark",
        expansion_weight=1.0,
        stress_weight=1.0,
        benchmark_name="N/A",
        benchmark_weight=1.0,
        use_case="Benchmark",
    ),
    PolicySpec(
        name="STATIC_RISK_BUDGET",
        kind="benchmark",
        expansion_weight=0.875,
        stress_weight=0.875,
        benchmark_name="N/A",
        benchmark_weight=0.875,
        use_case="UC-1",
    ),
    PolicySpec(
        name="STATIC_VOL_TARGET",
        kind="benchmark",
        expansion_weight=0.75,
        stress_weight=0.75,
        benchmark_name="N/A",
        benchmark_weight=0.75,
        use_case="UC-2",
    ),
    PolicySpec(
        name="STATIC_HEDGE_POLICY",
        kind="benchmark",
        expansion_weight=0.625,
        stress_weight=0.625,
        benchmark_name="N/A",
        benchmark_weight=0.625,
        use_case="UC-3",
    ),
    PolicySpec(
        name="MR001_RISK_BUDGET",
        kind="dynamic",
        expansion_weight=1.0,
        stress_weight=0.75,
        benchmark_name="STATIC_RISK_BUDGET",
        benchmark_weight=0.875,
        use_case="UC-1",
    ),
    PolicySpec(
        name="MR001_VOL_TARGET",
        kind="dynamic",
        expansion_weight=1.0,
        stress_weight=0.50,
        benchmark_name="STATIC_VOL_TARGET",
        benchmark_weight=0.75,
        use_case="UC-2",
    ),
    PolicySpec(
        name="MR001_HEDGE_ACTIVATION",
        kind="dynamic",
        expansion_weight=1.0,
        stress_weight=0.25,
        benchmark_name="STATIC_HEDGE_POLICY",
        benchmark_weight=0.625,
        use_case="UC-3",
    ),
    PolicySpec(
        name="MR001_PORTFOLIO_RISK_CONTROL",
        kind="dynamic",
        expansion_weight=1.0,
        stress_weight=0.0,
        benchmark_name="BUY_AND_HOLD",
        benchmark_weight=1.0,
        use_case="UC-4",
    ),
]


def load_regime_data() -> pd.DataFrame:
    frame = pd.read_csv(INPUT_PATH, parse_dates=["Datetime"])
    frame = frame.sort_values("Datetime").reset_index(drop=True)
    if "regime_label" not in frame.columns or "spy_close" not in frame.columns:
        raise RuntimeError("MR-001 output is missing required columns.")
    frame["next_return"] = frame["spy_close"].shift(-1) / frame["spy_close"] - 1.0
    frame["daily_return"] = frame["spy_close"].pct_change()
    frame["year"] = frame["Datetime"].dt.year
    return frame.dropna(subset=["next_return"]).copy()


def max_drawdown(returns: pd.Series) -> float:
    equity = (1.0 + returns.fillna(0.0)).cumprod()
    running_peak = equity.cummax()
    drawdown = equity / running_peak - 1.0
    return float(drawdown.min()) if not drawdown.empty else 0.0


def downside_deviation(returns: pd.Series) -> float:
    downside = np.minimum(returns.fillna(0.0).to_numpy(), 0.0)
    return float(np.std(downside, ddof=1) * math.sqrt(ANNUALIZATION)) if len(downside) > 1 else 0.0


def cvar(returns: pd.Series, alpha: float = 0.05) -> float:
    if returns.empty:
        return 0.0
    cutoff = returns.quantile(alpha)
    tail = returns[returns <= cutoff]
    return float(tail.mean()) if not tail.empty else float(cutoff)


def summarize_policy(name: str, use_case: str, kind: str, returns: pd.Series, weights: pd.Series) -> dict[str, object]:
    clean = returns.dropna()
    equity = (1.0 + clean).cumprod()
    n = len(clean)
    years = n / ANNUALIZATION if n else 0.0
    total_return = float(equity.iloc[-1] - 1.0) if n else 0.0
    ann_return = float((equity.iloc[-1] ** (ANNUALIZATION / n) - 1.0)) if n else 0.0
    ann_vol = float(clean.std(ddof=1) * math.sqrt(ANNUALIZATION)) if n > 1 else 0.0
    sortino = ann_return / downside_deviation(clean) if downside_deviation(clean) > 0 else 0.0
    max_dd = max_drawdown(clean)
    calmar = ann_return / abs(max_dd) if max_dd < 0 else 0.0
    win_rate = float((clean > 0).mean()) if n else 0.0
    avg_exposure = float(weights.mean()) if not weights.empty else 0.0
    avg_turnover = float(weights.diff().abs().fillna(0.0).mean()) if not weights.empty else 0.0
    lower_tail = float(clean.quantile(0.05)) if n else 0.0
    tail_cvar = cvar(clean, 0.05)

    return {
        "use_case": use_case,
        "policy": name,
        "policy_type": kind,
        "observations": n,
        "years_covered": round(years, 2),
        "total_return": total_return,
        "annualized_return": ann_return,
        "annualized_volatility": ann_vol,
        "sortino": sortino,
        "max_drawdown": max_dd,
        "calmar": calmar,
        "win_rate": win_rate,
        "average_exposure": avg_exposure,
        "average_daily_turnover": avg_turnover,
        "5pct_daily_return": lower_tail,
        "cvar_5pct_daily_return": tail_cvar,
    }


def build_policy_returns(frame: pd.DataFrame, policy: PolicySpec) -> tuple[pd.Series, pd.Series]:
    is_expansion = frame["regime_label"].astype(str).eq("EXPANSION")
    weights = pd.Series(
        np.where(is_expansion, policy.expansion_weight, policy.stress_weight),
        index=frame.index,
        dtype=float,
    )
    returns = weights * frame["next_return"].astype(float)
    returns.name = policy.name
    return returns, weights


def compare_to_benchmark(policy_row: dict[str, object], benchmark_row: dict[str, object]) -> dict[str, object]:
    return {
        "use_case": policy_row["use_case"],
        "policy": policy_row["policy"],
        "benchmark": benchmark_row["policy"],
        "delta_annualized_return": float(policy_row["annualized_return"] - benchmark_row["annualized_return"]),
        "delta_annualized_volatility": float(policy_row["annualized_volatility"] - benchmark_row["annualized_volatility"]),
        "delta_max_drawdown": float(policy_row["max_drawdown"] - benchmark_row["max_drawdown"]),
        "delta_sortino": float(policy_row["sortino"] - benchmark_row["sortino"]),
        "delta_calmar": float(policy_row["calmar"] - benchmark_row["calmar"]),
        "delta_average_exposure": float(policy_row["average_exposure"] - benchmark_row["average_exposure"]),
        "delta_cvar_5pct_daily_return": float(policy_row["cvar_5pct_daily_return"] - benchmark_row["cvar_5pct_daily_return"]),
    }


def evaluate_robustness(frame: pd.DataFrame, policy: PolicySpec) -> pd.DataFrame:
    periods = [
        ("2008_2012", "2008-01-31", "2012-12-31"),
        ("2013_2019", "2013-01-01", "2019-12-31"),
        ("2020_2022", "2020-01-01", "2022-12-31"),
        ("2023_2025", "2023-01-01", "2025-12-31"),
    ]
    rows = []
    for label, start, end in periods:
        segment = frame[(frame["Datetime"] >= pd.Timestamp(start)) & (frame["Datetime"] <= pd.Timestamp(end))].copy()
        if segment.empty:
            continue
        policy_returns, policy_weights = build_policy_returns(segment, policy)
        bench_spec = next(item for item in POLICIES if item.name == policy.benchmark_name)
        bench_returns, bench_weights = build_policy_returns(segment, bench_spec)

        policy_metrics = summarize_policy(policy.name, policy.use_case, policy.kind, policy_returns, policy_weights)
        bench_metrics = summarize_policy(bench_spec.name, bench_spec.use_case, bench_spec.kind, bench_returns, bench_weights)
        rows.append({
            "period": label,
            "policy": policy.name,
            "benchmark": bench_spec.name,
            "observations": int(policy_metrics["observations"]),
            "annualized_return": policy_metrics["annualized_return"],
            "benchmark_annualized_return": bench_metrics["annualized_return"],
            "delta_annualized_return": float(policy_metrics["annualized_return"] - bench_metrics["annualized_return"]),
            "annualized_volatility": policy_metrics["annualized_volatility"],
            "benchmark_annualized_volatility": bench_metrics["annualized_volatility"],
            "delta_annualized_volatility": float(policy_metrics["annualized_volatility"] - bench_metrics["annualized_volatility"]),
            "max_drawdown": policy_metrics["max_drawdown"],
            "benchmark_max_drawdown": bench_metrics["max_drawdown"],
            "delta_max_drawdown": float(policy_metrics["max_drawdown"] - bench_metrics["max_drawdown"]),
            "sortino": policy_metrics["sortino"],
            "benchmark_sortino": bench_metrics["sortino"],
            "delta_sortino": float(policy_metrics["sortino"] - bench_metrics["sortino"]),
            "calmar": policy_metrics["calmar"],
            "benchmark_calmar": bench_metrics["calmar"],
            "delta_calmar": float(policy_metrics["calmar"] - bench_metrics["calmar"]),
        })
    return pd.DataFrame(rows)


def write_markdown(path: Path, title: str, sections: list[str]) -> None:
    content = [f"# {title}", ""]
    content.extend(sections)
    path.write_text("\n".join(content).strip() + "\n", encoding="utf-8")


def main() -> None:
    frame = load_regime_data()

    policy_rows: list[dict[str, object]] = []
    policy_series: dict[str, pd.Series] = {}
    weight_series: dict[str, pd.Series] = {}

    for policy in POLICIES:
        returns, weights = build_policy_returns(frame, policy)
        policy_series[policy.name] = returns
        weight_series[policy.name] = weights
        policy_rows.append(summarize_policy(policy.name, policy.use_case, policy.kind, returns, weights))

    metrics = pd.DataFrame(policy_rows)

    comparison_rows: list[dict[str, object]] = []
    for policy in POLICIES:
        if policy.kind != "dynamic":
            continue
        policy_row = metrics.loc[metrics["policy"] == policy.name].iloc[0].to_dict()
        benchmark_row = metrics.loc[metrics["policy"] == policy.benchmark_name].iloc[0].to_dict()
        comparison_rows.append(compare_to_benchmark(policy_row, benchmark_row))

    comparison = pd.DataFrame(comparison_rows)

    robustness_rows = []
    for policy in [p for p in POLICIES if p.kind == "dynamic"]:
        robustness_rows.append(evaluate_robustness(frame, policy))
    robustness = pd.concat(robustness_rows, ignore_index=True) if robustness_rows else pd.DataFrame()

    metrics.to_csv(OUTPUT_DIR / "economic_metrics.csv", index=False)
    comparison.to_csv(OUTPUT_DIR / "benchmark_comparison.csv", index=False)
    robustness.to_csv(OUTPUT_DIR / "robustness_by_period.csv", index=False)

    def policy_summary(policy_name: str) -> dict[str, object]:
        return metrics.loc[metrics["policy"] == policy_name].iloc[0].to_dict()

    uc_map = {
        "UC-1": ("MR001_RISK_BUDGET", "STATIC_RISK_BUDGET"),
        "UC-2": ("MR001_VOL_TARGET", "STATIC_VOL_TARGET"),
        "UC-3": ("MR001_HEDGE_ACTIVATION", "STATIC_HEDGE_POLICY"),
        "UC-4": ("MR001_PORTFOLIO_RISK_CONTROL", "BUY_AND_HOLD"),
    }

    classification: dict[str, str] = {}
    for uc, (dyn, bench) in uc_map.items():
        drow = policy_summary(dyn)
        brow = policy_summary(bench)
        period_rows = robustness[robustness["policy"] == dyn] if not robustness.empty else pd.DataFrame()
        full_sample_supported = (
            (drow["annualized_return"] >= brow["annualized_return"])
            and (drow["annualized_volatility"] <= brow["annualized_volatility"])
            and (drow["max_drawdown"] > brow["max_drawdown"])
            and (drow["sortino"] >= brow["sortino"])
            and (drow["calmar"] >= brow["calmar"])
        )
        return_stable = False
        drawdown_stable = False
        if not period_rows.empty:
            return_stable = bool((period_rows["delta_annualized_return"] >= 0).mean() >= 0.75)
            drawdown_stable = bool((period_rows["delta_max_drawdown"] > 0).all())
        if full_sample_supported and return_stable and drawdown_stable:
            classification[uc] = "Supported by evidence"
        elif (drow["max_drawdown"] > brow["max_drawdown"]) and drawdown_stable:
            classification[uc] = "Partially supported"
        else:
            classification[uc] = "Not supported"

    # Markdown outputs
    write_markdown(
        OUTPUT_DIR / "ev001_economic_validation.md",
        "EV-001: MR-001 Economic Validation",
        [
            "## Scope",
            "MR-001 is evaluated only as a risk-forecasting construct inside predefined risk-management workflows.",
            "",
            "## Primary Result",
            comparison.to_string(index=False) if not comparison.empty else "No dynamic policies evaluated.",
            "",
            "## Use-Case Classifications",
            "\n".join([f"- {uc}: {classification[uc]}" for uc in ["UC-1", "UC-2", "UC-3", "UC-4"]]),
            "",
            "## Interpretation",
            "Economic value is assessed only as risk reduction, volatility management, hedge activation efficiency, and downside-risk control. No alpha claim is made.",
        ],
    )

    write_markdown(
        OUTPUT_DIR / "risk_budget_analysis.md",
        "Risk Budgeting Analysis",
        [
            "UC-1 compares a regime-aware 100% / 75% exposure ladder against a static 87.5% benchmark.",
            "",
            metrics.loc[metrics["use_case"] == "UC-1"].to_string(index=False),
            "",
            comparison.loc[comparison["use_case"] == "UC-1"].to_string(index=False) if not comparison.empty else "No comparison available.",
            "",
            f"Classification: {classification['UC-1']}",
        ],
    )

    write_markdown(
        OUTPUT_DIR / "volatility_targeting_analysis.md",
        "Volatility Targeting Analysis",
        [
            "UC-2 compares a regime-aware 100% / 50% exposure ladder against a static 75% benchmark.",
            "",
            metrics.loc[metrics["use_case"] == "UC-2"].to_string(index=False),
            "",
            comparison.loc[comparison["use_case"] == "UC-2"].to_string(index=False) if not comparison.empty else "No comparison available.",
            "",
            f"Classification: {classification['UC-2']}",
        ],
    )

    write_markdown(
        OUTPUT_DIR / "hedge_activation_analysis.md",
        "Hedge Activation Analysis",
        [
            "UC-3 compares a regime-aware 100% / 25% exposure ladder against a static 62.5% benchmark.",
            "",
            metrics.loc[metrics["use_case"] == "UC-3"].to_string(index=False),
            "",
            comparison.loc[comparison["use_case"] == "UC-3"].to_string(index=False) if not comparison.empty else "No comparison available.",
            "",
            f"Classification: {classification['UC-3']}",
        ],
    )

    write_markdown(
        OUTPUT_DIR / "portfolio_control_analysis.md",
        "Portfolio Control Analysis",
        [
            "UC-4 compares an expansion-only / stress-off regime control against buy-and-hold.",
            "",
            metrics.loc[metrics["use_case"] == "UC-4"].to_string(index=False),
            "",
            comparison.loc[comparison["use_case"] == "UC-4"].to_string(index=False) if not comparison.empty else "No comparison available.",
            "",
            f"Classification: {classification['UC-4']}",
        ],
    )

    periods_text = []
    if not robustness.empty:
        for policy in ["MR001_RISK_BUDGET", "MR001_VOL_TARGET", "MR001_HEDGE_ACTIVATION", "MR001_PORTFOLIO_RISK_CONTROL"]:
            segment = robustness[robustness["policy"] == policy]
            periods_text.append(f"### {policy}")
            periods_text.append(segment.to_string(index=False))
            periods_text.append("")
    write_markdown(
        OUTPUT_DIR / "robustness_analysis.md",
        "Robustness Analysis",
        [
            "The regime-aware policies were evaluated across fixed historical periods to check whether risk improvement is concentrated in one episode only.",
            "",
            "\n".join(periods_text) if periods_text else "No robustness periods available.",
        ],
    )

    write_markdown(
        OUTPUT_DIR / "benchmark_comparison.md",
        "Benchmark Comparison",
        [
            "Benchmark policies were predeclared as fixed exposure baselines. Dynamic MR-001 policies were compared only against their matched static counterparts.",
            "",
            metrics.to_string(index=False),
            "",
            comparison.to_string(index=False) if not comparison.empty else "No dynamic-to-benchmark comparison available.",
        ],
    )

    write_markdown(
        OUTPUT_DIR / "limitations.md",
        "Limitations",
        [
            "- The analysis uses a single market sleeve (SPY) with cash set to zero return, so it measures de-risking utility rather than full multi-asset portfolio construction.",
            "- Policies are evaluated on historical regime labels from MR-001; this is useful for utility assessment but still depends on the frozen construct and the chosen benchmark definitions.",
            "- No transaction costs, financing costs, or hedge instrument drag were modeled.",
            "- The study does not test alpha, directional forecasting, or production trading performance.",
        ],
    )

    write_markdown(
        OUTPUT_DIR / "executive_summary.md",
        "EV-001 Executive Summary",
        [
            "MR-001 is evaluated as a risk forecasting construct in four predefined decision workflows: risk budgeting, volatility targeting, hedge activation, and regime-aware portfolio risk control.",
            "",
            f"UC-1: {classification['UC-1']}",
            f"UC-2: {classification['UC-2']}",
            f"UC-3: {classification['UC-3']}",
            f"UC-4: {classification['UC-4']}",
            "",
            "The evidence is interpreted only as economic utility inside the predefined workflows. No alpha or universal superiority claim is made.",
        ],
    )


if __name__ == "__main__":
    main()
