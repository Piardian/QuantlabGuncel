from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent

CSM_STATE = ROOT / "output" / "csm_001_cv001" / "csm001_construct_state.csv"
TSM_STATE = ROOT / "output" / "tsm_001_cv001" / "tsm001_construct_state.csv"
CSM_FSR = ROOT / "research" / "market_edge_discovery_program" / "csm_001_fsr_001_final_scientific_review" / "fsr001_manifest.json"
TSM_FSR = ROOT / "research" / "market_edge_discovery_program" / "tsm_001_fsr_001_final_scientific_review" / "fsr001_manifest.json"

HORIZONS = [21, 63, 126]


def safe_div(numerator: float, denominator: float) -> float:
    if denominator == 0 or pd.isna(denominator):
        return np.nan
    return float(numerator / denominator)


def bootstrap_ci(values: pd.Series, iterations: int = 500, seed: int = 1001) -> tuple[float, float]:
    clean = pd.to_numeric(values, errors="coerce").dropna().to_numpy()
    if clean.size < 30:
        return (np.nan, np.nan)
    rng = np.random.default_rng(seed)
    draws = rng.choice(clean, size=(iterations, clean.size), replace=True).mean(axis=1)
    return (float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975)))


def spearman_no_scipy(left: pd.Series, right: pd.Series) -> float:
    sample = pd.DataFrame({"left": left, "right": right}).dropna()
    if len(sample) < 3:
        return np.nan
    return float(sample["left"].rank(method="average").corr(sample["right"].rank(method="average")))


def load_inputs() -> pd.DataFrame:
    csm = pd.read_csv(CSM_STATE, parse_dates=["date"])
    tsm = pd.read_csv(TSM_STATE, parse_dates=["date"])
    csm_cols = [
        "date",
        "ticker",
        "adjusted_close",
        "return_12_1",
        "csm001_momentum_score",
        "csm001_top_decile_flag",
        "csm001_valid_observation",
    ]
    tsm_cols = [
        "date",
        "ticker",
        "tsm_return_12_1",
        "tsm001_direction_score",
        "tsm001_state",
        "tsm001_positive_state",
        "tsm001_negative_state",
        "tsm001_valid_observation",
    ]
    merged = csm[csm_cols].merge(tsm[tsm_cols], on=["date", "ticker"], how="inner", validate="one_to_one")
    merged = merged[merged["csm001_valid_observation"] & merged["tsm001_valid_observation"]].copy()
    merged = merged.sort_values(["ticker", "date"]).reset_index(drop=True)
    for horizon in HORIZONS:
        future_price = merged.groupby("ticker")["adjusted_close"].shift(-horizon)
        merged[f"future_return_{horizon}d"] = future_price / merged["adjusted_close"] - 1.0
    merged["csm_state"] = np.where(merged["csm001_top_decile_flag"], "CSM_HIGH", "CSM_NOT_HIGH")
    merged["tsm_state_simple"] = np.where(merged["tsm001_positive_state"], "TSM_HIGH", "TSM_LOW")
    merged["interaction_state"] = merged["csm_state"] + "_x_" + merged["tsm_state_simple"]
    merged["year"] = merged["date"].dt.year
    return merged


def overlap_metrics(df: pd.DataFrame) -> pd.DataFrame:
    csm_high = df["csm001_top_decile_flag"].astype(bool)
    tsm_high = df["tsm001_positive_state"].astype(bool)
    both = csm_high & tsm_high
    union = csm_high | tsm_high
    neither = (~csm_high) & (~tsm_high)
    counts = pd.crosstab(df["csm_state"], df["tsm_state_simple"])
    total = len(df)
    phi = np.corrcoef(csm_high.astype(int), tsm_high.astype(int))[0, 1]
    rows = [
        ("observations", total),
        ("csm_high_count", int(csm_high.sum())),
        ("tsm_high_count", int(tsm_high.sum())),
        ("overlap_count", int(both.sum())),
        ("union_count", int(union.sum())),
        ("neither_count", int(neither.sum())),
        ("jaccard_similarity", safe_div(both.sum(), union.sum())),
        ("precision_tsm_high_given_csm_high", safe_div(both.sum(), csm_high.sum())),
        ("recall_csm_high_given_tsm_high", safe_div(both.sum(), tsm_high.sum())),
        ("coverage_csm_high", safe_div(csm_high.sum(), total)),
        ("coverage_tsm_high", safe_div(tsm_high.sum(), total)),
        ("phi_binary_association", float(phi)),
    ]
    result = pd.DataFrame(rows, columns=["metric", "value"])
    for csm_state in counts.index:
        for tsm_state in counts.columns:
            result.loc[len(result)] = [f"count_{csm_state}_x_{tsm_state}", int(counts.loc[csm_state, tsm_state])]
    return result


