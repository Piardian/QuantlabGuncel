from __future__ import annotations

from pathlib import Path
import math

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output"
SIMULATIONS = 10_000
INITIAL_EQUITY = 100_000.0
BASE_RISK_PER_TRADE = 0.01
RISK_OF_RUIN_LEVELS = [0.005, 0.01, 0.02]
RANDOM_SEED = 42
WINDOWS = [
    ("W1_2021", "2021-01-01", "2022-01-01"),
    ("W2_2022", "2022-01-01", "2023-01-01"),
    ("W3_2023", "2023-01-01", "2024-01-01"),
    ("W4_2024", "2024-01-01", "2025-01-01"),
]


def main() -> None:
    trades = _load_walk_forward_trades()
    if trades.empty:
        raise RuntimeError("No walk-forward trades found for Monte Carlo validation.")

    r_multiples = pd.to_numeric(trades["R_multiple"], errors="coerce").dropna().to_numpy(dtype=float)
    rng = np.random.default_rng(RANDOM_SEED)

    results = _run_monte_carlo(
        r_multiples=r_multiples,
        risk_per_trade=BASE_RISK_PER_TRADE,
        rng=rng,
    )
    results_path = OUTPUT_DIR / "monte_carlo_results.csv"
    results.to_csv(results_path, index=False)

    summary = _build_summary(results)
    summary_path = OUTPUT_DIR / "monte_carlo_summary.csv"
    summary.to_csv(summary_path, index=False)

    risk_of_ruin = _build_risk_of_ruin_report(r_multiples=r_multiples)
    risk_path = OUTPUT_DIR / "risk_of_ruin_report.csv"
    risk_of_ruin.to_csv(risk_path, index=False)

    print(results_path)
    print(summary_path)
    print(risk_path)


def _load_walk_forward_trades() -> pd.DataFrame:
    universe_path = OUTPUT_DIR / "walk_forward_universe.csv"
    if not universe_path.exists():
        raise RuntimeError("Missing walk_forward_universe.csv. Run walk-forward validation first.")

    tickers = pd.read_csv(universe_path)["ticker"].dropna().astype(str).tolist()
    frames = []
    for window_name, test_start, test_end in WINDOWS:
        for ticker in tickers:
            trades_path = OUTPUT_DIR / f"walk_forward_{window_name}_{ticker}" / "trades.csv"
            if not trades_path.exists():
                continue
            trades = pd.read_csv(trades_path, parse_dates=["entry_time", "exit_time"])
            if trades.empty:
                continue
            test_trades = trades[
                (trades["entry_time"] >= pd.Timestamp(test_start))
                & (trades["entry_time"] < pd.Timestamp(test_end))
            ].copy()
            if test_trades.empty:
                continue
            test_trades["window"] = window_name
            test_trades["ticker"] = ticker
            frames.append(test_trades)

    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def _run_monte_carlo(r_multiples: np.ndarray, risk_per_trade: float, rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    trade_count = len(r_multiples)
    for simulation_id in range(1, SIMULATIONS + 1):
        shuffled = rng.permutation(r_multiples)
        equity_curve = _equity_curve_from_r(shuffled, risk_per_trade)
        rows.append(
            {
                "simulation": simulation_id,
                "trade_count": trade_count,
                "final_equity": float(equity_curve[-1]),
                "max_drawdown": _max_drawdown(equity_curve),
                "profit_factor": _profit_factor(shuffled),
                "return": float((equity_curve[-1] / INITIAL_EQUITY) - 1.0),
                "longest_losing_streak": _longest_losing_streak(shuffled),
            }
        )
    return pd.DataFrame(rows)


def _equity_curve_from_r(r_multiples: np.ndarray, risk_per_trade: float) -> np.ndarray:
    equity = INITIAL_EQUITY
    values = [equity]
    for r_multiple in r_multiples:
        equity *= max(0.0, 1.0 + (float(r_multiple) * risk_per_trade))
        values.append(equity)
    return np.array(values, dtype=float)


def _max_drawdown(equity_curve: np.ndarray) -> float:
    running_peak = np.maximum.accumulate(equity_curve)
    drawdowns = (equity_curve / running_peak) - 1.0
    return float(abs(drawdowns.min()))


def _profit_factor(r_multiples: np.ndarray) -> float:
    gains = r_multiples[r_multiples > 0].sum()
    losses = abs(r_multiples[r_multiples < 0].sum())
    if losses <= 0:
        return math.inf if gains > 0 else 0.0
    return float(gains / losses)


def _longest_losing_streak(r_multiples: np.ndarray) -> int:
    longest = 0
    current = 0
    for r_multiple in r_multiples:
        if r_multiple < 0:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest


def _build_summary(results: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "mean_return": float(results["return"].mean()),
                "median_return": float(results["return"].median()),
                "5th_percentile_return": float(results["return"].quantile(0.05)),
                "95th_percentile_return": float(results["return"].quantile(0.95)),
                "mean_max_drawdown": float(results["max_drawdown"].mean()),
                "95th_percentile_drawdown": float(results["max_drawdown"].quantile(0.95)),
                "mean_profit_factor": float(results["profit_factor"].replace([math.inf, -math.inf], pd.NA).dropna().mean()),
                "worst_losing_streak": int(results["longest_losing_streak"].max()),
                "95th_percentile_losing_streak": float(results["longest_losing_streak"].quantile(0.95)),
            }
        ]
    )


def _build_risk_of_ruin_report(r_multiples: np.ndarray) -> pd.DataFrame:
    rows = []
    for risk_per_trade in RISK_OF_RUIN_LEVELS:
        rng = np.random.default_rng(RANDOM_SEED)
        ruin_count = 0
        max_drawdowns = []
        for _ in range(SIMULATIONS):
            shuffled = rng.permutation(r_multiples)
            equity_curve = _equity_curve_from_r(shuffled, risk_per_trade)
            max_drawdown = _max_drawdown(equity_curve)
            max_drawdowns.append(max_drawdown)
            if max_drawdown >= 0.50:
                ruin_count += 1
        rows.append(
            {
                "risk_per_trade": risk_per_trade,
                "simulations": SIMULATIONS,
                "ruin_threshold_drawdown": 0.50,
                "ruin_count": ruin_count,
                "risk_of_ruin": ruin_count / SIMULATIONS,
                "mean_max_drawdown": float(np.mean(max_drawdowns)),
                "95th_percentile_drawdown": float(np.quantile(max_drawdowns, 0.95)),
            }
        )
    return pd.DataFrame(rows)


if __name__ == "__main__":
    main()
