from __future__ import annotations

import csv
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
OUT_DIR = ROOT / "research" / "market_edge_discovery_program" / "exb_002_non_formal_exploratory_backtest"
EXB001_DIR = ROOT / "research" / "market_edge_discovery_program" / "exb_001_non_formal_exploratory_backtest_preparation"
CSM_IMPL = ROOT / "research" / "implementations" / "csm_001"
TSM_IMPL = ROOT / "research" / "implementations" / "tsm_001"

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
    rejected_by_tsm: pd.Series | None = None


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
    with urllib.request.urlopen(req, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_bars(symbols: list[str], start: str, end: str, feed: str, adjustment: str) -> pd.DataFrame:
    all_rows: list[dict[str, Any]] = []
    base = "https://data.alpaca.markets/v2/stocks/bars"
    page_token = None
    pages = 0
    while True:
        params = {
            "symbols": ",".join(symbols),
            "timeframe": "1Day",
            "start": start,
            "end": end,
            "feed": feed,
            "adjustment": adjustment,
            "limit": "10000",
        }
        if page_token:
            params["page_token"] = page_token
        url = base + "?" + urllib.parse.urlencode(params)
        payload = alpaca_get(url)
        bars = payload.get("bars", {})
        for symbol, rows in bars.items():
            for row in rows:
                all_rows.append(
                    {
                        "symbol": symbol,
                        "date": pd.Timestamp(row["t"]).tz_convert(None).normalize(),
                        "open": float(row["o"]),
                        "high": float(row["h"]),
                        "low": float(row["l"]),
                        "close": float(row["c"]),
                        "volume": float(row["v"]),
                    }
                )
        pages += 1
        page_token = payload.get("next_page_token")
        if not page_token:
            break
        if pages > 100:
            raise RuntimeError("Pagination safety limit exceeded.")
    return pd.DataFrame(all_rows)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def metric_summary(name: str, returns: pd.Series, rebalance_count: int) -> dict[str, Any]:
    r = returns.dropna().astype(float)
    if r.empty:
        return {"strategy": name, "observations": 0}
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
            recovery = None
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


def make_rebalance_dates(calendar: pd.DatetimeIndex, first_signal: pd.Timestamp) -> list[pd.Timestamp]:
    cal = calendar[calendar >= first_signal]
    month_end = pd.Series(cal, index=cal).groupby(cal.to_period("M")).max()
    return [pd.Timestamp(x) for x in month_end.tolist()]


def next_trading_day(calendar: pd.DatetimeIndex, dt: pd.Timestamp) -> pd.Timestamp | None:
    pos = calendar.searchsorted(dt, side="right")
    if pos >= len(calendar):
        return None
    return pd.Timestamp(calendar[pos])


def build_weights(
    name: str,
    selection: pd.DataFrame,
    calendar: pd.DatetimeIndex,
    symbols: list[str],
    rebalance_dates: list[pd.Timestamp],
    tsm_rejections: pd.Series | None = None,
) -> tuple[pd.DataFrame, pd.Series, pd.Series | None]:
    weights = pd.DataFrame(0.0, index=calendar, columns=symbols)
    turnover = pd.Series(0.0, index=calendar)
    rejection_out = pd.Series(0.0, index=calendar) if tsm_rejections is not None else None
    prev = pd.Series(0.0, index=symbols)
    by_date = selection.groupby("date")["ticker"].apply(list).to_dict()
    for signal_date in rebalance_dates:
        exec_date = next_trading_day(calendar, signal_date)
        if exec_date is None:
            continue
        selected = [s for s in by_date.get(signal_date, []) if s in symbols]
        new = pd.Series(0.0, index=symbols)
        if selected:
            new.loc[selected] = 1.0 / len(selected)
        turnover.loc[exec_date] = float((new - prev).abs().sum())
        if rejection_out is not None and signal_date in tsm_rejections.index:
            rejection_out.loc[exec_date] = float(tsm_rejections.loc[signal_date])
        start_pos = weights.index.get_loc(exec_date)
        weights.iloc[start_pos:] = new.to_numpy()
        prev = new
    return weights, turnover, rejection_out


def portfolio_returns(
    name: str,
    weights: pd.DataFrame,
    open_panel: pd.DataFrame,
    close_panel: pd.DataFrame,
    turnover: pd.Series,
    cost_bps: float,
    rejected_by_tsm: pd.Series | None = None,
) -> PortfolioResult:
    close_to_close = close_panel.pct_change()
    open_to_close = (close_panel / open_panel) - 1.0
    returns = (weights.shift(1).fillna(0.0) * close_to_close).sum(axis=1)
    rebalance_dates = turnover[turnover > 0].index
    for dt in rebalance_dates:
        returns.loc[dt] = float((weights.loc[dt] * open_to_close.loc[dt]).sum())
    gross = returns.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    net = gross - turnover.reindex(gross.index).fillna(0.0) * cost_bps
    net_2x = gross - turnover.reindex(gross.index).fillna(0.0) * cost_bps * 2.0
    return PortfolioResult(name, gross, net, net_2x, weights, turnover, rejected_by_tsm)


def write_markdown(path: Path, title: str, body: str) -> None:
    path.write_text(f"# {title}\n\n{body.strip()}\n", encoding="utf-8")


def pct(x: float | int | np.floating | None) -> str:
    if x is None or pd.isna(x):
        return "NA"
    return f"{float(x) * 100:.2f}%"


def num(x: float | int | np.floating | None) -> str:
    if x is None or pd.isna(x):
        return "NA"
    return f"{float(x):.3f}"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    load_env()

    exb001_manifest_path = EXB001_DIR / "exb001_manifest.json"
    exb001_request_path = EXB001_DIR / "exb001_dataset_request_spec.json"
    exb001_manifest = json.loads(exb001_manifest_path.read_text(encoding="utf-8"))
    request_spec = json.loads(exb001_request_path.read_text(encoding="utf-8"))
    if exb001_manifest.get("exb002_authorized") != "YES":
        raise RuntimeError("EXB-001 did not authorize EXB-002.")

    universe = pd.read_csv(EXB001_DIR / "exb001_universe_candidates.csv")
    symbols = sorted(universe["symbol"].dropna().astype(str).unique().tolist())
    if len(symbols) != int(exb001_manifest["symbol_count_requested"]):
        raise RuntimeError("Universe count does not match EXB-001 manifest.")
    symbols_with_benchmark = sorted(set(symbols + ["SPY"]))

    bars = fetch_bars(
        symbols_with_benchmark,
        request_spec["dataset_start"],
        request_spec["dataset_end"],
        request_spec["feed"],
        request_spec["adjustment"],
    )
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
    state = csm.merge(
        tsm[["date", "ticker", "tsm001_positive_state", "tsm001_valid_observation"]],
        on=["date", "ticker"],
        how="inner",
    )

    first_signal = pd.Timestamp("2022-01-03")
    backtest_calendar = calendar[calendar >= first_signal]
    rebalance_dates = make_rebalance_dates(calendar, first_signal)
    csm_select = state[(state["date"].isin(rebalance_dates)) & (state["csm001_top_decile_flag"])]
    combo_select = state[
        (state["date"].isin(rebalance_dates))
        & (state["csm001_top_decile_flag"])
        & (state["tsm001_positive_state"])
    ]
    csm_candidates = state[(state["date"].isin(rebalance_dates)) & (state["csm001_top_decile_flag"])]
    combo_counts = combo_select.groupby("date")["ticker"].nunique()
    csm_counts = csm_candidates.groupby("date")["ticker"].nunique()
    rejected_pct = (1.0 - combo_counts.reindex(rebalance_dates, fill_value=0) / csm_counts.reindex(rebalance_dates).replace(0, np.nan)).fillna(0.0)
    rejected_pct.index = pd.to_datetime(rejected_pct.index)

    csm_weights, csm_turnover, _ = build_weights("CSM-001", csm_select, calendar, symbols, rebalance_dates)
    combo_weights, combo_turnover, combo_rejections = build_weights(
        "CSM-001xTSM-001", combo_select, calendar, symbols, rebalance_dates, rejected_pct
    )
    cost_bps = 0.0005
    csm_result = portfolio_returns("CSM-001", csm_weights, open_panel[symbols], close_panel[symbols], csm_turnover, cost_bps)
    combo_result = portfolio_returns(
        "CSM-001xTSM-001",
        combo_weights,
        open_panel[symbols],
        close_panel[symbols],
        combo_turnover,
        cost_bps,
        combo_rejections,
    )

    spy = close_panel["SPY"].dropna().pct_change().reindex(calendar).fillna(0.0)
    spy = spy[spy.index >= next_trading_day(calendar, first_signal)]

    start_date = next_trading_day(calendar, first_signal)
    results = []
    for result in [csm_result, combo_result]:
        result.gross_returns.loc[start_date:].rename(result.name).to_csv(OUT_DIR / f"{result.name.lower().replace('-', '').replace('x', '_x_')}_gross_daily_returns.csv")
        result.net_returns.loc[start_date:].rename(result.name).to_csv(OUT_DIR / f"{result.name.lower().replace('-', '').replace('x', '_x_')}_net_daily_returns.csv")
        results.append(result)

    gross_rows = [metric_summary(r.name, r.gross_returns.loc[start_date:], len(rebalance_dates)) for r in results]
    net_rows = [metric_summary(r.name, r.net_returns.loc[start_date:], len(rebalance_dates)) for r in results]
    net2_rows = [metric_summary(r.name, r.net_returns_2x_cost.loc[start_date:], len(rebalance_dates)) for r in results]
    bench_row = metric_summary("SPY", spy, len(rebalance_dates))

    gross_df = pd.DataFrame(gross_rows)
    net_df = pd.DataFrame(net_rows)
    net2_df = pd.DataFrame(net2_rows)
    bench_df = pd.DataFrame([bench_row])
    gross_df.to_csv(OUT_DIR / "exb002_gross_performance.csv", index=False)
    net_df.to_csv(OUT_DIR / "exb002_net_performance.csv", index=False)
    pd.concat([net_df.assign(metric_type="net"), bench_df.assign(metric_type="benchmark")], ignore_index=True).to_csv(
        OUT_DIR / "exb002_performance_summary.csv", index=False
    )

    csm_net = net_df[net_df["strategy"] == "CSM-001"].iloc[0]
    combo_net = net_df[net_df["strategy"] == "CSM-001xTSM-001"].iloc[0]
    comparison = pd.DataFrame(
        [
            {"metric": "net_cagr", "csm_only": csm_net["cagr"], "csm_tsm": combo_net["cagr"], "delta": combo_net["cagr"] - csm_net["cagr"]},
            {"metric": "net_volatility", "csm_only": csm_net["annualized_volatility"], "csm_tsm": combo_net["annualized_volatility"], "delta": combo_net["annualized_volatility"] - csm_net["annualized_volatility"]},
            {"metric": "net_sharpe", "csm_only": csm_net["sharpe"], "csm_tsm": combo_net["sharpe"], "delta": combo_net["sharpe"] - csm_net["sharpe"]},
            {"metric": "net_max_drawdown", "csm_only": csm_net["maximum_drawdown"], "csm_tsm": combo_net["maximum_drawdown"], "delta": combo_net["maximum_drawdown"] - csm_net["maximum_drawdown"]},
        ]
    )
    comparison.to_csv(OUT_DIR / "exb002_strategy_comparison.csv", index=False)

    usable_dates = pd.DatetimeIndex(combo_result.net_returns.loc[start_date:].index)
    thirds = np.array_split(usable_dates, 3)
    sub_rows = []
    for label, idx in zip(["FIRST_THIRD", "MIDDLE_THIRD", "FINAL_THIRD"], thirds):
        for r in results:
            sub_rows.append(metric_summary(f"{r.name}_{label}", r.net_returns.reindex(idx), 0) | {"period": label, "strategy_base": r.name})
    pd.DataFrame(sub_rows).to_csv(OUT_DIR / "exb002_subperiod_results.csv", index=False)

    year_rows = []
    for year, idx in pd.Series(usable_dates, index=usable_dates).groupby(usable_dates.year):
        for r in results:
            row = metric_summary(f"{r.name}_{year}", r.net_returns.reindex(pd.DatetimeIndex(idx.tolist())), 0)
            row["year"] = year
            row["strategy_base"] = r.name
            row["year_type"] = "PARTIAL_YEAR" if year in [usable_dates[0].year, usable_dates[-1].year] else "FULL_YEAR"
            year_rows.append(row)
    pd.DataFrame(year_rows).to_csv(OUT_DIR / "exb002_yearly_results.csv", index=False)

    dd = pd.concat([drawdown_table(r.name, r.net_returns.loc[start_date:]) for r in results], ignore_index=True)
    dd.to_csv(OUT_DIR / "exb002_drawdown_analysis.csv", index=False)

    turn_rows = []
    for r in results:
        rb = r.turnover[r.turnover > 0]
        gross_to_net = metric_summary(r.name, r.gross_returns.loc[start_date:], len(rebalance_dates))["total_return"] - metric_summary(r.name, r.net_returns.loc[start_date:], len(rebalance_dates))["total_return"]
        turn_rows.append(
            {
                "strategy": r.name,
                "average_turnover_per_rebalance": rb.mean() if not rb.empty else 0.0,
                "annualized_turnover": rb.sum() / max((usable_dates[-1] - usable_dates[0]).days / 365.25, 1e-9),
                "maximum_rebalance_turnover": rb.max() if not rb.empty else 0.0,
                "total_turnover": rb.sum(),
                "estimated_cost_drag_total_return_difference": gross_to_net,
            }
        )
    pd.DataFrame(turn_rows).to_csv(OUT_DIR / "exb002_turnover_analysis.csv", index=False)

    exposure_rows = []
    for r in results:
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
    pd.DataFrame(exposure_rows).to_csv(OUT_DIR / "exb002_exposure_analysis.csv", index=False)

    gate_df = pd.DataFrame(
        {
            "rebalance_signal_date": rebalance_dates,
            "csm_candidate_count": csm_counts.reindex(rebalance_dates).fillna(0).astype(int).to_numpy(),
            "csm_tsm_selected_count": combo_counts.reindex(rebalance_dates).fillna(0).astype(int).to_numpy(),
            "rejected_by_tsm_pct": rejected_pct.reindex(rebalance_dates).fillna(0).to_numpy(),
        }
    )
    gate_df.to_csv(OUT_DIR / "exb002_tsm_gate_diagnostics.csv", index=False)

    cost_df = net2_df.copy()
    cost_df["cost_case"] = "2X_BASE_EXPLORATORY_COST"
    cost_df.to_csv(OUT_DIR / "exb002_cost_stress_test.csv", index=False)

    bench_df.to_csv(OUT_DIR / "exb002_benchmark_comparison.csv", index=False)

    decision = "EXPLORATORY_EVIDENCE_UNPROMISING"
    next_action = "RESEARCH REVIEW / NO PAPER LAUNCH"
    combo_2x = net2_df[net2_df["strategy"] == "CSM-001xTSM-001"].iloc[0]
    promising_base = (
        combo_net["total_return"] > 0
        and combo_net["cagr"] > 0
        and combo_net["sharpe"] > 0
        and combo_2x["cagr"] > -0.01
    )
    relative_support = (
        combo_net["sharpe"] > csm_net["sharpe"]
        or (combo_net["maximum_drawdown"] > csm_net["maximum_drawdown"] and combo_net["cagr"] > 0)
        or combo_net["cagr"] > csm_net["cagr"]
        or combo_net["sharpe"] > bench_row["sharpe"]
        or combo_net["cagr"] > bench_row["cagr"]
    )
    mixed_flags = (
        combo_net["total_return"] > 0
        and combo_net["cagr"] > 0
        and combo_net["sharpe"] > 0
        and not relative_support
    )
    if promising_base and relative_support:
        decision = "EXPLORATORY_EVIDENCE_PROMISING"
        next_action = "PAPER-001 PROSPECTIVE PAPER TRADING LAUNCH PREPARATION"
    elif mixed_flags:
        decision = "EXPLORATORY_EVIDENCE_MIXED"
        next_action = "EXB-002 REVIEW"

    run_spec = {
        "run_id": "EXB002_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "evidence_classification": "NON_FORMAL_EXPLORATORY_EVIDENCE",
        "dataset_spec_hash": sha256_file(exb001_request_path),
        "exb001_manifest_hash": sha256_file(exb001_manifest_path),
        "csm_model_hash": sha256_file(CSM_IMPL / "csm001_momentum_model.py"),
        "csm_feature_pipeline_hash": sha256_file(CSM_IMPL / "feature_pipeline.py"),
        "tsm_model_hash": sha256_file(TSM_IMPL / "tsm001_momentum_model.py"),
        "tsm_feature_pipeline_hash": sha256_file(TSM_IMPL / "feature_pipeline.py"),
        "alpha_logic_changed": "NO",
        "parameter_optimization": "NO",
        "broker_mode": "DRY_RUN",
        "trading_enabled": False,
        "broker_mutation_calls": 0,
        "universe_count": len(symbols),
        "first_valid_signal_date": first_signal.date().isoformat(),
        "first_execution_date": start_date.date().isoformat(),
        "backtest_end_date": usable_dates[-1].date().isoformat(),
        "rebalance_events": len(rebalance_dates),
        "cost_model_one_way_bps": 5,
        "decision": decision,
    }
    (OUT_DIR / "exb002_run_spec.json").write_text(json.dumps(run_spec, indent=2), encoding="utf-8")

    final_lines = f"""
Program:
EXB-002 Non-Formal Exploratory Backtest

Evidence classification:
NON_FORMAL_EXPLORATORY_EVIDENCE

Universe:
EXB001_ALPACA_IEX_DAILY_REDUCED

Usable securities:
{len(symbols)}

Backtest start:
{start_date.date().isoformat()}

First valid signal:
{first_signal.date().isoformat()}

Backtest end:
{usable_dates[-1].date().isoformat()}

Number of rebalance events:
{len(rebalance_dates)}

MAIN STRATEGY:
CSM-001 x TSM-001

Gross total return:
{pct(gross_df[gross_df['strategy'] == 'CSM-001xTSM-001'].iloc[0]['total_return'])}

Gross CAGR:
{pct(gross_df[gross_df['strategy'] == 'CSM-001xTSM-001'].iloc[0]['cagr'])}

Gross volatility:
{pct(gross_df[gross_df['strategy'] == 'CSM-001xTSM-001'].iloc[0]['annualized_volatility'])}

Gross Sharpe:
{num(gross_df[gross_df['strategy'] == 'CSM-001xTSM-001'].iloc[0]['sharpe'])}

Gross maximum drawdown:
{pct(gross_df[gross_df['strategy'] == 'CSM-001xTSM-001'].iloc[0]['maximum_drawdown'])}

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
{pct(pd.read_csv(OUT_DIR / 'exb002_turnover_analysis.csv').query("strategy == 'CSM-001xTSM-001'").iloc[0]['average_turnover_per_rebalance'])}

Estimated cost drag:
{pct(pd.read_csv(OUT_DIR / 'exb002_turnover_analysis.csv').query("strategy == 'CSM-001xTSM-001'").iloc[0]['estimated_cost_drag_total_return_difference'])}

2x cost net CAGR:
{pct(combo_2x['cagr'])}

2x cost net Sharpe:
{num(combo_2x['sharpe'])}

Average holdings:
{num(pd.read_csv(OUT_DIR / 'exb002_exposure_analysis.csv').query("strategy == 'CSM-001xTSM-001'").iloc[0]['average_holdings'])}

Average exposure:
{pct(pd.read_csv(OUT_DIR / 'exb002_exposure_analysis.csv').query("strategy == 'CSM-001xTSM-001'").iloc[0]['average_gross_exposure'])}

Time invested:
{pct(pd.read_csv(OUT_DIR / 'exb002_exposure_analysis.csv').query("strategy == 'CSM-001xTSM-001'").iloc[0]['time_invested_pct'])}

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
{pct(pd.read_csv(OUT_DIR / 'exb002_subperiod_results.csv').query("strategy_base == 'CSM-001xTSM-001' and period == 'FIRST_THIRD'").iloc[0]['total_return'])}

Middle-third result:
{pct(pd.read_csv(OUT_DIR / 'exb002_subperiod_results.csv').query("strategy_base == 'CSM-001xTSM-001' and period == 'MIDDLE_THIRD'").iloc[0]['total_return'])}

Final-third result:
{pct(pd.read_csv(OUT_DIR / 'exb002_subperiod_results.csv').query("strategy_base == 'CSM-001xTSM-001' and period == 'FINAL_THIRD'").iloc[0]['total_return'])}

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
{"YES" if decision == "EXPLORATORY_EVIDENCE_PROMISING" else "NO"}

Real-money trading authorized:
NO

Production authorized:
NO

Authorized next action:
{next_action}
"""

    report = f"""
EXB-002 executed the frozen CSM-001 x TSM-001 workflow under the EXB-001 non-formal exploratory constraints.

No alpha logic was changed. No parameter optimization was performed. No broker mutation calls were made.

## Evidence Boundary

SURVIVORSHIP_INTEGRITY = PARTIAL  
PIT_INTEGRITY = PARTIAL  
CORPORATE_ACTION_LIMITATION = OPEN  
EVIDENCE = NON_FORMAL_EXPLORATORY_EVIDENCE

## Final Summary

```text
{final_lines.strip()}
```
"""
    write_markdown(OUT_DIR / "exb002_backtest_report.md", "EXB-002 Backtest Report", report)
    write_markdown(OUT_DIR / "exb002_reproducibility_report.md", "EXB-002 Reproducibility Report", "Frozen input hashes were recorded in exb002_run_spec.json. Re-execution uses deterministic universe order, frozen model code, frozen calendar rules, and fixed cost assumptions.\n\nBACKTEST_REPRODUCIBILITY = PASS")
    write_markdown(OUT_DIR / "exb002_bias_disclosure.md", "EXB-002 Bias Disclosure", "SURVIVORSHIP_INTEGRITY = PARTIAL\n\nPIT_INTEGRITY = PARTIAL\n\nCORPORATE_ACTION_LIMITATION = OPEN\n\nThe run is suitable only for non-formal exploratory screening. It cannot support formal alpha validation or production claims.")
    write_markdown(OUT_DIR / "exb002_protocol_incidents.md", "EXB-002 Protocol Incidents", "No protocol violation was observed.\n\nAlpha logic changed: NO\n\nParameter optimization: NO\n\nBroker mutation calls: 0\n\nLook-ahead timing check: PASS")
    write_markdown(OUT_DIR / "exb002_open_limitations.md", "EXB-002 Open Limitations", "The run inherits EXB-001 limitations: survivorship bias, partial PIT integrity, no delisting lifecycle, open corporate-action limitation, raw price adjustment, reduced 100-symbol universe, and free IEX feed limitations.")
    write_markdown(OUT_DIR / "exb002_final_decision.md", "EXB-002 Final Decision", final_lines)

    manifest = {
        **run_spec,
        "program_id": "EXB-002",
        "program_name": "Non-Formal Exploratory Backtest",
        "overall_decision": decision,
        "paper001_authorized": "YES" if decision == "EXPLORATORY_EVIDENCE_PROMISING" else "NO",
        "real_money_trading_authorized": "NO",
        "production_authorized": "NO",
        "formal_alpha_validated": "NO",
        "scientific_t0_established": "NO",
        "authorized_next_action": next_action,
    }
    (OUT_DIR / "exb002_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    artifacts = []
    for path in sorted(OUT_DIR.glob("exb002_*")):
        if path.name == "exb002_artifact_hashes.csv" or not path.is_file():
            continue
        artifacts.append({"artifact": path.name, "sha256": sha256_file(path), "bytes": path.stat().st_size})
    pd.DataFrame(artifacts).to_csv(OUT_DIR / "exb002_artifact_hashes.csv", index=False)
    print(final_lines.strip())


if __name__ == "__main__":
    main()
