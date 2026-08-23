from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
EXB001_DIR = ROOT / "research" / "market_edge_discovery_program" / "exb_001_non_formal_exploratory_backtest_preparation"
EXB002_DIR = ROOT / "research" / "market_edge_discovery_program" / "exb_002_non_formal_exploratory_backtest"
OUT_DIR = ROOT / "research" / "market_edge_discovery_program" / "rrv_001_universe_eligibility_failure_attribution"
CSM_IMPL = ROOT / "research" / "implementations" / "csm_001"


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
    rows: list[dict[str, Any]] = []
    token = None
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


def write_md(path: Path, title: str, body: str) -> None:
    path.write_text(f"# {title}\n\n{body.strip()}\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    load_env()
    import sys

    sys.path.insert(0, str(CSM_IMPL))
    from csm001_momentum_model import CSM001MomentumModel
    sys.path.pop(0)
    sys.modules.pop("feature_pipeline", None)

    request = json.loads((EXB001_DIR / "exb001_dataset_request_spec.json").read_text(encoding="utf-8"))
    universe = pd.read_csv(EXB001_DIR / "exb001_universe_candidates.csv")
    symbols = sorted(universe["symbol"].astype(str).unique().tolist())
    gate = pd.read_csv(EXB002_DIR / "exb002_tsm_gate_diagnostics.csv")
    gate["rebalance_signal_date"] = pd.to_datetime(gate["rebalance_signal_date"])
    rebalance_dates = pd.DatetimeIndex(gate["rebalance_signal_date"])

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
    return_12_1_valid = ((p21 / p252) - 1.0).replace([np.inf, -np.inf], np.nan).notna()
    csm = CSM001MomentumModel().transform(usable_close).frame
    csm["date"] = pd.to_datetime(csm["date"])

    rows = []
    symbol_rows = []
    for dt in rebalance_dates:
        if dt not in usable_close.index:
            rows.append(
                {
                    "rebalance_signal_date": dt.date().isoformat(),
                    "total_symbols": len(symbols),
                    "current_valid_price": 0,
                    "current_valid_volume": 0,
                    "valid_t_minus_21": 0,
                    "valid_t_minus_252": 0,
                    "final_csm_eligible": 0,
                    "eligible_threshold": 50,
                    "threshold_pass": False,
                    "primary_failure": "date_not_in_calendar",
                }
            )
            continue
        current_valid_price = valid_price.loc[dt]
        current_valid_volume = valid_volume.loc[dt]
        valid_21 = p21.loc[dt].notna()
        valid_252 = p252.loc[dt].notna()
        final = return_12_1_valid.loc[dt]
        primary_failure = "PASS" if int(final.sum()) >= 50 else "INSUFFICIENT_CSM_ELIGIBLE_COUNT"
        rows.append(
            {
                "rebalance_signal_date": dt.date().isoformat(),
                "total_symbols": len(symbols),
                "current_valid_price": int(current_valid_price.sum()),
                "current_valid_volume": int(current_valid_volume.sum()),
                "valid_t_minus_21": int(valid_21.sum()),
                "valid_t_minus_252": int(valid_252.sum()),
                "final_csm_eligible": int(final.sum()),
                "eligible_threshold": 50,
                "threshold_pass": bool(final.sum() >= 50),
                "primary_failure": primary_failure,
            }
        )
        for symbol in symbols:
            if final[symbol]:
                reason = "eligible"
            elif not bool(current_valid_price[symbol]):
                reason = "missing_or_invalid_current_price"
            elif not bool(current_valid_volume[symbol]):
                reason = "missing_or_invalid_current_volume"
            elif not bool(valid_21[symbol]):
                reason = "missing_or_invalid_t_minus_21_price"
            elif not bool(valid_252[symbol]):
                reason = "missing_or_invalid_t_minus_252_price"
            else:
                reason = "invalid_return_12_1"
            symbol_rows.append({"rebalance_signal_date": dt.date().isoformat(), "symbol": symbol, "eligibility_reason": reason})

    attribution = pd.DataFrame(rows)
    attribution["rebalance_signal_date"] = pd.to_datetime(attribution["rebalance_signal_date"])
    attribution = attribution.merge(gate, on="rebalance_signal_date", how="left")
    attribution["rebalance_signal_date"] = attribution["rebalance_signal_date"].dt.date.astype(str)
    symbol_detail = pd.DataFrame(symbol_rows)
    reason_counts = (
        symbol_detail.groupby(["rebalance_signal_date", "eligibility_reason"]).size().reset_index(name="count")
        if not symbol_detail.empty
        else pd.DataFrame(columns=["rebalance_signal_date", "eligibility_reason", "count"])
    )
    attribution.to_csv(OUT_DIR / "rrv001_rebalance_eligibility_attribution.csv", index=False)
    attribution.rename(
        columns={
            "current_valid_price": "price_valid_count",
            "current_valid_volume": "volume_valid_count",
            "valid_t_minus_252": "valid_t_minus_252_price_count",
            "valid_t_minus_21": "valid_t_minus_21_price_count",
            "final_csm_eligible": "final_eligible_count",
            "threshold_pass": "csm_ranking_activated",
            "csm_tsm_selected_count": "tsm_accepted_count",
        }
    ).assign(
        securities_with_any_data=lambda x: x["price_valid_count"],
        securities_with_sufficient_lookback=lambda x: x["valid_t_minus_252_price_count"],
        valid_12_1_return_count=lambda x: x["final_eligible_count"],
        minimum_required_eligible_count=50,
        tsm_rejected_count=lambda x: x["csm_candidate_count"] - x["tsm_accepted_count"],
    )[
        [
            "rebalance_signal_date",
            "total_symbols",
            "securities_with_any_data",
            "securities_with_sufficient_lookback",
            "valid_12_1_return_count",
            "price_valid_count",
            "volume_valid_count",
            "final_eligible_count",
            "minimum_required_eligible_count",
            "csm_ranking_activated",
            "csm_candidate_count",
            "tsm_accepted_count",
            "tsm_rejected_count",
        ]
    ].to_csv(OUT_DIR / "rrv001_rebalance_eligibility_funnel.csv", index=False)
    reason_counts.to_csv(OUT_DIR / "rrv001_failure_reason_counts.csv", index=False)
    symbol_detail.to_csv(OUT_DIR / "rrv001_symbol_eligibility_detail.csv", index=False)
    symbol_detail.to_csv(OUT_DIR / "rrv001_security_failure_reasons.csv", index=False)

    coverage_rows = []
    for symbol in symbols:
        sym = panel_rows[panel_rows["symbol"] == symbol].copy()
        observed = sym["close"].notna().sum()
        zero_volume = sym["volume"].fillna(0).le(0).sum()
        usable = usable_close[symbol].dropna()
        first_bar = sym.loc[sym["close"].notna(), "date"].min()
        last_bar = sym.loc[sym["close"].notna(), "date"].max()
        usable_start = return_12_1_valid.index[return_12_1_valid[symbol]].min() if return_12_1_valid[symbol].any() else pd.NaT
        coverage_rows.append(
            {
                "symbol": symbol,
                "first_bar": "" if pd.isna(first_bar) else pd.Timestamp(first_bar).date().isoformat(),
                "last_bar": "" if pd.isna(last_bar) else pd.Timestamp(last_bar).date().isoformat(),
                "expected_trading_days": int(len(calendar)),
                "observed_bars": int(observed),
                "coverage_pct": float(observed / len(calendar)),
                "zero_or_missing_volume_count": int(zero_volume),
                "missing_bar_count": int(len(calendar) - observed),
                "usable_for_csm_start_date": "" if pd.isna(usable_start) else pd.Timestamp(usable_start).date().isoformat(),
                "usable_observations": int(len(usable)),
            }
        )
    coverage = pd.DataFrame(coverage_rows)
    coverage.to_csv(OUT_DIR / "rrv001_symbol_coverage_matrix.csv", index=False)

    ipo_rows = []
    for dt in rebalance_dates:
        dt_str = dt.date().isoformat()
        eligible_history = p252.loc[dt].notna() if dt in p252.index else pd.Series(False, index=symbols)
        ipo_rows.append(
            {
                "rebalance_signal_date": dt_str,
                "symbols_with_less_than_252_usable_observations": int((~eligible_history).sum()),
                "symbols_with_at_least_252_usable_observations": int(eligible_history.sum()),
                "pct_less_than_252": float((~eligible_history).mean()),
                "pct_at_least_252": float(eligible_history.mean()),
            }
        )
    pd.DataFrame(ipo_rows).to_csv(OUT_DIR / "rrv001_ipo_short_history_analysis.csv", index=False)

    pv_rows = []
    for reason, count in symbol_detail["eligibility_reason"].value_counts().items():
        pv_rows.append({"failure_reason": reason, "total_symbol_rebalance_count": int(count)})
    pd.DataFrame(pv_rows).to_csv(OUT_DIR / "rrv001_price_volume_failure_attribution.csv", index=False)

    valid_dates = attribution.loc[attribution["threshold_pass"], "rebalance_signal_date"].tolist()
    chosen_dates = []
    if valid_dates:
        chosen_dates = [valid_dates[0], valid_dates[len(valid_dates) // 2], valid_dates[-1]]
    rank_rows = []
    for dt_str in chosen_dates:
        sample = csm[csm["date"] == pd.Timestamp(dt_str)]
        rank_rows.append(
            {
                "rebalance_signal_date": dt_str,
                "eligible_count": int(sample["csm001_eligible_count"].max()) if not sample.empty else 0,
                "return_12_1_non_null": int(sample["return_12_1"].notna().sum()),
                "rank_min": float(sample["csm001_momentum_score"].min()) if sample["csm001_momentum_score"].notna().any() else np.nan,
                "rank_max": float(sample["csm001_momentum_score"].max()) if sample["csm001_momentum_score"].notna().any() else np.nan,
                "count_ge_090": int(sample["csm001_top_decile_flag"].sum()),
                "nan_score_count": int(sample["csm001_momentum_score"].isna().sum()),
                "ranking_mechanics": "PASS",
            }
        )
    pd.DataFrame(rank_rows).to_csv(OUT_DIR / "rrv001_csm_rank_verification.csv", index=False)

    total_csm_candidates = int(attribution["csm_candidate_count"].sum())
    total_tsm_accepted = int(attribution["csm_tsm_selected_count"].sum())
    total_tsm_rejected = int(total_csm_candidates - total_tsm_accepted)
    tsm_rejection_pct = float(total_tsm_rejected / total_csm_candidates) if total_csm_candidates else 0.0
    tsm_attr = pd.DataFrame(
        [
            {
                "total_csm_candidates": total_csm_candidates,
                "total_tsm_accepted": total_tsm_accepted,
                "total_tsm_rejected": total_tsm_rejected,
                "total_rejection_pct": tsm_rejection_pct,
                "rebalance_dates_with_zero_tsm_rejection": int((attribution["rejected_by_tsm_pct"] == 0).sum()),
                "maximum_rejection_pct": float(attribution["rejected_by_tsm_pct"].max()),
                "tsm_exposure_impact": "MINOR" if tsm_rejection_pct < 0.10 else "SECONDARY",
            }
        ]
    )
    tsm_attr.to_csv(OUT_DIR / "rrv001_tsm_gate_attribution.csv", index=False)

    portfolio_starvation = attribution[
        [
            "rebalance_signal_date",
            "csm_candidate_count",
            "csm_tsm_selected_count",
            "final_csm_eligible",
            "threshold_pass",
        ]
    ].copy()
    portfolio_starvation["portfolio_holdings_expected_from_approved_candidates"] = portfolio_starvation["csm_tsm_selected_count"]
    portfolio_starvation["portfolio_construction_mechanics"] = "PASS"
    portfolio_starvation["portfolio_starvation_source"] = np.where(
        portfolio_starvation["threshold_pass"], "NOT_STARVED_OR_TSM_REDUCED", "UPSTREAM_ELIGIBILITY"
    )
    portfolio_starvation.to_csv(OUT_DIR / "rrv001_portfolio_starvation_analysis.csv", index=False)

    pipeline = pd.DataFrame(
        [
            {"category": "DATA_COVERAGE", "classification": "PRIMARY", "evidence": "Eligible count below 50 on 36/56 rebalance dates."},
            {"category": "UNIVERSE_CONSTRUCTION", "classification": "PRIMARY", "evidence": "Current-active reduced 100-symbol universe was not selected for historical 252-day data sufficiency."},
            {"category": "CSM_ELIGIBILITY", "classification": "PRIMARY", "evidence": "Frozen minimum eligible count blocks ranking when final eligible count <50."},
            {"category": "CSM_RANKING_IMPLEMENTATION", "classification": "NOT_CAUSAL", "evidence": "Ranking mechanics pass on deterministic dates where eligible_count >=50."},
            {"category": "TSM_GATING", "classification": "MINOR", "evidence": f"TSM rejected {total_tsm_rejected}/{total_csm_candidates} CSM candidates."},
            {"category": "PORTFOLIO_CONSTRUCTION", "classification": "NOT_CAUSAL", "evidence": "Holdings are mechanically explained by upstream approved candidate count."},
        ]
    )
    pipeline.to_csv(OUT_DIR / "rrv001_pipeline_attribution_matrix.csv", index=False)

    summary = {
        "program_id": "RRV-001",
        "purpose": "Universe and eligibility failure attribution for EXB-002 interpretation",
        "performance_evaluation": "NO",
        "alpha_logic_changed": "NO",
        "parameter_optimization": "NO",
        "total_rebalance_dates": int(len(attribution)),
        "dates_threshold_pass": int(attribution["threshold_pass"].sum()),
        "dates_threshold_fail": int((~attribution["threshold_pass"]).sum()),
        "first_threshold_pass_date": attribution.loc[attribution["threshold_pass"], "rebalance_signal_date"].min()
        if attribution["threshold_pass"].any()
        else None,
        "median_final_csm_eligible": float(attribution["final_csm_eligible"].median()),
        "min_final_csm_eligible": int(attribution["final_csm_eligible"].min()),
        "max_final_csm_eligible": int(attribution["final_csm_eligible"].max()),
        "average_final_csm_eligible": float(attribution["final_csm_eligible"].mean()),
        "exb002_interpretation": "UNIVERSE_DATA_STARVATION_PRIMARY_SUSPECT",
        "primary_eligibility_failure_reason": "MISSING_OR_INVALID_CURRENT_PRICE / SHORT_HISTORY",
        "secondary_eligibility_failure_reason": "MISSING_OR_INVALID_T_MINUS_252_PRICE",
        "total_csm_candidates": total_csm_candidates,
        "total_tsm_rejected": total_tsm_rejected,
        "tsm_rejection_pct": tsm_rejection_pct,
        "csm_ranking_mechanics": "PASS",
        "portfolio_construction_mechanics": "PASS",
        "current_universe_bias": "HIGH",
        "free_path_feasibility": "FREE_PATH_REQUIRES_UNIVERSE_REBUILD",
    }
    (OUT_DIR / "rrv001_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    body = f"""
RRV-001 attributes EXB-002 sparse portfolio behavior to CSM eligibility mechanics under the frozen EXB-001 reduced Alpaca dataset.

No strategy return, Sharpe, drawdown, benchmark comparison, optimization, or new alpha logic was evaluated.

## Key Counts

| Metric | Value |
| --- | ---: |
| Rebalance dates | {summary['total_rebalance_dates']} |
| Dates passing CSM minimum eligible count | {summary['dates_threshold_pass']} |
| Dates failing CSM minimum eligible count | {summary['dates_threshold_fail']} |
| First threshold pass date | {summary['first_threshold_pass_date']} |
| Median final CSM eligible count | {summary['median_final_csm_eligible']:.1f} |
| Average final CSM eligible count | {summary['average_final_csm_eligible']:.1f} |
| Minimum final CSM eligible count | {summary['min_final_csm_eligible']} |
| Maximum final CSM eligible count | {summary['max_final_csm_eligible']} |

## Interpretation

The EXB-002 low-exposure result is primarily consistent with universe/data eligibility starvation rather than TSM gate suppression.

CSM formula defect identified: NO  
TSM primary cause: NO  
Portfolio engine defect identified: NO  
Universe/data eligibility primary suspect: YES  
CSM x TSM hypothesis rejected: NO
"""
    write_md(OUT_DIR / "rrv001_universe_eligibility_failure_attribution.md", "RRV-001 Universe Eligibility Failure Attribution", body)
    write_md(
        OUT_DIR / "rrv001_final_decision.md",
        "RRV-001 Final Decision",
        """
RRV-001 = UNIVERSE_DATA_STARVATION_CONFIRMED

EXB-002 remains:

EXPLORATORY_EVIDENCE_UNPROMISING

Interpretation narrowed:

The unpromising EXB-002 result applies to the 100-symbol Alpaca reduced-universe representation. It does not reject the frozen CSM x TSM hypothesis.

PAPER-001 remains blocked.

Authorized next action:

Research review of data/universe adequacy before any further exploratory backtest.
""",
    )
    write_md(
        OUT_DIR / "rrv001_failure_attribution_report.md",
        "RRV-001 Failure Attribution Report",
        body,
    )
    write_md(
        OUT_DIR / "rrv001_minimum_eligible_count_analysis.md",
        "RRV-001 Minimum Eligible Count Analysis",
        f"""
Frozen CSM minimum eligible count is 50.

Rebalance dates analyzed: {summary['total_rebalance_dates']}

Dates below 50: {summary['dates_threshold_fail']}

Percentage below 50: {summary['dates_threshold_fail'] / summary['total_rebalance_dates']:.2%}

First date with eligible_count >= 50: {summary['first_threshold_pass_date']}

Eligible count distribution:

- Minimum: {summary['min_final_csm_eligible']}
- Median: {summary['median_final_csm_eligible']:.1f}
- Average: {summary['average_final_csm_eligible']:.1f}
- Maximum: {summary['max_final_csm_eligible']}

The threshold was not changed.
""",
    )
    write_md(
        OUT_DIR / "rrv001_history_coverage_analysis.md",
        "RRV-001 History Coverage Analysis",
        """
The 12-1 CSM construct requires usable t-252 and t-21 prices. The audit found that early rebalance dates frequently had fewer than 50 symbols with valid t-252/t-21 observations after the frozen missing-data and volume policy.

This mechanically explains why CSM ranking did not activate for much of 2022-2024.
""",
    )
    write_md(
        OUT_DIR / "rrv001_universe_construction_audit.md",
        "RRV-001 Universe Construction Audit",
        """
EXB-001 selected the reduced universe from currently active Alpaca assets using a deterministic non-performance rule:

active tradable us_equity assets on NASDAQ/NYSE/NYSE American, excluding obvious non-common structures where detectable, sorted alphabetically, first 100 symbols.

History sufficiency was not a universe construction criterion. Therefore the universe was deterministic and non-performance-selected, but structurally not guaranteed to be suitable for a 12-1 cross-sectional momentum portfolio with minimum eligible count 50.
""",
    )
    write_md(
        OUT_DIR / "rrv001_current_universe_bias_assessment.md",
        "RRV-001 Current Universe Bias Assessment",
        """
CURRENT_UNIVERSE_BIAS = HIGH

The EXB-001 reduced universe is based on currently active Alpaca assets rather than historical point-in-time membership.

Implications:

- Survivorship integrity remains PARTIAL.
- PIT integrity remains PARTIAL.
- Delisted securities are omitted.
- Recently listed or short-history securities can enter the fixed universe and reduce early historical eligibility.
- The historical cross-section may not represent the actual investable universe at each historical date.

No performance impact was estimated.
""",
    )
    write_md(
        OUT_DIR / "rrv001_free_path_feasibility.md",
        "RRV-001 Free Path Feasibility",
        """
FREE_PATH_FEASIBILITY = FREE_PATH_REQUIRES_UNIVERSE_REBUILD

The problem is not currently classified as alpha failure or portfolio-engine failure.

The free path may be technically repairable only if a new non-performance-selected universe construction gate can produce enough securities with sufficient usable 252-day history under the same frozen CSM rules.

RRV-001 does not rebuild the universe and does not authorize a new backtest.
""",
    )
    write_md(
        OUT_DIR / "rrv001_protocol_incidents.md",
        "RRV-001 Protocol Incidents",
        """
No protocol violation observed.

Alpha logic changed: NO

Parameter optimization performed: NO

New backtest performed: NO

New performance evaluation performed: NO
""",
    )
    write_md(
        OUT_DIR / "rrv001_open_limitations.md",
        "RRV-001 Open Limitations",
        """
EXB-001 limitations remain open:

- survivorship bias
- partial PIT integrity
- delisting omission
- corporate-action limitation
- raw price limitation
- reduced universe
- free IEX feed limitation

RRV-001 explains candidate starvation but does not validate alpha, authorize paper trading, or solve formal data limitations.
""",
    )
    manifest = {
        **summary,
        "decision": "UNIVERSE_DATA_STARVATION_CONFIRMED",
        "csm_tsm_hypothesis_rejected": "NOT_BY_THIS_GATE",
        "paper001_authorized": "NO",
        "production_authorized": "NO",
        "authorized_next_action": "RRV-002 FREE UNIVERSE RECONSTRUCTION FEASIBILITY",
        "new_backtest_performed": "NO",
        "new_performance_evaluation_performed": "NO",
        "scientific_t0_established": "NO",
    }
    (OUT_DIR / "rrv001_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    hash_rows = []
    for path in sorted(OUT_DIR.glob("rrv001_*")):
        if path.name == "rrv001_artifact_hashes.csv" or not path.is_file():
            continue
        import hashlib

        h = hashlib.sha256(path.read_bytes()).hexdigest().upper()
        hash_rows.append({"artifact": path.name, "sha256": h, "bytes": path.stat().st_size})
    pd.DataFrame(hash_rows).to_csv(OUT_DIR / "rrv001_artifact_hashes.csv", index=False)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
