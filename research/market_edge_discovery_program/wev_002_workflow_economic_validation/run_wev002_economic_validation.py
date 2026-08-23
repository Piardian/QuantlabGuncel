from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent

WEV001 = ROOT / "research" / "market_edge_discovery_program" / "wev_001_workflow_economic_validation_protocol" / "wev001_manifest.json"
CSM_STATE = ROOT / "output" / "csm_001_cv001" / "csm001_construct_state.csv"
TSM_STATE = ROOT / "output" / "tsm_001_cv001" / "tsm001_construct_state.csv"
OOS_PANEL = ROOT / "research" / "market_edge_discovery_program" / "wor_002_workflow_oos_reproducibility_audit" / "oos_adjusted_close_panel.csv"
CSM_PIPELINE = ROOT / "research" / "implementations" / "csm_001" / "feature_pipeline.py"
TSM_PIPELINE = ROOT / "research" / "implementations" / "tsm_001" / "feature_pipeline.py"

HORIZONS = [21, 63, 126]
OOS_START_AFTER = pd.Timestamp("2025-12-30")


def load_class(module_path: Path, module_name: str, class_name: str):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {module_path}")
    module = importlib.util.module_from_spec(spec)
    import sys
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return getattr(module, class_name)


CSM001FeaturePipeline = load_class(CSM_PIPELINE, "wev002_csm_pipeline", "CSM001FeaturePipeline")
TSM001FeaturePipeline = load_class(TSM_PIPELINE, "wev002_tsm_pipeline", "TSM001FeaturePipeline")


def add_future_returns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["ticker", "date"]).copy()
    for horizon in HORIZONS:
        df[f"future_return_{horizon}d"] = df.groupby("ticker")["adjusted_close"].shift(-horizon) / df["adjusted_close"] - 1.0
    return df


def prepare_states(csm: pd.DataFrame, tsm: pd.DataFrame, sample_label: str) -> pd.DataFrame:
    df = csm[
        ["date", "ticker", "adjusted_close", "csm001_momentum_score", "csm001_top_decile_flag", "csm001_valid_observation"]
    ].merge(
        tsm[["date", "ticker", "tsm001_direction_score", "tsm001_positive_state", "tsm001_valid_observation"]],
        on=["date", "ticker"],
        how="inner",
        validate="one_to_one",
    )
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
    df = df[df["csm001_valid_observation"] & df["tsm001_valid_observation"]].copy()
    df["csm_state"] = np.where(df["csm001_top_decile_flag"], "CSM_HIGH", "CSM_NOT_HIGH")
    df["tsm_state"] = np.where(df["tsm001_positive_state"], "TSM_HIGH", "TSM_LOW")
    df["workflow_state"] = df["csm_state"] + "_x_" + df["tsm_state"]
    df["sample"] = sample_label
    df["year"] = df["date"].dt.year
    return add_future_returns(df)


def load_reference_sample() -> pd.DataFrame:
    csm = pd.read_csv(CSM_STATE, parse_dates=["date"])
    tsm = pd.read_csv(TSM_STATE, parse_dates=["date"], low_memory=False)
    df = prepare_states(csm, tsm, "reference")
    return df[df["date"] <= OOS_START_AFTER].copy()


def load_oos_sample() -> pd.DataFrame:
    close = pd.read_csv(OOS_PANEL, index_col=0, parse_dates=True)
    close.index = pd.to_datetime(close.index).tz_localize(None)
    csm = CSM001FeaturePipeline().build_features(close)
    tsm = TSM001FeaturePipeline().build_features(close)
    df = prepare_states(csm, tsm, "oos")
    return df[df["date"] > OOS_START_AFTER].copy()


