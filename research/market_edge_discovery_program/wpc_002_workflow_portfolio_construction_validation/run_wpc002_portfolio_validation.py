from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent

WPC001 = ROOT / "research" / "market_edge_discovery_program" / "wpc_001_workflow_portfolio_construction_protocol" / "wpc001_manifest.json"
CSM_STATE = ROOT / "output" / "csm_001_cv001" / "csm001_construct_state.csv"
TSM_STATE = ROOT / "output" / "tsm_001_cv001" / "tsm001_construct_state.csv"
CLOSE_PANEL = ROOT / "output" / "csm_001_cv001" / "adjusted_close_panel.csv"
OOS_START_AFTER = pd.Timestamp("2025-12-30")


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    close = pd.read_csv(CLOSE_PANEL, index_col=0, parse_dates=True)
    close.index = pd.to_datetime(close.index).tz_localize(None)
    csm = pd.read_csv(CSM_STATE, parse_dates=["date"])
    tsm = pd.read_csv(TSM_STATE, parse_dates=["date"], low_memory=False)
    states = csm[["date", "ticker", "csm001_top_decile_flag", "csm001_valid_observation"]].merge(
        tsm[["date", "ticker", "tsm001_positive_state", "tsm001_valid_observation"]],
        on=["date", "ticker"],
        how="inner",
        validate="one_to_one",
    )
    states["date"] = pd.to_datetime(states["date"]).dt.tz_localize(None)
    states = states[
        states["csm001_valid_observation"]
        & states["tsm001_valid_observation"]
        & states["date"].le(OOS_START_AFTER)
    ].copy()
    states["portfolio_group"] = np.where(
        states["csm001_top_decile_flag"] & states["tsm001_positive_state"],
        "workflow",
        np.where((~states["csm001_top_decile_flag"]) & states["tsm001_positive_state"], "benchmark", "other"),
    )
    return states, close


def build_rebalance_calendar(close: pd.DataFrame, first_signal_date: pd.Timestamp) -> pd.DataFrame:
    dates = pd.Series(close.index.sort_values(), name="date")
    valid = dates[dates.ge(first_signal_date) & dates.le(OOS_START_AFTER)].reset_index(drop=True)
    first_by_month = valid.groupby(valid.dt.to_period("M")).first().reset_index(drop=True)
    rows = []
    for i in range(len(first_by_month) - 1):
        signal = first_by_month.iloc[i]
        next_signal = first_by_month.iloc[i + 1]
        entry_candidates = valid[valid.gt(signal)]
        next_entry_candidates = valid[valid.gt(next_signal)]
        if entry_candidates.empty or next_entry_candidates.empty:
            continue
        entry = entry_candidates.iloc[0]
        next_entry = next_entry_candidates.iloc[0]
        exit_candidates = valid[valid.lt(next_entry)]
        exit_date = exit_candidates.iloc[-1] if not exit_candidates.empty else pd.NaT
        if pd.isna(exit_date) or exit_date <= entry:
            continue
        rows.append(
            {
                "period": str(signal.to_period("M")),
                "signal_date": signal,
                "entry_date": entry,
                "exit_date": exit_date,
                "next_signal_date": next_signal,
                "lookahead_ok": bool(entry > signal and exit_date > entry),
            }
        )
    return pd.DataFrame(rows)


def holdings_for(states: pd.DataFrame, calendar: pd.DataFrame, group: str) -> pd.DataFrame:
    rows = []
    for _, row in calendar.iterrows():
        day = states[(states["date"].eq(row["signal_date"])) & (states["portfolio_group"].eq(group))]
        tickers = sorted(day["ticker"].astype(str).unique())
        weight = 1.0 / len(tickers) if tickers else 0.0
        for ticker in tickers:
            rows.append(
                {
                    "period": row["period"],
                    "signal_date": row["signal_date"],
                    "entry_date": row["entry_date"],
                    "exit_date": row["exit_date"],
                    "ticker": ticker,
                    "weight": weight,
                    "portfolio_group": group,
                }
            )
    return pd.DataFrame(rows)


def attach_returns(holdings: pd.DataFrame, close: pd.DataFrame) -> pd.DataFrame:
    if holdings.empty:
        return holdings.assign(entry_price=np.nan, exit_price=np.nan, holding_return=np.nan)
    entry_prices = []
    exit_prices = []
    for _, row in holdings.iterrows():
        ticker = row["ticker"]
        entry = row["entry_date"]
        exit_date = row["exit_date"]
        entry_prices.append(close.at[entry, ticker] if ticker in close.columns and entry in close.index else np.nan)
        exit_prices.append(close.at[exit_date, ticker] if ticker in close.columns and exit_date in close.index else np.nan)
    result = holdings.copy()
    result["entry_price"] = entry_prices
    result["exit_price"] = exit_prices
    result["holding_return"] = result["exit_price"] / result["entry_price"] - 1.0
    return result


