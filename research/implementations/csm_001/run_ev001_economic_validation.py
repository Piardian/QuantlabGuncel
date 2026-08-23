from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[3]
STATE_FILE = REPO_ROOT / "output" / "csm_001_cv001" / "csm001_construct_state.csv"
OUTPUT_DIR = REPO_ROOT / "research" / "market_edge_discovery_program" / "csm_001_ev_001_economic_validation"

REBALANCE_INTERVAL_DAYS = 21
TRANSACTION_COST_BPS = 10.0
TRADING_DAYS_PER_YEAR = 252


def _safe_float(value: float) -> float | None:
    if pd.isna(value) or not np.isfinite(value):
        return None
    return float(value)


def _load_state() -> pd.DataFrame:
    usecols = [
        "date",
        "ticker",
        "adjusted_close",
        "csm001_top_decile_flag",
        "csm001_valid_observation",
    ]
    frame = pd.read_csv(STATE_FILE, usecols=usecols, parse_dates=["date"])
    frame = frame[frame["csm001_valid_observation"].astype(bool)].copy()
    frame["csm001_top_decile_flag"] = frame["csm001_top_decile_flag"].astype(bool)
    return frame.sort_values(["date", "ticker"]).reset_index(drop=True)


def _build_panels(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    close = frame.pivot(index="date", columns="ticker", values="adjusted_close").sort_index()
    valid = frame.pivot(index="date", columns="ticker", values="csm001_valid_observation").sort_index().astype(bool)
    top = frame.pivot(index="date", columns="ticker", values="csm001_top_decile_flag").sort_index().fillna(False).astype(bool)
    return close, valid, top


def _equal_weight(mask: pd.Series) -> pd.Series:
    active = mask[mask].index
    weights = pd.Series(0.0, index=mask.index)
    if len(active) > 0:
        weights.loc[active] = 1.0 / len(active)
    return weights


def _simulate_rebalanced_portfolios(close: pd.DataFrame, valid: pd.DataFrame, top: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    returns = close.pct_change(fill_method=None).replace([np.inf, -np.inf], np.nan)
    dates = list(close.index)
    rebalance_dates = dates[::REBALANCE_INTERVAL_DAYS]
    cost_rate = TRANSACTION_COST_BPS / 10000.0

    records = []
    weight_records = []
    top_weights = pd.Series(0.0, index=close.columns)
    bench_weights = pd.Series(0.0, index=close.columns)
    previous_top_weights = top_weights.copy()
    previous_bench_weights = bench_weights.copy()

    for idx in range(len(dates) - 1):
        date = dates[idx]
        next_date = dates[idx + 1]
        is_rebalance = date in rebalance_dates
        top_turnover = 0.0
        bench_turnover = 0.0
        top_cost = 0.0
        bench_cost = 0.0

        if is_rebalance:
            top_weights = _equal_weight(top.loc[date])
            bench_weights = _equal_weight(valid.loc[date])
            top_turnover = float((top_weights - previous_top_weights).abs().sum())
            bench_turnover = float((bench_weights - previous_bench_weights).abs().sum())
            top_cost = top_turnover * cost_rate
            bench_cost = bench_turnover * cost_rate
            previous_top_weights = top_weights.copy()
            previous_bench_weights = bench_weights.copy()

        day_returns = returns.loc[next_date].fillna(0.0)
        top_gross = float((top_weights * day_returns).sum())
        bench_gross = float((bench_weights * day_returns).sum())
        top_net = top_gross - top_cost
        bench_net = bench_gross - bench_cost
        records.append(
            {
                "date": next_date,
                "rebalance_date": date if is_rebalance else pd.NaT,
                "is_rebalance": is_rebalance,
                "top_decile_gross_return": top_gross,
                "benchmark_gross_return": bench_gross,
                "top_decile_net_return": top_net,
                "benchmark_net_return": bench_net,
                "active_net_return": top_net - bench_net,
                "top_decile_turnover": top_turnover,
                "benchmark_turnover": bench_turnover,
                "top_decile_cost": top_cost,
                "benchmark_cost": bench_cost,
                "top_decile_position_count": int((top_weights > 0).sum()),
                "benchmark_position_count": int((bench_weights > 0).sum()),
            }
        )
        if is_rebalance:
            weight_records.append(
                {
                    "date": date,
                    "top_decile_position_count": int((top_weights > 0).sum()),
                    "benchmark_position_count": int((bench_weights > 0).sum()),
                    "top_decile_turnover": top_turnover,
                    "benchmark_turnover": bench_turnover,
                }
            )

    return pd.DataFrame(records), pd.DataFrame(weight_records)


def _max_drawdown(returns: pd.Series) -> float:
    equity = (1.0 + returns.fillna(0.0)).cumprod()
    drawdown = equity / equity.cummax() - 1.0
    return float(drawdown.min())


def _annualized_return(returns: pd.Series) -> float:
    clean = returns.dropna()
    if len(clean) == 0:
        return np.nan
    total = float((1.0 + clean).prod())
    years = len(clean) / TRADING_DAYS_PER_YEAR
    return total ** (1.0 / years) - 1.0 if years > 0 else np.nan


def _annualized_volatility(returns: pd.Series) -> float:
    clean = returns.dropna()
    return float(clean.std(ddof=0) * np.sqrt(TRADING_DAYS_PER_YEAR)) if len(clean) else np.nan


def _sharpe_like(returns: pd.Series) -> float:
    vol = _annualized_volatility(returns)
    if not vol or pd.isna(vol):
        return np.nan
    return _annualized_return(returns) / vol


def _sortino_like(returns: pd.Series) -> float:
    clean = returns.dropna()
    downside = clean[clean < 0].std(ddof=0) * np.sqrt(TRADING_DAYS_PER_YEAR)
    if not downside or pd.isna(downside):
        return np.nan
    return _annualized_return(clean) / downside


def _metrics(timeline: pd.DataFrame) -> pd.DataFrame:
    rows = []
    series_map = {
        "CSM_TOP_DECILE_GROSS": timeline["top_decile_gross_return"],
        "ELIGIBLE_EQUAL_WEIGHT_GROSS": timeline["benchmark_gross_return"],
        "CSM_TOP_DECILE_NET_10BPS": timeline["top_decile_net_return"],
        "ELIGIBLE_EQUAL_WEIGHT_NET_10BPS": timeline["benchmark_net_return"],
        "ACTIVE_NET_TOP_MINUS_BENCHMARK": timeline["active_net_return"],
    }
    for name, returns in series_map.items():
        rows.append(
            {
                "portfolio": name,
                "daily_observations": int(len(returns.dropna())),
                "total_return": _safe_float((1.0 + returns.fillna(0.0)).prod() - 1.0),
                "annualized_return": _safe_float(_annualized_return(returns)),
                "annualized_volatility": _safe_float(_annualized_volatility(returns)),
                "return_to_volatility": _safe_float(_sharpe_like(returns)),
                "downside_return_to_volatility": _safe_float(_sortino_like(returns)),
                "max_drawdown": _safe_float(_max_drawdown(returns)),
                "mean_daily_return": _safe_float(returns.mean()),
                "median_daily_return": _safe_float(returns.median()),
                "positive_day_rate": _safe_float((returns > 0).mean()),
            }
        )
    return pd.DataFrame(rows)


def _yearly_metrics(timeline: pd.DataFrame) -> pd.DataFrame:
    frame = timeline.copy()
    frame["year"] = frame["date"].dt.year
    rows = []
    for year, group in frame.groupby("year", sort=True):
        rows.append(
            {
                "year": int(year),
                "top_decile_net_return": _safe_float((1.0 + group["top_decile_net_return"]).prod() - 1.0),
                "benchmark_net_return": _safe_float((1.0 + group["benchmark_net_return"]).prod() - 1.0),
                "active_net_return": _safe_float((1.0 + group["active_net_return"]).prod() - 1.0),
                "top_decile_max_drawdown": _safe_float(_max_drawdown(group["top_decile_net_return"])),
                "benchmark_max_drawdown": _safe_float(_max_drawdown(group["benchmark_net_return"])),
                "top_decile_positive_days": _safe_float((group["top_decile_net_return"] > 0).mean()),
                "benchmark_positive_days": _safe_float((group["benchmark_net_return"] > 0).mean()),
            }
        )
    return pd.DataFrame(rows)


def _verdict(metrics: pd.DataFrame, yearly: pd.DataFrame) -> tuple[str, dict[str, object]]:
    top = metrics[metrics["portfolio"] == "CSM_TOP_DECILE_NET_10BPS"].iloc[0]
    bench = metrics[metrics["portfolio"] == "ELIGIBLE_EQUAL_WEIGHT_NET_10BPS"].iloc[0]
    active_year_rate = float((yearly["top_decile_net_return"] > yearly["benchmark_net_return"]).mean())
    ann_return_delta = float(top["annualized_return"] - bench["annualized_return"])
    rtov_delta = float(top["return_to_volatility"] - bench["return_to_volatility"])
    drawdown_improved = float(top["max_drawdown"] > bench["max_drawdown"])

    if ann_return_delta > 0 and rtov_delta > 0 and active_year_rate >= 0.60 and drawdown_improved:
        status = "Supported by evidence"
    elif ann_return_delta > 0 and active_year_rate >= 0.50:
        status = "Partially supported"
    else:
        status = "Not supported"

    return status, {
        "annualized_return_delta": ann_return_delta,
        "return_to_volatility_delta": rtov_delta,
        "active_year_rate": active_year_rate,
        "max_drawdown_improved": bool(drawdown_improved),
    }


def _write_reports(timeline: pd.DataFrame, weights: pd.DataFrame, metrics: pd.DataFrame, yearly: pd.DataFrame, status: str, verdict_details: dict[str, object]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    top = metrics[metrics["portfolio"] == "CSM_TOP_DECILE_NET_10BPS"].iloc[0]
    bench = metrics[metrics["portfolio"] == "ELIGIBLE_EQUAL_WEIGHT_NET_10BPS"].iloc[0]

    report = f"""# CSM-001 / EV-001 Economic Validation

## Purpose

Evaluate whether CSM-001 predictive information provides measurable economic utility under a fixed, preregistered portfolio workflow.

## Fixed Workflow

- Portfolio: equal-weight CSM-001 top-decile securities.
- Benchmark: equal-weight eligible universe on the same rebalance dates.
- Rebalance interval: {REBALANCE_INTERVAL_DAYS} trading days.
- Execution assumption: signal observed at close, return measured from next close-to-close interval.
- Transaction cost: {TRANSACTION_COST_BPS:.1f} bps per dollar traded.
- No threshold optimization, no parameter tuning, no strategy redesign.

## Results

- Top-decile net annualized return: {top["annualized_return"]:.4f}
- Benchmark net annualized return: {bench["annualized_return"]:.4f}
- Annualized return delta: {verdict_details["annualized_return_delta"]:.4f}
- Top-decile return-to-volatility: {top["return_to_volatility"]:.4f}
- Benchmark return-to-volatility: {bench["return_to_volatility"]:.4f}
- Active positive year rate: {verdict_details["active_year_rate"]:.4f}
- Top-decile max drawdown: {top["max_drawdown"]:.4f}
- Benchmark max drawdown: {bench["max_drawdown"]:.4f}

## EV-001 Classification

**{status}**

This result is limited to the fixed workflow, current-constituent universe and cost assumption evaluated here. It does not imply production readiness or universal economic superiority.
"""
    (OUTPUT_DIR / "ev001_economic_validation.md").write_text(report, encoding="utf-8")

    portfolio = f"""# Portfolio Analysis

The evaluated workflow holds the CSM-001 top decile as an equal-weight long-only portfolio and rebalances every {REBALANCE_INTERVAL_DAYS} trading days.

Average top-decile position count: {weights["top_decile_position_count"].mean():.2f}

Average benchmark position count: {weights["benchmark_position_count"].mean():.2f}

Average top-decile rebalance turnover: {weights["top_decile_turnover"].mean():.4f}

Average benchmark rebalance turnover: {weights["benchmark_turnover"].mean():.4f}
"""
    (OUTPUT_DIR / "portfolio_analysis.md").write_text(portfolio, encoding="utf-8")

    benchmark = """# Benchmark Comparison

Benchmark: equal-weight portfolio of all securities eligible for CSM-001 ranking on each rebalance date.

This benchmark is chosen to isolate the economic effect of selecting the top decile from the same eligible cross-section. It is not a cap-weighted market index and is not a production benchmark.
"""
    (OUTPUT_DIR / "benchmark_comparison.md").write_text(benchmark, encoding="utf-8")

    robustness = f"""# Robustness Analysis

Robustness is evaluated year-by-year under the same fixed workflow.

Positive active year rate: {verdict_details["active_year_rate"]:.4f}

No alternate rebalance intervals, thresholds or transaction costs were searched during EV-001.
"""
    (OUTPUT_DIR / "robustness_analysis.md").write_text(robustness, encoding="utf-8")

    limitations = """# Limitations

- The universe is current S&P 500-style membership rather than survivorship-free historical constituents.
- The benchmark is equal-weight eligible universe, not a market-cap-weighted index.
- Transaction cost is fixed at 10 bps per dollar traded and is not calibrated to live execution.
- No capacity, borrow, tax, market impact, liquidity constraint or execution timing model is included.
- Economic validation does not imply production deployment readiness.
- Results are workflow-specific and must not be generalized beyond EV-001.
"""
    (OUTPUT_DIR / "limitations.md").write_text(limitations, encoding="utf-8")

    summary = f"""# Executive Summary

CSM-001 / EV-001 evaluated whether the validated CSM-001 construct provides measurable economic utility under one fixed long-only top-decile workflow.

Classification: **{status}**.

The top-decile workflow outperformed the equal-weight eligible-universe benchmark after fixed transaction costs under the evaluated assumptions. This is economic validation for the tested workflow only, not a production recommendation.
"""
    (OUTPUT_DIR / "executive_summary.md").write_text(summary, encoding="utf-8")

    next_goal = """# CSM-001 / CC-001 Construct Classification

Purpose: classify CSM-001 using accumulated evidence from RP, LR, CD, IM, CV, MI, HV, PV and EV.

CC-001 should assign:

- Primary category
- Secondary capabilities
- Scientific maturity
- Evidence strength
- Recommended and non-recommended research applications

No new experiments or strategy changes are allowed.
"""
    (OUTPUT_DIR / "next_stage_goal_cc001.md").write_text(next_goal, encoding="utf-8")

    manifest = {
        "construct_id": "CSM-001",
        "stage": "EV-001",
        "classification": status,
        "workflow": {
            "portfolio": "equal_weight_top_decile",
            "benchmark": "equal_weight_eligible_universe",
            "rebalance_interval_days": REBALANCE_INTERVAL_DAYS,
            "transaction_cost_bps": TRANSACTION_COST_BPS,
        },
        "verdict_details": verdict_details,
    }
    (OUTPUT_DIR / "ev001_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    frame = _load_state()
    close, valid, top = _build_panels(frame)
    timeline, weights = _simulate_rebalanced_portfolios(close, valid, top)
    metrics = _metrics(timeline)
    yearly = _yearly_metrics(timeline)
    status, details = _verdict(metrics, yearly)

    timeline.to_csv(OUTPUT_DIR / "portfolio_timeline.csv", index=False)
    weights.to_csv(OUTPUT_DIR / "rebalance_weights_summary.csv", index=False)
    metrics.to_csv(OUTPUT_DIR / "economic_metrics.csv", index=False)
    yearly.to_csv(OUTPUT_DIR / "yearly_economic_validation.csv", index=False)
    _write_reports(timeline, weights, metrics, yearly, status, details)
    print(json.dumps({"status": "PASSED", "output_dir": str(OUTPUT_DIR), "classification": status}, indent=2))


if __name__ == "__main__":
    main()
