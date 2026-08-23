from __future__ import annotations

import json
import sys
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
CSM_IMPL = ROOT / "research" / "implementations" / "csm_001"
TSM_IMPL = ROOT / "research" / "implementations" / "tsm_001"
UNIVERSE_FILE = ROOT / "sp500_current_universe.csv"
WOR001_MANIFEST = ROOT / "research" / "market_edge_discovery_program" / "wor_001_workflow_oos_reproducibility_protocol" / "wor001_manifest.json"

def load_class(module_path: Path, module_name: str, class_name: str):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return getattr(module, class_name)


CSM001FeaturePipeline = load_class(CSM_IMPL / "feature_pipeline.py", "wor002_csm_feature_pipeline", "CSM001FeaturePipeline")
TSM001FeaturePipeline = load_class(TSM_IMPL / "feature_pipeline.py", "wor002_tsm_feature_pipeline", "TSM001FeaturePipeline")


DOWNLOAD_START = "2024-01-01"
DOWNLOAD_END = "2026-08-04"
OOS_START_AFTER = pd.Timestamp("2025-12-30")
MIN_OOS_OBSERVATIONS = 10_000
MIN_OOS_DATES = 20


def to_yahoo_symbol(ticker: str) -> str:
    return ticker.replace(".", "-")


def from_yahoo_symbol(symbol: str, lookup: dict[str, str]) -> str:
    return lookup.get(symbol, symbol.replace("-", "."))


def load_universe() -> list[str]:
    frame = pd.read_csv(UNIVERSE_FILE)
    tickers = frame["ticker"].dropna().astype(str).str.strip()
    return sorted(t for t in tickers.unique() if t)


def download_close_panel(tickers: list[str]) -> tuple[pd.DataFrame, list[str]]:
    yahoo_symbols = [to_yahoo_symbol(t) for t in tickers]
    lookup = dict(zip(yahoo_symbols, tickers))
    chunks: list[pd.DataFrame] = []
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
            failed.extend(from_yahoo_symbol(s, lookup) for s in symbols)
            continue
        if data.empty:
            failed.extend(from_yahoo_symbol(s, lookup) for s in symbols)
            continue
        if isinstance(data.columns, pd.MultiIndex):
            if "Adj Close" in data.columns.get_level_values(0):
                close = data["Adj Close"].copy()
            elif "Close" in data.columns.get_level_values(0):
                close = data["Close"].copy()
            else:
                failed.extend(from_yahoo_symbol(s, lookup) for s in symbols)
                continue
        else:
            column = "Adj Close" if "Adj Close" in data.columns else "Close"
            close = data[[column]].copy()
            close.columns = symbols[:1]
        close = close.rename(columns=lambda symbol: from_yahoo_symbol(str(symbol), lookup))
        chunks.append(close)
    if not chunks:
        return pd.DataFrame(), sorted(set(failed))
    panel = pd.concat(chunks, axis=1)
    panel = panel.loc[:, ~panel.columns.duplicated()]
    panel = panel.reindex(sorted(panel.columns), axis=1)
    panel.index = pd.to_datetime(panel.index).tz_localize(None)
    all_nan = sorted(c for c in panel.columns if panel[c].notna().sum() == 0)
    missing = sorted(set(tickers) - set(panel.columns))
    return panel, sorted(set(failed).union(all_nan).union(missing))


def build_oos_states(close_panel: pd.DataFrame) -> pd.DataFrame:
    csm = CSM001FeaturePipeline().build_features(close_panel)
    tsm = TSM001FeaturePipeline().build_features(close_panel)
    merged = csm[
        [
            "date",
            "ticker",
            "csm001_momentum_score",
            "csm001_top_decile_flag",
            "csm001_valid_observation",
        ]
    ].merge(
        tsm[
            [
                "date",
                "ticker",
                "tsm001_direction_score",
                "tsm001_positive_state",
                "tsm001_valid_observation",
            ]
        ],
        on=["date", "ticker"],
        how="inner",
        validate="one_to_one",
    )
    merged["date"] = pd.to_datetime(merged["date"]).dt.tz_localize(None)
    oos = merged[
        (merged["date"] > OOS_START_AFTER)
        & merged["csm001_valid_observation"]
        & merged["tsm001_valid_observation"]
    ].copy()
    oos["csm_state"] = np.where(oos["csm001_top_decile_flag"], "CSM_HIGH", "CSM_NOT_HIGH")
    oos["tsm_state"] = np.where(oos["tsm001_positive_state"], "TSM_HIGH", "TSM_LOW")
    oos["workflow_state"] = oos["csm_state"] + "_x_" + oos["tsm_state"]
    oos["month"] = oos["date"].dt.to_period("M").astype(str)
    return oos