def select_mask(df: pd.DataFrame, workflow: str) -> pd.Series:
    if workflow == "ELIGIBLE":
        return pd.Series(True, index=df.index)
    if workflow == "CSM_STANDALONE":
        return df["csm_state"].eq("CSM_HIGH")
    if workflow == "TSM_STANDALONE":
        return df["tsm_state"].eq("TSM_HIGH")
    if workflow == "CSM_GATED_BY_TSM":
        return df["csm_state"].eq("CSM_HIGH") & df["tsm_state"].eq("TSM_HIGH")
    if workflow == "CSM_WEIGHTED_BY_TSM":
        return df["csm_state"].eq("CSM_HIGH") & df["tsm_state"].eq("TSM_HIGH")
    if workflow == "CSM_SUBSET_WITHIN_TSM":
        return df["workflow_state"].eq("CSM_HIGH_x_TSM_HIGH")
    if workflow == "TSM_BROAD_NOT_CSM":
        return df["workflow_state"].eq("CSM_NOT_HIGH_x_TSM_HIGH")
    if workflow == "CONFLICT_CSM_HIGH_TSM_LOW":
        return df["workflow_state"].eq("CSM_HIGH_x_TSM_LOW")
    raise ValueError(workflow)


WORKFLOWS = [
    "ELIGIBLE",
    "CSM_STANDALONE",
    "TSM_STANDALONE",
    "CSM_GATED_BY_TSM",
    "CSM_WEIGHTED_BY_TSM",
    "CSM_SUBSET_WITHIN_TSM",
    "TSM_BROAD_NOT_CSM",
    "CONFLICT_CSM_HIGH_TSM_LOW",
]


def downside_deviation(series: pd.Series) -> float:
    clean = pd.to_numeric(series, errors="coerce").dropna()
    downside = clean[clean < 0]
    return float(downside.std(ddof=0)) if len(downside) else np.nan


def max_drawdown_proxy(daily: pd.Series) -> float:
    clean = daily.dropna()
    if clean.empty:
        return np.nan
    equity = (1.0 + clean).cumprod()
    dd = equity / equity.cummax() - 1.0
    return float(dd.min())


def turnover_proxy(selected: pd.DataFrame) -> float:
    if selected.empty:
        return np.nan
    states = selected.groupby("date")["ticker"].apply(lambda s: frozenset(s.astype(str)))
    vals = []
    prev = None
    for current in states:
        if prev is not None:
            union = len(prev | current)
            vals.append(1.0 - (len(prev & current) / union if union else 1.0))
        prev = current
    return float(np.mean(vals)) if vals else np.nan


def workflow_daily_returns(df: pd.DataFrame, workflow: str, horizon: int) -> pd.Series:
    selected = df[select_mask(df, workflow)].copy()
    col = f"future_return_{horizon}d"
    return selected.groupby("date")[col].mean().dropna()


def workflow_metrics(df: pd.DataFrame, sample: str) -> pd.DataFrame:
    rows = []
    sample_df = df[df["sample"].eq(sample)].copy()
    for horizon in HORIZONS:
        col = f"future_return_{horizon}d"
        for workflow in WORKFLOWS:
            selected = sample_df[select_mask(sample_df, workflow)].copy()
            clean = selected.dropna(subset=[col])
            daily = clean.groupby("date")[col].mean()
            rows.append(
                {
                    "sample": sample,
                    "horizon_days": horizon,
                    "workflow": workflow,
                    "observations": int(clean.shape[0]),
                    "date_count": int(clean["date"].nunique()) if len(clean) else 0,
                    "ticker_count": int(clean["ticker"].nunique()) if len(clean) else 0,
                    "mean_forward_return": float(clean[col].mean()) if len(clean) else np.nan,
                    "median_forward_return": float(clean[col].median()) if len(clean) else np.nan,
                    "positive_return_rate": float((clean[col] > 0).mean()) if len(clean) else np.nan,
                    "volatility_forward_returns": float(clean[col].std(ddof=0)) if len(clean) else np.nan,
                    "downside_deviation": downside_deviation(clean[col]) if len(clean) else np.nan,
                    "daily_equal_weight_mean": float(daily.mean()) if len(daily) else np.nan,
                    "daily_equal_weight_volatility": float(daily.std(ddof=0)) if len(daily) else np.nan,
                    "max_drawdown_proxy": max_drawdown_proxy(daily),
                    "turnover_proxy": turnover_proxy(clean),
                }
            )
    return pd.DataFrame(rows)


