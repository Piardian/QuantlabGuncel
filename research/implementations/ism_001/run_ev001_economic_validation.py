from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[3]
STATE_FILE = REPO_ROOT / "output" / "ism_001" / "ism001_industry_momentum_state.csv"
OUTPUT_DIR = REPO_ROOT / "research" / "market_edge_discovery_program" / "ism_001_ev_001_economic_validation"

MONTHS_PER_YEAR = 12
TRANSACTION_COST_BPS = 10.0


def _repo_relative(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT)).replace("\\", "/")


def _safe_float(value: float) -> float | None:
    if pd.isna(value) or not np.isfinite(value):
        return None
    return float(value)


def _load_state() -> pd.DataFrame:
    if not STATE_FILE.exists():
        raise FileNotFoundError(f"Missing ISM-001 state file: {STATE_FILE}")
    frame = pd.read_csv(STATE_FILE, parse_dates=["month"], low_memory=False)
    frame = frame[frame["ism_valid_observation"].astype(bool)].copy()
    return frame.sort_values(["month", "industry_id"]).reset_index(drop=True)


def _equal_weight(mask: pd.Series) -> pd.Series:
    weights = pd.Series(0.0, index=mask.index, dtype=float)
    active = mask[mask].index
    if len(active):
        weights.loc[active] = 1.0 / len(active)
    return weights