def state_matrix(df: pd.DataFrame) -> pd.DataFrame:
    expected = ["CSM_HIGH_x_TSM_HIGH", "CSM_HIGH_x_TSM_LOW", "CSM_NOT_HIGH_x_TSM_HIGH", "CSM_NOT_HIGH_x_TSM_LOW"]
    total = len(df)
    rows = []
    for state in expected:
        g = df[df["workflow_state"] == state]
        rows.append(
            {
                "workflow_state": state,
                "observations": int(len(g)),
                "coverage": len(g) / total if total else np.nan,
                "ticker_count": int(g["ticker"].nunique()),
                "date_count": int(g["date"].nunique()),
            }
        )
    return pd.DataFrame(rows)


def agreement_metrics(df: pd.DataFrame, scope: str) -> dict[str, object]:
    csm_high = df["csm_state"].eq("CSM_HIGH")
    tsm_high = df["tsm_state"].eq("TSM_HIGH")
    both = csm_high & tsm_high
    union = csm_high | tsm_high
    return {
        "scope": scope,
        "observations": int(len(df)),
        "date_count": int(df["date"].nunique()) if len(df) else 0,
        "ticker_count": int(df["ticker"].nunique()) if len(df) else 0,
        "csm_high_count": int(csm_high.sum()),
        "tsm_high_count": int(tsm_high.sum()),
        "overlap_count": int(both.sum()),
        "csm_high_tsm_low_count": int((csm_high & ~tsm_high).sum()),
        "jaccard": float(both.sum() / union.sum()) if union.sum() else np.nan,
        "p_tsm_high_given_csm_high": float(both.sum() / csm_high.sum()) if csm_high.sum() else np.nan,
        "p_csm_high_given_tsm_high": float(both.sum() / tsm_high.sum()) if tsm_high.sum() else np.nan,
        "reproduces_nested_pattern": bool((csm_high & ~tsm_high).sum() == 0 and csm_high.sum() > 0 and tsm_high.sum() > csm_high.sum()),
    }


def nested_analysis(df: pd.DataFrame) -> pd.DataFrame:
    rows = [agreement_metrics(df, "full_oos")]
    for month, group in df.groupby("month"):
        rows.append(agreement_metrics(group, f"month_{month}"))
    return pd.DataFrame(rows)


def symbol_coverage(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for ticker, group in df.groupby("ticker"):
        rows.append(
            {
                "ticker": ticker,
                "observations": int(len(group)),
                "date_count": int(group["date"].nunique()),
                "csm_high_count": int(group["csm_state"].eq("CSM_HIGH").sum()),
                "tsm_high_count": int(group["tsm_state"].eq("TSM_HIGH").sum()),
                "csm_high_tsm_low_count": int(group["workflow_state"].eq("CSM_HIGH_x_TSM_LOW").sum()),
                "workflow_state_count": int(group["workflow_state"].nunique()),
            }
        )
    return pd.DataFrame(rows).sort_values("observations", ascending=False)


def availability_report(panel: pd.DataFrame, failed: list[str], oos: pd.DataFrame, universe_count: int) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "download_start": DOWNLOAD_START,
                "download_end_exclusive": DOWNLOAD_END,
                "oos_start_after": str(OOS_START_AFTER.date()),
                "panel_start": str(panel.index.min().date()) if not panel.empty else "",
                "panel_end": str(panel.index.max().date()) if not panel.empty else "",
                "configured_universe_count": universe_count,
                "downloaded_columns": int(panel.shape[1]) if not panel.empty else 0,
                "failed_symbols": len(failed),
                "oos_observations": int(len(oos)),
                "oos_dates": int(oos["date"].nunique()) if len(oos) else 0,
                "oos_tickers": int(oos["ticker"].nunique()) if len(oos) else 0,
                "sufficient_oos_observations": bool(len(oos) >= MIN_OOS_OBSERVATIONS),
                "sufficient_oos_dates": bool(oos["date"].nunique() >= MIN_OOS_DATES) if len(oos) else False,
            }
        ]
    )


