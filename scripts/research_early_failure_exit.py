"""Early Failure Exit Shadow Simulation — Research Only.

For every completed walk-forward trade on leadership_expansion_v1, evaluate
hypothetical early-exit scenarios:

    Scenario A — Day-1 failure exit: exit if Day1 close <= entry close
    Scenario B — Day-2 failure exit: exit if Day2 close <= entry close
    Scenario C — Day-3 failure exit: exit if Day3 close <= entry close
    Scenario D — Original strategy (baseline)

Production strategy is NEVER modified.
This is a post-hoc shadow simulation over historical trade data.

Outputs:
    output/early_failure_exit_comparison.csv   — per-scenario metrics
    output/early_failure_trade_impact.csv      — trade-level impact analysis
"""

from __future__ import annotations

import math
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from data.yahoo_data import MarketDataRequest, YahooFinanceDataSource  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
OUTPUT_DIR = ROOT / "output"
START = "2018-01-01"
END = "2025-01-01"
TIMEFRAME = "1d"

WINDOWS = [
    ("W1_2021", "2021-01-01", "2022-01-01"),
    ("W2_2022", "2022-01-01", "2023-01-01"),
    ("W3_2023", "2023-01-01", "2024-01-01"),
    ("W4_2024", "2024-01-01", "2025-01-01"),
]

# Scenario definitions: (label, check_day_offset)
# check_day_offset=0 means "keep original" (baseline)
# Baseline is first so impact analysis can compare against it.
SCENARIOS = [
    ("D_Original_Baseline", 0),
    ("A_Day1_Failure_Exit", 1),
    ("B_Day2_Failure_Exit", 2),
    ("C_Day3_Failure_Exit", 3),
]

INITIAL_CAPITAL = 10_000.0


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------
def _fetch_with_retry(
    data_source: YahooFinanceDataSource, ticker: str
) -> pd.DataFrame:
    last_error: Exception | None = None
    for _ in range(3):
        try:
            return data_source.fetch(
                MarketDataRequest(
                    ticker=ticker, start=START, end=END, timeframe=TIMEFRAME
                )
            )
        except Exception as exc:
            last_error = exc
            time.sleep(1)
    raise RuntimeError(
        f"Could not fetch data for {ticker}: {last_error}"
    ) from last_error


def _load_walk_forward_universe() -> list[str]:
    universe_path = OUTPUT_DIR / "walk_forward_universe.csv"
    if not universe_path.exists():
        raise RuntimeError(
            "Missing walk_forward_universe.csv. Run walk-forward validation first."
        )
    return pd.read_csv(universe_path)["ticker"].dropna().astype(str).tolist()