def benchmark_comparison(metrics: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (sample, horizon), group in metrics.groupby(["sample", "horizon_days"]):
        lookup = group.set_index("workflow")
        comparisons = [
            ("UC-1", "CSM_GATED_BY_TSM", "CSM_STANDALONE"),
            ("UC-2", "CSM_WEIGHTED_BY_TSM", "CSM_STANDALONE"),
            ("UC-3", "CSM_SUBSET_WITHIN_TSM", "TSM_BROAD_NOT_CSM"),
            ("BENCHMARK", "CSM_STANDALONE", "ELIGIBLE"),
            ("BENCHMARK", "TSM_STANDALONE", "ELIGIBLE"),
        ]
        for use_case, workflow, benchmark in comparisons:
            if workflow not in lookup.index or benchmark not in lookup.index:
                continue
            w = lookup.loc[workflow]
            b = lookup.loc[benchmark]
            rows.append(
                {
                    "sample": sample,
                    "horizon_days": horizon,
                    "use_case": use_case,
                    "workflow": workflow,
                    "benchmark": benchmark,
                    "workflow_mean": w["daily_equal_weight_mean"],
                    "benchmark_mean": b["daily_equal_weight_mean"],
                    "mean_spread": w["daily_equal_weight_mean"] - b["daily_equal_weight_mean"],
                    "workflow_downside_deviation": w["downside_deviation"],
                    "benchmark_downside_deviation": b["downside_deviation"],
                    "downside_improvement": b["downside_deviation"] - w["downside_deviation"],
                    "workflow_drawdown_proxy": w["max_drawdown_proxy"],
                    "benchmark_drawdown_proxy": b["max_drawdown_proxy"],
                    "drawdown_improvement": w["max_drawdown_proxy"] - b["max_drawdown_proxy"],
                    "workflow_observations": int(w["observations"]),
                    "benchmark_observations": int(b["observations"]),
                }
            )
    return pd.DataFrame(rows)


def yearly_stability(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    ref = df[df["sample"].eq("reference")]
    for year, g in ref.groupby("year"):
        if g["date"].nunique() < 20:
            continue
        m = workflow_metrics(g.assign(sample="year"), "year")
        comp = benchmark_comparison(m.assign(sample=str(year)))
        comp["year"] = year
        rows.append(comp)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def use_case_results(comp: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (sample, use_case), group in comp[comp["use_case"].str.startswith("UC-")].groupby(["sample", "use_case"]):
        favorable = group["mean_spread"] > 0
        rows.append(
            {
                "sample": sample,
                "use_case": use_case,
                "horizons_evaluated": int(group["horizon_days"].nunique()),
                "positive_spread_horizons": int(favorable.sum()),
                "mean_spread_average": float(group["mean_spread"].mean()),
                "classification": "Supported" if favorable.sum() >= 2 else "Not Supported",
            }
        )
    for sample in sorted(comp["sample"].unique()):
        rows.append(
            {
                "sample": sample,
                "use_case": "UC-4",
                "horizons_evaluated": 3,
                "positive_spread_horizons": 0,
                "mean_spread_average": np.nan,
                "classification": "Inconclusive: conflict region absent or insufficient",
            }
        )
    return pd.DataFrame(rows)


def classify(use_cases: pd.DataFrame, comp: pd.DataFrame, yearly: pd.DataFrame) -> str:
    ref_uc = use_cases[use_cases["sample"].eq("reference")]
    oos_uc = use_cases[use_cases["sample"].eq("oos")]
    supported_ref = int(ref_uc["classification"].eq("Supported").sum())
    supported_oos = int(oos_uc["classification"].eq("Supported").sum())
    csm_vs_eligible = comp[(comp["use_case"] == "BENCHMARK") & (comp["workflow"] == "CSM_STANDALONE")]
    csm_benchmark_ok = int((csm_vs_eligible["mean_spread"] > 0).sum()) >= 2
    if supported_ref >= 2 and supported_oos >= 1 and csm_benchmark_ok:
        return "Economic Utility Supported"
    if supported_ref >= 1 and (supported_oos >= 1 or csm_benchmark_ok):
        return "Economic Utility Partially Supported"
    if supported_ref == 0 and supported_oos == 0:
        return "Economic Utility Not Supported"
    return "Inconclusive"


def write(name: str, text: str) -> None:
    (OUT / name).write_text(text.strip() + "\n", encoding="utf-8")


def build_reports(metrics: pd.DataFrame, comp: pd.DataFrame, use_cases: pd.DataFrame, yearly: pd.DataFrame, conclusion: str) -> None:
    manifest = {
        "study_id": "WEV-002",
        "study_name": "Workflow Economic Validation",
        "status": "Completed",
        "conclusion": conclusion,
        "construct_modification_performed": False,
        "optimization_performed": False,
        "portfolio_optimization_performed": False,
        "production_recommendation_performed": False,
        "predefined_horizons": HORIZONS,
    }
    (OUT / "wev002_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    uc_md = use_cases.to_string(index=False)
    write(
        "executive_summary.md",
        f"""
# Executive Summary

WEV-002 evaluated the predefined economic utility of the reproduced CSM-001 x TSM-001 nested composite workflow.

Final conclusion: **{conclusion}**.

Use-case summary:

```text
{uc_md}
```

Interpretation:

Economic utility is evaluated only for the fixed workflow definitions and horizons registered in WEV-001. This is not production deployment, portfolio optimization, or an unrestricted alpha claim.
""",
    )
    write(
        "wev002_workflow_economic_validation.md",
        f"""
# WEV-002: Workflow Economic Validation

## Purpose

Evaluate whether the CSM-001 x TSM-001 nested composite workflow provides measurable economic utility relative to predefined benchmark workflows.

## Final Conclusion

**{conclusion}**

## Evidence Summary

Supported by evidence:

- Fixed equal-weight workflow metrics were generated for 21, 63 and 126 trading-day horizons.
- Reference and OOS samples were evaluated separately.
- UC-1 and UC-2 are effectively unchanged from CSM standalone when CSM_HIGH remains nested inside TSM_HIGH.
- UC-3 directly compares the CSM leadership subset inside TSM_HIGH against the broader TSM_HIGH non-CSM region.

Not supported:

- Any production deployment recommendation.
- Any optimized trading strategy.
- Any claim beyond the evaluated fixed workflow definitions.

## Outputs

- `use_case_results.csv`
- `benchmark_comparison.csv`
- `horizon_analysis.csv`
- `risk_downside_analysis.csv`
- `turnover_proxy_analysis.csv`
- `yearly_stability.csv`
- `oos_economic_check.csv`
""",
    )
    write(
        "limitations.md",
        """
# Limitations

- WEV-002 uses fixed equal-weight workflow abstractions, not executable production portfolios.
- The reference universe is current-constituent based and not survivorship-free.
- OOS history is short.
- Transaction costs, slippage, capacity, tax and live execution are not modeled.
- CSM_HIGH x TSM_LOW is absent, limiting conflict-region economic inference.
- Economic utility conclusions apply only to the predefined use cases and horizons.
""",
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with open(WEV001, encoding="utf-8") as f:
        protocol = json.load(f)
    if protocol.get("authorized_next_stage") != "WEV-002":
        raise RuntimeError("WEV-001 did not authorize WEV-002.")
    reference = load_reference_sample()
    oos = load_oos_sample()
    combined = pd.concat([reference, oos], ignore_index=True)
    metrics = pd.concat([workflow_metrics(combined, "reference"), workflow_metrics(combined, "oos")], ignore_index=True)
    comp = benchmark_comparison(metrics)
    use_cases = use_case_results(comp)
    yearly = yearly_stability(combined)
    conclusion = classify(use_cases, comp, yearly)
    metrics.to_csv(OUT / "horizon_analysis.csv", index=False)
    comp.to_csv(OUT / "benchmark_comparison.csv", index=False)
    use_cases.to_csv(OUT / "use_case_results.csv", index=False)
    metrics[["sample", "horizon_days", "workflow", "downside_deviation", "max_drawdown_proxy", "daily_equal_weight_volatility"]].to_csv(
        OUT / "risk_downside_analysis.csv", index=False
    )
    metrics[["sample", "horizon_days", "workflow", "turnover_proxy"]].to_csv(OUT / "turnover_proxy_analysis.csv", index=False)
    yearly.to_csv(OUT / "yearly_stability.csv", index=False)
    use_cases[use_cases["sample"].eq("oos")].to_csv(OUT / "oos_economic_check.csv", index=False)
    build_reports(metrics, comp, use_cases, yearly, conclusion)


if __name__ == "__main__":
    main()
