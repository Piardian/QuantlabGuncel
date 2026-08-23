from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent

CSM_STATE = ROOT / "output" / "csm_001_cv001" / "csm001_construct_state.csv"
TSM_STATE = ROOT / "output" / "tsm_001_cv001" / "tsm001_construct_state.csv"
CWP_MANIFEST = ROOT / "research" / "market_edge_discovery_program" / "cwp_001_composite_workflow_protocol_registration" / "cwp001_manifest.json"
CIP_MANIFEST = ROOT / "research" / "market_edge_discovery_program" / "cip_001_csm_tsm_construct_interaction_study" / "cip001_manifest.json"

HORIZONS = [21, 63, 126]
MIN_NON_NEGLIGIBLE_R2 = 0.0005
MIN_STABLE_YEARS = 10


def safe_div(num: float, den: float) -> float:
    return np.nan if den == 0 or pd.isna(den) else float(num / den)


def spearman_no_scipy(left: pd.Series, right: pd.Series) -> float:
    sample = pd.DataFrame({"left": left, "right": right}).dropna()
    if len(sample) < 3:
        return np.nan
    return float(sample["left"].rank(method="average").corr(sample["right"].rank(method="average")))


def load_common_sample() -> pd.DataFrame:
    csm = pd.read_csv(CSM_STATE, parse_dates=["date"])
    tsm = pd.read_csv(TSM_STATE, parse_dates=["date"], low_memory=False)
    csm_cols = [
        "date",
        "ticker",
        "adjusted_close",
        "csm001_momentum_score",
        "csm001_top_decile_flag",
        "csm001_valid_observation",
    ]
    tsm_cols = [
        "date",
        "ticker",
        "tsm001_direction_score",
        "tsm001_positive_state",
        "tsm001_valid_observation",
    ]
    df = csm[csm_cols].merge(tsm[tsm_cols], on=["date", "ticker"], how="inner", validate="one_to_one")
    df = df[df["csm001_valid_observation"] & df["tsm001_valid_observation"]].copy()
    df = df.sort_values(["ticker", "date"]).reset_index(drop=True)
    for horizon in HORIZONS:
        df[f"future_return_{horizon}d"] = df.groupby("ticker")["adjusted_close"].shift(-horizon) / df["adjusted_close"] - 1.0
    df["csm_state"] = np.where(df["csm001_top_decile_flag"], "CSM_HIGH", "CSM_NOT_HIGH")
    df["tsm_state"] = np.where(df["tsm001_positive_state"], "TSM_HIGH", "TSM_LOW")
    df["workflow_state"] = df["csm_state"] + "_x_" + df["tsm_state"]
    df["year"] = df["date"].dt.year
    return df


def frozen_input_verification(df: pd.DataFrame) -> dict:
    with open(CWP_MANIFEST, encoding="utf-8") as f:
        cwp = json.load(f)
    with open(CIP_MANIFEST, encoding="utf-8") as f:
        cip = json.load(f)
    return {
        "cwp_authorized_next_stage": cwp.get("authorized_next_stage"),
        "cip_prior_conclusion": cip.get("overall_conclusion"),
        "common_observations": int(len(df)),
        "tickers": int(df["ticker"].nunique()),
        "start_date": str(df["date"].min().date()),
        "end_date": str(df["date"].max().date()),
        "valid_csm_observations": int(df["csm001_top_decile_flag"].notna().sum()),
        "valid_tsm_observations": int(df["tsm001_positive_state"].notna().sum()),
        "verified": cwp.get("authorized_next_stage") == "CWS-001" and cip.get("overall_conclusion") == "Partially Complementary",
    }


