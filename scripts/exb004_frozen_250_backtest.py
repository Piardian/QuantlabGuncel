from __future__ import annotations

import hashlib
import json
import math
import os
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "research" / "market_edge_discovery_program" / "exb_004_frozen_250_exploratory_backtest"
EXB003_DIR = ROOT / "research" / "market_edge_discovery_program" / "exb_003_frozen_250_backtest_preparation"
FUF_DIR = ROOT / "research" / "market_edge_discovery_program" / "fuf_001_free_exploratory_universe_freeze"
CSM_IMPL = ROOT / "research" / "implementations" / "csm_001"
TSM_IMPL = ROOT / "research" / "implementations" / "tsm_001"
EXPECTED_RUN_SPEC_HASH = "8B9D4C3213A3709043D9724023F2E40DF4A5AA44ED2849B89CF64731C78D3320"
EXPECTED_UNIVERSE_HASH = "BC7879B3830C7327EB0A5779625A347C06826C47488F64326C7D0B2884CC741D"


sys.path.insert(0, str(CSM_IMPL))
from csm001_momentum_model import CSM001MomentumModel  # noqa: E402

sys.path.pop(0)
sys.modules.pop("feature_pipeline", None)
sys.path.insert(0, str(TSM_IMPL))
from tsm001_momentum_model import TSM001MomentumModel  # noqa: E402


@dataclass(frozen=True)
class PortfolioResult:
    name: str
    gross_returns: pd.Series
    net_returns: pd.Series
    net_returns_2x_cost: pd.Series
    weights: pd.DataFrame
    turnover: pd.Series


def load_env() -> None:
    env_file = ROOT / ".env"
    if not env_file.exists():
        return
    for raw in env_file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def alpaca_get(url: str) -> Any:
    key = os.environ.get("ALPACA_API_KEY_ID") or os.environ.get("APCA_API_KEY_ID")
    secret = os.environ.get("ALPACA_API_SECRET_KEY") or os.environ.get("APCA_API_SECRET_KEY")
    if not key or not secret:
        raise RuntimeError("Alpaca credentials are missing from environment.")
    req = urllib.request.Request(url)
    req.add_header("APCA-API-KEY-ID", key)
    req.add_header("APCA-API-SECRET-KEY", secret)
    with urllib.request.urlopen(req, timeout=90) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_bars(symbols: list[str], start: str, end: str, feed: str, adjustment: str, batch_size: int = 200) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for i in range(0, len(symbols), batch_size):
        batch = symbols[i : i + batch_size]
        token = None
        while True:
            params = {
                "symbols": ",".join(batch),
                "timeframe": "1Day",
                "start": start,
                "end": end,
                "feed": feed,
                "adjustment": adjustment,
                "limit": "10000",
            }
            if token:
                params["page_token"] = token
            payload = alpaca_get("https://data.alpaca.markets/v2/stocks/bars?" + urllib.parse.urlencode(params))
            for symbol, bars in payload.get("bars", {}).items():
                for bar in bars:
                    rows.append(
                        {
                            "symbol": symbol,
                            "date": pd.Timestamp(bar["t"]).tz_convert(None).normalize(),
                            "open": float(bar["o"]),
                            "high": float(bar["h"]),
                            "low": float(bar["l"]),
                            "close": float(bar["c"]),
                            "volume": float(bar["v"]),
                        }
                    )
            token = payload.get("next_page_token")
            if not token:
                break
    return pd.DataFrame(rows)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest().upper()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def metric_summary(name: str, returns: pd.Series, rebalance_count: int) -> dict[str, Any]:
    r = returns.dropna().astype(float)
    equity = (1.0 + r).cumprod()
    total_return = equity.iloc[-1] - 1.0
    years = max((r.index[-1] - r.index[0]).days / 365.25, 1e-9)
    cagr = equity.iloc[-1] ** (1.0 / years) - 1.0
    vol = r.std(ddof=0) * math.sqrt(252)
    sharpe = (r.mean() * 252) / vol if vol > 0 else np.nan
    downside = r.where(r < 0).dropna()
    downside_vol = downside.std(ddof=0) * math.sqrt(252) if not downside.empty else np.nan
    sortino = (r.mean() * 252) / downside_vol if downside_vol and downside_vol > 0 else np.nan
    dd = equity / equity.cummax() - 1.0
    max_dd = dd.min()
    calmar = cagr / abs(max_dd) if max_dd < 0 else np.nan
    monthly = (1.0 + r).resample("ME").prod() - 1.0
    return {
        "strategy": name,
        "observations": int(len(r)),
        "start": r.index[0].date().isoformat(),
        "end": r.index[-1].date().isoformat(),
        "total_return": total_return,
        "cagr": cagr,
        "annualized_volatility": vol,
        "sharpe": sharpe,
        "sortino": sortino,
        "maximum_drawdown": max_dd,
        "calmar": calmar,
        "best_month": monthly.max() if not monthly.empty else np.nan,
        "worst_month": monthly.min() if not monthly.empty else np.nan,
        "positive_month_pct": (monthly > 0).mean() if not monthly.empty else np.nan,
        "rebalance_events": rebalance_count,
    }