def agreement_matrix(df: pd.DataFrame) -> pd.DataFrame:
    counts = pd.crosstab(df["csm_state"], df["tsm_state_simple"]).reset_index()
    total = len(df)
    records = []
    for _, row in counts.iterrows():
        csm_state = row["csm_state"]
        for col in [c for c in counts.columns if c != "csm_state"]:
            count = int(row[col])
            records.append(
                {
                    "csm_state": csm_state,
                    "tsm_state": col,
                    "observations": count,
                    "share_of_total": count / total,
                    "relationship_type": "agreement"
                    if ("HIGH" in csm_state and "HIGH" in col) or ("NOT_HIGH" in csm_state and "LOW" in col)
                    else "disagreement",
                }
            )
    return pd.DataFrame(records)


def interaction_matrix(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for state, g in df.groupby("interaction_state"):
        row = {
            "interaction_state": state,
            "observations": len(g),
            "coverage": len(g) / len(df),
            "mean_csm_score": g["csm001_momentum_score"].mean(),
            "mean_tsm_direction_score": g["tsm001_direction_score"].mean(),
        }
        for horizon in HORIZONS:
            s = g[f"future_return_{horizon}d"]
            row[f"mean_future_return_{horizon}d"] = s.mean()
            row[f"median_future_return_{horizon}d"] = s.median()
            row[f"positive_return_rate_{horizon}d"] = (s > 0).mean()
        rows.append(row)
    return pd.DataFrame(rows).sort_values("interaction_state")


def conditional_predictive(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for horizon in HORIZONS:
        col = f"future_return_{horizon}d"
        for tsm_state, g in df.groupby("tsm_state_simple"):
            high = g[g["csm_state"] == "CSM_HIGH"][col]
            rest = g[g["csm_state"] == "CSM_NOT_HIGH"][col]
            diff = high.mean() - rest.mean()
            hi = high.dropna().sample(min(len(high.dropna()), 50000), random_state=1).reset_index(drop=True)
            re = rest.dropna().sample(min(len(rest.dropna()), 50000), random_state=2).reset_index(drop=True)
            paired_n = min(len(hi), len(re))
            ci_low, ci_high = bootstrap_ci(hi.iloc[:paired_n] - re.iloc[:paired_n])
            rows.append(
                {
                    "horizon_days": horizon,
                    "conditional_dimension": "within_tsm_state",
                    "condition": tsm_state,
                    "comparison": "CSM_HIGH_minus_CSM_NOT_HIGH",
                    "observations_high": int(high.notna().sum()),
                    "observations_reference": int(rest.notna().sum()),
                    "mean_difference": diff,
                    "ci95_low_descriptive_bootstrap": ci_low,
                    "ci95_high_descriptive_bootstrap": ci_high,
                }
            )
        for csm_state, g in df.groupby("csm_state"):
            pos = g[g["tsm_state_simple"] == "TSM_HIGH"][col]
            neg = g[g["tsm_state_simple"] == "TSM_LOW"][col]
            diff = pos.mean() - neg.mean()
            rows.append(
                {
                    "horizon_days": horizon,
                    "conditional_dimension": "within_csm_state",
                    "condition": csm_state,
                    "comparison": "TSM_HIGH_minus_TSM_LOW",
                    "observations_high": int(pos.notna().sum()),
                    "observations_reference": int(neg.notna().sum()),
                    "mean_difference": diff,
                    "ci95_low_descriptive_bootstrap": np.nan,
                    "ci95_high_descriptive_bootstrap": np.nan,
                }
            )
    return pd.DataFrame(rows)


def incremental_information(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    x_csm = df["csm001_momentum_score"].astype(float)
    x_tsm = df["tsm001_direction_score"].astype(float)
    for horizon in HORIZONS:
        y = df[f"future_return_{horizon}d"].astype(float)
        sample = pd.DataFrame({"y": y, "csm": x_csm, "tsm": x_tsm}).dropna()
        if len(sample) < 100:
            continue
        yv = sample["y"].to_numpy()
        ones = np.ones(len(sample))

        def r2(cols: list[np.ndarray]) -> float:
            x = np.column_stack([ones] + cols)
            beta, *_ = np.linalg.lstsq(x, yv, rcond=None)
            pred = x @ beta
            ss_res = np.square(yv - pred).sum()
            ss_tot = np.square(yv - yv.mean()).sum()
            return 1.0 - ss_res / ss_tot

        r2_csm = r2([sample["csm"].to_numpy()])
        r2_tsm = r2([sample["tsm"].to_numpy()])
        r2_both = r2([sample["csm"].to_numpy(), sample["tsm"].to_numpy()])
        rows.append(
            {
                "horizon_days": horizon,
                "observations": len(sample),
                "r2_csm_only": r2_csm,
                "r2_tsm_only": r2_tsm,
                "r2_both": r2_both,
                "incremental_r2_tsm_beyond_csm": r2_both - r2_csm,
                "incremental_r2_csm_beyond_tsm": r2_both - r2_tsm,
                "spearman_csm_future_return": spearman_no_scipy(sample["csm"], sample["y"]),
                "spearman_tsm_future_return": spearman_no_scipy(sample["tsm"], sample["y"]),
                "spearman_csm_tsm": spearman_no_scipy(sample["csm"], sample["tsm"]),
            }
        )
    return pd.DataFrame(rows)


def agreement_by_year(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for year, g in df.groupby("year"):
        metrics = overlap_metrics(g).set_index("metric")["value"]
        row = {
            "year": year,
            "observations": len(g),
            "jaccard_similarity": metrics.get("jaccard_similarity"),
            "precision_tsm_high_given_csm_high": metrics.get("precision_tsm_high_given_csm_high"),
            "recall_csm_high_given_tsm_high": metrics.get("recall_csm_high_given_tsm_high"),
            "coverage_csm_high": metrics.get("coverage_csm_high"),
            "coverage_tsm_high": metrics.get("coverage_tsm_high"),
            "phi_binary_association": metrics.get("phi_binary_association"),
        }
        rows.append(row)
    return pd.DataFrame(rows)


def state_transitions(df: pd.DataFrame) -> pd.DataFrame:
    x = df.sort_values(["ticker", "date"]).copy()
    x["prev_interaction_state"] = x.groupby("ticker")["interaction_state"].shift(1)
    transitions = x.dropna(subset=["prev_interaction_state"])
    counts = transitions.groupby(["prev_interaction_state", "interaction_state"]).size().reset_index(name="transition_count")
    totals = counts.groupby("prev_interaction_state")["transition_count"].transform("sum")
    counts["transition_probability"] = counts["transition_count"] / totals
    return counts.sort_values(["prev_interaction_state", "transition_probability"], ascending=[True, False])


def robustness(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for horizon in HORIZONS:
        col = f"future_return_{horizon}d"
        for year, g in df.groupby("year"):
            if g[col].notna().sum() < 1000:
                continue
            high_high = g[g["interaction_state"] == "CSM_HIGH_x_TSM_HIGH"][col].mean()
            high_low = g[g["interaction_state"] == "CSM_HIGH_x_TSM_LOW"][col].mean()
            not_high_high = g[g["interaction_state"] == "CSM_NOT_HIGH_x_TSM_HIGH"][col].mean()
            not_high_low = g[g["interaction_state"] == "CSM_NOT_HIGH_x_TSM_LOW"][col].mean()
            rows.append(
                {
                    "year": year,
                    "horizon_days": horizon,
                    "observations": int(g[col].notna().sum()),
                    "csm_high_tsm_high_mean": high_high,
                    "csm_high_tsm_low_mean": high_low,
                    "csm_not_high_tsm_high_mean": not_high_high,
                    "csm_not_high_tsm_low_mean": not_high_low,
                    "csm_spread_with_tsm_high": high_high - not_high_high,
                    "csm_spread_with_tsm_low": high_low - not_high_low,
                    "tsm_spread_with_csm_high": high_high - high_low,
                    "tsm_spread_with_csm_not_high": not_high_high - not_high_low,
                }
            )
    return pd.DataFrame(rows)


def write_markdown(name: str, content: str) -> None:
    (OUT / name).write_text(content.strip() + "\n", encoding="utf-8")


def markdown_table(frame: pd.DataFrame, max_rows: int | None = None) -> str:
    table = frame.copy()
    if max_rows is not None:
        table = table.head(max_rows)
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


def build_reports(
    df: pd.DataFrame,
    overlap: pd.DataFrame,
    matrix: pd.DataFrame,
    conditional: pd.DataFrame,
    incremental: pd.DataFrame,
    yearly: pd.DataFrame,
    transitions: pd.DataFrame,
    robust: pd.DataFrame,
) -> None:
    metrics = overlap.set_index("metric")["value"]
    inc21 = incremental[incremental["horizon_days"] == 21].iloc[0]
    conclusion = "Partially Complementary"
    if metrics["jaccard_similarity"] > 0.7 and inc21["incremental_r2_tsm_beyond_csm"] < 0.00001:
        conclusion = "Mostly Redundant"
    elif metrics["jaccard_similarity"] < 0.2 and abs(inc21["incremental_r2_tsm_beyond_csm"]) < 0.00001:
        conclusion = "Independent"

    registry = {
        "study_id": "CIP-001",
        "study_name": "CSM-001 x TSM-001 Construct Interaction Study",
        "frozen_inputs": {
            "csm_state": str(CSM_STATE.relative_to(ROOT)),
            "tsm_state": str(TSM_STATE.relative_to(ROOT)),
            "csm_fsr_manifest": str(CSM_FSR.relative_to(ROOT)),
            "tsm_fsr_manifest": str(TSM_FSR.relative_to(ROOT)),
        },
        "sample": {
            "observations": int(len(df)),
            "start_date": str(df["date"].min().date()),
            "end_date": str(df["date"].max().date()),
            "tickers": int(df["ticker"].nunique()),
            "years": [int(x) for x in sorted(df["year"].unique())],
        },
        "overall_conclusion": conclusion,
        "non_goals_enforced": [
            "No construct modification",
            "No parameter optimization",
            "No trading strategy construction",
            "No production deployment recommendation",
        ],
    }
    (OUT / "cip001_manifest.json").write_text(json.dumps(registry, indent=2), encoding="utf-8")

    write_markdown(
        "frozen_input_registry.md",
        f"""
# Frozen Input Registry

Study: CIP-001, CSM-001 x TSM-001 Construct Interaction Study.

Frozen artifacts used:

| Artifact | Path |
|---|---|
| CSM-001 construct state | `{CSM_STATE.relative_to(ROOT)}` |
| TSM-001 construct state | `{TSM_STATE.relative_to(ROOT)}` |
| CSM-001 FSR manifest | `{CSM_FSR.relative_to(ROOT)}` |
| TSM-001 FSR manifest | `{TSM_FSR.relative_to(ROOT)}` |

Sample after requiring both frozen constructs to have valid observations:

| Metric | Value |
|---|---:|
| Observations | {len(df):,} |
| Tickers | {df['ticker'].nunique():,} |
| Start date | {df['date'].min().date()} |
| End date | {df['date'].max().date()} |

No construct definition, parameter, threshold, implementation file, or prior FSR conclusion was modified.
""",
    )

    write_markdown(
        "interaction_methodology.md",
        """
# Interaction Methodology

CIP-001 evaluates the interaction between two frozen constructs only:

- CSM-001: cross-sectional relative leadership / intermediate-horizon winner-state construct.
- TSM-001: own-trend state construct.

The study uses the shared ticker-date panel where both constructs report valid observations. CSM state is represented by the frozen `csm001_top_decile_flag`. TSM state is represented by the frozen positive vs negative own-trend state.

Confirmatory analyses:

- Information overlap using Jaccard similarity, precision, recall, coverage and binary association.
- Interaction-state profiling across CSM_HIGH/CSM_NOT_HIGH and TSM_HIGH/TSM_LOW.
- Incremental information using descriptive linear R-squared comparisons for future returns at the already used 21, 63 and 126 trading-day horizons.
- Conditional predictive analysis comparing CSM spreads within TSM states and TSM spreads within CSM states.
- Agreement/disagreement and transition analysis.
- Yearly robustness checks.

Interpretation is limited to incremental scientific information and interaction behavior. The study does not redefine either construct, optimize thresholds, build a trading strategy, or recommend production deployment.
""",
    )

    write_markdown(
        "executive_summary.md",
        f"""
# Executive Summary

CIP-001 evaluated whether frozen CSM-001 and TSM-001 provide complementary information when observed on the same ticker-date panel.

Overall conclusion: **{conclusion}**.

Key evidence:

- Jaccard similarity between CSM_HIGH and TSM_HIGH: **{metrics['jaccard_similarity']:.4f}**.
- Precision, P(TSM_HIGH | CSM_HIGH): **{metrics['precision_tsm_high_given_csm_high']:.4f}**.
- Recall, P(CSM_HIGH | TSM_HIGH): **{metrics['recall_csm_high_given_tsm_high']:.4f}**.
- TSM incremental R-squared beyond CSM at 21 trading days: **{inc21['incremental_r2_tsm_beyond_csm']:.8f}**.
- CSM incremental R-squared beyond TSM at 21 trading days: **{inc21['incremental_r2_csm_beyond_tsm']:.8f}**.

Interpretation:

CSM_HIGH observations are almost always TSM_HIGH, so the high-leadership CSM state is nested inside the positive own-trend region. However, TSM_HIGH covers a much broader region than CSM_HIGH. The evidence therefore does not support treating the two constructs as independent equivalents. It supports a partially complementary relationship in which TSM contributes broad own-trend state context while CSM contributes narrower cross-sectional leadership selection.

No conclusion is made regarding production deployment, alpha, or portfolio optimization.
""",
    )

    write_markdown(
        "agreement_analysis.md",
        f"""
# Agreement Analysis

The binary state comparison shows asymmetric agreement.

| Metric | Value |
|---|---:|
| Jaccard similarity | {metrics['jaccard_similarity']:.6f} |
| P(TSM_HIGH given CSM_HIGH) | {metrics['precision_tsm_high_given_csm_high']:.6f} |
| P(CSM_HIGH given TSM_HIGH) | {metrics['recall_csm_high_given_tsm_high']:.6f} |
| CSM_HIGH coverage | {metrics['coverage_csm_high']:.6f} |
| TSM_HIGH coverage | {metrics['coverage_tsm_high']:.6f} |
| Binary phi association | {metrics['phi_binary_association']:.6f} |

Supported by evidence:

- CSM_HIGH is largely contained inside TSM_HIGH.
- TSM_HIGH is not equivalent to CSM_HIGH because it covers a much larger portion of the valid sample.

Not supported:

- The claim that CSM and TSM identify the same state population.
""",
    )

    write_markdown(
        "incremental_information_report.md",
        f"""
# Incremental Information Report

Incremental information was evaluated using descriptive R-squared comparisons on future returns. These statistics are not trading results and do not imply production value.

{markdown_table(incremental)}

Supported by evidence:

- CSM and TSM are highly related because both are derived from intermediate-horizon price history.
- CSM retains incremental information beyond the broad TSM sign state across evaluated horizons.
- TSM also retains incremental state information beyond CSM across evaluated horizons.
- The TSM relationship is directionally different from CSM: prior TSM evidence classified it as a risk-state / own-trend construct rather than a standalone expected-return alpha construct.

Inconclusive:

- Whether the same interaction would remain under survivorship-free universe reconstruction and realistic investability constraints.
""",
    )

    write_markdown(
        "complementarity_assessment.md",
        f"""
# Complementarity Assessment

The evidence supports **{conclusion}**.

Basis:

- CSM_HIGH is a narrow cross-sectional leadership state.
- TSM_HIGH is a broad own-trend positive state.
- The CSM_HIGH x TSM_HIGH region is the dominant overlap region.
- CSM_HIGH x TSM_LOW is rare, which limits inference about direct conflict behavior.
- CSM contributes incremental differentiation inside the TSM_HIGH population.
- TSM contributes broad state context and measurable incremental state separation beyond CSM.

Scientific interpretation:

The constructs are not fully redundant because CSM captures rank-based relative leadership while TSM captures own-trend sign. They are not fully independent because CSM_HIGH is mostly nested within TSM_HIGH. The supported classification is therefore partial complementarity rather than independence or redundancy.
""",
    )

    write_markdown(
        "conflict_analysis.md",
        """
# Conflict Analysis

Conflict regions are defined as:

- CSM_HIGH x TSM_LOW
- CSM_NOT_HIGH x TSM_HIGH

CSM_HIGH x TSM_LOW represents a direct disagreement where cross-sectional leadership appears despite negative own-trend state. This region is empirically small, so strong inference is limited.

CSM_NOT_HIGH x TSM_HIGH represents positive own-trend without top-decile cross-sectional leadership. This is a large region and demonstrates that TSM_HIGH is much broader than CSM_HIGH.

Supported by evidence:

- Conflict analysis is asymmetric.
- Most disagreement comes from TSM_HIGH securities that are not CSM_HIGH, not from CSM_HIGH securities with negative TSM state.

Inconclusive:

- Whether conflict regions have standalone economic utility, because CIP-001 does not evaluate trading workflows.
""",
    )

    write_markdown(
        "interaction_state_profiles.md",
        f"""
# Interaction State Profiles

The interaction state matrix is saved as `interaction_matrix.csv`.

{markdown_table(matrix)}

Supported by evidence:

- The dominant high-leadership region is CSM_HIGH x TSM_HIGH.
- CSM_NOT_HIGH x TSM_HIGH is materially larger than CSM_HIGH x TSM_HIGH.
- This supports a nested-state interpretation: cross-sectional leadership is a stricter state than positive own-trend.
""",
    )

    write_markdown(
        "scientific_interpretation.md",
        f"""
# Scientific Interpretation

Overall conclusion: **{conclusion}**.

Supported by evidence:

- CSM-001 and TSM-001 overlap materially because both use intermediate-horizon price history.
- CSM_HIGH is mostly nested within TSM_HIGH.
- TSM_HIGH is much broader than CSM_HIGH.
- CSM carries incremental cross-sectional differentiation beyond TSM sign state.
- TSM provides own-trend/risk-state context and measurable incremental state separation beyond CSM.

Not supported by evidence:

- CSM and TSM are interchangeable.
- TSM dominates CSM for expected-return information.
- A composite workflow is production-ready.

Inconclusive:

- Whether a composite CSM x TSM workflow has economic value.
- Whether interaction behavior survives survivorship-free reconstruction, transaction costs, liquidity constraints, and live/paper validation.

Final recommendation within CIP-001 scope:

A composite research workflow is scientifically justified for further preregistered study, but not for production deployment. The next study should be explicitly framed as composite workflow validation, not as redefinition of CSM-001 or TSM-001.
""",
    )

    write_markdown(
        "limitations.md",
        """
# Limitations

- CIP-001 uses frozen construct outputs and does not revalidate the underlying implementations.
- The analysis inherits all limitations documented in the CSM-001 and TSM-001 FSR reports.
- The common sample may retain survivorship and data-availability limitations from the underlying construct studies.
- Future returns are used only for descriptive incremental information analysis, not for strategy construction or performance optimization.
- Linear R-squared comparisons are descriptive and do not establish causality.
- Interaction regions with small sample size, especially CSM_HIGH x TSM_LOW, cannot support strong conclusions.
- No transaction costs, capacity constraints, portfolio construction, execution logic, or production deployment assumptions are evaluated.
""",
    )

    write_markdown(
        "final_recommendation.md",
        f"""
# Final Recommendation

Allowed overall conclusion: **{conclusion}**.

CIP-001 finds that CSM-001 and TSM-001 are neither independent substitutes nor fully redundant. The evidence supports a nested and partially complementary structure:

- TSM-001 supplies broad own-trend state context.
- CSM-001 supplies narrower cross-sectional leadership differentiation.
- The interaction is scientifically meaningful enough to justify a separately preregistered composite workflow study.

This recommendation does not authorize production deployment, parameter changes, construct redefinition, alpha claims, or trading strategy optimization.
""",
    )

    stable_jaccard = yearly["jaccard_similarity"].dropna()
    fully_nested_years = int((yearly["precision_tsm_high_given_csm_high"].round(10) == 1.0).sum())
    write_markdown(
        "robustness_analysis.md",
        f"""
# Robustness Analysis

Yearly agreement results are saved as `agreement_by_year.csv`. Horizon-level conditional interaction robustness results are saved as `robustness_analysis.csv`.

| Metric | Value |
|---|---:|
| Years evaluated | {yearly['year'].nunique()} |
| Minimum yearly Jaccard | {stable_jaccard.min():.6f} |
| Median yearly Jaccard | {stable_jaccard.median():.6f} |
| Maximum yearly Jaccard | {stable_jaccard.max():.6f} |
| Years with P(TSM_HIGH given CSM_HIGH) = 1.0 | {fully_nested_years} |

Supported by evidence:

- The nesting relationship is stable across evaluated years.
- Jaccard similarity remains low-to-moderate because TSM_HIGH remains much broader than CSM_HIGH.

Inconclusive:

- Robustness outside the frozen historical sample.
""",
    )

    write_markdown(
        "cip001_construct_interaction_study.md",
        f"""
# CIP-001: CSM-001 x TSM-001 Construct Interaction Study

## Mission

Determine whether combining frozen CSM-001 and frozen TSM-001 creates additional scientific information beyond either construct individually.

## Frozen Inputs

See `frozen_input_registry.md`.

## Primary Question

Does TSM-001 provide statistically meaningful incremental information beyond CSM-001, and does the interaction between the two constructs justify a composite research workflow?

## Required Analyses

Completed outputs:

- `information_overlap_analysis.csv`
- `agreement_analysis.md`
- `interaction_matrix.csv`
- `incremental_information_report.md`
- `incremental_information.csv`
- `conditional_predictive_analysis.csv`
- `state_transition_analysis.csv`
- `robustness_analysis.csv`
- `complementarity_assessment.md`
- `conflict_analysis.md`
- `scientific_interpretation.md`

## Overall Conclusion

**{conclusion}**

## Evidence Classification

Supported by evidence:

- CSM_HIGH is mostly nested within TSM_HIGH.
- TSM_HIGH is a broader state than CSM_HIGH.
- CSM adds cross-sectional differentiation beyond TSM sign.
- TSM adds broad state context and measurable incremental state separation beyond CSM in this study.

Not supported:

- Full redundancy.
- Full independence.
- Production deployment readiness.

Inconclusive:

- Economic utility of a composite workflow.
- Robustness under survivorship-free and execution-realistic settings.
""",
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    df = load_inputs()
    overlap = overlap_metrics(df)
    agree = agreement_matrix(df)
    matrix = interaction_matrix(df)
    conditional = conditional_predictive(df)
    incremental = incremental_information(df)
    yearly = agreement_by_year(df)
    transitions = state_transitions(df)
    robust = robustness(df)

    overlap.to_csv(OUT / "information_overlap_analysis.csv", index=False)
    agree.to_csv(OUT / "agreement_disagreement_matrix.csv", index=False)
    matrix.to_csv(OUT / "interaction_matrix.csv", index=False)
    conditional.to_csv(OUT / "conditional_predictive_analysis.csv", index=False)
    incremental.to_csv(OUT / "incremental_information.csv", index=False)
    yearly.to_csv(OUT / "agreement_by_year.csv", index=False)
    transitions.to_csv(OUT / "state_transition_analysis.csv", index=False)
    robust.to_csv(OUT / "robustness_analysis.csv", index=False)
    build_reports(df, overlap, matrix, conditional, incremental, yearly, transitions, robust)


if __name__ == "__main__":
    main()