def classify(availability: pd.DataFrame, nested: pd.DataFrame) -> str:
    avail = availability.iloc[0]
    if not bool(avail["sufficient_oos_observations"]) or not bool(avail["sufficient_oos_dates"]):
        return "Inconclusive"
    full = nested[nested["scope"] == "full_oos"].iloc[0]
    month_rows = nested[nested["scope"].str.startswith("month_")]
    stable_months = int(month_rows["reproduces_nested_pattern"].sum()) if len(month_rows) else 0
    total_months = int(len(month_rows))
    if bool(full["reproduces_nested_pattern"]) and total_months > 0 and stable_months / total_months >= 0.75:
        return "Reproduced"
    if bool(full["reproduces_nested_pattern"]):
        return "Partially Reproduced"
    return "Not Reproduced"


def write(path: str, text: str) -> None:
    (OUT / path).write_text(text.strip() + "\n", encoding="utf-8")


def build_reports(availability: pd.DataFrame, matrix: pd.DataFrame, nested: pd.DataFrame, coverage: pd.DataFrame, conclusion: str, failed: list[str]) -> None:
    avail = availability.iloc[0]
    full = nested[nested["scope"] == "full_oos"].iloc[0] if len(nested) else {}
    comparison = pd.DataFrame(
        [
            {"metric": "jaccard", "cws001_reference": 0.13971035124702275, "wor002_oos": full.get("jaccard", np.nan)},
            {"metric": "p_tsm_high_given_csm_high", "cws001_reference": 1.0, "wor002_oos": full.get("p_tsm_high_given_csm_high", np.nan)},
            {"metric": "p_csm_high_given_tsm_high", "cws001_reference": 0.13971035124702275, "wor002_oos": full.get("p_csm_high_given_tsm_high", np.nan)},
            {"metric": "csm_high_tsm_low_count", "cws001_reference": 0.0, "wor002_oos": full.get("csm_high_tsm_low_count", np.nan)},
        ]
    )
    comparison.to_csv(OUT / "reproducibility_comparison.csv", index=False)
    pd.DataFrame({"failed_symbol": failed}).to_csv(OUT / "failed_symbols.csv", index=False)
    manifest = {
        "study_id": "WOR-002",
        "study_name": "Workflow Out-of-Sample Reproducibility Audit",
        "status": "Completed",
        "conclusion": conclusion,
        "oos_non_overlap_verified": True,
        "oos_start_after": str(OOS_START_AFTER.date()),
        "oos_observations": int(avail["oos_observations"]),
        "oos_dates": int(avail["oos_dates"]),
        "oos_tickers": int(avail["oos_tickers"]),
        "construct_modification_performed": False,
        "optimization_performed": False,
        "trading_performance_evaluated": False,
        "economic_utility_evaluated": False,
        "production_recommendation_performed": False,
    }
    (OUT / "wor002_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    write(
        "executive_summary.md",
        f"""
# Executive Summary

WOR-002 executed the WOR-001 out-of-sample reproducibility protocol for the CSM-001 x TSM-001 nested composite workflow.

Final conclusion: **{conclusion}**.

OOS sample:

- OOS dates: {int(avail['oos_dates'])}
- OOS observations: {int(avail['oos_observations']):,}
- OOS tickers: {int(avail['oos_tickers'])}
- OOS period starts after: {OOS_START_AFTER.date()}

Key OOS evidence:

- P(TSM_HIGH | CSM_HIGH): {full.get('p_tsm_high_given_csm_high', np.nan):.6f}
- P(CSM_HIGH | TSM_HIGH): {full.get('p_csm_high_given_tsm_high', np.nan):.6f}
- Jaccard similarity: {full.get('jaccard', np.nan):.6f}
- CSM_HIGH x TSM_LOW count: {int(full.get('csm_high_tsm_low_count', 0))}

No trading performance, alpha, economic utility or production deployment conclusion is authorized.
""",
    )
    write(
        "wor002_oos_reproducibility_audit.md",
        f"""
# WOR-002: Workflow Out-of-Sample Reproducibility Audit

## Purpose

Test whether the CSM-001 x TSM-001 nested workflow structure reproduces on non-overlapping OOS data after 2025-12-30.

## Final Conclusion

**{conclusion}**

## Data Availability

- Configured universe count: {int(avail['configured_universe_count'])}
- Downloaded columns: {int(avail['downloaded_columns'])}
- Failed symbols: {int(avail['failed_symbols'])}
- OOS observations: {int(avail['oos_observations']):,}
- OOS dates: {int(avail['oos_dates'])}
- OOS tickers: {int(avail['oos_tickers'])}

## Evidence Classification

Supported by evidence:

- OOS observations are non-overlapping with CWS-001.
- Frozen CSM-001 and TSM-001 pipelines were used without parameter changes.
- OOS workflow state matrix and agreement metrics were generated.

Conclusion-specific evidence:

- P(TSM_HIGH | CSM_HIGH): {full.get('p_tsm_high_given_csm_high', np.nan):.6f}
- P(CSM_HIGH | TSM_HIGH): {full.get('p_csm_high_given_tsm_high', np.nan):.6f}
- CSM_HIGH x TSM_LOW count: {int(full.get('csm_high_tsm_low_count', 0))}

Not supported:

- Any production deployment claim.
- Any alpha claim.
- Any economic utility claim.

## Outputs

- `oos_data_availability.csv`
- `oos_workflow_state_matrix.csv`
- `oos_nested_state_analysis.csv`
- `oos_agreement_metrics.csv`
- `oos_time_stability_analysis.csv`
- `oos_symbol_coverage_analysis.csv`
- `reproducibility_comparison.csv`
""",
    )
    write(
        "limitations.md",
        """
# Limitations

- WOR-002 is a reproducibility audit only.
- The OOS period is short relative to the 2011-2025 reference sample.
- The universe remains current-constituent based, not survivorship-free.
- Data availability depends on downloaded public market data.
- No predictive, economic, trading, portfolio, capacity, slippage or production conclusion is authorized.
""",
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with open(WOR001_MANIFEST, encoding="utf-8") as f:
        protocol = json.load(f)
    if protocol.get("authorized_next_stage") != "WOR-002":
        raise RuntimeError("WOR-001 did not authorize WOR-002.")
    tickers = load_universe()
    panel, failed = download_close_panel(tickers)
    if panel.empty:
        oos = pd.DataFrame()
    else:
        (OUT / "oos_adjusted_close_panel.csv").parent.mkdir(parents=True, exist_ok=True)
        panel.to_csv(OUT / "oos_adjusted_close_panel.csv")
        oos = build_oos_states(panel)
    availability = availability_report(panel, failed, oos, len(tickers))
    matrix = state_matrix(oos) if len(oos) else pd.DataFrame()
    nested = nested_analysis(oos) if len(oos) else pd.DataFrame()
    agreement = nested.copy()
    time_stability = nested[nested["scope"].str.startswith("month_")].copy() if len(nested) else pd.DataFrame()
    coverage = symbol_coverage(oos) if len(oos) else pd.DataFrame()
    conclusion = classify(availability, nested) if len(nested) else "Inconclusive"
    availability.to_csv(OUT / "oos_data_availability.csv", index=False)
    matrix.to_csv(OUT / "oos_workflow_state_matrix.csv", index=False)
    nested.to_csv(OUT / "oos_nested_state_analysis.csv", index=False)
    agreement.to_csv(OUT / "oos_agreement_metrics.csv", index=False)
    time_stability.to_csv(OUT / "oos_time_stability_analysis.csv", index=False)
    coverage.to_csv(OUT / "oos_symbol_coverage_analysis.csv", index=False)
    build_reports(availability, matrix, nested, coverage, conclusion, failed)


if __name__ == "__main__":
    main()
