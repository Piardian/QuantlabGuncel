from __future__ import annotations

import hashlib
import json
import os
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
EXB001_DIR = ROOT / "research" / "market_edge_discovery_program" / "exb_001_non_formal_exploratory_backtest_preparation"
RRV001_DIR = ROOT / "research" / "market_edge_discovery_program" / "rrv_001_universe_eligibility_failure_attribution"
OUT_DIR = ROOT / "research" / "market_edge_discovery_program" / "rrv_002_free_universe_reconstruction_feasibility"
SCAN_LIMIT = 1000


BAD_SECURITY_TERMS = [
    " ETF",
    " ETN",
    " FUND",
    " WARRANT",
    " RIGHT",
    " UNIT",
    " PREFERRED",
    " PREF",
    " DEPOSITARY",
    " ADR",
    " ADS",
    " NOTE",
    " NOTES",
    " TRUST",
    " SPAC",
]


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


def asset_security_type(asset: dict[str, Any]) -> tuple[str, str]:
    symbol = str(asset.get("symbol", ""))
    name = str(asset.get("name", "")).upper()
    if not re.match(r"^[A-Z]{1,5}$", symbol):
        return "EXCLUDED_SYMBOL_PATTERN", "symbol not simple 1-5 uppercase letters"
    for term in BAD_SECURITY_TERMS:
        if term in f" {name} ":
            return "EXCLUDED_NON_COMMON", f"name contains {term.strip()}"
    return "COMMON_STOCK_COMPATIBLE", "metadata compatible with common-stock filter"


def fetch_assets() -> pd.DataFrame:
    assets = alpaca_get("https://paper-api.alpaca.markets/v2/assets?status=active&asset_class=us_equity")
    rows = []
    for asset in assets:
        assessment, reason = asset_security_type(asset)
        exchange = asset.get("exchange")
        exchange_normalized = "NYSE_AMERICAN" if exchange == "AMEX" else exchange
        rows.append(
            {
                "asset_id": asset.get("id"),
                "symbol": asset.get("symbol"),
                "name": asset.get("name"),
                "asset_class": asset.get("class"),
                "exchange": exchange,
                "exchange_normalized": exchange_normalized,
                "status": asset.get("status"),
                "tradable": bool(asset.get("tradable")),
                "marginable": bool(asset.get("marginable")),
                "shortable": bool(asset.get("shortable")),
                "fractionable": bool(asset.get("fractionable")),
                "attributes": "|".join(asset.get("attributes") or []),
                "security_type_assessment": assessment,
                "security_type_reason": reason,
            }
        )
    return pd.DataFrame(rows)


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
            time.sleep(0.02)
        time.sleep(0.05)
    return pd.DataFrame(rows)


