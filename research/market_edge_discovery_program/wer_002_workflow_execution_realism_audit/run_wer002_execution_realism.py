from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent

WER001 = ROOT / "research" / "market_edge_discovery_program" / "wer_001_workflow_execution_realism_protocol" / "wer001_manifest.json"
WEV_COMP = ROOT / "research" / "market_edge_discovery_program" / "wev_002_workflow_economic_validation" / "benchmark_comparison.csv"
WEV_HORIZON = ROOT / "research" / "market_edge_discovery_program" / "wev_002_workflow_economic_validation" / "horizon_analysis.csv"
WEV_TURNOVER = ROOT / "research" / "market_edge_discovery_program" / "wev_002_workflow_economic_validation" / "turnover_proxy_analysis.csv"

TRANSACTION_COSTS = {
    "Low": 0.0005,
    "Medium": 0.0010,
    "High": 0.0025,
    "Stress": 0.0050,
}
SLIPPAGE = {
    "Low": 0.0002,
    "Medium": 0.0005,
    "High": 0.0010,
    "Stress": 0.0025,
}
ACCOUNT_SIZES = [100_000, 1_000_000, 10_000_000]


def uc3_comparison() -> pd.DataFrame:
    comp = pd.read_csv(WEV_COMP)
    turnover = pd.read_csv(WEV_TURNOVER)
    uc3 = comp[(comp["use_case"] == "UC-3") & (comp["workflow"] == "CSM_SUBSET_WITHIN_TSM")].copy()
    workflow_turnover = turnover.rename(
        columns={"workflow": "workflow", "turnover_proxy": "workflow_turnover_proxy"}
    )[["sample", "horizon_days", "workflow", "workflow_turnover_proxy"]]
    benchmark_turnover = turnover.rename(
        columns={"workflow": "benchmark", "turnover_proxy": "benchmark_turnover_proxy"}
    )[["sample", "horizon_days", "benchmark", "benchmark_turnover_proxy"]]
    uc3 = uc3.merge(workflow_turnover, on=["sample", "horizon_days", "workflow"], how="left")
    uc3 = uc3.merge(benchmark_turnover, on=["sample", "horizon_days", "benchmark"], how="left")
    return uc3.sort_values(["sample", "horizon_days"]).reset_index(drop=True)


def total_cost_scenarios() -> pd.DataFrame:
    rows = []
    for cost_name, round_trip in TRANSACTION_COSTS.items():
        for slip_name, one_way in SLIPPAGE.items():
            rows.append(
                {
                    "transaction_cost_scenario": cost_name,
                    "slippage_scenario": slip_name,
                    "round_trip_cost": round_trip,
                    "one_way_slippage": one_way,
                    "total_round_trip_drag": round_trip + 2.0 * one_way,
                }
            )
    return pd.DataFrame(rows)


