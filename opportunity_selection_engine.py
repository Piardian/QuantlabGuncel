"""Opportunity Selection Research Framework.

Research-only layer between signal generation and portfolio execution. It
does not change the strategy or replay existing orders. Policies are
interchangeable and every decision is recorded for later portfolio replay.

Example:
    python opportunity_selection_engine.py \
      --opportunities output/forward_simulation_readiness.csv \
      --output-dir output/opportunity_selection --max-positions 3
"""

from __future__ import annotations

import argparse
import math
from abc import ABC, abstractmethod
from pathlib import Path

import numpy as np
import pandas as pd


POLICY_NAMES = ["ARRIVAL_ORDER", "RANDOM", "UNLIMITED_CAPACITY", "ORACLE_DIAGNOSTIC", "STATIC_FEATURE_RANKING"]
FUTURE_COLUMNS = {"R_multiple", "pnl_dollars", "exit_reason", "holding_days", "mae", "mfe", "outcome"}
RANK_FEATURES = ["rs60", "atr_percent", "momentum_strength", "volatility", "distance_above_ema200"]


class SelectionPolicy(ABC):
    name: str

    @abstractmethod
    def rank(self, opportunities: pd.DataFrame) -> pd.DataFrame:
        """Return same opportunities in selection priority order."""


class ArrivalOrderPolicy(SelectionPolicy):
    name = "ARRIVAL_ORDER"

    def rank(self, opportunities: pd.DataFrame) -> pd.DataFrame:
        return opportunities.copy()


class RandomPolicy(SelectionPolicy):
    name = "RANDOM"

    def rank(self, opportunities: pd.DataFrame) -> pd.DataFrame:
        return opportunities.sample(frac=1.0, random_state=20260720).copy()


class UnlimitedCapacityPolicy(SelectionPolicy):
    name = "UNLIMITED_CAPACITY"

    def rank(self, opportunities: pd.DataFrame) -> pd.DataFrame:
        return opportunities.copy()


class OracleDiagnosticPolicy(SelectionPolicy):
    name = "ORACLE_DIAGNOSTIC"

    def rank(self, opportunities: pd.DataFrame) -> pd.DataFrame:
        if "R_multiple" not in opportunities:
            return opportunities.copy()
        return opportunities.sort_values("R_multiple", ascending=False, na_position="last").copy()


class StaticFeatureRankingPolicy(SelectionPolicy):
    name = "STATIC_FEATURE_RANKING"

    def rank(self, opportunities: pd.DataFrame) -> pd.DataFrame:
        available = [feature for feature in RANK_FEATURES if feature in opportunities.columns]
        if not available:
            return opportunities.copy()
        ranked = opportunities.copy()
        score = pd.Series(0.0, index=ranked.index)
        for feature in available:
            values = pd.to_numeric(ranked[feature], errors="coerce")
            std = values.std(ddof=1)
            if pd.notna(std) and std > 0:
                score = score + (values - values.mean()) / std
        ranked["selection_score"] = score
        return ranked.sort_values(["selection_score", "opportunity_id"], ascending=[False, True], na_position="last")


def main() -> None:
    args = _parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    opportunities = _load_opportunities(Path(args.opportunities), args.research_id)
    policies = [ArrivalOrderPolicy(), RandomPolicy(), UnlimitedCapacityPolicy(), OracleDiagnosticPolicy(), StaticFeatureRankingPolicy()]

    ledger = opportunities.copy()
    ledger.to_csv(output_dir / "opportunity_ledger.csv", index=False)
    decisions = []
    for policy in policies:
        decisions.extend(_make_decisions(ledger, policy, args.max_positions))
    decisions_frame = pd.DataFrame(decisions)
    decisions_frame.to_csv(output_dir / "selection_decisions.csv", index=False)
    decisions_frame[decisions_frame["decision"] != "EXECUTED"].to_csv(output_dir / "missed_opportunities.csv", index=False)
    comparison = _compare_policies(decisions_frame)
    comparison.to_csv(output_dir / "policy_comparison.csv", index=False)
    _write_report(output_dir / "portfolio_replay_report.md", ledger, decisions_frame, comparison, args.max_positions)
    print(output_dir / "opportunity_ledger.csv")
    print(output_dir / "selection_decisions.csv")
    print(output_dir / "policy_comparison.csv")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--opportunities", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--max-positions", type=int, default=3)
    parser.add_argument("--research-id", default="unknown")
    return parser.parse_args()


def _load_opportunities(path: Path, research_id: str) -> pd.DataFrame:
    frame = pd.read_csv(path)
    required = {"ticker"}
    if not required.issubset(frame.columns):
        raise ValueError(f"Opportunity input must contain {sorted(required)}")
    date_column = "signal_date" if "signal_date" in frame.columns else "entry_date"
    if date_column not in frame.columns:
        raise ValueError("Opportunity input requires signal_date or entry_date")
    frame = frame.copy()
    frame[date_column] = pd.to_datetime(frame[date_column], errors="coerce")
    frame = frame.dropna(subset=[date_column, "ticker"]).reset_index(drop=True)
    frame.insert(0, "opportunity_id", [f"OPP-{index:07d}" for index in range(1, len(frame) + 1)])
    frame.insert(1, "research_run_id", research_id)
    frame.insert(2, "signal_timestamp", frame[date_column])
    if "current_open_positions" not in frame and "active_positions_before_signal" in frame:
        frame["current_open_positions"] = frame["active_positions_before_signal"]
    for column, default in {
        "initial_stop": np.nan, "risk_distance": np.nan, "atr14": np.nan,
        "atr_percent": np.nan, "distance_above_ema50": np.nan, "distance_above_ema200": np.nan,
        "ema50_slope": np.nan, "ema200_slope": np.nan, "rs20": np.nan, "rs60": np.nan,
        "rs120": np.nan, "relative_volume": np.nan, "breakout_distance": np.nan,
        "current_open_positions": 0, "available_slots": np.nan, "portfolio_exposure": np.nan,
        "cash_available": np.nan, "strategy_version": "leadership_expansion_v1",
    }.items():
        if column not in frame:
            frame[column] = default
    frame["strategy_version"] = frame["strategy_version"].fillna("leadership_expansion_v1")
    return frame