def portfolio_returns(calendar: pd.DataFrame, holdings: pd.DataFrame, group: str) -> pd.DataFrame:
    rows = []
    for _, row in calendar.iterrows():
        h = holdings[(holdings["period"].eq(row["period"])) & (holdings["portfolio_group"].eq(group))]
        valid = h.dropna(subset=["holding_return"])
        rows.append(
            {
                "period": row["period"],
                "signal_date": row["signal_date"],
                "entry_date": row["entry_date"],
                "exit_date": row["exit_date"],
                "portfolio_group": group,
                "holding_count": int(len(h)),
                "valid_return_count": int(len(valid)),
                "portfolio_return": float((valid["weight"] * valid["holding_return"]).sum()) if len(valid) else 0.0,
                "cash_period": bool(len(h) == 0),
            }
        )
    return pd.DataFrame(rows)


def accounting_checks(calendar: pd.DataFrame, workflow: pd.DataFrame, benchmark: pd.DataFrame, returns: pd.DataFrame) -> pd.DataFrame:
    checks = [
        ("calendar_non_empty", len(calendar) > 0),
        ("entry_after_signal", bool((calendar["entry_date"] > calendar["signal_date"]).all())),
        ("exit_after_entry", bool((calendar["exit_date"] > calendar["entry_date"]).all())),
        ("lookahead_ok", bool(calendar["lookahead_ok"].all())),
        ("workflow_holdings_exist", len(workflow) > 0),
        ("benchmark_holdings_exist", len(benchmark) > 0),
        ("workflow_missing_return_rate_lt_1pct", workflow["holding_return"].isna().mean() < 0.01 if len(workflow) else False),
        ("benchmark_missing_return_rate_lt_1pct", benchmark["holding_return"].isna().mean() < 0.01 if len(benchmark) else False),
        ("returns_generated", len(returns) > 0),
    ]
    return pd.DataFrame([{"check": k, "passed": bool(v)} for k, v in checks])


