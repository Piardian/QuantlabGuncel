from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[3]
STATE_FILE = REPO_ROOT / "output" / "tsm_001_cv001" / "tsm001_construct_state.csv"
OUTPUT_DIR = REPO_ROOT / "research" / "market_edge_discovery_program" / "tsm_001_ev_001_economic_validation"
TRADING_DAYS = 252


def _repo_relative(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT)).replace("\\", "/")


def _load_state() -> pd.DataFrame:
    if not STATE_FILE.exists():
        raise FileNotFoundError(f"Missing TSM-001 state file: {STATE_FILE}")
    frame = pd.read_csv(STATE_FILE, parse_dates=["date"], low_memory=False)
    frame = frame[frame["tsm001_valid_observation"].astype(bool)].copy()
    return frame.sort_values(["ticker", "date"]).reset_index(drop=True)


def _build_daily_panel(frame: pd.DataFrame) -> pd.DataFrame:
    pieces = []
    for _, group in frame.groupby("ticker", sort=True):
        group = group.sort_values("date").copy()
        group["next_return_1d"] = group["adjusted_close"].shift(-1) / group["adjusted_close"] - 1.0
        pieces.append(group[["date", "ticker", "tsm001_state", "next_return_1d"]])
    return pd.concat(pieces, ignore_index=True).dropna(subset=["next_return_1d"])


