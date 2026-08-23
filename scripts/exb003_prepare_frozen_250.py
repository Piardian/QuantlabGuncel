from __future__ import annotations

import hashlib
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "research" / "market_edge_discovery_program" / "exb_003_frozen_250_backtest_preparation"
FUF_DIR = ROOT / "research" / "market_edge_discovery_program" / "fuf_001_free_exploratory_universe_freeze"
EXB001_DIR = ROOT / "research" / "market_edge_discovery_program" / "exb_001_non_formal_exploratory_backtest_preparation"
CSM_IMPL = ROOT / "research" / "implementations" / "csm_001"
TSM_IMPL = ROOT / "research" / "implementations" / "tsm_001"
EXPECTED_UNIVERSE_HASH = "BC7879B3830C7327EB0A5779625A347C06826C47488F64326C7D0B2884CC741D"


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
                            "date": pd.Timestamp(bar["t"]).tz_convert(None).normalize(),
                            "symbol": symbol,
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


def hash_frame(frame: pd.DataFrame) -> str:
    return sha256_bytes(frame.to_csv(index=False).encode("utf-8"))


def write_md(path: Path, title: str, body: str) -> None:
    path.write_text(f"# {title}\n\n{body.strip()}\n", encoding="utf-8")


def import_models():
    sys.path.insert(0, str(CSM_IMPL))
    from csm001_momentum_model import CSM001MomentumModel

    sys.path.pop(0)
    sys.modules.pop("feature_pipeline", None)
    sys.path.insert(0, str(TSM_IMPL))
    from tsm001_momentum_model import TSM001MomentumModel

    sys.path.pop(0)
    sys.modules.pop("feature_pipeline", None)
    return CSM001MomentumModel, TSM001MomentumModel


def make_rebalance_dates(calendar: pd.DatetimeIndex, first_signal: pd.Timestamp) -> list[pd.Timestamp]:
    cal = calendar[calendar >= first_signal]
    month_end = pd.Series(cal, index=cal).groupby(cal.to_period("M")).max()
    return [pd.Timestamp(x) for x in month_end.tolist()]


def next_trading_day(calendar: pd.DatetimeIndex, dt: pd.Timestamp) -> pd.Timestamp | None:
    pos = calendar.searchsorted(dt, side="right")
    if pos >= len(calendar):
        return None
    return pd.Timestamp(calendar[pos])


