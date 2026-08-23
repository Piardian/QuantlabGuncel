from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent

WLC001 = ROOT / "research" / "market_edge_discovery_program" / "wlc_001_workflow_liquidity_capacity_protocol" / "wlc001_manifest.json"
CSM_STATE = ROOT / "output" / "csm_001_cv001" / "csm001_construct_state.csv"
TSM_STATE = ROOT / "output" / "tsm_001_cv001" / "tsm001_construct_state.csv"
OOS_PANEL = ROOT / "research" / "market_edge_discovery_program" / "wor_002_workflow_oos_reproducibility_audit" / "oos_adjusted_close_panel.csv"
UNIVERSE = ROOT / "sp500_current_universe.csv"
CSM_PIPELINE = ROOT / "research" / "implementations" / "csm_001" / "feature_pipeline.py"
TSM_PIPELINE = ROOT / "research" / "implementations" / "tsm_001" / "feature_pipeline.py"

DOWNLOAD_START = "2010-01-01"
DOWNLOAD_END = "2026-08-04"
OOS_START_AFTER = pd.Timestamp("2025-12-30")
LIQUIDITY_THRESHOLDS = [10_000_000, 50_000_000, 100_000_000]
ACCOUNT_SIZES = [100_000, 1_000_000, 10_000_000]
PARTICIPATION_LIMITS = [0.01, 0.05]


def load_class(module_path: Path, module_name: str, class_name: str):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {module_path}")
    module = importlib.util.module_from_spec(spec)
    import sys
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return getattr(module, class_name)


CSM001FeaturePipeline = load_class(CSM_PIPELINE, "wlc002_csm_pipeline", "CSM001FeaturePipeline")
TSM001FeaturePipeline = load_class(TSM_PIPELINE, "wlc002_tsm_pipeline", "TSM001FeaturePipeline")


def to_yahoo(ticker: str) -> str:
    return ticker.replace(".", "-")


def from_yahoo(symbol: str, lookup: dict[str, str]) -> str:
    return lookup.get(symbol, symbol.replace("-", "."))


def load_universe() -> list[str]:
    df = pd.read_csv(UNIVERSE)
    return sorted(df["ticker"].dropna().astype(str).str.strip().unique())


