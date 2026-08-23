"""Adversarial audit of current exit behaviour using the frozen master dataset."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
import pandas as pd


OUTLIER_LEVELS = [0.01, 0.05, 0.10]


def main() -> None:
    args = _args()
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    trades = pd.read_csv(args.trades)
    trades = _prepare(trades)
    winners = trades[trades["R_multiple"] > 0]
    losers = trades[trades["R_multiple"] < 0]

    mae = _excursion_analysis(trades, "mae", winners, losers)
    mfe = _excursion_analysis(trades, "mfe", winners, losers)
    holding = _holding_analysis(trades)
    retention = _retention_analysis(trades)
    exits = _exit_analysis(trades)
    time_profit = _unavailable_time_file("time_to_profit", "Per-bar MFE path was not recorded in the master journal.")
    time_failure = _unavailable_time_file("time_to_failure", "Per-bar MAE path and stop-hit timestamps were not recorded in the master journal.")
    stability = _stability(trades)
    outliers = _outlier_audit(trades)

    mae.to_csv(out / "mae_analysis.csv", index=False)
    mfe.to_csv(out / "mfe_analysis.csv", index=False)
    holding.to_csv(out / "holding_duration_analysis.csv", index=False)
    retention.to_csv(out / "profit_retention_analysis.csv", index=False)
    exits.to_csv(out / "exit_reason_analysis.csv", index=False)
    time_profit.to_csv(out / "time_to_profit_analysis.csv", index=False)
    time_failure.to_csv(out / "time_to_failure_analysis.csv", index=False)
    stability.to_csv(out / "lifecycle_stability.csv", index=False)
    outliers.to_csv(out / "outlier_audit.csv", index=False)
    summary = _summary(trades, retention, exits, stability, outliers)
    summary.to_csv(out / "trade_lifecycle_summary.csv", index=False)
    _report(out / "trade_lifecycle_research.md", args.trades, summary, retention, exits, stability, outliers)
    print(out / "trade_lifecycle_research.md")


def _args():
    p = argparse.ArgumentParser()
    p.add_argument("--trades", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    return p.parse_args()


def _prepare(frame):
    result = frame.copy()
    for col in ["R_multiple", "mae", "mfe", "holding_days", "pnl_dollars"]:
        result[col] = pd.to_numeric(result[col], errors="coerce") if col in result else np.nan
    result["entry_time"] = pd.to_datetime(result.get("entry_time"), errors="coerce")
    result["year"] = result["entry_time"].dt.year
    result["profit_retention_ratio"] = np.where(result["mfe"] > 0, result["R_multiple"] / result["mfe"], np.nan)
    return result.dropna(subset=["R_multiple"])


def _excursion_analysis(trades, field, winners, losers):
    rows = []
    for label, group in [("ALL", trades), ("WINNERS", winners), ("LOSERS", losers)]:
        values = group[field].dropna()
        rows.append({"metric": field.upper(), "horizon": "FINAL_TRADE_LIFECYCLE", "group": label, "trade_count": len(values), "mean_R": values.mean() if len(values) else None, "median_R": values.median() if len(values) else None, "p25_R": values.quantile(.25) if len(values) else None, "p75_R": values.quantile(.75) if len(values) else None, "missing_pct": group[field].isna().mean()*100 if len(group) else None})
    for horizon in [1, 3, 5, 10]:
        rows.append({"metric": field.upper(), "horizon": f"{horizon}_BARS", "group": "UNAVAILABLE_IN_MASTER_DATASET", "trade_count": None, "mean_R": None, "median_R": None, "p25_R": None, "p75_R": None, "missing_pct": None})
    return pd.DataFrame(rows)


def _holding_analysis(trades):
    groups = {
        "WINNERS": trades[trades.R_multiple > 0],
        "LOSERS": trades[trades.R_multiple < 0],
        "LARGE_WINNERS_TOP20": trades[trades.R_multiple >= trades.R_multiple.quantile(.8)],
        "SMALL_WINNERS_BOTTOM20_POSITIVE": trades[(trades.R_multiple > 0) & (trades.R_multiple <= trades.loc[trades.R_multiple > 0, "R_multiple"].quantile(.2))],
        "LARGE_LOSERS_BOTTOM20": trades[trades.R_multiple <= trades.R_multiple.quantile(.2)],
    }
    return pd.DataFrame([_basic_row("holding_days", name, group["holding_days"]) for name, group in groups.items()])


def _retention_analysis(trades):
    groups = {
        "ALL_WITH_POSITIVE_MFE": trades[trades.mfe > 0],
        "WINNERS": trades[(trades.R_multiple > 0) & (trades.mfe > 0)],
        "LOSERS_WITH_POSITIVE_MFE": trades[(trades.R_multiple < 0) & (trades.mfe > 0)],
    }
    rows = []
    for name, group in groups.items():
        values = group.profit_retention_ratio.dropna()
        rows.append({"group": name, "trade_count": len(values), "mean_retention_ratio": values.mean() if len(values) else None, "median_retention_ratio": values.median() if len(values) else None, "p25_retention_ratio": values.quantile(.25) if len(values) else None, "p75_retention_ratio": values.quantile(.75) if len(values) else None, "negative_retention_pct": (values < 0).mean()*100 if len(values) else None})
    return pd.DataFrame(rows)


def _exit_analysis(trades):
    rows = []
    for reason, group in trades.groupby("exit_reason", dropna=False):
        r = group.R_multiple.dropna()
        rows.append({"exit_reason": str(reason), "trade_count": len(group), "win_rate": (r > 0).mean()*100 if len(r) else None, "avg_R": r.mean() if len(r) else None, "median_R": r.median() if len(r) else None, "profit_factor": _pf(r), "expectancy": r.mean() if len(r) else None, "mean_holding_days": group.holding_days.mean(), "median_holding_days": group.holding_days.median()})
    return pd.DataFrame(rows).sort_values("trade_count", ascending=False)


def _stability(trades):
    rows = []
    for year, group in trades.groupby("year", dropna=True):
        rows.append(_stability_row("YEAR", str(int(year)), group))
    for ticker, group in trades.groupby("ticker", dropna=True):
        rows.append(_stability_row("TICKER", str(ticker), group))
    return pd.DataFrame(rows)


def _stability_row(kind, label, group):
    win = group[group.R_multiple > 0]
    retention = group.loc[group.mfe > 0, "profit_retention_ratio"].dropna()
    return {"dimension": kind, "segment": label, "trade_count": len(group), "avg_R": group.R_multiple.mean(), "win_rate": (group.R_multiple > 0).mean()*100, "median_R": group.R_multiple.median(), "median_retention_ratio": retention.median() if len(retention) else None, "avg_holding_days": group.holding_days.mean(), "sample_sufficient": len(group) >= 30}


def _outlier_audit(trades):
    rows = []
    winners = trades[trades.R_multiple > 0]
    baseline = _aggregate_metrics(trades)
    rows.append({"removal": "NONE", "trades_remaining": len(trades), **baseline})
    for level in OUTLIER_LEVELS:
        cutoff = winners.R_multiple.quantile(1-level)
        trimmed = trades[~((trades.R_multiple > 0) & (trades.R_multiple >= cutoff))]
        metrics = _aggregate_metrics(trimmed)
        rows.append({"removal": f"TOP_{int(level*100)}_PCT_WINNERS", "trades_remaining": len(trimmed), "removed_winners": int(len(trades)-len(trimmed)), "cutoff_R": cutoff, **metrics})
    return pd.DataFrame(rows)


def _aggregate_metrics(trades):
    r = trades.R_multiple
    retention = trades.loc[trades.mfe > 0, "profit_retention_ratio"].dropna()
    return {"avg_R": r.mean(), "median_R": r.median(), "profit_factor": _pf(r), "win_rate": (r > 0).mean()*100, "median_retention_ratio": retention.median() if len(retention) else None}


def _basic_row(metric, group, values):
    values = values.dropna()
    return {"metric": metric, "group": group, "trade_count": len(values), "mean": values.mean() if len(values) else None, "median": values.median() if len(values) else None, "p25": values.quantile(.25) if len(values) else None, "p75": values.quantile(.75) if len(values) else None}


def _unavailable_time_file(metric, limitation):
    return pd.DataFrame([{"metric": metric, "status": "UNAVAILABLE_IN_MASTER_DATASET", "reason": limitation}])


def _pf(values):
    profit = float(values[values > 0].sum())
    loss = abs(float(values[values < 0].sum()))
    return profit/loss if loss else (math.inf if profit else 0.0)


def _summary(trades, retention, exits, stability, outliers):
    all_retention = retention[retention.group == "ALL_WITH_POSITIVE_MFE"]
    base = outliers.iloc[0]
    trim10 = outliers[outliers.removal == "TOP_10_PCT_WINNERS"].iloc[0]
    return pd.DataFrame([{
        "total_trades": len(trades), "avg_R": trades.R_multiple.mean(), "win_rate": (trades.R_multiple > 0).mean()*100,
        "median_profit_retention": all_retention.median_retention_ratio.iloc[0] if not all_retention.empty else None,
        "exit_reasons": exits.exit_reason.nunique(), "years_with_trades": stability[stability.dimension == "YEAR"].segment.nunique(),
        "tickers_with_trades": stability[stability.dimension == "TICKER"].segment.nunique(),
        "avg_R_after_top10pct_winner_removal": trim10.avg_R, "profit_factor_after_top10pct_winner_removal": trim10.profit_factor,
        "outlier_dependence": "HIGH" if trim10.avg_R <= 0 or trim10.profit_factor <= 1 else "NOT_CONFIRMED",
        "time_path_data": "UNAVAILABLE_IN_MASTER_DATASET",
        "conclusion": "Requires More Data",
    }])


def _report(path, source, summary, retention, exits, stability, outliers):
    lines = ["# Trade Lifecycle & Exit Attribution Audit", "", f"Source: `{source}`", "", "This audit measures current lifecycle behaviour only. It does not prove entry edge or that an alternative exit would be better.", "", "## Summary", "", summary.to_string(index=False), "", "## Profit Retention", "", retention.to_string(index=False), "", "## Exit Attribution", "", exits.to_string(index=False), "", "## Outlier Audit", "", outliers.to_string(index=False), "", "## Dataset Limitations", "", "- Entry-to-bar path data is not in the master journal, so 1/3/5/10 bar excursions and time-to-threshold statistics are unavailable.", "- Intrabar order of MFE/MAE cannot be inferred from final lifecycle extrema.", "- Attribution is descriptive; it does not establish causality or prescribe a replacement exit.", "- Per-symbol independent backtests are not a shared-account portfolio replay."]
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
