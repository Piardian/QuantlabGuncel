"""RC-A3 factorial EMA200 interaction analysis over the frozen RC-A1 runs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


EXPERIMENTS = [
    "RC-A1-E0_BASELINE",
    "RC-A1-E1_NO_EMA200_PRICE",
    "RC-A1-E2_NO_EMA200_SLOPE",
    "RC-A1-E3_NO_EMA200_ARCHITECTURE",
]
METRICS = ["trade_count", "profit_factor", "avg_R", "expectancy"]
BOOTSTRAP_ITERATIONS = 10_000
SEED = 20260723


def main() -> None:
    global EXPERIMENTS
    args = _args()
    EXPERIMENTS = args.experiments
    _require_baseline_validations(args.baseline_dir)
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    trades = {name: pd.read_csv(args.a1_dir / f"{name}_trades.csv", parse_dates=["entry_time"]) for name in EXPERIMENTS}
    summary = pd.DataFrame([_metrics(name, frame) for name, frame in trades.items()])
    baseline = summary.iloc[0]
    for metric in ["trade_count", "profit_factor", "avg_R", "expectancy", "win_rate", "median_R"]:
        summary[f"delta_{metric}"] = summary[metric] - baseline[metric]
    summary.to_csv(output / "interaction_summary.csv", index=False)

    yearly = _segmented(trades, "year")
    symbols = _segmented(trades, "ticker")
    yearly.to_csv(output / "interaction_yearly.csv", index=False)
    symbols.to_csv(output / "interaction_symbol.csv", index=False)
    bootstrap = _bootstrap(trades, BOOTSTRAP_ITERATIONS, SEED)
    bootstrap.to_csv(output / "bootstrap_interaction.csv", index=False)
    permutation = _sign_flip_permutation(symbols, BOOTSTRAP_ITERATIONS, SEED)
    permutation.to_csv(output / "permutation_interaction.csv", index=False)
    effects = _effects(summary, yearly, symbols, bootstrap, permutation, args.experiment_id)
    (output / "interaction_effects.json").write_text(json.dumps(effects, indent=2), encoding="utf-8")
    _report(output / args.report_name, summary, effects, bootstrap, permutation, args.experiment_id)


def _metrics(experiment: str, trades: pd.DataFrame) -> dict[str, float | int | str]:
    r = pd.to_numeric(trades["R_multiple"], errors="coerce").dropna()
    wins, losses = r[r > 0], r[r < 0]
    return {
        "experiment": experiment,
        "trade_count": len(r),
        "win_rate": float((r > 0).mean() * 100),
        "profit_factor": float(wins.sum() / abs(losses.sum())) if len(losses) else np.inf,
        "expectancy": float(r.mean()),
        "avg_R": float(r.mean()),
        "median_R": float(r.median()),
        "largest_winner": float(r.max()),
        "largest_loser": float(r.min()),
        "average_holding_days": float(pd.to_numeric(trades["holding_days"], errors="coerce").mean()),
    }


def _interaction(rows: pd.DataFrame) -> dict[str, float]:
    indexed = rows.set_index("experiment")
    return {
        metric: float(indexed.loc[EXPERIMENTS[3], metric] - indexed.loc[EXPERIMENTS[1], metric]
                      - indexed.loc[EXPERIMENTS[2], metric] + indexed.loc[EXPERIMENTS[0], metric])
        for metric in METRICS
    }


def _segmented(trades: dict[str, pd.DataFrame], dimension: str) -> pd.DataFrame:
    rows = []
    for experiment, frame in trades.items():
        working = frame.copy()
        if dimension == "year":
            working["year"] = working["entry_time"].dt.year
        for value, group in working.groupby(dimension):
            rows.append({dimension: value, **_metrics(experiment, group)})
    result = pd.DataFrame(rows)
    interactions = []
    for value, group in result.groupby(dimension):
        if set(group.experiment) == set(EXPERIMENTS):
            interactions.append({dimension: value, **{f"interaction_{key}": value for key, value in _interaction(group).items()}})
    return result.merge(pd.DataFrame(interactions), on=dimension, how="left")


def _ticker_statistics(trades: dict[str, pd.DataFrame], tickers: list[str]) -> dict[str, np.ndarray]:
    arrays = {}
    for experiment, frame in trades.items():
        r = pd.to_numeric(frame["R_multiple"], errors="coerce")
        stats = pd.DataFrame({"ticker": frame["ticker"], "r": r}).dropna().groupby("ticker").agg(
            trade_count=("r", "size"), total_r=("r", "sum"), win_r=("r", lambda x: x[x > 0].sum()), loss_r=("r", lambda x: -x[x < 0].sum()),
        ).reindex(tickers, fill_value=0.0)
        arrays[experiment] = stats[["trade_count", "total_r", "win_r", "loss_r"]].to_numpy(dtype=float)
    return arrays


def _metric_from_stats(values: np.ndarray) -> np.ndarray:
    count, total, wins, losses = values[:, 0], values[:, 1], values[:, 2], values[:, 3]
    avg = np.divide(total, count, out=np.full(len(count), np.nan), where=count > 0)
    pf = np.divide(wins, losses, out=np.full(len(count), np.nan), where=losses > 0)
    return np.column_stack([count, pf, avg, avg])


def _bootstrap(trades: dict[str, pd.DataFrame], iterations: int, seed: int) -> pd.DataFrame:
    tickers = sorted(set.intersection(*(set(frame.ticker) for frame in trades.values())))
    stats = _ticker_statistics(trades, tickers)
    rng = np.random.default_rng(seed)
    weights = rng.multinomial(len(tickers), np.full(len(tickers), 1 / len(tickers)), size=iterations)
    metrics = {name: _metric_from_stats(weights @ value) for name, value in stats.items()}
    effects = {
        "interaction": metrics[EXPERIMENTS[3]] - metrics[EXPERIMENTS[1]] - metrics[EXPERIMENTS[2]] + metrics[EXPERIMENTS[0]],
        "first_filter_removal": metrics[EXPERIMENTS[1]] - metrics[EXPERIMENTS[0]],
        "second_filter_removal": metrics[EXPERIMENTS[2]] - metrics[EXPERIMENTS[0]],
    }
    rows = []
    for effect_name, effect_values in effects.items():
        for index, metric in enumerate(METRICS):
            values = effect_values[:, index]
            rows.append({"effect": effect_name, "metric": metric, "iterations": iterations, "mean_interaction": float(np.nanmean(values)), "ci_2_5": float(np.nanquantile(values, .025)), "ci_97_5": float(np.nanquantile(values, .975)), "standard_error": float(np.nanstd(values, ddof=1))})
    return pd.DataFrame(rows)


def _sign_flip_permutation(symbols: pd.DataFrame, iterations: int, seed: int) -> pd.DataFrame:
    interaction_columns = ["interaction_trade_count", "interaction_profit_factor", "interaction_avg_R", "interaction_expectancy"]
    compact = symbols.drop_duplicates("ticker").set_index("ticker")
    # Reconstruct per-ticker interactions from the repeated experiment rows.
    rows = []
    rng = np.random.default_rng(seed)
    for metric, column in zip(METRICS, interaction_columns):
        values = symbols.groupby("ticker")[column].first().dropna().to_numpy(dtype=float)
        observed = float(values.mean())
        signs = rng.choice(np.array([-1.0, 1.0]), size=(iterations, len(values)))
        null = (signs * values).mean(axis=1)
        exceedances = int((np.abs(null) >= abs(observed)).sum())
        rows.append({"metric": metric, "method": "ticker_level_sign_flip_descriptive", "observed_interaction": observed, "null_mean": float(null.mean()), "null_standard_error": float(null.std(ddof=1)), "empirical_p_value_two_sided": float((exceedances + 1) / (iterations + 1)), "ticker_count": len(values), "iterations": iterations})
    return pd.DataFrame(rows)


def _effects(summary, yearly, symbols, bootstrap, permutation, experiment_id):
    observed = _interaction(summary)
    bootstrap_by_metric = bootstrap.loc[bootstrap.effect == "interaction"].set_index("metric").to_dict("index")
    first_bootstrap = bootstrap.loc[bootstrap.effect == "first_filter_removal"].set_index("metric").to_dict("index")
    second_bootstrap = bootstrap.loc[bootstrap.effect == "second_filter_removal"].set_index("metric").to_dict("index")
    permutation_by_metric = permutation.set_index("metric").to_dict("index")
    stability = {}
    for metric in METRICS:
        column = f"interaction_{metric}"
        year_values = yearly.groupby("year")[column].first().dropna()
        symbol_values = symbols.groupby("ticker")[column].first().dropna()
        stability[metric] = {
            "positive_year_fraction": float((year_values > 0).mean()),
            "positive_ticker_fraction": float((symbol_values > 0).mean()),
        }
    avg = bootstrap_by_metric["avg_R"]
    perm = permutation_by_metric["avg_R"]
    magnitude = abs(observed["avg_R"])
    # Fixed RC-A3 criterion: <0.02R is economically negligible; no class may pass with CI spanning zero or p >= .05.
    if magnitude < .02:
        classification = "None"
    elif avg["ci_2_5"] <= 0 <= avg["ci_97_5"] or perm["empirical_p_value_two_sided"] >= .05:
        classification = "Inconclusive"
    elif magnitude >= .10 and min(stability["avg_R"].values()) >= .70:
        classification = "Strong"
    elif magnitude >= .05 and min(stability["avg_R"].values()) >= .60:
        classification = "Moderate"
    else:
        classification = "Weak"
    independent = {
        "first_filter_delta_avg_R": float(summary.iloc[1].avg_R - summary.iloc[0].avg_R),
        "second_filter_delta_avg_R": float(summary.iloc[2].avg_R - summary.iloc[0].avg_R),
    }
    def independent_classification(delta, boot):
        if abs(delta) < .02:
            return "None"
        if boot["ci_2_5"] <= 0 <= boot["ci_97_5"]:
            return "Inconclusive"
        return "Weak"
    independent_classifications = {
        "first_filter": independent_classification(independent["first_filter_delta_avg_R"], first_bootstrap["avg_R"]),
        "second_filter": independent_classification(independent["second_filter_delta_avg_R"], second_bootstrap["avg_R"]),
    }
    return {"experiment_id": experiment_id, "interaction_formula": "E3 - E1 - E2 + E0", "observed_interactions": observed, "independent_effects": independent, "independent_bootstrap": {"first_filter": first_bootstrap["avg_R"], "second_filter": second_bootstrap["avg_R"]}, "independent_classifications": independent_classifications, "bootstrap": bootstrap_by_metric, "permutation": permutation_by_metric, "stability": stability, "classification": classification, "classification_rule": "Average-R magnitude <0.02R is None. Larger effects require bootstrap CI excluding zero and descriptive sign-flip p<0.05; Moderate/Strong additionally require fixed magnitude and direction-stability thresholds.", "statistical_limit": "The sign-flip result is descriptive, not a randomized-treatment causal p-value; strategy variants share the same deterministic market history."}


def _require_baseline_validations(directory: Path) -> None:
    reports = sorted(directory.glob("*/baseline_validation_report.md"))
    if len(reports) != 4 or any("Trade records identical: True" not in path.read_text(encoding="utf-8") for path in reports):
        raise RuntimeError("Four passing baseline validations are required before RC-A3 analysis.")


def _report(path, summary, effects, bootstrap, permutation, experiment_id):
    lines = [f"# {experiment_id} Factorial Interaction Study", "", "## Experiment Metrics", "", summary.to_string(index=False), "", "## Interaction Effects", "", json.dumps(effects, indent=2), "", "## Bootstrap", "", bootstrap.to_string(index=False), "", "## Sign-Flip Permutation", "", permutation.to_string(index=False), "", "## Scope Limitation", "", "Sign-flip p-values are descriptive because deterministic strategy variants are not randomized treatments. No causal claim is made."]
    path.write_text("\n".join(lines), encoding="utf-8")


def _args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--a1-dir", type=Path, required=True)
    parser.add_argument("--baseline-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--experiment-id", default="RC-A3")
    parser.add_argument("--experiments", nargs=4, default=EXPERIMENTS)
    parser.add_argument("--report-name", default="ema_interaction_study.md")
    return parser.parse_args()


if __name__ == "__main__":
    main()