def position_count_analysis(returns: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for group, g in returns.groupby("portfolio_group"):
        rows.append(
            {
                "portfolio_group": group,
                "periods": int(len(g)),
                "mean_holding_count": float(g["holding_count"].mean()),
                "median_holding_count": float(g["holding_count"].median()),
                "min_holding_count": int(g["holding_count"].min()),
                "max_holding_count": int(g["holding_count"].max()),
            }
        )
    return pd.DataFrame(rows)


def cash_period_analysis(returns: pd.DataFrame) -> pd.DataFrame:
    return returns.groupby("portfolio_group").agg(
        periods=("period", "count"),
        cash_periods=("cash_period", "sum"),
        cash_period_rate=("cash_period", "mean"),
    ).reset_index()


def turnover_analysis(holdings: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for group, g in holdings.groupby("portfolio_group"):
        sets = g.groupby("period")["ticker"].apply(lambda s: frozenset(s.astype(str)))
        vals = []
        prev = None
        for current in sets:
            if prev is not None:
                union = len(prev | current)
                vals.append(1.0 - (len(prev & current) / union if union else 1.0))
            prev = current
        rows.append(
            {
                "portfolio_group": group,
                "transitions": len(vals),
                "mean_turnover_proxy": float(np.mean(vals)) if vals else np.nan,
                "median_turnover_proxy": float(np.median(vals)) if vals else np.nan,
            }
        )
    return pd.DataFrame(rows)


def missing_data_report(workflow: pd.DataFrame, benchmark: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for group, h in [("workflow", workflow), ("benchmark", benchmark)]:
        rows.append(
            {
                "portfolio_group": group,
                "holdings": int(len(h)),
                "missing_entry_price": int(h["entry_price"].isna().sum()),
                "missing_exit_price": int(h["exit_price"].isna().sum()),
                "missing_holding_return": int(h["holding_return"].isna().sum()),
                "missing_holding_return_rate": float(h["holding_return"].isna().mean()) if len(h) else np.nan,
            }
        )
    return pd.DataFrame(rows)


def gross_comparison(returns: pd.DataFrame) -> pd.DataFrame:
    pivot = returns.pivot(index="period", columns="portfolio_group", values="portfolio_return").reset_index()
    pivot["workflow_minus_benchmark"] = pivot["workflow"] - pivot["benchmark"]
    summary = pd.DataFrame(
        [
            {
                "periods": int(len(pivot)),
                "workflow_mean_return": float(pivot["workflow"].mean()),
                "benchmark_mean_return": float(pivot["benchmark"].mean()),
                "mean_spread": float(pivot["workflow_minus_benchmark"].mean()),
                "positive_spread_rate": float((pivot["workflow_minus_benchmark"] > 0).mean()),
                "workflow_compound_return": float((1.0 + pivot["workflow"]).prod() - 1.0),
                "benchmark_compound_return": float((1.0 + pivot["benchmark"]).prod() - 1.0),
            }
        ]
    )
    return summary


def classify(checks: pd.DataFrame, returns: pd.DataFrame) -> str:
    all_checks = bool(checks["passed"].all())
    no_cash = bool((returns["cash_period"] == False).all())
    if all_checks and no_cash:
        return "Portfolio Construction Supported"
    if all_checks:
        return "Portfolio Construction Partially Supported"
    return "Portfolio Construction Not Supported"


def write(name: str, text: str) -> None:
    (OUT / name).write_text(text.strip() + "\n", encoding="utf-8")


def build_reports(conclusion: str, calendar: pd.DataFrame, checks: pd.DataFrame, comparison: pd.DataFrame) -> None:
    comp = comparison.iloc[0]
    manifest = {
        "study_id": "WPC-002",
        "study_name": "Workflow Portfolio Construction Validation",
        "status": "Completed",
        "conclusion": conclusion,
        "rebalance_periods": int(len(calendar)),
        "accounting_checks_passed": bool(checks["passed"].all()),
        "gross_mean_spread": float(comp["mean_spread"]),
        "optimization_performed": False,
        "production_recommendation_performed": False,
        "cost_adjusted_accounting_performed": False,
    }
    (OUT / "wpc002_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    write(
        "executive_summary.md",
        f"""
# Executive Summary

WPC-002 validated gross monthly equal-weight portfolio construction for the UC-3 CSM-001 x TSM-001 workflow.

Final conclusion: **{conclusion}**.

Key evidence:

- Rebalance periods: {len(calendar)}
- Accounting checks passed: {checks['passed'].all()}
- Workflow mean monthly return: {comp['workflow_mean_return']:.6f}
- Benchmark mean monthly return: {comp['benchmark_mean_return']:.6f}
- Gross mean spread: {comp['mean_spread']:.6f}
- Positive spread rate: {comp['positive_spread_rate']:.4f}

This is gross research accounting only. It is not production deployment or cost-adjusted portfolio validation.
""",
    )
    write(
        "wpc002_portfolio_construction_validation.md",
        f"""
# WPC-002: Workflow Portfolio Construction Validation

## Purpose

Validate whether the UC-3 workflow can be converted into a deterministic monthly equal-weight research portfolio with auditable accounting.

## Final Conclusion

**{conclusion}**

## Accounting Rule Implemented

- Signal date: first trading day of each calendar month.
- Entry date: next trading day after signal date.
- Exit date: trading day immediately before the next entry date.
- Portfolio return: equal-weight mean of selected holding returns.
- Cash return: 0% if no holdings exist.

## Evidence Classification

Supported by evidence:

- Rebalance calendar was constructed deterministically.
- Entry dates occur after signal dates.
- Exit dates occur after entry dates.
- Workflow and benchmark use identical timing.
- Gross portfolio return series was generated.

Not supported:

- Production deployment.
- Cost-adjusted portfolio performance.
- Portfolio optimization.

## Outputs

- `rebalance_calendar.csv`
- `workflow_holdings.csv`
- `benchmark_holdings.csv`
- `portfolio_return_series.csv`
- `portfolio_accounting_checks.csv`
- `position_count_analysis.csv`
- `cash_period_analysis.csv`
- `turnover_analysis.csv`
- `missing_data_report.csv`
- `gross_benchmark_comparison.csv`
""",
    )
    write(
        "limitations.md",
        """
# Limitations

- WPC-002 validates gross accounting only.
- Costs, slippage, taxes, capacity and live execution are not included in portfolio returns.
- The universe remains current-constituent based.
- No max position limit is imposed.
- Results do not authorize production deployment.
""",
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with open(WPC001, encoding="utf-8") as f:
        protocol = json.load(f)
    if protocol.get("authorized_next_stage") != "WPC-002":
        raise RuntimeError("WPC-001 did not authorize WPC-002.")
    states, close = load_inputs()
    calendar = build_rebalance_calendar(close, states["date"].min())
    workflow = attach_returns(holdings_for(states, calendar, "workflow"), close)
    benchmark = attach_returns(holdings_for(states, calendar, "benchmark"), close)
    holdings = pd.concat([workflow, benchmark], ignore_index=True)
    returns = pd.concat([portfolio_returns(calendar, workflow, "workflow"), portfolio_returns(calendar, benchmark, "benchmark")], ignore_index=True)
    checks = accounting_checks(calendar, workflow, benchmark, returns)
    positions = position_count_analysis(returns)
    cash = cash_period_analysis(returns)
    turnover = turnover_analysis(holdings)
    missing = missing_data_report(workflow, benchmark)
    comparison = gross_comparison(returns)
    conclusion = classify(checks, returns)

    calendar.to_csv(OUT / "rebalance_calendar.csv", index=False)
    workflow.to_csv(OUT / "workflow_holdings.csv", index=False)
    benchmark.to_csv(OUT / "benchmark_holdings.csv", index=False)
    returns.to_csv(OUT / "portfolio_return_series.csv", index=False)
    checks.to_csv(OUT / "portfolio_accounting_checks.csv", index=False)
    positions.to_csv(OUT / "position_count_analysis.csv", index=False)
    cash.to_csv(OUT / "cash_period_analysis.csv", index=False)
    turnover.to_csv(OUT / "turnover_analysis.csv", index=False)
    missing.to_csv(OUT / "missing_data_report.csv", index=False)
    comparison.to_csv(OUT / "gross_benchmark_comparison.csv", index=False)
    build_reports(conclusion, calendar, checks, comparison)


if __name__ == "__main__":
    main()