def download_ohlcv(tickers: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    yahoo_symbols = [to_yahoo(t) for t in tickers]
    lookup = dict(zip(yahoo_symbols, tickers))
    close_chunks: list[pd.DataFrame] = []
    volume_chunks: list[pd.DataFrame] = []
    failed: list[str] = []
    for start in range(0, len(yahoo_symbols), 80):
        symbols = yahoo_symbols[start : start + 80]
        try:
            data = yf.download(
                tickers=symbols,
                start=DOWNLOAD_START,
                end=DOWNLOAD_END,
                auto_adjust=False,
                progress=False,
                group_by="column",
                threads=True,
            )
        except Exception:
            failed.extend(from_yahoo(s, lookup) for s in symbols)
            continue
        if data.empty:
            failed.extend(from_yahoo(s, lookup) for s in symbols)
            continue
        if isinstance(data.columns, pd.MultiIndex):
            close_key = "Close" if "Close" in data.columns.get_level_values(0) else "Adj Close"
            if close_key not in data.columns.get_level_values(0) or "Volume" not in data.columns.get_level_values(0):
                failed.extend(from_yahoo(s, lookup) for s in symbols)
                continue
            close = data[close_key].copy()
            volume = data["Volume"].copy()
        else:
            if "Volume" not in data.columns:
                failed.extend(from_yahoo(s, lookup) for s in symbols)
                continue
            close_key = "Close" if "Close" in data.columns else "Adj Close"
            close = data[[close_key]].copy()
            volume = data[["Volume"]].copy()
            close.columns = symbols[:1]
            volume.columns = symbols[:1]
        close = close.rename(columns=lambda s: from_yahoo(str(s), lookup))
        volume = volume.rename(columns=lambda s: from_yahoo(str(s), lookup))
        close_chunks.append(close)
        volume_chunks.append(volume)
    if not close_chunks:
        return pd.DataFrame(), pd.DataFrame(), sorted(set(failed))
    close_panel = pd.concat(close_chunks, axis=1)
    volume_panel = pd.concat(volume_chunks, axis=1)
    close_panel = close_panel.loc[:, ~close_panel.columns.duplicated()].reindex(sorted(set(close_panel.columns)), axis=1)
    volume_panel = volume_panel.loc[:, ~volume_panel.columns.duplicated()].reindex(close_panel.columns, axis=1)
    close_panel.index = pd.to_datetime(close_panel.index).tz_localize(None)
    volume_panel.index = pd.to_datetime(volume_panel.index).tz_localize(None)
    all_nan = sorted(c for c in volume_panel.columns if volume_panel[c].notna().sum() == 0)
    missing = sorted(set(tickers) - set(volume_panel.columns))
    return close_panel, volume_panel, sorted(set(failed).union(all_nan).union(missing))


def reference_states() -> pd.DataFrame:
    csm = pd.read_csv(CSM_STATE, parse_dates=["date"])
    tsm = pd.read_csv(TSM_STATE, parse_dates=["date"], low_memory=False)
    return prepare_states(csm, tsm, "reference")


def oos_states() -> pd.DataFrame:
    close = pd.read_csv(OOS_PANEL, index_col=0, parse_dates=True)
    close.index = pd.to_datetime(close.index).tz_localize(None)
    csm = CSM001FeaturePipeline().build_features(close)
    tsm = TSM001FeaturePipeline().build_features(close)
    return prepare_states(csm, tsm, "oos")


def prepare_states(csm: pd.DataFrame, tsm: pd.DataFrame, sample: str) -> pd.DataFrame:
    merged = csm[["date", "ticker", "adjusted_close", "csm001_top_decile_flag", "csm001_valid_observation"]].merge(
        tsm[["date", "ticker", "tsm001_positive_state", "tsm001_valid_observation"]],
        on=["date", "ticker"],
        how="inner",
        validate="one_to_one",
    )
    merged["date"] = pd.to_datetime(merged["date"]).dt.tz_localize(None)
    merged = merged[merged["csm001_valid_observation"] & merged["tsm001_valid_observation"]].copy()
    if sample == "reference":
        merged = merged[merged["date"] <= OOS_START_AFTER].copy()
    else:
        merged = merged[merged["date"] > OOS_START_AFTER].copy()
    merged["sample"] = sample
    merged["workflow_state"] = np.where(
        merged["csm001_top_decile_flag"] & merged["tsm001_positive_state"],
        "CSM_HIGH_x_TSM_HIGH",
        np.where((~merged["csm001_top_decile_flag"]) & merged["tsm001_positive_state"], "CSM_NOT_HIGH_x_TSM_HIGH", "OTHER"),
    )
    return merged


def build_liquidity_features(close: pd.DataFrame, volume: pd.DataFrame) -> pd.DataFrame:
    dollar = close * volume
    adv20 = dollar.rolling(20, min_periods=10).mean()
    adv60 = dollar.rolling(60, min_periods=30).mean()
    records = []
    for ticker in dollar.columns:
        records.append(
            pd.DataFrame(
                {
                    "date": dollar.index,
                    "ticker": ticker,
                    "close": close[ticker].to_numpy(dtype=float),
                    "volume": volume[ticker].to_numpy(dtype=float),
                    "dollar_volume": dollar[ticker].to_numpy(dtype=float),
                    "adv20": adv20[ticker].to_numpy(dtype=float),
                    "adv60": adv60[ticker].to_numpy(dtype=float),
                }
            )
        )
    return pd.concat(records, ignore_index=True)


def selected_name_liquidity(states: pd.DataFrame, liquidity: pd.DataFrame) -> pd.DataFrame:
    selected = states[states["workflow_state"].eq("CSM_HIGH_x_TSM_HIGH")].copy()
    return selected.merge(liquidity, on=["date", "ticker"], how="left", validate="many_to_one")


def data_availability(close: pd.DataFrame, volume: pd.DataFrame, failed: list[str], selected: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "download_start": DOWNLOAD_START,
                "download_end_exclusive": DOWNLOAD_END,
                "downloaded_close_columns": int(close.shape[1]),
                "downloaded_volume_columns": int(volume.shape[1]),
                "failed_symbols": len(failed),
                "selected_observations": int(len(selected)),
                "selected_with_volume": int(selected["volume"].notna().sum()) if "volume" in selected else 0,
                "selected_with_adv20": int(selected["adv20"].notna().sum()) if "adv20" in selected else 0,
                "selected_with_adv60": int(selected["adv60"].notna().sum()) if "adv60" in selected else 0,
                "volume_coverage": float(selected["volume"].notna().mean()) if len(selected) else np.nan,
                "adv20_coverage": float(selected["adv20"].notna().mean()) if len(selected) else np.nan,
                "adv60_coverage": float(selected["adv60"].notna().mean()) if len(selected) else np.nan,
            }
        ]
    )