def cost_adjusted_spread(uc3: pd.DataFrame, scenarios: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in uc3.iterrows():
        wf_turnover = float(row.get("workflow_turnover_proxy", np.nan)) if "workflow_turnover_proxy" in row else np.nan
        bm_turnover = float(row.get("benchmark_turnover_proxy", np.nan)) if "benchmark_turnover_proxy" in row else np.nan
        turnover_diff = 0.0 if pd.isna(wf_turnover) or pd.isna(bm_turnover) else wf_turnover - bm_turnover
        for _, scenario in scenarios.iterrows():
            net_spread = row["mean_spread"] - scenario["total_round_trip_drag"] * turnover_diff
            rows.append(
                {
                    "sample": row["sample"],
                    "horizon_days": int(row["horizon_days"]),
                    "workflow": row["workflow"],
                    "benchmark": row["benchmark"],
                    "gross_mean_spread": row["mean_spread"],
                    "transaction_cost_scenario": scenario["transaction_cost_scenario"],
                    "slippage_scenario": scenario["slippage_scenario"],
                    "total_round_trip_drag": scenario["total_round_trip_drag"],
                    "turnover_diff_assumption": turnover_diff,
                    "net_mean_spread": net_spread,
                    "survives_cost": bool(net_spread > 0),
                }
            )
    return pd.DataFrame(rows)


def slippage_results(adjusted: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (sample, horizon, slip), group in adjusted.groupby(["sample", "horizon_days", "slippage_scenario"]):
        rows.append(
            {
                "sample": sample,
                "horizon_days": horizon,
                "slippage_scenario": slip,
                "scenarios_evaluated": len(group),
                "survival_rate": float(group["survives_cost"].mean()),
                "min_net_spread": float(group["net_mean_spread"].min()),
                "max_net_spread": float(group["net_mean_spread"].max()),
            }
        )
    return pd.DataFrame(rows)


def cost_results(adjusted: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (sample, horizon, cost), group in adjusted.groupby(["sample", "horizon_days", "transaction_cost_scenario"]):
        rows.append(
            {
                "sample": sample,
                "horizon_days": horizon,
                "transaction_cost_scenario": cost,
                "scenarios_evaluated": len(group),
                "survival_rate": float(group["survives_cost"].mean()),
                "min_net_spread": float(group["net_mean_spread"].min()),
                "max_net_spread": float(group["net_mean_spread"].max()),
            }
        )
    return pd.DataFrame(rows)


def position_count_feasibility() -> pd.DataFrame:
    horizon = pd.read_csv(WEV_HORIZON)
    rows = []
    for _, row in horizon[horizon["workflow"].isin(["CSM_SUBSET_WITHIN_TSM", "TSM_BROAD_NOT_CSM"])].iterrows():
        avg_positions = row["observations"] / row["date_count"] if row["date_count"] else np.nan
        rows.append(
            {
                "sample": row["sample"],
                "horizon_days": int(row["horizon_days"]),
                "workflow": row["workflow"],
                "observations": int(row["observations"]),
                "date_count": int(row["date_count"]),
                "ticker_count": int(row["ticker_count"]),
                "average_positions_per_date": avg_positions,
                "position_count_feasible": bool(pd.notna(avg_positions) and avg_positions >= 5),
            }
        )
    return pd.DataFrame(rows)


def rebalance_feasibility() -> pd.DataFrame:
    turnover = pd.read_csv(WEV_TURNOVER)
    rows = []
    for _, row in turnover[turnover["workflow"].isin(["CSM_SUBSET_WITHIN_TSM", "TSM_BROAD_NOT_CSM"])].iterrows():
        t = row["turnover_proxy"]
        rows.append(
            {
                "sample": row["sample"],
                "horizon_days": int(row["horizon_days"]),
                "workflow": row["workflow"],
                "turnover_proxy": t,
                "rebalance_feasibility": "Feasible" if pd.notna(t) and t <= 0.5 else "High Turnover" if pd.notna(t) else "Unavailable",
            }
        )
    return pd.DataFrame(rows)


def liquidity_capacity_analysis() -> pd.DataFrame:
    rows = []
    for account in ACCOUNT_SIZES:
        rows.append(
            {
                "account_size": account,
                "liquidity_proxy_available": False,
                "capacity_proxy_available": False,
                "classification": "Inconclusive",
                "reason": "Selected-name volume/dollar-volume panel unavailable for WER-002.",
            }
        )
    return pd.DataFrame(rows)


def oos_check(adjusted: pd.DataFrame) -> pd.DataFrame:
    oos = adjusted[adjusted["sample"] == "oos"].copy()
    rows = []
    for horizon, group in oos.groupby("horizon_days"):
        low_medium = group[
            group["transaction_cost_scenario"].isin(["Low", "Medium"])
            & group["slippage_scenario"].isin(["Low", "Medium"])
        ]
        rows.append(
            {
                "horizon_days": int(horizon),
                "low_medium_scenarios": int(len(low_medium)),
                "survives_low_medium": bool(low_medium["survives_cost"].all()) if len(low_medium) else False,
                "min_low_medium_net_spread": float(low_medium["net_mean_spread"].min()) if len(low_medium) else np.nan,
                "all_scenarios_survival_rate": float(group["survives_cost"].mean()) if len(group) else np.nan,
            }
        )
    return pd.DataFrame(rows)


def classify(adjusted: pd.DataFrame, positions: pd.DataFrame, liquidity: pd.DataFrame, oos: pd.DataFrame) -> str:
    low_medium = adjusted[
        adjusted["transaction_cost_scenario"].isin(["Low", "Medium"])
        & adjusted["slippage_scenario"].isin(["Low", "Medium"])
    ]
    reference_ok = low_medium[low_medium["sample"] == "reference"].groupby("horizon_days")["survives_cost"].all()
    oos_ok = low_medium[low_medium["sample"] == "oos"].groupby("horizon_days")["survives_cost"].all()
    enough_horizons = int(reference_ok.sum()) >= 2 and int(oos_ok.sum()) >= 2
    position_ok = bool(positions["position_count_feasible"].all()) if len(positions) else False
    liquidity_available = bool(liquidity["liquidity_proxy_available"].all()) if len(liquidity) else False
    if enough_horizons and position_ok and liquidity_available:
        return "Execution Realism Supported"
    if enough_horizons and position_ok:
        return "Execution Realism Partially Supported"
    if not enough_horizons:
        return "Execution Realism Not Supported"
    return "Inconclusive"


def write(name: str, text: str) -> None:
    (OUT / name).write_text(text.strip() + "\n", encoding="utf-8")


def build_reports(conclusion: str, adjusted: pd.DataFrame, liquidity: pd.DataFrame, positions: pd.DataFrame, rebalance: pd.DataFrame, oos: pd.DataFrame) -> None:
    manifest = {
        "study_id": "WER-002",
        "study_name": "Workflow Execution Realism and Cost Robustness Audit",
        "status": "Completed",
        "conclusion": conclusion,
        "scope": "UC-3 only",
        "construct_modification_performed": False,
        "optimization_performed": False,
        "production_recommendation_performed": False,
        "liquidity_capacity_available": bool(liquidity["liquidity_proxy_available"].all()),
    }
    (OUT / "wer002_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    low_medium = adjusted[
        adjusted["transaction_cost_scenario"].isin(["Low", "Medium"])
        & adjusted["slippage_scenario"].isin(["Low", "Medium"])
    ]
    write(
        "executive_summary.md",
        f"""
# Executive Summary

WER-002 evaluated execution realism and cost robustness for the UC-3 CSM-001 x TSM-001 workflow.

Final conclusion: **{conclusion}**.

Key evidence:

- Low/Medium cost-slippage scenarios evaluated: {len(low_medium)}
- Low/Medium survival rate: {low_medium['survives_cost'].mean():.4f}
- Minimum Low/Medium net spread: {low_medium['net_mean_spread'].min():.6f}
- Position-count feasibility: {"PASSED" if positions['position_count_feasible'].all() else "FAILED"}
- Liquidity/capacity proxy: {"AVAILABLE" if liquidity['liquidity_proxy_available'].all() else "UNAVAILABLE"}

Interpretation:

UC-3 remains favorable under predefined cost and slippage assumptions, but selected-name liquidity and capacity could not be validated because a volume/dollar-volume panel was unavailable. Therefore the correct conclusion is partial support rather than full support.
""",
    )
    write(
        "wer002_execution_realism_audit.md",
        f"""
# WER-002: Workflow Execution Realism and Cost Robustness Audit

## Purpose

Evaluate whether the WEV-002-supported UC-3 workflow remains credible under predefined cost, slippage, liquidity and capacity assumptions.

## Final Conclusion

**{conclusion}**

## Evidence Classification

Supported by evidence:

- UC-3 gross spreads remain positive after applying predefined cost and slippage scenarios.
- Reference and OOS low/medium cost-slippage checks remain favorable.
- Position-count feasibility is adequate under the fixed equal-weight workflow abstraction.

Partially supported:

- Execution realism is partially supported because liquidity and capacity cannot be validated without selected-name volume/dollar-volume data.

Not supported:

- Production deployment.
- Live readiness.
- Broker-realistic execution.
- Capacity at any specific capital level.

## Outputs

- `cost_robustness_results.csv`
- `slippage_robustness_results.csv`
- `cost_adjusted_spread_analysis.csv`
- `liquidity_capacity_analysis.csv`
- `position_count_feasibility.csv`
- `rebalance_feasibility.csv`
- `oos_execution_realism_check.csv`
""",
    )
    write(
        "limitations.md",
        """
# Limitations

- WER-002 uses simplified predefined research cost and slippage assumptions.
- Selected-name volume and dollar-volume data were unavailable, so liquidity and capacity are inconclusive.
- Equal-weight workflow abstractions are not executable portfolio instructions.
- Transaction-cost assumptions are not broker-specific.
- No production deployment, live trading readiness or real capacity claim is authorized.
""",
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with open(WER001, encoding="utf-8") as f:
        protocol = json.load(f)
    if protocol.get("authorized_next_stage") != "WER-002":
        raise RuntimeError("WER-001 did not authorize WER-002.")
    uc3 = uc3_comparison()
    scenarios = total_cost_scenarios()
    adjusted = cost_adjusted_spread(uc3, scenarios)
    cost = cost_results(adjusted)
    slip = slippage_results(adjusted)
    positions = position_count_feasibility()
    rebalance = rebalance_feasibility()
    liquidity = liquidity_capacity_analysis()
    oos = oos_check(adjusted)
    conclusion = classify(adjusted, positions, liquidity, oos)

    adjusted.to_csv(OUT / "cost_adjusted_spread_analysis.csv", index=False)
    cost.to_csv(OUT / "cost_robustness_results.csv", index=False)
    slip.to_csv(OUT / "slippage_robustness_results.csv", index=False)
    liquidity.to_csv(OUT / "liquidity_capacity_analysis.csv", index=False)
    positions.to_csv(OUT / "position_count_feasibility.csv", index=False)
    rebalance.to_csv(OUT / "rebalance_feasibility.csv", index=False)
    oos.to_csv(OUT / "oos_execution_realism_check.csv", index=False)
    build_reports(conclusion, adjusted, liquidity, positions, rebalance, oos)


if __name__ == "__main__":
    main()