def _make_decisions(ledger: pd.DataFrame, policy: SelectionPolicy, max_positions: int) -> list[dict[str, object]]:
    results = []
    for signal_date, group in ledger.groupby("signal_timestamp", sort=True):
        ranked = policy.rank(group)
        active_values = pd.to_numeric(group["current_open_positions"], errors="coerce").dropna()
        active = int(active_values.iloc[0]) if not active_values.empty else 0
        available = max(int(max_positions - active), 0)
        unlimited = policy.name == "UNLIMITED_CAPACITY"
        for rank, (_, row) in enumerate(ranked.iterrows(), start=1):
            selected = unlimited or rank <= available
            if selected:
                decision, reason = "EXECUTED", "SELECTED_BY_POLICY"
            elif active >= max_positions:
                decision, reason = "MISSED", "CAPACITY"
            else:
                decision, reason = "MISSED", "CAPACITY_OR_UNAVAILABLE_SLOT"
            results.append({
                "policy": policy.name,
                "opportunity_id": row["opportunity_id"],
                "signal_timestamp": signal_date,
                "ticker": row["ticker"],
                "selection_rank": rank,
                "available_slots": available,
                "decision": decision,
                "miss_reason": reason if decision == "MISSED" else "",
                "uses_future_information": policy.name == "ORACLE_DIAGNOSTIC",
            })
    return results


def _compare_policies(decisions: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for policy, group in decisions.groupby("policy", sort=True):
        selected = group[group["decision"] == "EXECUTED"]
        metric_values = _decision_metrics(selected)
        rows.append({
            "policy": policy,
            "executed_trades": int(len(selected)),
            "missed_trades": int((group["decision"] == "MISSED").sum()),
            **metric_values,
            "capacity_utilization": float(len(selected) / len(group)) if len(group) else 0.0,
            "opportunity_capture_rate": float(len(selected) / len(group)) if len(group) else 0.0,
            "missed_opportunity_cost": None,
            "future_information_used": policy == "ORACLE_DIAGNOSTIC",
            "comparison_status": "DIAGNOSTIC_ONLY" if policy == "ORACLE_DIAGNOSTIC" else "RESEARCH_COMPARISON",
        })
    return pd.DataFrame(rows)


def _decision_metrics(selected: pd.DataFrame) -> dict[str, float | None]:
    if "R_multiple" not in selected.columns:
        return {
            "win_rate": None, "avg_R": None, "expectancy": None,
            "profit_factor": None, "net_return": None, "max_drawdown": None,
            "exposure": None,
        }
    r_values = pd.to_numeric(selected["R_multiple"], errors="coerce").dropna()
    if r_values.empty:
        return {
            "win_rate": None, "avg_R": None, "expectancy": None,
            "profit_factor": None, "net_return": None, "max_drawdown": None,
            "exposure": None,
        }
    pnl = pd.to_numeric(selected.get("pnl_dollars", pd.Series(dtype=float)), errors="coerce").dropna()
    gross_profit = float(pnl[pnl > 0].sum())
    gross_loss = abs(float(pnl[pnl < 0].sum()))
    return {
        "win_rate": float((r_values > 0).mean() * 100.0),
        "avg_R": float(r_values.mean()),
        "expectancy": float(r_values.mean()),
        "profit_factor": gross_profit / gross_loss if gross_loss else None,
        "net_return": float(pnl.sum()) if not pnl.empty else None,
        "max_drawdown": None,
        "exposure": None,
    }


def _write_report(path: Path, ledger: pd.DataFrame, decisions: pd.DataFrame, comparison: pd.DataFrame, max_positions: int) -> None:
    policy_lines = []
    for row in comparison.to_dict("records"):
        policy_lines.append(f"- {row['policy']}: executed={row['executed_trades']}, missed={row['missed_trades']}, capture={row['opportunity_capture_rate']:.2%}")
    lines = [
        "# Portfolio Replay Report", "",
        "This is an opportunity-selection research framework. It does not modify strategy execution.", "",
        f"Opportunities: {len(ledger)}", f"Policies: {decisions['policy'].nunique() if not decisions.empty else 0}", f"Max positions: {max_positions}", "",
        "## Policy Comparison", "", *policy_lines, "",
        "## Important Limitations", "",
        "- The input ledger must be generated from signal-time information only.",
        "- Post-trade labels are not used by valid selection policies.",
        "- ORACLE_DIAGNOSTIC uses future R only as a theoretical upper bound and must never be used live.",
        "- This first framework records selection decisions; a full shared-account cash/exits replay must attach complete market data and is a separate validation step.",
        "- No policy is declared superior by this report.",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