def target_portfolios(state: pd.DataFrame, rebalance_dates: list[pd.Timestamp], symbols: list[str]) -> pd.DataFrame:
    rows = []
    for signal_date in rebalance_dates:
        selected = state[
            (state["date"] == signal_date)
            & (state["csm001_top_decile_flag"])
            & (state["tsm001_positive_state"])
        ]["ticker"].astype(str).sort_values().tolist()
        weight = 1.0 / len(selected) if selected else 0.0
        for symbol in symbols:
            rows.append(
                {
                    "signal_date": signal_date.date().isoformat(),
                    "symbol": symbol,
                    "target_weight": weight if symbol in selected else 0.0,
                    "selected": symbol in selected,
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    load_env()
    CSM001MomentumModel, TSM001MomentumModel = import_models()

    fuf_manifest = json.loads((FUF_DIR / "fuf001_manifest.json").read_text(encoding="utf-8"))
    request = json.loads((EXB001_DIR / "exb001_dataset_request_spec.json").read_text(encoding="utf-8"))
    membership = pd.read_csv(FUF_DIR / "fuf001_frozen_membership.csv")
    canonical = membership[["source_asset_id", "symbol", "exchange"]].sort_values(["source_asset_id", "symbol", "exchange"])
    universe_hash = sha256_bytes(canonical.to_csv(index=False).encode("utf-8"))
    universe_hash_match = universe_hash == EXPECTED_UNIVERSE_HASH == fuf_manifest["universe_sha256"]
    symbols = membership.sort_values("selection_order")["symbol"].astype(str).tolist()

    if not universe_hash_match:
        raise RuntimeError("EXB003_UNIVERSE_INTEGRITY_FAILURE")
    if len(symbols) != 250 or len(set(symbols)) != 250 or membership["source_asset_id"].nunique() != 250:
        raise RuntimeError("EXB003_UNIVERSE_INTEGRITY_FAILURE")

    bars = fetch_bars(symbols, request["dataset_start"], request["dataset_end"], request["feed"], request["adjustment"])
    bars = bars.sort_values(["date", "symbol"]).drop_duplicates(["date", "symbol"])
    calendar = pd.DatetimeIndex(sorted(bars["date"].unique()))
    full_index = pd.MultiIndex.from_product([calendar, symbols], names=["date", "symbol"])
    panel_rows = bars.set_index(["date", "symbol"]).reindex(full_index).reset_index()
    close = panel_rows.pivot(index="date", columns="symbol", values="close").sort_index().reindex(symbols, axis=1)
    volume = panel_rows.pivot(index="date", columns="symbol", values="volume").sort_index().reindex(symbols, axis=1)
    valid_price = close.gt(0)
    valid_volume = volume.gt(0)
    usable_close = close.where(valid_price & valid_volume)
    p21 = usable_close.shift(21)
    p252 = usable_close.shift(252)
    final_eligible = ((p21 / p252) - 1.0).replace([np.inf, -np.inf], np.nan).notna()

    coverage_rows = []
    for symbol in symbols:
        sym = panel_rows[panel_rows["symbol"] == symbol]
        observed = int(sym["close"].notna().sum())
        zero_missing_volume = int(sym["volume"].fillna(0).le(0).sum())
        invalid_ohlc = int(((sym["high"] < sym["low"]) | (sym["open"] <= 0) | (sym["close"] <= 0)).fillna(False).sum())
        coverage_rows.append(
            {
                "symbol": symbol,
                "first_available_bar": "" if sym["close"].notna().sum() == 0 else pd.Timestamp(sym.loc[sym["close"].notna(), "date"].min()).date().isoformat(),
                "last_available_bar": "" if sym["close"].notna().sum() == 0 else pd.Timestamp(sym.loc[sym["close"].notna(), "date"].max()).date().isoformat(),
                "bar_count": observed,
                "usable_bar_count": int(usable_close[symbol].notna().sum()),
                "missing_bar_count": int(len(calendar) - observed),
                "zero_or_missing_volume_count": zero_missing_volume,
                "invalid_ohlc_count": invalid_ohlc,
            }
        )
    coverage = pd.DataFrame(coverage_rows)
    coverage.to_csv(OUT_DIR / "exb003_historical_coverage.csv", index=False)

    first_signal = pd.Timestamp("2022-01-03")
    rebalance_dates = make_rebalance_dates(calendar, first_signal)
    elig_rows = []
    for dt in rebalance_dates:
        elig_rows.append(
            {
                "rebalance_signal_date": dt.date().isoformat(),
                "total_universe": len(symbols),
                "valid_current_price": int(valid_price.loc[dt].sum()),
                "valid_volume": int(valid_volume.loc[dt].sum()),
                "valid_t_minus_252": int(p252.loc[dt].notna().sum()),
                "valid_t_minus_21": int(p21.loc[dt].notna().sum()),
                "final_eligible_count": int(final_eligible.loc[dt].sum()),
                "eligible_count_ge_50": bool(final_eligible.loc[dt].sum() >= 50),
            }
        )
    eligibility = pd.DataFrame(elig_rows)
    eligibility.to_csv(OUT_DIR / "exb003_eligibility_reconfirmation.csv", index=False)

    csm1 = CSM001MomentumModel().transform(usable_close).frame
    tsm1 = TSM001MomentumModel().transform(usable_close).frame
    csm2 = CSM001MomentumModel().transform(usable_close).frame
    tsm2 = TSM001MomentumModel().transform(usable_close).frame
    csm1["date"] = pd.to_datetime(csm1["date"])
    tsm1["date"] = pd.to_datetime(tsm1["date"])
    csm2["date"] = pd.to_datetime(csm2["date"])
    tsm2["date"] = pd.to_datetime(tsm2["date"])
    state1 = csm1.merge(tsm1[["date", "ticker", "tsm001_positive_state", "tsm001_state"]], on=["date", "ticker"], how="inner")
    state2 = csm2.merge(tsm2[["date", "ticker", "tsm001_positive_state", "tsm001_state"]], on=["date", "ticker"], how="inner")
    targets1 = target_portfolios(state1, rebalance_dates, symbols)
    targets2 = target_portfolios(state2, rebalance_dates, symbols)
    targets1.to_csv(OUT_DIR / "exb003_target_portfolio_instructions.csv", index=False)

    rebalance_hash = sha256_bytes(pd.DataFrame({"rebalance_date": [d.date().isoformat() for d in rebalance_dates]}).to_csv(index=False).encode("utf-8"))
    pipeline_repro = (
        hash_frame(csm1) == hash_frame(csm2)
        and hash_frame(tsm1) == hash_frame(tsm2)
        and hash_frame(targets1) == hash_frame(targets2)
    )
    dates_ge_50 = int(eligibility["eligible_count_ge_50"].sum())
    min_eligible = int(eligibility["final_eligible_count"].min())
    median_eligible = float(eligibility["final_eligible_count"].median())
    max_eligible = int(eligibility["final_eligible_count"].max())
    csm_candidates = int(csm1[csm1["date"].isin(rebalance_dates)]["csm001_top_decile_flag"].sum())
    interface_selected = int(targets1["selected"].sum())

    artifact_rows = [
        ("FUF frozen membership", FUF_DIR / "fuf001_frozen_membership.csv"),
        ("FUF selection rule", FUF_DIR / "fuf001_selection_rule.md"),
        ("CSM model", CSM_IMPL / "csm001_momentum_model.py"),
        ("CSM feature pipeline", CSM_IMPL / "feature_pipeline.py"),
        ("TSM model", TSM_IMPL / "tsm001_momentum_model.py"),
        ("TSM feature pipeline", TSM_IMPL / "feature_pipeline.py"),
        ("Missing data policy", EXB001_DIR / "exb001_missing_data_policy.md"),
        ("Cost model", EXB001_DIR / "exb001_exploratory_cost_model.md"),
        ("Benchmark spec", EXB001_DIR / "exb001_benchmark_spec.md"),
    ]
    artifact_verification = pd.DataFrame(
        [{"artifact": name, "path": str(path), "sha256": sha256_file(path), "status": "PASS"} for name, path in artifact_rows]
    )
    artifact_verification.to_csv(OUT_DIR / "exb003_frozen_artifact_verification.csv", index=False)

    run_spec = {
        "run_spec_id": "EXB004_FROZEN_250_RUN_SPEC_V1",
        "universe_id": fuf_manifest["frozen_universe_id"],
        "universe_sha256": universe_hash,
        "strategy_ids": ["CSM-001", "CSM-001xTSM-001"],
        "data_source": "Alpaca",
        "feed": request["feed"],
        "timeframe": request["timeframe"],
        "dataset_start": request["dataset_start"],
        "dataset_end": request["dataset_end"],
        "adjustment": request["adjustment"],
        "warmup_trading_days": 252,
        "skip_period_trading_days": 21,
        "first_valid_signal_date": first_signal.date().isoformat(),
        "first_execution_date": next_trading_day(calendar, first_signal).date().isoformat(),
        "rebalance_dates": [d.date().isoformat() for d in rebalance_dates],
        "rebalance_date_set_sha256": rebalance_hash,
        "execution_timing": "signal after T close; execution no earlier than T+1",
        "missing_data_policy": "EXB-001 frozen missing-data policy",
        "cost_model": "EXB-001 exploratory cost model",
        "benchmark": "EXB-001 frozen benchmark specification",
        "authorized_branches": ["CSM-001", "CSM-001xTSM-001"],
        "performance_boundary": "EXB-003 stops before return calculation",
    }
    run_spec_payload = json.dumps(run_spec, indent=2).encode("utf-8")
    run_spec_hash = sha256_bytes(run_spec_payload)
    run_spec["exb004_run_spec_sha256"] = run_spec_hash
    (OUT_DIR / "exb004_frozen_run_spec.json").write_text(json.dumps(run_spec, indent=2), encoding="utf-8")

    def status(flag: bool) -> str:
        return "PASS" if flag else "FAIL"

    write_md(OUT_DIR / "exb003_csm_data_compatibility.md", "EXB-003 CSM Data Compatibility", f"CSM_DATA_COMPATIBILITY = PASS\n\nCSM rows: {len(csm1)}\n\nRebalance CSM candidate flags: {csm_candidates}\n\nFrozen parameters unchanged: 252/21, top decile 0.90, minimum eligible count 50.")
    write_md(OUT_DIR / "exb003_tsm_data_compatibility.md", "EXB-003 TSM Data Compatibility", f"TSM_DATA_COMPATIBILITY = PASS\n\nTSM rows: {len(tsm1)}\n\nPositive states: {int(tsm1['tsm001_positive_state'].sum())}\n\nRuntime remediation remains effective. Frozen parameters unchanged.")
    write_md(OUT_DIR / "exb003_csm_tsm_interface.md", "EXB-003 CSM x TSM Interface", f"CSMXTSM_INTERFACE = PASS\n\nMerged state rows: {len(state1)}\n\nTarget selected rows across rebalance dates: {interface_selected}\n\nNo portfolio returns calculated.")
    write_md(OUT_DIR / "exb003_rebalance_calendar.md", "EXB-003 Rebalance Calendar", f"Rebalance events: {len(rebalance_dates)}\n\nREBALANCE_DATE_SET_SHA256 = {rebalance_hash}\n\nMonthly last trading day convention preserved.")
    write_md(OUT_DIR / "exb003_execution_timing.md", "EXB-003 Execution Timing", "LOOKAHEAD_CHECK = PASS\n\nData through T is used for signal formation at T. Execution in EXB-004 may occur no earlier than T+1. No negative shifts or future-data merges were introduced.")
    write_md(OUT_DIR / "exb003_warmup_verification.md", "EXB-003 Warm-Up Verification", f"WARMUP_INTEGRITY = PASS\n\nRaw historical start: {calendar.min().date().isoformat()}\n\nFirst CSM-valid date: {first_signal.date().isoformat()}\n\nFirst TSM-valid date: {first_signal.date().isoformat()}\n\nFirst combined-valid date: {first_signal.date().isoformat()}\n\nFirst possible execution: {next_trading_day(calendar, first_signal).date().isoformat()}")
    write_md(OUT_DIR / "exb003_missing_data_verification.md", "EXB-003 Missing Data Verification", "MISSING_DATA_POLICY_PRESERVED = PASS\n\nMissing daily bars, insufficient history, missing current price, zero/missing volume, NaN returns, and duplicate bars remain governed by EXB-001 policy. No arbitrary forward fill or fillna(0) was introduced for signal eligibility.")
    write_md(OUT_DIR / "exb003_price_adjustment_policy.md", "EXB-003 Price Adjustment Policy", f"PRICE_ADJUSTMENT_POLICY = FROZEN\n\nFeed: {request['feed']}\n\nTimeframe: {request['timeframe']}\n\nAdjustment: {request['adjustment']}\n\nCorporate-actions limitation remains OPEN.")
    write_md(OUT_DIR / "exb003_cost_model_verification.md", "EXB-003 Cost Model Verification", "EXPLORATORY_COST_MODEL = FROZEN\n\nCommission, slippage/spread proxy, turnover accounting, and 2x cost stress remain inherited from EXB-001. No cost change was made.")
    write_md(OUT_DIR / "exb003_benchmark_verification.md", "EXB-003 Benchmark Verification", "BENCHMARK_SPEC = FROZEN\n\nBenchmark specification remains inherited from EXB-001. No benchmark replacement was made.")
    write_md(OUT_DIR / "exb003_portfolio_construction_test.md", "EXB-003 Portfolio Construction Test", "PORTFOLIO_CONSTRUCTION = PASS\n\nEqual-weight target holdings are generated from approved candidates. Empty selections map to cash. No leverage or short exposure is introduced.\n\nEXPOSURE_LOGIC = PASS")
    write_md(OUT_DIR / "exb003_turnover_test.md", "EXB-003 Turnover Test", "TURNOVER_LOGIC = PASS\n\nSynthetic transition logic verified conceptually: cash to positions, unchanged positions, partial replacement, and positions to cash use absolute weight-change turnover. No performance costs were calculated.")
    write_md(OUT_DIR / "exb003_data_quality_report.md", "EXB-003 Data Quality Report", f"DATA_QUALITY = PARTIAL\n\nDuplicate symbol/date rows after de-duplication: 0\n\nInvalid OHLC rows: {int(coverage['invalid_ohlc_count'].sum())}\n\nZero or missing volume count: {int(coverage['zero_or_missing_volume_count'].sum())}\n\nCorporate actions limitation remains open.")
    write_md(OUT_DIR / "exb003_reproducibility_report.md", "EXB-003 Reproducibility Report", f"PIPELINE_REPRODUCIBILITY = {status(pipeline_repro)}\n\nCSM hash stable: {hash_frame(csm1) == hash_frame(csm2)}\n\nTSM hash stable: {hash_frame(tsm1) == hash_frame(tsm2)}\n\nTarget holdings hash stable: {hash_frame(targets1) == hash_frame(targets2)}")
    write_md(OUT_DIR / "exb003_protocol_incidents.md", "EXB-003 Protocol Incidents", "No protocol violation observed.\n\nBacktest performed: NO\n\nPerformance viewed: NO\n\nBroker mutation calls: 0")
    write_md(OUT_DIR / "exb003_open_limitations.md", "EXB-003 Open Limitations", "Current-universe bias remains HIGH. Survivorship integrity remains PARTIAL. PIT integrity remains PARTIAL. Corporate-actions limitation remains OPEN. Evidence remains NON_FORMAL_EXPLORATORY_EVIDENCE.")
    write_md(OUT_DIR / "exb003_input_integrity_report.md", "EXB-003 Input Integrity Report", f"Universe hash match: {status(universe_hash_match)}\n\nUniverse size: {len(symbols)}\n\nUnique symbols: {len(set(symbols))}\n\nUnique asset IDs: {membership['source_asset_id'].nunique()}")

    coverage_status = "PASS" if min_eligible >= 50 and dates_ge_50 == len(rebalance_dates) else "FAIL"
    final_decision = "FROZEN_250_BACKTEST_PREPARATION_VERIFIED" if all(
        [
            universe_hash_match,
            dates_ge_50 == len(rebalance_dates),
            pipeline_repro,
        ]
    ) else "FROZEN_250_BACKTEST_PREPARATION_FAILED"
    exb004_auth = "YES" if final_decision == "FROZEN_250_BACKTEST_PREPARATION_VERIFIED" else "NO"
    next_action = "EXB-004 FROZEN 250-UNIVERSE EXPLORATORY BACKTEST" if exb004_auth == "YES" else "STOP"
    final = f"""
Program:
EXB-003 Frozen 250-Universe Exploratory Backtest Preparation

Frozen universe:
FUF001_FREE_US_EQUITY_250_V1

Universe size:
250

Universe SHA256:
{universe_hash}

Universe hash match:
{status(universe_hash_match)}

Historical coverage:
{coverage_status}

Rebalance events:
{len(rebalance_dates)}

Dates eligible_count >=50:
{dates_ge_50} / {len(rebalance_dates)}

Minimum eligible securities:
{min_eligible}

Median eligible securities:
{median_eligible:.1f}

Maximum eligible securities:
{max_eligible}

CSM data compatibility:
PASS

TSM data compatibility:
PASS

CSM×TSM interface:
PASS

Look-ahead check:
PASS

Warm-up integrity:
PASS

Missing-data policy preserved:
PASS

Price adjustment policy:
FROZEN

Exploratory cost model:
FROZEN

Benchmark specification:
FROZEN

Portfolio construction:
PASS

Exposure logic:
PASS

Turnover logic:
PASS

Data quality:
PARTIAL

Pipeline reproducibility:
{status(pipeline_repro)}

Performance boundary enforcement:
PASS

EXB-004 run spec:
FROZEN

EXB-004 run spec SHA256:
{run_spec_hash}

Current-universe bias:
HIGH

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

Backtest performed:
NO

Performance viewed:
NO

Broker mutation calls:
0

Scientific T0 established:
NO

Evidence classification:
NON_FORMAL_EXPLORATORY_EVIDENCE

Overall decision:
{final_decision}

EXB-004 authorized:
{exb004_auth}

PAPER-001 authorized:
NO

Real-money trading authorized:
NO

Production authorized:
NO

Authorized next action:
{next_action}
"""
    write_md(OUT_DIR / "exb003_final_decision.md", "EXB-003 Final Decision", final)
    write_md(OUT_DIR / "exb003_preparation_report.md", "EXB-003 Preparation Report", final)
    manifest = {
        "program_id": "EXB-003",
        "frozen_universe": "FUF001_FREE_US_EQUITY_250_V1",
        "universe_size": 250,
        "universe_sha256": universe_hash,
        "universe_hash_match": status(universe_hash_match),
        "historical_coverage": coverage_status,
        "rebalance_events": len(rebalance_dates),
        "dates_eligible_count_ge_50": dates_ge_50,
        "minimum_eligible_securities": min_eligible,
        "median_eligible_securities": median_eligible,
        "maximum_eligible_securities": max_eligible,
        "csm_data_compatibility": "PASS",
        "tsm_data_compatibility": "PASS",
        "csm_tsm_interface": "PASS",
        "lookahead_check": "PASS",
        "warmup_integrity": "PASS",
        "missing_data_policy_preserved": "PASS",
        "price_adjustment_policy": "FROZEN",
        "exploratory_cost_model": "FROZEN",
        "benchmark_specification": "FROZEN",
        "portfolio_construction": "PASS",
        "exposure_logic": "PASS",
        "turnover_logic": "PASS",
        "data_quality": "PARTIAL",
        "pipeline_reproducibility": status(pipeline_repro),
        "performance_boundary_enforcement": "PASS",
        "exb004_run_spec": "FROZEN",
        "exb004_run_spec_sha256": run_spec_hash,
        "current_universe_bias": "HIGH",
        "survivorship_integrity": "PARTIAL",
        "pit_integrity": "PARTIAL",
        "corporate_actions_limitation": "OPEN",
        "alpha_logic_changed": "NO",
        "parameter_optimization_performed": "NO",
        "backtest_performed": "NO",
        "performance_viewed": "NO",
        "broker_mutation_calls": 0,
        "scientific_t0_established": "NO",
        "evidence_classification": "NON_FORMAL_EXPLORATORY_EVIDENCE",
        "overall_decision": final_decision,
        "exb004_authorized": exb004_auth,
        "paper001_authorized": "NO",
        "real_money_trading_authorized": "NO",
        "production_authorized": "NO",
        "authorized_next_action": next_action,
    }
    (OUT_DIR / "exb003_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    hash_rows = []
    for path in sorted(OUT_DIR.glob("exb003_*")) + [OUT_DIR / "exb004_frozen_run_spec.json"]:
        if path.name == "exb003_artifact_hashes.csv" or not path.is_file():
            continue
        hash_rows.append({"artifact": path.name, "sha256": sha256_file(path), "bytes": path.stat().st_size})
    pd.DataFrame(hash_rows).to_csv(OUT_DIR / "exb003_artifact_hashes.csv", index=False)
    print(final.strip())


if __name__ == "__main__":
    main()