def threshold_results(selected: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for sample, group in selected.groupby("sample"):
        for threshold in LIQUIDITY_THRESHOLDS:
            rows.append(
                {
                    "sample": sample,
                    "adv_threshold": threshold,
                    "observations": int(len(group)),
                    "adv20_pass_rate": float((group["adv20"] >= threshold).mean()) if len(group) else np.nan,
                    "adv60_pass_rate": float((group["adv60"] >= threshold).mean()) if len(group) else np.nan,
                    "median_adv20": float(group["adv20"].median()) if len(group) else np.nan,
                    "median_adv60": float(group["adv60"].median()) if len(group) else np.nan,
                }
            )
    return pd.DataFrame(rows)


def capacity_results(selected: pd.DataFrame) -> pd.DataFrame:
    daily_counts = selected.groupby(["sample", "date"])["ticker"].nunique().rename("position_count").reset_index()
    enriched = selected.merge(daily_counts, on=["sample", "date"], how="left")
    rows = []
    for sample, group in enriched.groupby("sample"):
        for account in ACCOUNT_SIZES:
            position_dollars = account / group["position_count"].replace(0, np.nan)
            for limit in PARTICIPATION_LIMITS:
                ratio20 = position_dollars / group["adv20"]
                ratio60 = position_dollars / group["adv60"]
                rows.append(
                    {
                        "sample": sample,
                        "account_size": account,
                        "participation_limit": limit,
                        "observations": int(len(group)),
                        "pass_rate_adv20": float((ratio20 <= limit).mean()),
                        "pass_rate_adv60": float((ratio60 <= limit).mean()),
                        "median_participation_adv20": float(ratio20.median()),
                        "median_participation_adv60": float(ratio60.median()),
                    }
                )
    return pd.DataFrame(rows)


def oos_check(thresholds: pd.DataFrame, capacity: pd.DataFrame) -> pd.DataFrame:
    thr = thresholds[(thresholds["sample"] == "oos") & (thresholds["adv_threshold"] == 50_000_000)]
    cap = capacity[(capacity["sample"] == "oos") & (capacity["account_size"].isin([100_000, 1_000_000])) & (capacity["participation_limit"] == 0.01)]
    return pd.DataFrame(
        [
            {
                "oos_adv50_pass_rate_adv20": float(thr["adv20_pass_rate"].iloc[0]) if len(thr) else np.nan,
                "oos_adv50_pass_rate_adv60": float(thr["adv60_pass_rate"].iloc[0]) if len(thr) else np.nan,
                "oos_100k_1m_1pct_all_pass_adv20": bool((cap["pass_rate_adv20"] >= 0.95).all()) if len(cap) else False,
                "oos_100k_1m_1pct_all_pass_adv60": bool((cap["pass_rate_adv60"] >= 0.95).all()) if len(cap) else False,
            }
        ]
    )


def missing_report(selected: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for sample, group in selected.groupby("sample"):
        rows.append(
            {
                "sample": sample,
                "observations": int(len(group)),
                "missing_volume": int(group["volume"].isna().sum()),
                "missing_adv20": int(group["adv20"].isna().sum()),
                "missing_adv60": int(group["adv60"].isna().sum()),
                "missing_volume_rate": float(group["volume"].isna().mean()),
                "missing_adv20_rate": float(group["adv20"].isna().mean()),
                "missing_adv60_rate": float(group["adv60"].isna().mean()),
            }
        )
    return pd.DataFrame(rows)


def classify(availability: pd.DataFrame, thresholds: pd.DataFrame, capacity: pd.DataFrame, oos: pd.DataFrame) -> str:
    avail = availability.iloc[0]
    if avail["adv20_coverage"] < 0.90 or avail["adv60_coverage"] < 0.90:
        return "Inconclusive"
    ref50 = thresholds[(thresholds["sample"] == "reference") & (thresholds["adv_threshold"] == 50_000_000)]
    oos50 = thresholds[(thresholds["sample"] == "oos") & (thresholds["adv_threshold"] == 50_000_000)]
    ref_pass = bool(len(ref50) and ref50["adv20_pass_rate"].iloc[0] >= 0.80)
    oos_pass = bool(len(oos50) and oos50["adv20_pass_rate"].iloc[0] >= 0.80)
    cap_small = capacity[(capacity["account_size"].isin([100_000, 1_000_000])) & (capacity["participation_limit"] == 0.01)]
    cap_large = capacity[(capacity["account_size"] == 10_000_000) & (capacity["participation_limit"] == 0.01)]
    small_ok = bool(len(cap_small) and (cap_small["pass_rate_adv20"] >= 0.95).all())
    large_ok = bool(len(cap_large) and (cap_large["pass_rate_adv20"] >= 0.95).all())
    if ref_pass and oos_pass and small_ok and large_ok:
        return "Liquidity Capacity Supported"
    if ref_pass and oos_pass and small_ok:
        return "Liquidity Capacity Partially Supported"
    if not ref_pass or not oos_pass:
        return "Liquidity Capacity Not Supported"
    return "Inconclusive"


def write(name: str, text: str) -> None:
    (OUT / name).write_text(text.strip() + "\n", encoding="utf-8")


def build_reports(conclusion: str, availability: pd.DataFrame, thresholds: pd.DataFrame, capacity: pd.DataFrame, oos: pd.DataFrame, failed: list[str]) -> None:
    avail = availability.iloc[0]
    ref50 = thresholds[(thresholds["sample"] == "reference") & (thresholds["adv_threshold"] == 50_000_000)].iloc[0]
    oos50 = thresholds[(thresholds["sample"] == "oos") & (thresholds["adv_threshold"] == 50_000_000)].iloc[0]
    manifest = {
        "study_id": "WLC-002",
        "study_name": "Workflow Liquidity and Capacity Audit",
        "status": "Completed",
        "conclusion": conclusion,
        "scope": "UC-3 only",
        "selected_observations": int(avail["selected_observations"]),
        "volume_coverage": float(avail["volume_coverage"]),
        "construct_modification_performed": False,
        "optimization_performed": False,
        "production_recommendation_performed": False,
    }
    (OUT / "wlc002_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    pd.DataFrame({"failed_symbol": failed}).to_csv(OUT / "failed_symbols.csv", index=False)
    write(
        "executive_summary.md",
        f"""
# Executive Summary

WLC-002 evaluated selected-name liquidity and capacity for the UC-3 CSM-001 x TSM-001 workflow.

Final conclusion: **{conclusion}**.

Key evidence:

- Selected observations: {int(avail['selected_observations']):,}
- Volume coverage: {avail['volume_coverage']:.4f}
- ADV20 coverage: {avail['adv20_coverage']:.4f}
- Reference $50M ADV20 pass rate: {ref50['adv20_pass_rate']:.4f}
- OOS $50M ADV20 pass rate: {oos50['adv20_pass_rate']:.4f}

Interpretation:

Liquidity and capacity are evaluated only for the predefined UC-3 selected-name workflow and registered account-size grid. This is not production deployment or live readiness.
""",
    )
    write(
        "wlc002_liquidity_capacity_audit.md",
        f"""
# WLC-002: Workflow Liquidity and Capacity Audit

## Purpose

Determine whether the UC-3 workflow has sufficient selected-name liquidity and capacity under predefined account-size and participation assumptions.

## Final Conclusion

**{conclusion}**

## Evidence Classification

Supported by evidence:

- OHLCV volume data were obtained and selected-name dollar-volume features were calculated.
- Reference and OOS liquidity threshold pass rates were generated.
- Account-size participation feasibility was evaluated for $100k, $1M and $10M.

Conclusion-specific evidence:

- Reference $50M ADV20 pass rate: {ref50['adv20_pass_rate']:.4f}
- OOS $50M ADV20 pass rate: {oos50['adv20_pass_rate']:.4f}
- OOS 100k/1M 1% ADV20 pass check: {oos['oos_100k_1m_1pct_all_pass_adv20'].iloc[0]}

Not supported:

- Production deployment.
- Broker-realistic execution.
- Live readiness.

## Outputs

- `liquidity_data_availability.csv`
- `selected_name_liquidity.csv`
- `liquidity_threshold_results.csv`
- `capacity_results.csv`
- `participation_limit_results.csv`
- `oos_liquidity_capacity_check.csv`
- `missing_data_report.csv`
""",
    )
    write(
        "limitations.md",
        """
# Limitations

- WLC-002 uses public OHLCV volume data and simplified dollar-volume proxies.
- ADV thresholds do not model intraday execution quality or order-book depth.
- Participation limits are research feasibility proxies.
- The universe remains current-constituent based.
- No production deployment, broker execution, tax, slippage or live-readiness conclusion is authorized.
""",
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with open(WLC001, encoding="utf-8") as f:
        protocol = json.load(f)
    if protocol.get("authorized_next_stage") != "WLC-002":
        raise RuntimeError("WLC-001 did not authorize WLC-002.")
    tickers = load_universe()
    close, volume, failed = download_ohlcv(tickers)
    close.to_csv(OUT / "ohlcv_close_panel.csv")
    volume.to_csv(OUT / "ohlcv_volume_panel.csv")
    states = pd.concat([reference_states(), oos_states()], ignore_index=True)
    liquidity = build_liquidity_features(close, volume)
    selected = selected_name_liquidity(states, liquidity)
    availability = data_availability(close, volume, failed, selected)
    thresholds = threshold_results(selected)
    capacity = capacity_results(selected)
    participation = capacity.copy()
    oos = oos_check(thresholds, capacity)
    missing = missing_report(selected)
    conclusion = classify(availability, thresholds, capacity, oos)

    availability.to_csv(OUT / "liquidity_data_availability.csv", index=False)
    selected.to_csv(OUT / "selected_name_liquidity.csv", index=False)
    thresholds.to_csv(OUT / "liquidity_threshold_results.csv", index=False)
    capacity.to_csv(OUT / "capacity_results.csv", index=False)
    participation.to_csv(OUT / "participation_limit_results.csv", index=False)
    oos.to_csv(OUT / "oos_liquidity_capacity_check.csv", index=False)
    missing.to_csv(OUT / "missing_data_report.csv", index=False)
    build_reports(conclusion, availability, thresholds, capacity, oos, failed)


if __name__ == "__main__":
    main()