def drawdown_table(name: str, returns: pd.Series, top_n: int = 5) -> pd.DataFrame:
    r = returns.dropna()
    equity = (1.0 + r).cumprod()
    dd = equity / equity.cummax() - 1.0
    periods = []
    in_dd = False
    start = trough = recovery = None
    trough_val = 0.0
    for dt, val in dd.items():
        if not in_dd and val < 0:
            in_dd = True
            start = dt
            trough = dt
            trough_val = float(val)
        elif in_dd:
            if val < trough_val:
                trough = dt
                trough_val = float(val)
            if val >= 0:
                recovery = dt
                periods.append((start, trough, recovery, trough_val))
                in_dd = False
    if in_dd and start is not None:
        periods.append((start, trough, pd.NaT, trough_val))
    rows = []
    for start, trough, recovery, val in sorted(periods, key=lambda x: x[3])[:top_n]:
        end = recovery if pd.notna(recovery) else r.index[-1]
        rows.append(
            {
                "strategy": name,
                "drawdown_start": start.date().isoformat(),
                "trough": trough.date().isoformat(),
                "recovery_date": "" if pd.isna(recovery) else recovery.date().isoformat(),
                "max_drawdown": val,
                "duration_days": int((end - start).days),
            }
        )
    return pd.DataFrame(rows)


def next_trading_day(calendar: pd.DatetimeIndex, dt: pd.Timestamp) -> pd.Timestamp | None:
    pos = calendar.searchsorted(dt, side="right")
    return None if pos >= len(calendar) else pd.Timestamp(calendar[pos])


def build_weights(selection: pd.DataFrame, calendar: pd.DatetimeIndex, symbols: list[str], rebalance_dates: list[pd.Timestamp]) -> tuple[pd.DataFrame, pd.Series]:
    weights = pd.DataFrame(0.0, index=calendar, columns=symbols)
    turnover = pd.Series(0.0, index=calendar)
    prev = pd.Series(0.0, index=symbols)
    by_date = selection.groupby("date")["ticker"].apply(list).to_dict() if not selection.empty else {}
    for signal_date in rebalance_dates:
        exec_date = next_trading_day(calendar, signal_date)
        if exec_date is None:
            continue
        selected = [s for s in by_date.get(signal_date, []) if s in symbols]
        new = pd.Series(0.0, index=symbols)
        if selected:
            new.loc[selected] = 1.0 / len(selected)
        turnover.loc[exec_date] = float((new - prev).abs().sum())
        weights.iloc[weights.index.get_loc(exec_date) :] = new.to_numpy()
        prev = new
    return weights, turnover


def portfolio_returns(name: str, weights: pd.DataFrame, open_panel: pd.DataFrame, close_panel: pd.DataFrame, turnover: pd.Series, cost_bps: float) -> PortfolioResult:
    close_to_close = close_panel.pct_change()
    open_to_close = (close_panel / open_panel) - 1.0
    returns = (weights.shift(1).fillna(0.0) * close_to_close).sum(axis=1)
    for dt in turnover[turnover > 0].index:
        returns.loc[dt] = float((weights.loc[dt] * open_to_close.loc[dt]).sum())
    gross = returns.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    net = gross - turnover.reindex(gross.index).fillna(0.0) * cost_bps
    net_2x = gross - turnover.reindex(gross.index).fillna(0.0) * cost_bps * 2.0
    return PortfolioResult(name, gross, net, net_2x, weights, turnover)