def _build_weight_panels(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    returns = frame.pivot(index="month", columns="industry_id", values="industry_return").sort_index()
    valid = frame.pivot(index="month", columns="industry_id", values="ism_valid_observation").sort_index().fillna(False).astype(bool)
    state = frame.pivot(index="month", columns="industry_id", values="ism_state").sort_index()

    weights: dict[str, list[pd.Series]] = {
        "STATIC_EQUAL_WEIGHT": [],
        "UC1_TOP_DECILE_LONG_ONLY": [],
        "UC2_TOP_MINUS_BOTTOM_DOLLAR_NEUTRAL": [],
        "UC3_50_50_BENCHMARK_TOP_TILT": [],
    }
    dates = []
    for month in returns.index:
        valid_weights = _equal_weight(valid.loc[month])
        top_weights = _equal_weight(state.loc[month].eq("TOP_DECILE"))
        bottom_weights = _equal_weight(state.loc[month].eq("BOTTOM_DECILE"))
        spread_weights = top_weights - bottom_weights
        tilt_weights = 0.5 * valid_weights + 0.5 * top_weights
        dates.append(month)
        weights["STATIC_EQUAL_WEIGHT"].append(valid_weights)
        weights["UC1_TOP_DECILE_LONG_ONLY"].append(top_weights)
        weights["UC2_TOP_MINUS_BOTTOM_DOLLAR_NEUTRAL"].append(spread_weights)
        weights["UC3_50_50_BENCHMARK_TOP_TILT"].append(tilt_weights)

    panels = {name: pd.DataFrame(rows, index=dates).reindex(columns=returns.columns).fillna(0.0) for name, rows in weights.items()}
    return returns, panels


def _portfolio_timeline(returns: pd.DataFrame, weight_panels: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    cost_rate = TRANSACTION_COST_BPS / 10000.0
    records = []
    turnover_records = []
    dates = list(returns.index)
    previous_weights = {name: pd.Series(0.0, index=returns.columns) for name in weight_panels}
    for idx in range(len(dates) - 1):
        decision_month = dates[idx]
        realized_month = dates[idx + 1]
        next_returns = returns.loc[realized_month].fillna(0.0)
        record = {"decision_month": decision_month, "realized_month": realized_month}
        turnover_record = {"decision_month": decision_month}
        for name, panel in weight_panels.items():
            weights = panel.loc[decision_month]
            turnover = float((weights - previous_weights[name]).abs().sum())
            gross = float((weights * next_returns).sum())
            cost = turnover * cost_rate
            record[f"{name}_gross_return"] = gross
            record[f"{name}_net_return"] = gross - cost
            record[f"{name}_turnover"] = turnover
            record[f"{name}_cost"] = cost
            record[f"{name}_position_count"] = int((weights.abs() > 0).sum())
            turnover_record[f"{name}_turnover"] = turnover
            previous_weights[name] = weights.copy()
        records.append(record)
        turnover_records.append(turnover_record)
    return pd.DataFrame(records), pd.DataFrame(turnover_records)


def _max_drawdown(returns: pd.Series) -> float:
    equity = (1.0 + returns.fillna(0.0)).cumprod()
    peak = equity.cummax()
    return float((equity / peak - 1.0).min())


def _annualized_return(returns: pd.Series) -> float:
    clean = returns.dropna()
    if clean.empty:
        return np.nan
    total = float((1.0 + clean).prod())
    years = len(clean) / MONTHS_PER_YEAR
    return total ** (1.0 / years) - 1.0 if years > 0 and total > 0 else np.nan


def _annualized_volatility(returns: pd.Series) -> float:
    clean = returns.dropna()
    return float(clean.std(ddof=0) * np.sqrt(MONTHS_PER_YEAR)) if len(clean) else np.nan


def _return_to_volatility(returns: pd.Series) -> float:
    ann_vol = _annualized_volatility(returns)
    if not ann_vol or pd.isna(ann_vol):
        return np.nan
    return _annualized_return(returns) / ann_vol


def _sortino_like(returns: pd.Series) -> float:
    clean = returns.dropna()
    downside = clean[clean < 0].std(ddof=0) * np.sqrt(MONTHS_PER_YEAR)
    if not downside or pd.isna(downside):
        return np.nan
    return _annualized_return(clean) / downside


def _metrics(timeline: pd.DataFrame) -> pd.DataFrame:
    rows = []
    workflows = ["STATIC_EQUAL_WEIGHT", "UC1_TOP_DECILE_LONG_ONLY", "UC2_TOP_MINUS_BOTTOM_DOLLAR_NEUTRAL", "UC3_50_50_BENCHMARK_TOP_TILT"]
    for workflow in workflows:
        returns = timeline[f"{workflow}_net_return"]
        rows.append(
            {
                "workflow": workflow,
                "monthly_observations": int(len(returns.dropna())),
                "total_return": _safe_float((1.0 + returns.fillna(0.0)).prod() - 1.0),
                "annualized_return": _safe_float(_annualized_return(returns)),
                "annualized_volatility": _safe_float(_annualized_volatility(returns)),
                "return_to_volatility": _safe_float(_return_to_volatility(returns)),
                "downside_return_to_volatility": _safe_float(_sortino_like(returns)),
                "max_drawdown": _safe_float(_max_drawdown(returns)),
                "mean_monthly_return": _safe_float(returns.mean()),
                "median_monthly_return": _safe_float(returns.median()),
                "positive_month_rate": _safe_float((returns > 0).mean()),
                "average_turnover": _safe_float(timeline[f"{workflow}_turnover"].mean()),
                "average_position_count": _safe_float(timeline[f"{workflow}_position_count"].mean()),
            }
        )
    result = pd.DataFrame(rows)
    baseline = result[result["workflow"] == "STATIC_EQUAL_WEIGHT"].iloc[0]
    for column in ["annualized_return", "annualized_volatility", "return_to_volatility", "downside_return_to_volatility", "max_drawdown"]:
        result[f"delta_{column}_vs_static"] = result[column] - baseline[column]
    return result


def _yearly_metrics(timeline: pd.DataFrame) -> pd.DataFrame:
    frame = timeline.copy()
    frame["year"] = frame["realized_month"].dt.year
    workflows = ["STATIC_EQUAL_WEIGHT", "UC1_TOP_DECILE_LONG_ONLY", "UC2_TOP_MINUS_BOTTOM_DOLLAR_NEUTRAL", "UC3_50_50_BENCHMARK_TOP_TILT"]
    rows = []
    for year, group in frame.groupby("year", sort=True):
        for workflow in workflows:
            returns = group[f"{workflow}_net_return"]
            rows.append(
                {
                    "year": int(year),
                    "workflow": workflow,
                    "total_return": _safe_float((1.0 + returns.fillna(0.0)).prod() - 1.0),
                    "annualized_volatility": _safe_float(_annualized_volatility(returns)),
                    "return_to_volatility": _safe_float(_return_to_volatility(returns)),
                    "max_drawdown": _safe_float(_max_drawdown(returns)),
                }
            )
    return pd.DataFrame(rows)


def _classify(metrics: pd.DataFrame, yearly: pd.DataFrame) -> tuple[str, dict[str, str], dict[str, object]]:
    baseline = metrics[metrics["workflow"] == "STATIC_EQUAL_WEIGHT"].iloc[0]
    classifications: dict[str, str] = {"STATIC_EQUAL_WEIGHT": "Benchmark"}
    details: dict[str, object] = {}
    for workflow in ["UC1_TOP_DECILE_LONG_ONLY", "UC2_TOP_MINUS_BOTTOM_DOLLAR_NEUTRAL", "UC3_50_50_BENCHMARK_TOP_TILT"]:
        row = metrics[metrics["workflow"] == workflow].iloc[0]
        year_pivot = yearly.pivot(index="year", columns="workflow", values="total_return")
        if workflow == "UC2_TOP_MINUS_BOTTOM_DOLLAR_NEUTRAL":
            positive_year_rate = float((year_pivot[workflow] > 0).mean())
            ann_return_ok = row["annualized_return"] > 0
            risk_adjusted_ok = row["return_to_volatility"] > 0
            if ann_return_ok and risk_adjusted_ok and positive_year_rate >= 0.60:
                classifications[workflow] = "Supported by evidence"
            elif ann_return_ok and positive_year_rate >= 0.50:
                classifications[workflow] = "Partially supported"
            else:
                classifications[workflow] = "Not supported"
            details[workflow] = {"positive_year_rate": positive_year_rate}
        else:
            outperform_year_rate = float((year_pivot[workflow] > year_pivot["STATIC_EQUAL_WEIGHT"]).mean())
            ann_delta = float(row["annualized_return"] - baseline["annualized_return"])
            rtov_delta = float(row["return_to_volatility"] - baseline["return_to_volatility"])
            dd_improved = bool(row["max_drawdown"] > baseline["max_drawdown"])
            if ann_delta > 0 and rtov_delta > 0 and outperform_year_rate >= 0.60:
                classifications[workflow] = "Supported by evidence"
            elif ann_delta > 0 and outperform_year_rate >= 0.50:
                classifications[workflow] = "Partially supported"
            else:
                classifications[workflow] = "Not supported"
            details[workflow] = {
                "annualized_return_delta": ann_delta,
                "return_to_volatility_delta": rtov_delta,
                "max_drawdown_improved": dd_improved,
                "outperform_year_rate": outperform_year_rate,
            }
    supported = sum(1 for value in classifications.values() if value == "Supported by evidence")
    partial = sum(1 for value in classifications.values() if value == "Partially supported")
    if supported >= 2:
        overall = "Supported by evidence"
    elif supported + partial >= 2:
        overall = "Partially supported"
    else:
        overall = "Not supported"
    return overall, classifications, details


def _write_reports(timeline: pd.DataFrame, turnover: pd.DataFrame, metrics: pd.DataFrame, yearly: pd.DataFrame, overall: str, classifications: dict[str, str], details: dict[str, object]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timeline.to_csv(OUTPUT_DIR / "portfolio_return_series.csv", index=False)
    turnover.to_csv(OUTPUT_DIR / "rebalance_turnover_summary.csv", index=False)
    metrics.to_csv(OUTPUT_DIR / "economic_metrics.csv", index=False)
    yearly.to_csv(OUTPUT_DIR / "yearly_economic_validation.csv", index=False)

    metric_lookup = metrics.set_index("workflow")
    lines = []
    for workflow, row in metric_lookup.iterrows():
        lines.append(
            f"- {workflow}: classification {classifications[workflow]}, "
            f"ann return {row['annualized_return']:.4f}, ann vol {row['annualized_volatility']:.4f}, "
            f"max drawdown {row['max_drawdown']:.4f}, return/vol {row['return_to_volatility']:.4f}"
        )
    result_lines = "\n".join(lines)

    (OUTPUT_DIR / "ev001_economic_validation.md").write_text(
        f"""# ISM-001 / EV-001 Economic Validation

## Purpose

Evaluate whether ISM-001 predictive information provides measurable economic utility under fixed, preregistered industry-level workflows.

This is economic validation only. It is not construct modification, not alpha discovery, not stock-level signal assignment and not a recommendation for production deployment.

## Fixed Workflows

- Benchmark: `STATIC_EQUAL_WEIGHT`, equal-weight all valid Ken French 49 industry portfolios.
- UC-1: `UC1_TOP_DECILE_LONG_ONLY`, equal-weight TOP_DECILE industries.
- UC-2: `UC2_TOP_MINUS_BOTTOM_DOLLAR_NEUTRAL`, equal-weight TOP_DECILE long and BOTTOM_DECILE short research spread.
- UC-3: `UC3_50_50_BENCHMARK_TOP_TILT`, 50% equal-weight benchmark plus 50% equal-weight TOP_DECILE tilt.

## Fixed Assumptions

- Rebalance frequency: monthly.
- Signal timing: state observed at month `t`, realized return measured during month `t+1`.
- Transaction cost: {TRANSACTION_COST_BPS:.1f} bps per dollar of turnover.
- No threshold optimization, no parameter tuning, no workflow redesign after observing results.

## Results

{result_lines}

## EV-001 Classification

**{overall}**

This result is limited to the fixed industry-level workflows and assumptions evaluated here. It does not imply production readiness, universal economic superiority or individual-stock applicability.
""",
        encoding="utf-8",
    )

    (OUTPUT_DIR / "industry_workflow_analysis.md").write_text(
        """# Industry Workflow Analysis

The workflows are industry-portfolio workflows only:

- Long-only industry leadership selection.
- Long-short industry leadership-versus-laggard spread.
- Benchmark-plus-leadership tilt.

No individual stock mapping was performed.
""",
        encoding="utf-8",
    )

    (OUTPUT_DIR / "benchmark_comparison.md").write_text(
        """# Benchmark Comparison

Benchmark:

`STATIC_EQUAL_WEIGHT`

This benchmark equally weights all valid Ken French 49 industry portfolios on each monthly decision date.

It is used to isolate whether ISM state information provides economic utility relative to the same industry universe.
""",
        encoding="utf-8",
    )

    (OUTPUT_DIR / "turnover_cost_analysis.md").write_text(
        f"""# Turnover And Cost Analysis

Transaction cost assumption:

```text
{TRANSACTION_COST_BPS:.1f} bps per dollar of turnover
```

Average turnover and average position count are reported in `economic_metrics.csv`.

No transaction-cost optimization or cost sensitivity sweep was performed.
""",
        encoding="utf-8",
    )

    (OUTPUT_DIR / "robustness_analysis.md").write_text(
        """# Robustness Analysis

Robustness was evaluated year-by-year under the same fixed workflows.

Output:

- `yearly_economic_validation.csv`

No alternate rebalancing schedules, thresholds, costs or workflow variants were searched.
""",
        encoding="utf-8",
    )

    (OUTPUT_DIR / "limitations.md").write_text(
        """# Limitations

- EV-001 uses Ken French industry portfolios, not investable ETF or stock-level implementation.
- Dollar-neutral spread returns are research spread returns, not a production-ready shorting workflow.
- Transaction cost is fixed at 10 bps per dollar traded and is not calibrated to live execution.
- No market impact, capacity, borrow, tax, liquidity or execution-timing model is included.
- Economic validation is workflow-specific and cannot be generalized beyond the evaluated assumptions.
- This stage does not recommend production deployment.
""",
        encoding="utf-8",
    )

    (OUTPUT_DIR / "executive_summary.md").write_text(
        f"""# Executive Summary

ISM-001 / EV-001 evaluated whether the validated industry momentum construct provides measurable economic utility under fixed industry-level workflows.

Overall classification:

**{overall}**

Workflow classifications:

{chr(10).join(f"- {key}: {value}" for key, value in classifications.items())}

No stock-level signal assignment, production recommendation, threshold optimization or strategy redesign was performed.
""",
        encoding="utf-8",
    )

    (OUTPUT_DIR / "next_stage_goal_cc001.md").write_text(
        """# ISM-001 / CC-001 Construct Classification

Purpose:

Classify ISM-001 using accumulated evidence from RP, LR, CD, IM, CV, MI, HV, PV and EV.

Classify:

- Primary category
- Secondary capabilities
- Scientific maturity
- Evidence strength
- Recommended and non-recommended research applications

No new empirical analysis is permitted.
""",
        encoding="utf-8",
    )

    manifest = {
        "construct_id": "ISM-001",
        "stage": "EV-001",
        "overall_conclusion": overall,
        "workflow_classifications": classifications,
        "workflow_details": details,
        "source_state_file": _repo_relative(STATE_FILE),
        "monthly_observations": int(len(timeline)),
        "first_realized_month": timeline["realized_month"].min().strftime("%Y-%m-%d"),
        "last_realized_month": timeline["realized_month"].max().strftime("%Y-%m-%d"),
        "transaction_cost_bps": TRANSACTION_COST_BPS,
        "next_stage": "CC-001",
    }
    (OUTPUT_DIR / "ev001_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def run_economic_validation() -> dict[str, object]:
    state = _load_state()
    returns, weight_panels = _build_weight_panels(state)
    timeline, turnover = _portfolio_timeline(returns, weight_panels)
    metrics = _metrics(timeline)
    yearly = _yearly_metrics(timeline)
    overall, classifications, details = _classify(metrics, yearly)
    _write_reports(timeline, turnover, metrics, yearly, overall, classifications, details)
    return {
        "monthly_observations": int(len(timeline)),
        "workflow_classifications": classifications,
        "overall_conclusion": overall,
        "status": "COMPLETE",
    }


if __name__ == "__main__":
    print(json.dumps(run_economic_validation(), indent=2))