def _load_walk_forward_trades(universe: list[str]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for window_name, test_start, test_end in WINDOWS:
        for ticker in universe:
            trades_path = (
                OUTPUT_DIR / f"walk_forward_{window_name}_{ticker}" / "trades.csv"
            )
            if not trades_path.exists():
                continue
            trades = pd.read_csv(
                trades_path, parse_dates=["entry_time", "exit_time"]
            )
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


def _position_for_date(
    dataframe: pd.DataFrame, date: pd.Timestamp
) -> int | None:
    normalized = date.normalize()
    matches = [
        i for i, dt in enumerate(dataframe.index.normalize()) if dt == normalized
    ]
    return matches[0] if matches else None


# ---------------------------------------------------------------------------
# Shadow simulation per trade
# ---------------------------------------------------------------------------
def _simulate_trade(
    trade: pd.Series,
    market_data: pd.DataFrame,
    check_day_offset: int,
) -> dict[str, object]:
    """Return shadow-adjusted trade metrics for a single trade.

    If check_day_offset == 0 → return original trade unchanged (baseline).
    Otherwise → check if close on day N <= entry close.
        If failure detected → hypothetical exit at day N close.
        If NOT detected     → keep original outcome.
    """
    entry_price = float(trade["entry_price"])
    stop_loss = float(trade["stop_loss"])
    position_size = float(trade["position_size"])
    original_pnl = float(trade["pnl_dollars"])
    original_r = float(trade["R_multiple"])
    original_exit_price = float(trade["exit_price"])
    original_duration = int(trade["trade_duration_bars"])
    original_exit_reason = str(trade["exit_reason"])

    initial_risk_per_share = abs(entry_price - stop_loss)
    initial_risk = initial_risk_per_share * position_size

    # Baseline — return original as-is
    if check_day_offset == 0:
        return {
            "modified": False,
            "exit_price": original_exit_price,
            "pnl_dollars": original_pnl,
            "R_multiple": original_r,
            "exit_reason": original_exit_reason,
            "trade_duration_bars": original_duration,
        }

    # Find entry bar position in market data
    entry_pos = _position_for_date(
        market_data, pd.Timestamp(trade["entry_time"])
    )
    if entry_pos is None:
        # Cannot evaluate — keep original
        return {
            "modified": False,
            "exit_price": original_exit_price,
            "pnl_dollars": original_pnl,
            "R_multiple": original_r,
            "exit_reason": original_exit_reason,
            "trade_duration_bars": original_duration,
        }

    entry_close = float(market_data.iloc[entry_pos]["Close"])
    check_pos = entry_pos + check_day_offset

    # Not enough future bars to evaluate
    if check_pos >= len(market_data):
        return {
            "modified": False,
            "exit_price": original_exit_price,
            "pnl_dollars": original_pnl,
            "R_multiple": original_r,
            "exit_reason": original_exit_reason,
            "trade_duration_bars": original_duration,
        }

    # Original trade already exited before check day
    if original_duration < check_day_offset:
        return {
            "modified": False,
            "exit_price": original_exit_price,
            "pnl_dollars": original_pnl,
            "R_multiple": original_r,
            "exit_reason": original_exit_reason,
            "trade_duration_bars": original_duration,
        }

    check_close = float(market_data.iloc[check_pos]["Close"])

    # Failure condition: day N close <= entry close
    if check_close <= entry_close:
        # Hypothetical exit at the check-day close
        shadow_pnl_per_share = check_close - entry_price
        shadow_pnl = shadow_pnl_per_share * position_size
        shadow_r = (shadow_pnl / initial_risk) if initial_risk > 0 else 0.0

        return {
            "modified": True,
            "exit_price": check_close,
            "pnl_dollars": shadow_pnl,
            "R_multiple": shadow_r,
            "exit_reason": f"EARLY_EXIT_DAY{check_day_offset}",
            "trade_duration_bars": check_day_offset,
        }

    # Failure NOT detected → keep original
    return {
        "modified": False,
        "exit_price": original_exit_price,
        "pnl_dollars": original_pnl,
        "R_multiple": original_r,
        "exit_reason": original_exit_reason,
        "trade_duration_bars": original_duration,
    }


# ---------------------------------------------------------------------------
# Metrics calculation
# ---------------------------------------------------------------------------
def _calculate_scenario_metrics(
    results: list[dict[str, object]],
) -> dict[str, object]:
    """Given a list of shadow-trade dicts, compute aggregate metrics."""
    if not results:
        return {
            "trade_count": 0,
            "avg_R": 0.0,
            "expectancy": 0.0,
            "profit_factor": 0.0,
            "winrate": 0.0,
            "net_pnl": 0.0,
            "max_drawdown": 0.0,
        }

    rs = [float(r["R_multiple"]) for r in results]
    pnls = [float(r["pnl_dollars"]) for r in results]

    trade_count = len(rs)
    avg_r = sum(rs) / trade_count
    expectancy = avg_r  # expectancy ≡ avg_R for 1R-normalized trades

    gross_profit = sum(p for p in pnls if p > 0)
    gross_loss = abs(sum(p for p in pnls if p < 0))
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (
        float("inf") if gross_profit > 0 else 0.0
    )

    wins = sum(1 for r in rs if r > 0)
    winrate = (wins / trade_count) * 100.0

    net_pnl = sum(pnls)

    # Max drawdown on cumulative PnL curve
    cumulative = 0.0
    peak = 0.0
    max_dd = 0.0
    for pnl in pnls:
        cumulative += pnl
        if cumulative > peak:
            peak = cumulative
        dd = peak - cumulative
        if dd > max_dd:
            max_dd = dd

    # Express drawdown as % of initial capital
    max_dd_pct = (max_dd / INITIAL_CAPITAL) * 100.0 if INITIAL_CAPITAL > 0 else 0.0

    return {
        "trade_count": trade_count,
        "avg_R": round(avg_r, 4),
        "expectancy": round(expectancy, 4),
        "profit_factor": round(profit_factor, 4) if math.isfinite(profit_factor) else float("inf"),
        "winrate": round(winrate, 2),
        "net_pnl": round(net_pnl, 2),
        "max_drawdown": round(max_dd_pct, 2),
    }


# ---------------------------------------------------------------------------
# Impact analysis
# ---------------------------------------------------------------------------
def _calculate_impact(
    scenario_label: str,
    results: list[dict[str, object]],
    baseline_results: list[dict[str, object]],
) -> dict[str, object]:
    """Calculate trade-level impact: how many trades changed, R saved vs lost."""
    modified = [r for r in results if r["modified"]]
    num_modified = len(modified)

    if num_modified == 0:
        return {
            "scenario": scenario_label,
            "number_of_trades_modified": 0,
            "average_R_saved": 0.0,
            "average_R_lost": 0.0,
        }

    # For modified trades, compare shadow R vs original R
    # Build baseline lookup by index (results and baseline_results share order)
    r_deltas: list[float] = []
    for i, (shadow, orig) in enumerate(zip(results, baseline_results)):
        if not shadow["modified"]:
            continue
        orig_r = float(orig["R_multiple"])
        shadow_r = float(shadow["R_multiple"])
        delta = shadow_r - orig_r  # positive = we saved R, negative = we lost R
        r_deltas.append(delta)

    saved = [d for d in r_deltas if d > 0]
    lost = [d for d in r_deltas if d < 0]

    avg_saved = (sum(saved) / len(saved)) if saved else 0.0
    avg_lost = (sum(lost) / len(lost)) if lost else 0.0

    return {
        "scenario": scenario_label,
        "number_of_trades_modified": num_modified,
        "average_R_saved": round(avg_saved, 4),
        "average_R_lost": round(avg_lost, 4),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    print("=" * 70)
    print("EARLY FAILURE EXIT — SHADOW SIMULATION RESEARCH")
    print("Production strategy is NOT modified.")
    print("=" * 70)

    data_source = YahooFinanceDataSource()
    universe = _load_walk_forward_universe()

    print(f"\nUniverse: {universe}")
    print("Loading market data...")
    market_cache: dict[str, pd.DataFrame] = {}
    for ticker in universe:
        market_cache[ticker] = _fetch_with_retry(
            data_source=data_source, ticker=ticker
        )
        print(f"  {ticker}: {len(market_cache[ticker])} bars loaded")

    print("Loading walk-forward trades...")
    trades = _load_walk_forward_trades(universe=universe)
    if trades.empty:
        print("ERROR: No walk-forward trades found. Run walk-forward validation first.")
        return
    print(f"  Total test-window trades: {len(trades)}")

    # -------------------------------------------------------------------
    # Run shadow simulation for each scenario
    # -------------------------------------------------------------------
    comparison_rows: list[dict[str, object]] = []
    impact_rows: list[dict[str, object]] = []
    baseline_results: list[dict[str, object]] | None = None

    for scenario_label, check_day in SCENARIOS:
        print(f"\n--- Scenario: {scenario_label} (check_day={check_day}) ---")

        scenario_results: list[dict[str, object]] = []
        for _, trade in trades.iterrows():
            ticker = str(trade["ticker"])
            if ticker not in market_cache:
                continue
            result = _simulate_trade(
                trade=trade,
                market_data=market_cache[ticker],
                check_day_offset=check_day,
            )
            scenario_results.append(result)

        metrics = _calculate_scenario_metrics(scenario_results)
        metrics["scenario"] = scenario_label
        comparison_rows.append(metrics)

        modified_count = sum(1 for r in scenario_results if r["modified"])
        print(f"  Trades evaluated: {len(scenario_results)}")
        print(f"  Trades modified:  {modified_count}")
        print(f"  Avg R:            {metrics['avg_R']}")
        print(f"  Win rate:         {metrics['winrate']}%")
        print(f"  Net PnL:          ${metrics['net_pnl']}")
        print(f"  Max drawdown:     {metrics['max_drawdown']}%")
        print(f"  Profit factor:    {metrics['profit_factor']}")

        # Store baseline for impact comparison
        if check_day == 0:
            baseline_results = scenario_results
        else:
            if baseline_results is not None:
                impact = _calculate_impact(
                    scenario_label=scenario_label,
                    results=scenario_results,
                    baseline_results=baseline_results,
                )
                impact_rows.append(impact)

    # -------------------------------------------------------------------
    # Output 1: early_failure_exit_comparison.csv
    # -------------------------------------------------------------------
    col_order = [
        "scenario", "trade_count", "avg_R", "expectancy",
        "profit_factor", "winrate", "net_pnl", "max_drawdown",
    ]
    comparison_df = pd.DataFrame(comparison_rows)[col_order]
    scenario_order = {s[0]: i for i, s in enumerate([
        ("A_Day1_Failure_Exit", 1), ("B_Day2_Failure_Exit", 2),
        ("C_Day3_Failure_Exit", 3), ("D_Original_Baseline", 0),
    ])}
    comparison_df = comparison_df.sort_values(
        "scenario", key=lambda s: s.map(scenario_order)
    ).reset_index(drop=True)
    comparison_path = OUTPUT_DIR / "early_failure_exit_comparison.csv"
    comparison_df.to_csv(comparison_path, index=False)
    print(f"\n{'=' * 70}")
    print(f"OUTPUT 1: {comparison_path}")
    print(comparison_df.to_string(index=False))

    # -------------------------------------------------------------------
    # Output 2: early_failure_trade_impact.csv
    # -------------------------------------------------------------------
    impact_df = pd.DataFrame(impact_rows)
    impact_path = OUTPUT_DIR / "early_failure_trade_impact.csv"
    impact_df.to_csv(impact_path, index=False)
    print(f"\nOUTPUT 2: {impact_path}")
    print(impact_df.to_string(index=False))

    # -------------------------------------------------------------------
    # Verdict
    # -------------------------------------------------------------------
    print(f"\n{'=' * 70}")
    print("RESEARCH CONCLUSION")
    print("=" * 70)
    if baseline_results is not None and comparison_rows:
        baseline_metrics = next(
            r for r in comparison_rows if r["scenario"] == "D_Original_Baseline"
        )
        baseline_avg_r = float(baseline_metrics["avg_R"])
        baseline_pf = float(baseline_metrics["profit_factor"])
        baseline_net = float(baseline_metrics["net_pnl"])

        for row in comparison_rows:
            if row["scenario"] == "D_Original_Baseline":
                continue
            label = row["scenario"]
            s_avg_r = float(row["avg_R"])
            s_pf = float(row["profit_factor"])
            s_net = float(row["net_pnl"])

            r_delta = s_avg_r - baseline_avg_r
            pnl_delta = s_net - baseline_net

            verdict = "IMPROVES" if (r_delta > 0 and pnl_delta > 0) else (
                "MIXED" if (r_delta > 0 or pnl_delta > 0) else "HURTS"
            )

            print(f"\n  {label}:")
            print(f"    Avg R delta:      {r_delta:+.4f}")
            print(f"    Net PnL delta:    ${pnl_delta:+,.2f}")
            print(f"    Profit factor:    {s_pf:.4f} (baseline: {baseline_pf:.4f})")
            print(f"    --> Verdict:      {verdict}")

        # Check for impact on winners
        for impact_row in impact_rows:
            label = impact_row["scenario"]
            avg_lost = float(impact_row["average_R_lost"])
            if avg_lost < -0.5:
                print(f"\n  WARNING: {label} average_R_lost = {avg_lost:.4f}R")
                print("    This scenario may be destroying winners.")

    print(f"\n{'=' * 70}")
    print("REMINDER: This is research only. No production code was modified.")
    print("=" * 70)


if __name__ == "__main__":
    main()