def _portfolio_returns(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for date, group in panel.groupby("date", sort=True):
        all_ret = group["next_return_1d"].mean()
        positive = group[group["tsm001_state"] == "POSITIVE"]
        negative = group[group["tsm001_state"] == "NEGATIVE"]
        positive_breadth = len(positive) / len(group) if len(group) else np.nan
        positive_only = positive["next_return_1d"].mean() if len(positive) else 0.0
        risk_control = positive_breadth * positive_only
        defensive_scale = 1.0 if positive_breadth >= 0.60 else 0.50
        defensive = defensive_scale * all_ret
        rows.append(
            {
                "date": date,
                "static_equal_weight": all_ret,
                "positive_only_cash_remainder": positive_only * positive_breadth,
                "risk_control_positive_breadth_scaled": risk_control,
                "defensive_breadth_scaled_equal_weight": defensive,
                "positive_breadth": positive_breadth,
                "valid_count": int(len(group)),
                "positive_count": int(len(positive)),
                "negative_count": int(len(negative)),
            }
        )
    return pd.DataFrame(rows).dropna()


def _max_drawdown(returns: pd.Series) -> float:
    equity = (1.0 + returns.fillna(0.0)).cumprod()
    peak = equity.cummax()
    return float((equity / peak - 1.0).min())


def _metrics(returns: pd.Series) -> dict[str, float]:
    clean = returns.dropna()
    if clean.empty:
        return {}
    total_return = float((1.0 + clean).prod() - 1.0)
    years = len(clean) / TRADING_DAYS
    annualized_return = float((1.0 + total_return) ** (1.0 / years) - 1.0) if years > 0 and total_return > -1 else np.nan
    annualized_volatility = float(clean.std(ddof=1) * np.sqrt(TRADING_DAYS))
    downside = clean[clean < 0]
    downside_volatility = float(downside.std(ddof=1) * np.sqrt(TRADING_DAYS)) if len(downside) > 1 else np.nan
    return_to_volatility = annualized_return / annualized_volatility if annualized_volatility else np.nan
    downside_return_ratio = annualized_return / downside_volatility if downside_volatility else np.nan
    return {
        "daily_observations": int(len(clean)),
        "total_return": total_return,
        "annualized_return": annualized_return,
        "annualized_volatility": annualized_volatility,
        "downside_volatility": downside_volatility,
        "return_to_volatility": return_to_volatility,
        "downside_return_ratio": downside_return_ratio,
        "max_drawdown": _max_drawdown(clean),
        "mean_daily_return": float(clean.mean()),
        "median_daily_return": float(clean.median()),
        "positive_day_rate": float((clean > 0).mean()),
    }


def _economic_metrics(portfolio: pd.DataFrame) -> pd.DataFrame:
    strategies = [
        "static_equal_weight",
        "positive_only_cash_remainder",
        "risk_control_positive_breadth_scaled",
        "defensive_breadth_scaled_equal_weight",
    ]
    rows = []
    for strategy in strategies:
        row = {"workflow": strategy}
        row.update(_metrics(portfolio[strategy]))
        rows.append(row)
    result = pd.DataFrame(rows)
    baseline = result[result["workflow"] == "static_equal_weight"].iloc[0]
    for col in ["annualized_return", "annualized_volatility", "downside_volatility", "max_drawdown", "return_to_volatility", "downside_return_ratio"]:
        result[f"delta_{col}_vs_static"] = result[col] - baseline[col]
    return result


def _yearly_metrics(portfolio: pd.DataFrame) -> pd.DataFrame:
    frame = portfolio.copy()
    frame["year"] = frame["date"].dt.year
    rows = []
    for year, group in frame.groupby("year", sort=True):
        for strategy in ["static_equal_weight", "positive_only_cash_remainder", "risk_control_positive_breadth_scaled", "defensive_breadth_scaled_equal_weight"]:
            metric = _metrics(group[strategy])
            rows.append(
                {
                    "year": int(year),
                    "workflow": strategy,
                    "total_return": metric["total_return"],
                    "annualized_volatility": metric["annualized_volatility"],
                    "max_drawdown": metric["max_drawdown"],
                    "return_to_volatility": metric["return_to_volatility"],
                }
            )
    return pd.DataFrame(rows)


def _classify(metrics: pd.DataFrame) -> tuple[str, dict[str, str]]:
    baseline = metrics[metrics["workflow"] == "static_equal_weight"].iloc[0]
    classifications: dict[str, str] = {}
    for _, row in metrics.iterrows():
        workflow = row["workflow"]
        if workflow == "static_equal_weight":
            classifications[workflow] = "Benchmark"
            continue
        better_vol = row["annualized_volatility"] < baseline["annualized_volatility"]
        better_dd = row["max_drawdown"] > baseline["max_drawdown"]
        better_downside = row["downside_return_ratio"] > baseline["downside_return_ratio"]
        if better_vol and better_dd and better_downside:
            classifications[workflow] = "Supported by evidence"
        elif (better_vol and better_dd) or (better_dd and better_downside) or (better_vol and better_downside):
            classifications[workflow] = "Partially supported"
        else:
            classifications[workflow] = "Not supported"
    supported = sum(1 for v in classifications.values() if v == "Supported by evidence")
    partial = sum(1 for v in classifications.values() if v == "Partially supported")
    if supported >= 1:
        overall = "Supported by evidence"
    elif partial >= 1:
        overall = "Partially supported"
    else:
        overall = "Not supported"
    return overall, classifications


def _write_markdown(name: str, content: str) -> None:
    (OUTPUT_DIR / name).write_text(content.strip() + "\n", encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    state = _load_state()
    panel = _build_daily_panel(state)
    portfolio = _portfolio_returns(panel)
    metrics = _economic_metrics(portfolio)
    yearly = _yearly_metrics(portfolio)
    overall, classifications = _classify(metrics)

    portfolio.to_csv(OUTPUT_DIR / "portfolio_return_series.csv", index=False)
    metrics.to_csv(OUTPUT_DIR / "economic_metrics.csv", index=False)
    yearly.to_csv(OUTPUT_DIR / "yearly_economic_metrics.csv", index=False)

    manifest = {
        "construct_id": "TSM-001",
        "stage": "EV-001",
        "source_state_file": _repo_relative(STATE_FILE),
        "daily_observations": int(len(portfolio)),
        "first_date": portfolio["date"].min().strftime("%Y-%m-%d"),
        "last_date": portfolio["date"].max().strftime("%Y-%m-%d"),
        "workflow_classifications": classifications,
        "overall_conclusion": overall,
    }
    (OUTPUT_DIR / "ev001_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    metric_lookup = metrics.set_index("workflow")
    lines = []
    for workflow, row in metric_lookup.iterrows():
        lines.append(
            f"- {workflow}: classification {classifications[workflow]}, "
            f"ann return {row['annualized_return']:.4f}, ann vol {row['annualized_volatility']:.4f}, "
            f"max drawdown {row['max_drawdown']:.4f}, return/vol {row['return_to_volatility']:.4f}"
        )

    _write_markdown(
        "ev001_economic_validation.md",
        f"""
# TSM-001 / EV-001 Economic Validation

## Purpose

Evaluate whether TSM-001 predictive risk-state information provides measurable economic utility under fixed, preregistered risk-management workflows.

This is economic validation only. It is not alpha discovery, not construct modification, and not a recommendation for production deployment.

## Fixed Workflows

- Benchmark: static equal-weight available universe.
- UC-1: positive-only exposure with cash remainder.
- UC-2: positive-breadth-scaled risk control.
- UC-3: defensive equal-weight scaling when positive breadth is below 60%.

No threshold optimization or parameter tuning was performed. The 60% defensive threshold was fixed before execution as a simple majority-breadth rule.

## Evidence Base

- Source state file: `{_repo_relative(STATE_FILE)}`
- Daily observations: {len(portfolio):,}
- Date range: {portfolio['date'].min().date()} to {portfolio['date'].max().date()}

## Results

{chr(10).join(lines)}

## EV-001 Classification

**{overall}**

The conclusion is limited to the fixed workflows evaluated here. No universal economic superiority, trading alpha or production readiness is inferred.
""",
    )
    _write_markdown(
        "risk_budget_analysis.md",
        """
# Risk Budget Analysis

Risk budgeting was represented by the positive-only exposure workflow with cash remainder. This workflow allocates exposure only to securities in POSITIVE TSM-001 state and leaves the unallocated fraction in cash.
""",
    )
    _write_markdown(
        "volatility_management_analysis.md",
        """
# Volatility Management Analysis

Volatility management was evaluated by comparing annualized volatility and downside volatility against the static equal-weight benchmark.
""",
    )
    _write_markdown(
        "drawdown_analysis.md",
        """
# Drawdown Analysis

Drawdown utility was evaluated through maximum drawdown relative to the static equal-weight benchmark.
""",
    )
    _write_markdown(
        "benchmark_comparison.md",
        """
# Benchmark Comparison

All workflows were compared against the static equal-weight available-universe benchmark on identical dates.

No buy/sell signal model, transaction-cost model, capacity model or execution engine was evaluated.
""",
    )
    _write_markdown(
        "robustness_analysis.md",
        """
# Robustness Analysis

Year-by-year metrics are stored in `yearly_economic_metrics.csv`.

This EV stage uses fixed workflows only. No robustness grid or parameter sweep was performed because that would constitute optimization.
""",
    )
    _write_markdown(
        "limitations.md",
        """
# Limitations

- The source universe is current-constituent based and not survivorship-free.
- Workflows are simplified research workflows, not executable production systems.
- Cash return is assumed to be zero.
- No costs, turnover, taxes, margin, borrow constraints or liquidity constraints were modeled.
- Results cannot be interpreted as alpha or production readiness.
""",
    )
    _write_markdown(
        "executive_summary.md",
        f"""
# Executive Summary

TSM-001 / EV-001 is complete.

Overall conclusion: **{overall}**

TSM-001 was evaluated as a risk-state construct in fixed risk-management workflows. The study assessed whether its validated risk information translated into improved volatility, drawdown or downside risk-adjusted behavior versus a static equal-weight benchmark.

No alpha, Sharpe optimization or production recommendation was made.
""",
    )
    _write_markdown(
        "next_stage_goal_cc001.md",
        """
# TSM-001 / CC-001 Construct Classification

Purpose: classify TSM-001 using the accumulated evidence from RP through EV.

Classify:

- Primary category
- Secondary capabilities
- Scientific maturity
- Evidence strength
- Recommended and non-recommended application domains

No new empirical analysis is permitted.
""",
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
