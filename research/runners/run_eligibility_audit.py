"""RC-A2 descriptive eligibility and rejection-region audit."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import backtrader as bt
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from config.settings import load_config
from data.yahoo_data import MarketDataRequest, YahooFinanceDataSource
from engine.backtest_engine import PandasOHLCVData
from main import build_strategy_params
from research.audit_strategies import LeadershipExpansionEligibilityAuditStrategy


FILTER_COLUMNS = [
    "relative_strength_pass", "leadership_quality_pass", "ema200_price_pass",
    "ema200_slope_pass", "ema50_price_pass", "atr_expansion_pass",
    "breakout_confirmation_pass",
]


def main() -> None:
    args = _args()
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    config = load_config(args.config)
    config.strategy_name = "leadership_expansion_v1"
    params = build_strategy_params(config)
    universe = pd.read_csv(args.universe).iloc[:, 0].dropna().astype(str).str.upper().tolist()
    source = YahooFinanceDataSource()
    benchmark = source.fetch(MarketDataRequest(config.benchmark_ticker, args.warmup_start, args.end, "1d"))
    records, errors = [], []

    for number, ticker in enumerate(universe, start=1):
        try:
            stock = source.fetch(MarketDataRequest(ticker, args.warmup_start, args.end, "1d"))
            rows = _audit_ticker(stock, benchmark, params, ticker)
            records.extend(rows)
        except Exception as exc:
            errors.append({"ticker": ticker, "error": repr(exc)})
        print(f"{number}/{len(universe)} {ticker}")

    candidates = pd.DataFrame(records)
    candidates["date"] = pd.to_datetime(candidates["date"])
    candidates = candidates.loc[(candidates["date"] >= pd.Timestamp(args.start)) & (candidates["date"] < pd.Timestamp(args.end))].copy()
    candidates.insert(0, "candidate_id", range(1, len(candidates) + 1))
    candidates.insert(2, "timeframe", "1d")
    candidates.to_csv(output / "candidate_signal_table.csv", index=False)

    eligibility = _eligibility_matrix(candidates)
    eligibility.to_csv(output / "eligibility_matrix.csv", index=False)
    profiles = _profiles(candidates)
    profiles.to_csv(output / "rejection_profiles.csv", index=False)
    ema_breakdown = _ema_breakdown(candidates, args.a1_dir)
    ema_breakdown.to_csv(output / "ema200_rejection_breakdown.csv", index=False)
    _cooccurrence(candidates).to_csv(output / "cooccurrence_matrix.csv", index=False)
    _segment_summary(candidates, candidates["date"].dt.year.rename("year")).to_csv(output / "yearly_eligibility.csv", index=False)
    _segment_summary(candidates, candidates["ticker"].rename("ticker")).to_csv(output / "symbol_eligibility.csv", index=False)
    summary = {
        "experiment_id": "RC-A2",
        "candidate_signals": int(len(candidates)),
        "accepted_candidates": int(candidates["accepted"].sum()),
        "rejected_candidates": int(candidates["rejected"].sum()),
        "source_universe_symbols": len(universe),
        "successful_symbols": len(universe) - len(errors),
        "failed_symbols": len(errors),
        "causal_conclusions": False,
        "scope": "Observational eligibility states only; no strategy performance comparison or ablation.",
    }
    (output / "eligibility_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    pd.DataFrame(errors).to_csv(output / "eligibility_errors.csv", index=False)
    _report(output / "eligibility_audit.md", summary, profiles, ema_breakdown, errors)


def _audit_ticker(stock, benchmark, params, ticker):
    cerebro = bt.Cerebro(stdstats=False)
    cerebro.adddata(PandasOHLCVData(dataname=stock))
    cerebro.adddata(PandasOHLCVData(dataname=benchmark))
    audit_params = dict(params)
    audit_params["skip_relative_strength_filter"] = ticker == "SPY"
    cerebro.addstrategy(LeadershipExpansionEligibilityAuditStrategy, **audit_params)
    strategy = cerebro.run()[0]
    return [{"ticker": ticker, **record} for record in strategy.candidate_records]


def _eligibility_matrix(candidates):
    rows = []
    for column in FILTER_COLUMNS:
        passed = int(candidates[column].sum())
        rows.append({"component": column.removesuffix("_pass").upper(), "pass_count": passed, "fail_count": int(len(candidates) - passed), "pass_pct": passed / len(candidates) * 100})
    rows.extend([
        {"component": "ALL_PRODUCTION_FILTERS", "pass_count": int(candidates.accepted.sum()), "fail_count": int(candidates.rejected.sum()), "pass_pct": candidates.accepted.mean() * 100},
    ])
    return pd.DataFrame(rows)


def _profiles(candidates):
    rejected = candidates.loc[candidates.rejected]
    result = rejected.groupby("failing_components").size().rename("candidate_count").reset_index()
    result["percent_of_rejected"] = result["candidate_count"] / len(rejected) * 100
    return result.sort_values(["candidate_count", "failing_components"], ascending=[False, True]).head(20)


def _ema_breakdown(candidates, a1_dir):
    rows = []
    classes = {
        "EMA200_PRICE_ONLY": (~candidates.ema200_price_pass) & candidates.ema200_slope_pass,
        "EMA200_SLOPE_ONLY": candidates.ema200_price_pass & (~candidates.ema200_slope_pass),
        "EMA200_BOTH": (~candidates.ema200_price_pass) & (~candidates.ema200_slope_pass),
        "EMA200_NEITHER": candidates.ema200_price_pass & candidates.ema200_slope_pass,
    }
    for label, mask in classes.items():
        rows.append({"population": "ALL_CANDIDATES", "ema200_state": label, "candidate_count": int(mask.sum())})

    e3_only, baseline_only = _a1_entry_differences(a1_dir)
    rows.append({"population": "RC_A1_NET_TRADE_COUNT_DIFFERENCE", "ema200_state": "NET_DIFFERENCE_NOT_A_TRADE_SET", "candidate_count": len(e3_only) - len(baseline_only)})
    rows.append({"population": "RC_A1_BASELINE_ONLY_ENTRIES", "ema200_state": "ENTRY_KEY_ONLY", "candidate_count": len(baseline_only)})
    if not e3_only.empty:
        keyed = candidates.copy()
        keyed["entry_time"] = keyed.groupby("ticker")["date"].shift(-1)
        matched = e3_only.merge(keyed[["ticker", "entry_time", "ema200_price_pass", "ema200_slope_pass"]], on=["ticker", "entry_time"], how="left")
        for label, mask in {
            "EMA200_PRICE_ONLY": (~matched.ema200_price_pass) & matched.ema200_slope_pass,
            "EMA200_SLOPE_ONLY": matched.ema200_price_pass & (~matched.ema200_slope_pass),
            "EMA200_BOTH": (~matched.ema200_price_pass) & (~matched.ema200_slope_pass),
            "EMA200_NEITHER": matched.ema200_price_pass & matched.ema200_slope_pass,
            "UNMATCHED": matched.ema200_price_pass.isna() | matched.ema200_slope_pass.isna(),
        }.items():
            rows.append({"population": "RC_A1_E3_ONLY_ENTRIES", "ema200_state": label, "candidate_count": int(mask.sum())})
    return pd.DataFrame(rows)


def _a1_entry_differences(a1_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    base = pd.read_csv(a1_dir / "RC-A1-E0_BASELINE_trades.csv", parse_dates=["entry_time"])
    joint = pd.read_csv(a1_dir / "RC-A1-E3_NO_EMA200_ARCHITECTURE_trades.csv", parse_dates=["entry_time"])
    keys = ["ticker", "entry_time"]
    baseline_keys = set(map(tuple, base[keys].itertuples(index=False, name=None)))
    joint_keys = set(map(tuple, joint[keys].itertuples(index=False, name=None)))
    e3_only = joint.loc[~joint[keys].apply(tuple, axis=1).isin(baseline_keys), keys].copy()
    baseline_only = base.loc[~base[keys].apply(tuple, axis=1).isin(joint_keys), keys].copy()
    return e3_only, baseline_only


def _cooccurrence(candidates):
    rows = []
    for left in FILTER_COLUMNS:
        for right in FILTER_COLUMNS:
            rows.append({"row_component": left.removesuffix("_pass").upper(), "column_component": right.removesuffix("_pass").upper(), "simultaneous_fail_count": int((~candidates[left] & ~candidates[right]).sum())})
    return pd.DataFrame(rows)


def _segment_summary(candidates, segments):
    copy = candidates.copy()
    copy[segments.name] = segments.values
    return copy.groupby(segments.name).agg(candidate_count=("candidate_id", "count"), accepted_count=("accepted", "sum"), rejected_count=("rejected", "sum")).reset_index()


def _report(path, summary, profiles, ema_breakdown, errors):
    lines = ["# RC-A2 Eligibility & Rejection Region Audit", "", "## Scope", "", "Observational eligibility states only. No ablation, performance comparison, ranking, or causal conclusion was performed.", "", "## Counts", "", json.dumps(summary, indent=2), "", "## Top Rejection Profiles", "", profiles.to_string(index=False), "", "## EMA200 Breakdown", "", ema_breakdown.to_string(index=False), "", "## Data Errors", "", str(len(errors))]
    path.write_text("\n".join(lines), encoding="utf-8")


def _args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--universe", type=Path, required=True)
    parser.add_argument("--a1-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--warmup-start", default="2009-01-01")
    parser.add_argument("--start", default="2010-01-01")
    parser.add_argument("--end", default="2026-01-01")
    parser.add_argument("--config", type=Path, default=None)
    return parser.parse_args()


if __name__ == "__main__":
    main()