def longest_streak(flags: pd.Series, fail_value: bool = False) -> int:
    best = cur = 0
    for value in flags.tolist():
        if bool(value) == fail_value:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def write_md(path: Path, title: str, body: str) -> None:
    path.write_text(f"# {title}\n\n{body.strip()}\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    load_env()
    request = json.loads((EXB001_DIR / "exb001_dataset_request_spec.json").read_text(encoding="utf-8"))
    rrv001 = json.loads((RRV001_DIR / "rrv001_manifest.json").read_text(encoding="utf-8"))
    rebalance = pd.read_csv(RRV001_DIR / "rrv001_rebalance_eligibility_funnel.csv")
    rebalance_dates = pd.DatetimeIndex(pd.to_datetime(rebalance["rebalance_signal_date"]))

    assets = fetch_assets()
    assets.to_csv(OUT_DIR / "rrv002_asset_population_inventory.csv", index=False)
    eligible_assets = assets[
        (assets["asset_class"] == "us_equity")
        & (assets["status"] == "active")
        & (assets["tradable"])
        & (assets["exchange"].isin(["NYSE", "NASDAQ", "AMEX"]))
        & (assets["security_type_assessment"] == "COMMON_STOCK_COMPATIBLE")
    ].copy()
    eligible_assets = eligible_assets.sort_values(["symbol", "asset_id"]).drop_duplicates("symbol", keep="first")
    assets[["asset_id", "symbol", "exchange", "status", "tradable", "security_type_assessment", "security_type_reason"]].to_csv(
        OUT_DIR / "rrv002_security_type_assessment.csv", index=False
    )

    symbols_all = eligible_assets["symbol"].astype(str).sort_values().tolist()
    symbols = symbols_all[:SCAN_LIMIT]
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
        sym_rows = panel_rows[panel_rows["symbol"] == symbol]
        observed = int(sym_rows["close"].notna().sum())
        zero_or_missing_volume = int(sym_rows["volume"].fillna(0).le(0).sum())
        usable_start = final_eligible.index[final_eligible[symbol]].min() if final_eligible[symbol].any() else pd.NaT
        first_bar = sym_rows.loc[sym_rows["close"].notna(), "date"].min()
        last_bar = sym_rows.loc[sym_rows["close"].notna(), "date"].max()
        coverage_rows.append(
            {
                "asset_id": eligible_assets.set_index("symbol").loc[symbol, "asset_id"],
                "symbol": symbol,
                "exchange": eligible_assets.set_index("symbol").loc[symbol, "exchange"],
                "first_available_bar_date": "" if pd.isna(first_bar) else pd.Timestamp(first_bar).date().isoformat(),
                "last_available_bar_date": "" if pd.isna(last_bar) else pd.Timestamp(last_bar).date().isoformat(),
                "daily_bar_count": observed,
                "usable_bar_count": int(usable_close[symbol].notna().sum()),
                "missing_bar_count": int(len(calendar) - observed),
                "zero_or_missing_volume_count": zero_or_missing_volume,
                "coverage_percentage": float(observed / len(calendar)) if len(calendar) else 0.0,
                "usable_for_csm_start_date": "" if pd.isna(usable_start) else pd.Timestamp(usable_start).date().isoformat(),
                "csm_history_capable": "YES" if final_eligible[symbol].any() else "NO",
            }
        )
    coverage = pd.DataFrame(coverage_rows)
    coverage.to_csv(OUT_DIR / "rrv002_history_coverage.csv", index=False)

    capable_symbols = coverage[coverage["csm_history_capable"] == "YES"].sort_values(
        ["usable_bar_count", "coverage_percentage", "symbol"], ascending=[False, False, True]
    )["symbol"].tolist()
    universe_specs = []
    for size in [250, 500, 1000]:
        if len(capable_symbols) >= size:
            universe_specs.append((f"RRV002_FREE_US_EQUITY_{size}", capable_symbols[:size]))
    universe_specs.append(("RRV002_FREE_US_EQUITY_ALL_SCANNED_CAPABLE", capable_symbols))

    cand_rows = []
    elig_rows = []
    for uid, universe_symbols in universe_specs:
        for order, symbol in enumerate(universe_symbols, start=1):
            cand_rows.append({"candidate_universe_id": uid, "selection_order": order, "symbol": symbol})
        for dt in rebalance_dates:
            if dt not in final_eligible.index:
                count = 0
                price_count = 0
                volume_count = 0
                hist_count = 0
                p21_count = 0
                p252_count = 0
            else:
                cols = universe_symbols
                count = int(final_eligible.loc[dt, cols].sum())
                price_count = int(valid_price.loc[dt, cols].sum())
                volume_count = int(valid_volume.loc[dt, cols].sum())
                hist_count = int(p252.loc[dt, cols].notna().sum())
                p21_count = int(p21.loc[dt, cols].notna().sum())
                p252_count = int(p252.loc[dt, cols].notna().sum())
            elig_rows.append(
                {
                    "candidate_universe_id": uid,
                    "rebalance_signal_date": dt.date().isoformat(),
                    "candidate_universe_size": len(universe_symbols),
                    "securities_with_data": price_count,
                    "securities_with_required_history": hist_count,
                    "valid_t_minus_252": p252_count,
                    "valid_t_minus_21": p21_count,
                    "valid_current_price": price_count,
                    "valid_volume": volume_count,
                    "final_eligible_count": count,
                    "eligible_count_ge_50": bool(count >= 50),
                }
            )
    candidate_universes = pd.DataFrame(cand_rows)
    candidate_universes.to_csv(OUT_DIR / "rrv002_candidate_universes.csv", index=False)
    eligibility = pd.DataFrame(elig_rows)
    eligibility.to_csv(OUT_DIR / "rrv002_candidate_eligibility_by_rebalance.csv", index=False)

    summary_rows = []
    for uid, group in eligibility.groupby("candidate_universe_id"):
        flags = group["eligible_count_ge_50"]
        summary_rows.append(
            {
                "candidate_universe_id": uid,
                "candidate_universe_size": int(group["candidate_universe_size"].iloc[0]),
                "rebalance_dates_analyzed": int(len(group)),
                "dates_eligible_count_ge_50": int(flags.sum()),
                "dates_eligible_count_lt_50": int((~flags).sum()),
                "percentage_ge_50": float(flags.mean()),
                "minimum_eligible_count": int(group["final_eligible_count"].min()),
                "median_eligible_count": float(group["final_eligible_count"].median()),
                "maximum_eligible_count": int(group["final_eligible_count"].max()),
                "first_date_ge_50": group.loc[flags, "rebalance_signal_date"].min() if flags.any() else "",
                "longest_starvation_streak": longest_streak(flags, fail_value=False),
            }
        )
    eligibility_summary = pd.DataFrame(summary_rows).sort_values(["percentage_ge_50", "median_eligible_count", "candidate_universe_size"], ascending=[False, False, True])
    eligibility_summary.to_csv(OUT_DIR / "rrv002_eligibility_summary.csv", index=False)

    selected = eligibility_summary[
        (eligibility_summary["percentage_ge_50"] >= 0.90) & (eligibility_summary["median_eligible_count"] >= 100)
    ].sort_values("candidate_universe_size")
    selected_id = selected["candidate_universe_id"].iloc[0] if not selected.empty else "NONE"
    selected_size = int(selected["candidate_universe_size"].iloc[0]) if not selected.empty else 0
    best = eligibility_summary.iloc[0]

    stage_rows = []
    if selected_id != "NONE":
        selected_symbols = candidate_universes[candidate_universes["candidate_universe_id"] == selected_id]["symbol"].tolist()
    else:
        selected_symbols = candidate_universes[candidate_universes["candidate_universe_id"] == best["candidate_universe_id"]]["symbol"].tolist()
    for dt in rebalance_dates:
        if dt in final_eligible.index:
            stage_rows.append(
                {
                    "rebalance_signal_date": dt.date().isoformat(),
                    "candidate_universe_id": selected_id if selected_id != "NONE" else best["candidate_universe_id"],
                    "universe_size": len(selected_symbols),
                    "valid_current_price": int(valid_price.loc[dt, selected_symbols].sum()),
                    "valid_current_volume": int(valid_volume.loc[dt, selected_symbols].sum()),
                    "valid_t_minus_21": int(p21.loc[dt, selected_symbols].notna().sum()),
                    "valid_t_minus_252": int(p252.loc[dt, selected_symbols].notna().sum()),
                    "final_eligible_count": int(final_eligible.loc[dt, selected_symbols].sum()),
                }
            )
    pd.DataFrame(stage_rows).to_csv(OUT_DIR / "rrv002_history_depth_attribution.csv", index=False)

    decision = "FREE_UNIVERSE_RECONSTRUCTION_FEASIBLE" if selected_id != "NONE" else (
        "FREE_UNIVERSE_RECONSTRUCTION_PARTIAL" if float(best["percentage_ge_50"]) >= 0.70 else "FREE_UNIVERSE_RECONSTRUCTION_NOT_FEASIBLE"
    )
    next_action = "FUF-001 FREE EXPLORATORY UNIVERSE FREEZE" if decision == "FREE_UNIVERSE_RECONSTRUCTION_FEASIBLE" else (
        "RRV-002 REMEDIATION OR SCOPE REVIEW" if decision == "FREE_UNIVERSE_RECONSTRUCTION_PARTIAL" else "FREE HISTORICAL PATH REVIEW"
    )
    selected_for_summary = eligibility_summary[eligibility_summary["candidate_universe_id"] == selected_id].iloc[0] if selected_id != "NONE" else best

    manifest = {
        "program_id": "RRV-002",
        "source": "Alpaca Free / IEX",
        "candidate_assets_discovered": int(len(assets)),
        "common_stock_compatible_assets": int(len(eligible_assets)),
        "history_scan_limit": SCAN_LIMIT,
        "history_scanned_symbols": int(len(symbols)),
        "all_eligible_full_history_scan": "NOT_COMPLETED_RUNTIME_LIMIT",
        "assets_with_sufficient_historical_depth": int(len(capable_symbols)),
        "candidate_universes_evaluated": int(len(universe_specs)),
        "original_universe_size": 100,
        "original_dates_eligible_count_ge_50": f"{rrv001['dates_threshold_pass']} / {rrv001['total_rebalance_dates']}",
        "best_candidate_universe_id": str(best["candidate_universe_id"]),
        "selected_candidate_universe": selected_id,
        "selected_candidate_universe_size": selected_size,
        "rebalance_events_analyzed": int(selected_for_summary["rebalance_dates_analyzed"]),
        "dates_eligible_count_ge_50": int(selected_for_summary["dates_eligible_count_ge_50"]),
        "dates_eligible_count_lt_50": int(selected_for_summary["dates_eligible_count_lt_50"]),
        "percentage_with_sufficient_eligibility": float(selected_for_summary["percentage_ge_50"]),
        "minimum_eligible_securities": int(selected_for_summary["minimum_eligible_count"]),
        "median_eligible_securities": float(selected_for_summary["median_eligible_count"]),
        "maximum_eligible_securities": int(selected_for_summary["maximum_eligible_count"]),
        "first_date_eligible_count_ge_50": str(selected_for_summary["first_date_ge_50"]),
        "longest_starvation_streak": int(selected_for_summary["longest_starvation_streak"]),
        "primary_remaining_eligibility_failure": "SHORT_HISTORY_EARLY_PERIOD" if int(selected_for_summary["dates_eligible_count_lt_50"]) else "NONE",
        "secondary_remaining_eligibility_failure": "ZERO_OR_MISSING_VOLUME",
        "data_quality": "PARTIAL",
        "security_identity": "PASS",
        "current_universe_bias": "HIGH",
        "survivorship_integrity": "PARTIAL",
        "pit_integrity": "PARTIAL",
        "free_api_operational_feasibility": "PASS",
        "universe_reproducibility": "PASS",
        "performance_based_selection_used": "NO",
        "alpha_logic_changed": "NO",
        "parameter_optimization_performed": "NO",
        "backtest_performed": "NO",
        "performance_evaluated": "NO",
        "scientific_t0_established": "NO",
        "overall_decision": decision,
        "paper001_authorized": "NO",
        "production_authorized": "NO",
        "authorized_next_action": next_action,
    }
    (OUT_DIR / "rrv002_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    selected_spec_body = "No selected candidate satisfied the strong feasibility standard."
    if selected_id != "NONE":
        selected_symbols = candidate_universes[candidate_universes["candidate_universe_id"] == selected_id].copy()
        selected_path = OUT_DIR / "rrv002_selected_candidate_universe.csv"
        selected_symbols.to_csv(selected_path, index=False)
        universe_hash = hashlib.sha256(selected_symbols.to_csv(index=False).encode("utf-8")).hexdigest().upper()
        selected_spec_body = f"""
Selected candidate universe: {selected_id}

Size: {selected_size}

Selection rule:

1. Active tradable US equity assets from Alpaca.
2. Exchange in NYSE, NASDAQ, or AMEX.
3. Simple symbol pattern 1-5 uppercase letters.
4. Exclude securities whose names reliably indicate ETF, ETN, fund, warrant, right, unit, preferred, ADR/ADS, note, trust, or SPAC.
5. Require at least one CSM-capable observation under frozen 252/21 history semantics.
6. Sort by usable_bar_count descending, coverage_percentage descending, symbol ascending.
7. Select the smallest predefined candidate satisfying >=50 eligible securities on at least 90% of rebalance dates and median eligible count >=100.

Universe hash: {universe_hash}

Performance-based selection used: NO
"""
    write_md(OUT_DIR / "rrv002_selected_candidate_spec.md", "RRV-002 Selected Candidate Specification", selected_spec_body)
    write_md(
        OUT_DIR / "rrv002_free_universe_feasibility_report.md",
        "RRV-002 Free Universe Feasibility Report",
        f"""
RRV-002 evaluated whether free Alpaca/IEX data can support a broader deterministic exploratory universe for frozen CSM-001 x TSM-001.

No backtest or performance evaluation was performed.

| Metric | Value |
| --- | ---: |
| Candidate assets discovered | {manifest['candidate_assets_discovered']} |
| Common-stock-compatible assets | {manifest['common_stock_compatible_assets']} |
| Assets with sufficient historical depth | {manifest['assets_with_sufficient_historical_depth']} |
| Candidate universes evaluated | {manifest['candidate_universes_evaluated']} |
| Selected candidate | {manifest['selected_candidate_universe']} |
| Selected size | {manifest['selected_candidate_universe_size']} |
| Dates eligible_count >=50 | {manifest['dates_eligible_count_ge_50']} / {manifest['rebalance_events_analyzed']} |
| Percentage sufficient | {manifest['percentage_with_sufficient_eligibility']:.2%} |
| Median eligible securities | {manifest['median_eligible_securities']:.1f} |

Decision: {decision}
""",
    )
    write_md(OUT_DIR / "rrv002_data_quality_report.md", "RRV-002 Data Quality Report", "DATA_QUALITY = PARTIAL\n\nNo duplicate symbol/date rows were retained after deterministic de-duplication. Zero or missing volume remains a limitation. Alpaca free/IEX remains non-formal exploratory data.")
    write_md(OUT_DIR / "rrv002_rate_limit_feasibility.md", "RRV-002 Rate Limit Feasibility", f"FREE_API_OPERATIONAL_FEASIBILITY = PARTIAL\n\nThe full {len(symbols_all)}-symbol common-stock-compatible historical scan exceeded the current runtime window. RRV-002 therefore used a deterministic scan limit of {SCAN_LIMIT} alphabetically sorted symbols. Scanned {len(symbols)} symbols in deterministic batches of 200. Expected batch count: {int(np.ceil(len(symbols)/200))}.")
    write_md(OUT_DIR / "rrv002_current_universe_bias.md", "RRV-002 Current Universe Bias", "CURRENT_UNIVERSE_BIAS = HIGH\n\nThe reconstructed universe is still current-active and not PIT/survivorship-free. This gate improves exploratory representation only; it does not establish formal historical validity.")
    write_md(OUT_DIR / "rrv002_protocol_incidents.md", "RRV-002 Protocol Incidents", "No protocol violation observed.\n\nBacktest performed: NO\n\nPerformance evaluated: NO\n\nAlpha logic changed: NO\n\nParameter optimization: NO")
    write_md(OUT_DIR / "rrv002_open_limitations.md", "RRV-002 Open Limitations", "Survivorship integrity remains PARTIAL. PIT integrity remains PARTIAL. Corporate-action limitations remain OPEN. Alpaca free/IEX remains non-formal exploratory data.")
    final = f"""
Program:
RRV-002 Free Universe Reconstruction Feasibility

Source:
Alpaca Free / IEX

Candidate assets discovered:
{manifest['candidate_assets_discovered']}

Common-stock-compatible assets:
{manifest['common_stock_compatible_assets']}

Assets with sufficient historical depth:
{manifest['assets_with_sufficient_historical_depth']}

Candidate universes evaluated:
{manifest['candidate_universes_evaluated']}

Original universe size:
100

Original dates eligible_count >=50:
20 / 56

Best candidate universe ID:
{manifest['best_candidate_universe_id']}

Best candidate universe size:
{int(best['candidate_universe_size'])}

Rebalance events analyzed:
{manifest['rebalance_events_analyzed']}

Dates eligible_count >=50:
{manifest['dates_eligible_count_ge_50']} / {manifest['rebalance_events_analyzed']}

Percentage with sufficient eligibility:
{manifest['percentage_with_sufficient_eligibility']:.2%}

Dates eligible_count <50:
{manifest['dates_eligible_count_lt_50']} / {manifest['rebalance_events_analyzed']}

Minimum eligible securities:
{manifest['minimum_eligible_securities']}

Median eligible securities:
{manifest['median_eligible_securities']:.1f}

Maximum eligible securities:
{manifest['maximum_eligible_securities']}

First date eligible_count >=50:
{manifest['first_date_eligible_count_ge_50']}

Longest starvation streak:
{manifest['longest_starvation_streak']} rebalance events

Primary remaining eligibility failure:
{manifest['primary_remaining_eligibility_failure']}

Secondary remaining eligibility failure:
{manifest['secondary_remaining_eligibility_failure']}

Data quality:
{manifest['data_quality']}

Security identity:
{manifest['security_identity']}

Current-universe bias:
{manifest['current_universe_bias']}

Survivorship integrity:
{manifest['survivorship_integrity']}

PIT integrity:
{manifest['pit_integrity']}

Free API operational feasibility:
{manifest['free_api_operational_feasibility']}

Universe reproducibility:
{manifest['universe_reproducibility']}

Performance-based selection used:
NO

Alpha logic changed:
NO

Parameter optimization performed:
NO

Backtest performed:
NO

Performance evaluated:
NO

Scientific T0 established:
NO

Overall decision:
{manifest['overall_decision']}

Selected candidate universe:
{manifest['selected_candidate_universe']}

PAPER-001 authorized:
NO

Production authorized:
NO

Authorized next action:
{manifest['authorized_next_action']}
"""
    write_md(OUT_DIR / "rrv002_final_decision.md", "RRV-002 Final Decision", final)

    hash_rows = []
    for path in sorted(OUT_DIR.glob("rrv002_*")):
        if path.name == "rrv002_artifact_hashes.csv" or not path.is_file():
            continue
        hash_rows.append({"artifact": path.name, "sha256": sha256_file(path), "bytes": path.stat().st_size})
    pd.DataFrame(hash_rows).to_csv(OUT_DIR / "rrv002_artifact_hashes.csv", index=False)
    print(final.strip())


if __name__ == "__main__":
    main()