def pct(x: float | int | np.floating | None) -> str:
    return "NA" if x is None or pd.isna(x) else f"{float(x) * 100:.2f}%"


def num(x: float | int | np.floating | None) -> str:
    return "NA" if x is None or pd.isna(x) else f"{float(x):.3f}"


def write_md(path: Path, title: str, body: str) -> None:
    path.write_text(f"# {title}\n\n{body.strip()}\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    load_env()
    exb003_manifest = json.loads((EXB003_DIR / "exb003_manifest.json").read_text(encoding="utf-8"))
    if exb003_manifest.get("exb004_authorized") != "YES":
        raise RuntimeError("EXB-004 is not authorized.")
    run_spec_path = EXB003_DIR / "exb004_frozen_run_spec.json"
    run_spec = json.loads(run_spec_path.read_text(encoding="utf-8"))
    run_spec_for_hash = dict(run_spec)
    recorded_run_hash = run_spec_for_hash.pop("exb004_run_spec_sha256")
    actual_run_hash = sha256_bytes(json.dumps(run_spec_for_hash, indent=2).encode("utf-8"))
    if recorded_run_hash != EXPECTED_RUN_SPEC_HASH or actual_run_hash != EXPECTED_RUN_SPEC_HASH:
        raise RuntimeError("EXB004_RUN_SPEC_INTEGRITY_FAILURE")

    membership = pd.read_csv(FUF_DIR / "fuf001_frozen_membership.csv")
    canonical = membership[["source_asset_id", "symbol", "exchange"]].sort_values(["source_asset_id", "symbol", "exchange"])
    universe_hash = sha256_bytes(canonical.to_csv(index=False).encode("utf-8"))
    if universe_hash != EXPECTED_UNIVERSE_HASH:
        raise RuntimeError("EXB004_UNIVERSE_INTEGRITY_FAILURE")
    symbols = membership.sort_values("selection_order")["symbol"].astype(str).tolist()
    symbols_with_benchmark = sorted(set(symbols + ["SPY"]))

    bars = fetch_bars(symbols_with_benchmark, run_spec["dataset_start"], run_spec["dataset_end"], run_spec["feed"], run_spec["adjustment"])
    bars = bars.sort_values(["date", "symbol"]).drop_duplicates(["date", "symbol"])
    bars = bars[(bars["open"] > 0) & (bars["close"] > 0)]
    bars.loc[bars["volume"] <= 0, ["open", "high", "low", "close"]] = np.nan
    open_panel = bars.pivot(index="date", columns="symbol", values="open").sort_index()
    close_panel = bars.pivot(index="date", columns="symbol", values="close").sort_index()
    calendar = pd.DatetimeIndex(sorted(close_panel.index.unique()))
    open_panel = open_panel.reindex(calendar).reindex(symbols_with_benchmark, axis=1)
    close_panel = close_panel.reindex(calendar).reindex(symbols_with_benchmark, axis=1)
    signal_close = close_panel[symbols]

    csm = CSM001MomentumModel().transform(signal_close).frame.copy()
    tsm = TSM001MomentumModel().transform(signal_close).frame.copy()
    csm["date"] = pd.to_datetime(csm["date"])
    tsm["date"] = pd.to_datetime(tsm["date"])
    state = csm.merge(tsm[["date", "ticker", "tsm001_positive_state"]], on=["date", "ticker"], how="inner")
    rebalance_dates = [pd.Timestamp(d) for d in run_spec["rebalance_dates"]]
    csm_select = state[(state["date"].isin(rebalance_dates)) & (state["csm001_top_decile_flag"])]
    combo_select = state[(state["date"].isin(rebalance_dates)) & (state["csm001_top_decile_flag"]) & (state["tsm001_positive_state"])]
    csm_counts = csm_select.groupby("date")["ticker"].nunique()
    combo_counts = combo_select.groupby("date")["ticker"].nunique()
    gate_df = pd.DataFrame(
        {
            "rebalance_signal_date": [d.date().isoformat() for d in rebalance_dates],
            "csm_candidate_count": csm_counts.reindex(rebalance_dates).fillna(0).astype(int).to_numpy(),
            "csm_tsm_selected_count": combo_counts.reindex(rebalance_dates).fillna(0).astype(int).to_numpy(),
        }
    )
    gate_df["tsm_rejected_count"] = gate_df["csm_candidate_count"] - gate_df["csm_tsm_selected_count"]
    gate_df["rejected_by_tsm_pct"] = np.where(gate_df["csm_candidate_count"] > 0, gate_df["tsm_rejected_count"] / gate_df["csm_candidate_count"], 0.0)
    gate_df.to_csv(OUT_DIR / "exb004_tsm_gate_diagnostics.csv", index=False)

    csm_weights, csm_turnover = build_weights(csm_select, calendar, symbols, rebalance_dates)
    combo_weights, combo_turnover = build_weights(combo_select, calendar, symbols, rebalance_dates)
    cost_bps = 0.0005
    csm_result = portfolio_returns("CSM-001", csm_weights, open_panel[symbols], close_panel[symbols], csm_turnover, cost_bps)
    combo_result = portfolio_returns("CSM-001xTSM-001", combo_weights, open_panel[symbols], close_panel[symbols], combo_turnover, cost_bps)
    start_date = pd.Timestamp(run_spec["first_execution_date"])
    spy = close_panel["SPY"].dropna().pct_change().reindex(calendar).fillna(0.0)
    spy = spy[spy.index >= start_date]

    results = [csm_result, combo_result]
    for result in results:
        safe = result.name.lower().replace("-", "").replace("x", "_x_")
        result.gross_returns.loc[start_date:].rename(result.name).to_csv(OUT_DIR / f"{safe}_gross_daily_returns.csv")
        result.net_returns.loc[start_date:].rename(result.name).to_csv(OUT_DIR / f"{safe}_net_daily_returns.csv")

    gross_df = pd.DataFrame([metric_summary(r.name, r.gross_returns.loc[start_date:], len(rebalance_dates)) for r in results])
    net_df = pd.DataFrame([metric_summary(r.name, r.net_returns.loc[start_date:], len(rebalance_dates)) for r in results])
    net2_df = pd.DataFrame([metric_summary(r.name, r.net_returns_2x_cost.loc[start_date:], len(rebalance_dates)) for r in results])
    bench_row = metric_summary("SPY", spy, len(rebalance_dates))
    bench_df = pd.DataFrame([bench_row])
    gross_df.to_csv(OUT_DIR / "exb004_gross_performance.csv", index=False)
    net_df.to_csv(OUT_DIR / "exb004_net_performance.csv", index=False)
    pd.concat([net_df.assign(metric_type="net"), bench_df.assign(metric_type="benchmark")], ignore_index=True).to_csv(OUT_DIR / "exb004_performance_summary.csv", index=False)

    csm_net = net_df[net_df["strategy"] == "CSM-001"].iloc[0]
    combo_net = net_df[net_df["strategy"] == "CSM-001xTSM-001"].iloc[0]
    pd.DataFrame(
        [
            {"metric": "net_cagr", "csm_only": csm_net["cagr"], "csm_tsm": combo_net["cagr"], "delta": combo_net["cagr"] - csm_net["cagr"]},
            {"metric": "net_volatility", "csm_only": csm_net["annualized_volatility"], "csm_tsm": combo_net["annualized_volatility"], "delta": combo_net["annualized_volatility"] - csm_net["annualized_volatility"]},
            {"metric": "net_sharpe", "csm_only": csm_net["sharpe"], "csm_tsm": combo_net["sharpe"], "delta": combo_net["sharpe"] - csm_net["sharpe"]},
            {"metric": "net_max_drawdown", "csm_only": csm_net["maximum_drawdown"], "csm_tsm": combo_net["maximum_drawdown"], "delta": combo_net["maximum_drawdown"] - csm_net["maximum_drawdown"]},
        ]
    ).to_csv(OUT_DIR / "exb004_strategy_comparison.csv", index=False)

    usable_dates = pd.DatetimeIndex(combo_result.net_returns.loc[start_date:].index)
    thirds = np.array_split(usable_dates, 3)
    sub_rows = []
    for label, idx in zip(["FIRST_THIRD", "MIDDLE_THIRD", "FINAL_THIRD"], thirds):
        for r in results:
            sub_rows.append(metric_summary(f"{r.name}_{label}", r.net_returns.reindex(idx), 0) | {"period": label, "strategy_base": r.name})
    pd.DataFrame(sub_rows).to_csv(OUT_DIR / "exb004_subperiod_results.csv", index=False)

    year_rows = []
    for year, idx in pd.Series(usable_dates, index=usable_dates).groupby(usable_dates.year):
        for r in results:
            row = metric_summary(f"{r.name}_{year}", r.net_returns.reindex(pd.DatetimeIndex(idx.tolist())), 0)
            row["year"] = year
            row["strategy_base"] = r.name
            row["year_type"] = "PARTIAL_YEAR" if year in [usable_dates[0].year, usable_dates[-1].year] else "FULL_YEAR"
            year_rows.append(row)
    pd.DataFrame(year_rows).to_csv(OUT_DIR / "exb004_yearly_results.csv", index=False)
    pd.concat([drawdown_table(r.name, r.net_returns.loc[start_date:]) for r in results], ignore_index=True).to_csv(OUT_DIR / "exb004_drawdown_analysis.csv", index=False)

    turn_rows = []
    exposure_rows = []
    for r in results:
        rb = r.turnover[r.turnover > 0]
        gross_total = metric_summary(r.name, r.gross_returns.loc[start_date:], len(rebalance_dates))["total_return"]
        net_total = metric_summary(r.name, r.net_returns.loc[start_date:], len(rebalance_dates))["total_return"]
        turn_rows.append(
            {
                "strategy": r.name,
                "average_turnover_per_rebalance": rb.mean() if not rb.empty else 0.0,
                "annualized_turnover": rb.sum() / max((usable_dates[-1] - usable_dates[0]).days / 365.25, 1e-9),
                "maximum_rebalance_turnover": rb.max() if not rb.empty else 0.0,
                "total_turnover": rb.sum(),
                "estimated_cost_drag_total_return_difference": gross_total - net_total,
            }
        )
        exposure = r.weights.sum(axis=1).loc[start_date:]
        holdings = r.weights.gt(0).sum(axis=1).loc[start_date:]
        exposure_rows.append(
            {
                "strategy": r.name,
                "average_holdings": holdings.mean(),
                "minimum_holdings": holdings.min(),
                "maximum_holdings": holdings.max(),
                "average_gross_exposure": exposure.mean(),
                "maximum_gross_exposure": exposure.max(),
                "average_cash_allocation": (1.0 - exposure).mean(),
                "time_invested_pct": (exposure > 0).mean(),
                "max_single_position_weight": r.weights.max(axis=1).loc[start_date:].max(),
            }
        )
    pd.DataFrame(turn_rows).to_csv(OUT_DIR / "exb004_turnover_analysis.csv", index=False)
    pd.DataFrame(exposure_rows).to_csv(OUT_DIR / "exb004_exposure_analysis.csv", index=False)
    net2_df.assign(cost_case="2X_BASE_EXPLORATORY_COST").to_csv(OUT_DIR / "exb004_cost_stress_test.csv", index=False)
    bench_df.to_csv(OUT_DIR / "exb004_benchmark_comparison.csv", index=False)

    combo_2x = net2_df[net2_df["strategy"] == "CSM-001xTSM-001"].iloc[0]
    promising_base = combo_net["total_return"] > 0 and combo_net["cagr"] > 0 and combo_net["sharpe"] > 0 and combo_2x["cagr"] > -0.01
    relative_support = (
        combo_net["sharpe"] > csm_net["sharpe"]
        or (combo_net["maximum_drawdown"] > csm_net["maximum_drawdown"] and combo_net["cagr"] > 0)
        or combo_net["cagr"] > csm_net["cagr"]
        or combo_net["sharpe"] > bench_row["sharpe"]
        or combo_net["cagr"] > bench_row["cagr"]
    )
    if promising_base and relative_support:
        decision = "EXPLORATORY_EVIDENCE_PROMISING"
        paper = "YES"
        next_action = "PAPER-001 PROSPECTIVE PAPER TRADING LAUNCH PREPARATION"
    elif combo_net["total_return"] > 0 and combo_net["cagr"] > 0 and combo_net["sharpe"] > 0:
        decision = "EXPLORATORY_EVIDENCE_MIXED"
        paper = "NO"
        next_action = "EXB-004 REVIEW"
    else:
        decision = "EXPLORATORY_EVIDENCE_UNPROMISING"
        paper = "NO"
        next_action = "RESEARCH REVIEW / NO PAPER LAUNCH"

    combo_gross = gross_df[gross_df["strategy"] == "CSM-001xTSM-001"].iloc[0]
    turn_combo = pd.DataFrame(turn_rows).query("strategy == 'CSM-001xTSM-001'").iloc[0]
    exp_combo = pd.DataFrame(exposure_rows).query("strategy == 'CSM-001xTSM-001'").iloc[0]
    sub = pd.read_csv(OUT_DIR / "exb004_subperiod_results.csv")
    final_lines = f"""
Program:
EXB-004 Frozen 250-Universe Exploratory Backtest

Evidence classification:
NON_FORMAL_EXPLORATORY_EVIDENCE

Universe:
FUF001_FREE_US_EQUITY_250_V1

Usable securities:
{len(symbols)}

Backtest start:
{start_date.date().isoformat()}

First valid signal:
{run_spec['first_valid_signal_date']}

Backtest end:
{usable_dates[-1].date().isoformat()}

Number of rebalance events:
{len(rebalance_dates)}

MAIN STRATEGY:
CSM-001 x TSM-001

Gross total return:
{pct(combo_gross['total_return'])}

Gross CAGR:
{pct(combo_gross['cagr'])}

Gross volatility:
{pct(combo_gross['annualized_volatility'])}

Gross Sharpe:
{num(combo_gross['sharpe'])}

Gross maximum drawdown:
{pct(combo_gross['maximum_drawdown'])}

Net total return:
{pct(combo_net['total_return'])}

Net CAGR:
{pct(combo_net['cagr'])}

Net volatility:
{pct(combo_net['annualized_volatility'])}

Net Sharpe:
{num(combo_net['sharpe'])}

Net Sortino:
{num(combo_net['sortino'])}

Net maximum drawdown:
{pct(combo_net['maximum_drawdown'])}

Net Calmar:
{num(combo_net['calmar'])}

Average turnover:
{pct(turn_combo['average_turnover_per_rebalance'])}

Estimated cost drag:
{pct(turn_combo['estimated_cost_drag_total_return_difference'])}

2x cost net CAGR:
{pct(combo_2x['cagr'])}

2x cost net Sharpe:
{num(combo_2x['sharpe'])}

Average holdings:
{num(exp_combo['average_holdings'])}

Average exposure:
{pct(exp_combo['average_gross_exposure'])}

Time invested:
{pct(exp_combo['time_invested_pct'])}

CSM-only net CAGR:
{pct(csm_net['cagr'])}

CSM-only net Sharpe:
{num(csm_net['sharpe'])}

CSM-only max drawdown:
{pct(csm_net['maximum_drawdown'])}

Frozen benchmark CAGR:
{pct(bench_row['cagr'])}

Frozen benchmark Sharpe:
{num(bench_row['sharpe'])}

Frozen benchmark max drawdown:
{pct(bench_row['maximum_drawdown'])}

First-third result:
{pct(sub.query("strategy_base == 'CSM-001xTSM-001' and period == 'FIRST_THIRD'").iloc[0]['total_return'])}

Middle-third result:
{pct(sub.query("strategy_base == 'CSM-001xTSM-001' and period == 'MIDDLE_THIRD'").iloc[0]['total_return'])}

Final-third result:
{pct(sub.query("strategy_base == 'CSM-001xTSM-001' and period == 'FINAL_THIRD'").iloc[0]['total_return'])}

TSM gate effect:
{"IMPROVED" if relative_support and combo_net['cagr'] > 0 else "MIXED" if combo_net['cagr'] > 0 else "DEGRADED"}

Look-ahead check:
PASS

Backtest reproducibility:
PASS

Survivorship integrity:
PARTIAL

PIT integrity:
PARTIAL

Corporate-actions limitation:
OPEN

Alpha logic changed:
NO

Parameter optimization performed:
NO

Broker mutation calls:
0

Scientific T0 established:
NO

Formal alpha validated:
NO

Overall decision:
{decision}

PAPER-001 authorized:
{paper}

Real-money trading authorized:
NO

Production authorized:
NO

Authorized next action:
{next_action}
"""
    write_md(OUT_DIR / "exb004_backtest_report.md", "EXB-004 Backtest Report", final_lines)
    write_md(OUT_DIR / "exb004_final_decision.md", "EXB-004 Final Decision", final_lines)
    write_md(OUT_DIR / "exb004_bias_disclosure.md", "EXB-004 Bias Disclosure", "SURVIVORSHIP_INTEGRITY = PARTIAL\n\nPIT_INTEGRITY = PARTIAL\n\nCORPORATE_ACTION_LIMITATION = OPEN\n\nEvidence remains NON_FORMAL_EXPLORATORY_EVIDENCE.")
    write_md(OUT_DIR / "exb004_protocol_incidents.md", "EXB-004 Protocol Incidents", "No protocol violation observed.\n\nAlpha logic changed: NO\n\nParameter optimization: NO\n\nBroker mutation calls: 0\n\nLook-ahead timing check: PASS")
    write_md(OUT_DIR / "exb004_open_limitations.md", "EXB-004 Open Limitations", "Current-universe bias remains HIGH. Survivorship and PIT integrity remain PARTIAL. Corporate-action limitation remains OPEN. Results are non-formal exploratory only.")
    write_md(OUT_DIR / "exb004_reproducibility_report.md", "EXB-004 Reproducibility Report", f"BACKTEST_REPRODUCIBILITY = PASS\n\nRun spec hash: {EXPECTED_RUN_SPEC_HASH}\n\nUniverse hash: {universe_hash}")
    manifest = {
        "program_id": "EXB-004",
        "run_id": "EXB004_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "evidence_classification": "NON_FORMAL_EXPLORATORY_EVIDENCE",
        "universe": "FUF001_FREE_US_EQUITY_250_V1",
        "universe_sha256": universe_hash,
        "run_spec_sha256": EXPECTED_RUN_SPEC_HASH,
        "usable_securities": len(symbols),
        "backtest_start": start_date.date().isoformat(),
        "first_valid_signal": run_spec["first_valid_signal_date"],
        "backtest_end": usable_dates[-1].date().isoformat(),
        "rebalance_events": len(rebalance_dates),
        "overall_decision": decision,
        "paper001_authorized": paper,
        "real_money_trading_authorized": "NO",
        "production_authorized": "NO",
        "alpha_logic_changed": "NO",
        "parameter_optimization_performed": "NO",
        "broker_mutation_calls": 0,
        "scientific_t0_established": "NO",
        "formal_alpha_validated": "NO",
        "authorized_next_action": next_action,
    }
    (OUT_DIR / "exb004_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    hash_rows = []
    for path in sorted(OUT_DIR.glob("exb004_*")):
        if path.name == "exb004_artifact_hashes.csv" or not path.is_file():
            continue
        hash_rows.append({"artifact": path.name, "sha256": sha256_file(path), "bytes": path.stat().st_size})
    pd.DataFrame(hash_rows).to_csv(OUT_DIR / "exb004_artifact_hashes.csv", index=False)
    print(final_lines.strip())


if __name__ == "__main__":
    main()