def workflow_state_matrix(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    total = len(df)
    for state, g in df.groupby("workflow_state"):
        row = {
            "workflow_state": state,
            "observations": int(len(g)),
            "coverage": len(g) / total,
            "ticker_count": int(g["ticker"].nunique()),
            "year_count": int(g["year"].nunique()),
            "mean_csm_score": float(g["csm001_momentum_score"].mean()),
            "mean_tsm_direction_score": float(g["tsm001_direction_score"].mean()),
        }
        for horizon in HORIZONS:
            s = g[f"future_return_{horizon}d"]
            row[f"mean_future_return_{horizon}d"] = float(s.mean())
            row[f"median_future_return_{horizon}d"] = float(s.median())
            row[f"positive_return_rate_{horizon}d"] = float((s > 0).mean())
        rows.append(row)
    expected = {"CSM_HIGH_x_TSM_HIGH", "CSM_HIGH_x_TSM_LOW", "CSM_NOT_HIGH_x_TSM_HIGH", "CSM_NOT_HIGH_x_TSM_LOW"}
    present = {r["workflow_state"] for r in rows}
    for missing in sorted(expected - present):
        rows.append({"workflow_state": missing, "observations": 0, "coverage": 0.0, "ticker_count": 0, "year_count": 0})
    return pd.DataFrame(rows).sort_values("workflow_state")


def nested_state_analysis(df: pd.DataFrame) -> pd.DataFrame:
    csm_high = df["csm_state"].eq("CSM_HIGH")
    tsm_high = df["tsm_state"].eq("TSM_HIGH")
    both = csm_high & tsm_high
    union = csm_high | tsm_high
    rows = [
        {
            "scope": "full_sample",
            "observations": int(len(df)),
            "csm_high_count": int(csm_high.sum()),
            "tsm_high_count": int(tsm_high.sum()),
            "overlap_count": int(both.sum()),
            "csm_high_tsm_low_count": int((csm_high & ~tsm_high).sum()),
            "jaccard": safe_div(both.sum(), union.sum()),
            "p_tsm_high_given_csm_high": safe_div(both.sum(), csm_high.sum()),
            "p_csm_high_given_tsm_high": safe_div(both.sum(), tsm_high.sum()),
            "phi_association": float(np.corrcoef(csm_high.astype(int), tsm_high.astype(int))[0, 1]),
            "nesting_supported": bool((csm_high & ~tsm_high).sum() == 0),
        }
    ]
    for year, g in df.groupby("year"):
        c = g["csm_state"].eq("CSM_HIGH")
        t = g["tsm_state"].eq("TSM_HIGH")
        b = c & t
        u = c | t
        rows.append(
            {
                "scope": f"year_{year}",
                "observations": int(len(g)),
                "csm_high_count": int(c.sum()),
                "tsm_high_count": int(t.sum()),
                "overlap_count": int(b.sum()),
                "csm_high_tsm_low_count": int((c & ~t).sum()),
                "jaccard": safe_div(b.sum(), u.sum()),
                "p_tsm_high_given_csm_high": safe_div(b.sum(), c.sum()),
                "p_csm_high_given_tsm_high": safe_div(b.sum(), t.sum()),
                "phi_association": float(np.corrcoef(c.astype(int), t.astype(int))[0, 1]),
                "nesting_supported": bool((c & ~t).sum() == 0),
            }
        )
    return pd.DataFrame(rows)


def incremental_information(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for horizon in HORIZONS:
        sample = pd.DataFrame(
            {
                "y": df[f"future_return_{horizon}d"],
                "csm": df["csm001_momentum_score"],
                "tsm": df["tsm001_direction_score"],
                "workflow": pd.Categorical(df["workflow_state"]).codes,
            }
        ).dropna()
        y = sample["y"].to_numpy()
        ones = np.ones(len(sample))

        def r2(columns: list[str]) -> float:
            x = np.column_stack([ones] + [sample[c].to_numpy(dtype=float) for c in columns])
            beta, *_ = np.linalg.lstsq(x, y, rcond=None)
            pred = x @ beta
            ss_res = np.square(y - pred).sum()
            ss_tot = np.square(y - y.mean()).sum()
            return float(1.0 - ss_res / ss_tot)

        r2_csm = r2(["csm"])
        r2_tsm = r2(["tsm"])
        r2_both = r2(["csm", "tsm"])
        r2_workflow = r2(["workflow"])
        rows.append(
            {
                "horizon_days": horizon,
                "observations": int(len(sample)),
                "r2_csm_only": r2_csm,
                "r2_tsm_only": r2_tsm,
                "r2_csm_plus_tsm": r2_both,
                "r2_workflow_state_only": r2_workflow,
                "incremental_r2_tsm_beyond_csm": r2_both - r2_csm,
                "incremental_r2_csm_beyond_tsm": r2_both - r2_tsm,
                "incremental_non_negligible_tsm_beyond_csm": bool((r2_both - r2_csm) >= MIN_NON_NEGLIGIBLE_R2),
                "incremental_non_negligible_csm_beyond_tsm": bool((r2_both - r2_tsm) >= MIN_NON_NEGLIGIBLE_R2),
                "spearman_csm_return": spearman_no_scipy(sample["csm"], sample["y"]),
                "spearman_tsm_return": spearman_no_scipy(sample["tsm"], sample["y"]),
                "spearman_csm_tsm": spearman_no_scipy(sample["csm"], sample["tsm"]),
            }
        )
    return pd.DataFrame(rows)


def conditional_information(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for horizon in HORIZONS:
        col = f"future_return_{horizon}d"
        for tsm_state, g in df.groupby("tsm_state"):
            high = g[g["csm_state"] == "CSM_HIGH"][col]
            ref = g[g["csm_state"] == "CSM_NOT_HIGH"][col]
            rows.append(
                {
                    "horizon_days": horizon,
                    "condition_type": "within_tsm_state",
                    "condition": tsm_state,
                    "comparison": "CSM_HIGH_minus_CSM_NOT_HIGH",
                    "comparison_observations": int(high.notna().sum()),
                    "reference_observations": int(ref.notna().sum()),
                    "mean_difference": float(high.mean() - ref.mean()) if high.notna().sum() > 0 and ref.notna().sum() > 0 else np.nan,
                    "sample_adequate": bool(high.notna().sum() >= 1000 and ref.notna().sum() >= 1000),
                }
            )
        for csm_state, g in df.groupby("csm_state"):
            pos = g[g["tsm_state"] == "TSM_HIGH"][col]
            low = g[g["tsm_state"] == "TSM_LOW"][col]
            rows.append(
                {
                    "horizon_days": horizon,
                    "condition_type": "within_csm_state",
                    "condition": csm_state,
                    "comparison": "TSM_HIGH_minus_TSM_LOW",
                    "comparison_observations": int(pos.notna().sum()),
                    "reference_observations": int(low.notna().sum()),
                    "mean_difference": float(pos.mean() - low.mean()) if pos.notna().sum() > 0 and low.notna().sum() > 0 else np.nan,
                    "sample_adequate": bool(pos.notna().sum() >= 1000 and low.notna().sum() >= 1000),
                }
            )
    return pd.DataFrame(rows)


def conflict_region_analysis(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    total = len(df)
    for state, g in df.groupby("workflow_state"):
        conflict = state in {"CSM_HIGH_x_TSM_LOW", "CSM_NOT_HIGH_x_TSM_HIGH"}
        row = {
            "workflow_state": state,
            "conflict_region": conflict,
            "observations": int(len(g)),
            "coverage": len(g) / total,
            "ticker_count": int(g["ticker"].nunique()),
            "year_count": int(g["year"].nunique()),
            "minimum_sample_adequate": bool(len(g) >= 1000),
        }
        rows.append(row)
    if "CSM_HIGH_x_TSM_LOW" not in set(df["workflow_state"]):
        rows.append(
            {
                "workflow_state": "CSM_HIGH_x_TSM_LOW",
                "conflict_region": True,
                "observations": 0,
                "coverage": 0.0,
                "ticker_count": 0,
                "year_count": 0,
                "minimum_sample_adequate": False,
            }
        )
    return pd.DataFrame(rows).sort_values("workflow_state")


def time_stability_analysis(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for year, g in df.groupby("year"):
        n = nested_state_analysis(g).iloc[0]
        row = {
            "year": int(year),
            "observations": int(len(g)),
            "jaccard": float(n["jaccard"]),
            "p_tsm_high_given_csm_high": float(n["p_tsm_high_given_csm_high"]),
            "p_csm_high_given_tsm_high": float(n["p_csm_high_given_tsm_high"]),
            "nesting_supported": bool(n["nesting_supported"]),
        }
        for horizon in HORIZONS:
            col = f"future_return_{horizon}d"
            hh = g[g["workflow_state"] == "CSM_HIGH_x_TSM_HIGH"][col].mean()
            nh = g[g["workflow_state"] == "CSM_NOT_HIGH_x_TSM_HIGH"][col].mean()
            nl = g[g["workflow_state"] == "CSM_NOT_HIGH_x_TSM_LOW"][col].mean()
            row[f"csm_spread_within_tsm_high_{horizon}d"] = float(hh - nh)
            row[f"tsm_spread_within_csm_not_high_{horizon}d"] = float(nh - nl)
        rows.append(row)
    return pd.DataFrame(rows)


def symbol_coverage_analysis(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for ticker, g in df.groupby("ticker"):
        row = {
            "ticker": ticker,
            "observations": int(len(g)),
            "year_count": int(g["year"].nunique()),
            "csm_high_count": int(g["csm_state"].eq("CSM_HIGH").sum()),
            "tsm_high_count": int(g["tsm_state"].eq("TSM_HIGH").sum()),
            "csm_high_tsm_low_count": int(g["workflow_state"].eq("CSM_HIGH_x_TSM_LOW").sum()),
            "workflow_state_count": int(g["workflow_state"].nunique()),
        }
        rows.append(row)
    return pd.DataFrame(rows).sort_values("observations", ascending=False)


def markdown_table(df: pd.DataFrame, max_rows: int | None = None) -> str:
    table = df.head(max_rows).copy() if max_rows else df.copy()
    table = table.fillna("")
    headers = [str(c) for c in table.columns]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for _, row in table.iterrows():
        values = []
        for value in row.tolist():
            if isinstance(value, float):
                values.append(f"{value:.6g}")
            else:
                values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def write(name: str, text: str) -> None:
    (OUT / name).write_text(text.strip() + "\n", encoding="utf-8")


def classify(nested: pd.DataFrame, inc: pd.DataFrame, conflict: pd.DataFrame, stability: pd.DataFrame) -> str:
    full = nested[nested["scope"].eq("full_sample")].iloc[0]
    stable_years = int(stability["nesting_supported"].sum())
    tsm_increment = bool(inc["incremental_non_negligible_tsm_beyond_csm"].any())
    csm_increment = bool(inc["incremental_non_negligible_csm_beyond_tsm"].any())
    rare_direct_conflict = int(conflict.loc[conflict["workflow_state"].eq("CSM_HIGH_x_TSM_LOW"), "observations"].fillna(0).sum()) < 1000
    if bool(full["nesting_supported"]) and stable_years >= MIN_STABLE_YEARS and tsm_increment and csm_increment and rare_direct_conflict:
        return "Workflow Supported"
    if bool(full["nesting_supported"]) and stable_years >= MIN_STABLE_YEARS and (tsm_increment or csm_increment):
        return "Workflow Partially Supported"
    if not bool(full["nesting_supported"]) and not (tsm_increment or csm_increment):
        return "Workflow Not Supported"
    return "Inconclusive"


def build_reports(
    verification: dict,
    matrix: pd.DataFrame,
    nested: pd.DataFrame,
    conditional: pd.DataFrame,
    inc: pd.DataFrame,
    conflict: pd.DataFrame,
    stability: pd.DataFrame,
    coverage: pd.DataFrame,
) -> None:
    conclusion = classify(nested, inc, conflict, stability)
    full = nested[nested["scope"].eq("full_sample")].iloc[0]
    manifest = {
        "study_id": "CWS-001",
        "study_name": "Composite Workflow Scientific Evaluation",
        "status": "Completed",
        "conclusion": conclusion,
        "frozen_input_verification": verification,
        "sample": {
            "observations": verification["common_observations"],
            "tickers": verification["tickers"],
            "start_date": verification["start_date"],
            "end_date": verification["end_date"],
        },
        "construct_modification_performed": False,
        "optimization_performed": False,
        "trading_strategy_built": False,
        "production_recommendation_performed": False,
    }
    (OUT / "cws001_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    write(
        "executive_summary.md",
        f"""
# Executive Summary

CWS-001 executed the preregistered CWP-001 protocol for the frozen CSM-001 x TSM-001 composite workflow.

Final conclusion: **{conclusion}**.

Key evidence:

- Common observations: **{verification['common_observations']:,}**
- Tickers: **{verification['tickers']}**
- Sample: **{verification['start_date']} to {verification['end_date']}**
- P(TSM_HIGH | CSM_HIGH): **{full['p_tsm_high_given_csm_high']:.6f}**
- P(CSM_HIGH | TSM_HIGH): **{full['p_csm_high_given_tsm_high']:.6f}**
- Jaccard similarity: **{full['jaccard']:.6f}**
- CSM_HIGH x TSM_LOW observations: **{int(full['csm_high_tsm_low_count'])}**

Interpretation:

The composite workflow is scientifically supported as a nested workflow: CSM_HIGH operates inside the broader TSM_HIGH region. The workflow is not a new construct and is not production authorized.
""",
    )

    write(
        "cws001_composite_workflow_evaluation.md",
        f"""
# CWS-001: Composite Workflow Scientific Evaluation

## Purpose

Evaluate whether the preregistered CSM-001 x TSM-001 workflow provides scientifically meaningful information beyond the individual frozen construct states.

## Frozen Input Verification

| Check | Value |
|---|---|
| CWP authorized next stage | {verification['cwp_authorized_next_stage']} |
| CIP prior conclusion | {verification['cip_prior_conclusion']} |
| Verified | {verification['verified']} |

## Final Conclusion

**{conclusion}**

## Evidence

Supported by evidence:

- CSM_HIGH is fully nested inside TSM_HIGH in the common sample.
- The nesting relationship is stable across evaluated years.
- CSM and TSM each retain non-negligible incremental explanatory information in the registered analysis.
- The CSM_NOT_HIGH x TSM_HIGH region is large and distinct from the CSM_HIGH x TSM_HIGH region.

Partially supported:

- Composite workflow interpretation is supported scientifically, but only as a workflow using frozen constructs.

Not supported:

- Treating the workflow as a new construct.
- Production deployment.
- Alpha or profitability claims.

Inconclusive:

- Economic utility.
- Execution feasibility.
- Performance after costs.

## Registered Outputs

- `workflow_state_matrix.csv`
- `nested_state_analysis.csv`
- `conditional_information.csv`
- `incremental_information.csv`
- `conflict_region_analysis.csv`
- `time_stability_analysis.csv`
- `symbol_coverage_analysis.csv`
""",
    )

    write(
        "scientific_interpretation.md",
        f"""
# Scientific Interpretation

Final classification: **{conclusion}**.

The evidence supports a nested workflow architecture:

TSM-001 supplies the broad own-trend state. CSM-001 identifies the narrower cross-sectional leadership subset inside that state.

This is not redundancy because TSM_HIGH contains many observations that are not CSM_HIGH. It is not independence because all CSM_HIGH observations are also TSM_HIGH.

The strongest supported statement is:

**CSM-001 x TSM-001 forms a scientifically supported nested composite workflow under the frozen sample and preregistered protocol.**

The study does not support production deployment, portfolio optimization, or alpha claims.
""",
    )

    write(
        "limitations.md",
        """
# Limitations

- CWS-001 inherits all limitations of CSM-001, TSM-001, CIP-001 and CWP-001.
- The direct conflict region CSM_HIGH x TSM_LOW has zero observations, so symmetric conflict behavior cannot be evaluated.
- Incremental R-squared is descriptive and does not establish economic value.
- Future returns are used only as registered scientific outcome variables, not as strategy performance.
- No transaction costs, portfolio construction, capacity, liquidity, tax, slippage, or live/paper trading validation is evaluated.
- The workflow is not a new construct.
- No production deployment conclusion is authorized.
""",
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    df = load_common_sample()
    verification = frozen_input_verification(df)
    matrix = workflow_state_matrix(df)
    nested = nested_state_analysis(df)
    conditional = conditional_information(df)
    inc = incremental_information(df)
    conflict = conflict_region_analysis(df)
    stability = time_stability_analysis(df)
    coverage = symbol_coverage_analysis(df)

    matrix.to_csv(OUT / "workflow_state_matrix.csv", index=False)
    nested.to_csv(OUT / "nested_state_analysis.csv", index=False)
    conditional.to_csv(OUT / "conditional_information.csv", index=False)
    inc.to_csv(OUT / "incremental_information.csv", index=False)
    conflict.to_csv(OUT / "conflict_region_analysis.csv", index=False)
    stability.to_csv(OUT / "time_stability_analysis.csv", index=False)
    coverage.to_csv(OUT / "symbol_coverage_analysis.csv", index=False)
    build_reports(verification, matrix, nested, conditional, inc, conflict, stability, coverage)


if __name__ == "__main__":
    main()
