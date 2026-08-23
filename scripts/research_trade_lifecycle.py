"""Trade Lifecycle Analysis — Research Only.

Analyzes where strategy profits actually come from across all walk-forward
trades on leadership_expansion_v1.

Outputs:
    output/trade_lifecycle_analysis.csv    — per-trade raw data
    output/profit_concentration.csv        — top-N profit concentration
    output/duration_bucket_analysis.csv    — performance by holding period
    output/exit_reason_contribution.csv    — performance by exit type

Production strategy is NEVER modified.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
OUTPUT_DIR = ROOT / "output"

WINDOWS = [
    ("W1_2021", "2021-01-01", "2022-01-01"),
    ("W2_2022", "2022-01-01", "2023-01-01"),
    ("W3_2023", "2023-01-01", "2024-01-01"),
    ("W4_2024", "2024-01-01", "2025-01-01"),
]

DURATION_BUCKETS = [
    ("0-5",   0,  5),
    ("6-10",  6,  10),
    ("11-20", 11, 20),
    ("21-40", 21, 40),
    ("40+",   41, 999_999),
]


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# 1. Trade Lifecycle — per-trade raw data
# ---------------------------------------------------------------------------
def _build_lifecycle(trades: pd.DataFrame) -> pd.DataFrame:
    """Extract the fields requested for every trade."""
    df = trades.copy()
    df["entry_year"] = df["entry_time"].dt.year
    cols = [
        "ticker",
        "entry_time",
        "exit_time",
        "entry_year",
        "trade_duration_bars",
        "R_multiple",
        "pnl_dollars",
        "exit_reason",
        "window",
    ]
    return df[cols].reset_index(drop=True)


# ---------------------------------------------------------------------------
# 2. Profit concentration
# ---------------------------------------------------------------------------
def _build_profit_concentration(lifecycle: pd.DataFrame) -> pd.DataFrame:
    """What % of total profits comes from top-N trades?"""
    sorted_by_pnl = lifecycle.sort_values("pnl_dollars", ascending=False).reset_index(
        drop=True
    )
    total_pnl = sorted_by_pnl["pnl_dollars"].sum()
    total_r = sorted_by_pnl["R_multiple"].sum()
    total_trades = len(sorted_by_pnl)

    rows = []
    for n in [5, 10, 20]:
        top_n = sorted_by_pnl.head(n)
        top_n_pnl = top_n["pnl_dollars"].sum()
        top_n_r = top_n["R_multiple"].sum()

        pnl_pct = (top_n_pnl / total_pnl * 100.0) if total_pnl != 0 else 0.0
        r_pct = (top_n_r / total_r * 100.0) if total_r != 0 else 0.0

        rows.append(
            {
                "group": f"Top {n} trades",
                "trade_count": n,
                "total_trades": total_trades,
                "pct_of_trades": round(n / total_trades * 100.0, 2),
                "sum_pnl": round(top_n_pnl, 2),
                "total_pnl": round(total_pnl, 2),
                "pct_of_total_pnl": round(pnl_pct, 2),
                "sum_R": round(top_n_r, 4),
                "total_R": round(total_r, 4),
                "pct_of_total_R": round(r_pct, 2),
                "avg_R_top_n": round(float(top_n["R_multiple"].mean()), 4),
                "avg_R_remaining": round(
                    float(sorted_by_pnl.iloc[n:]["R_multiple"].mean()), 4
                )
                if len(sorted_by_pnl) > n
                else 0.0,
            }
        )

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 3. Duration bucket analysis
# ---------------------------------------------------------------------------
def _build_duration_buckets(lifecycle: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for label, lo, hi in DURATION_BUCKETS:
        bucket = lifecycle[
            (lifecycle["trade_duration_bars"] >= lo)
            & (lifecycle["trade_duration_bars"] <= hi)
        ]
        if bucket.empty:
            rows.append(
                {
                    "duration_bucket": label,
                    "trade_count": 0,
                    "avg_R": 0.0,
                    "total_R": 0.0,
                    "winrate": 0.0,
                    "avg_pnl": 0.0,
                    "total_pnl": 0.0,
                }
            )
            continue

        r_vals = bucket["R_multiple"].astype(float)
        pnl_vals = bucket["pnl_dollars"].astype(float)
        wins = (r_vals > 0).sum()

        rows.append(
            {
                "duration_bucket": label,
                "trade_count": int(len(bucket)),
                "avg_R": round(float(r_vals.mean()), 4),
                "total_R": round(float(r_vals.sum()), 4),
                "winrate": round(wins / len(bucket) * 100.0, 2),
                "avg_pnl": round(float(pnl_vals.mean()), 2),
                "total_pnl": round(float(pnl_vals.sum()), 2),
            }
        )

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 4. Exit reason contribution
# ---------------------------------------------------------------------------
def _build_exit_reason_contribution(lifecycle: pd.DataFrame) -> pd.DataFrame:
    reasons = ["ATR_TRAIL", "STOP", "EMA_EXIT", "TIME_EXIT"]
    rows = []
    for reason in reasons:
        group = lifecycle[lifecycle["exit_reason"] == reason]
        if group.empty:
            rows.append(
                {
                    "exit_reason": reason,
                    "trade_count": 0,
                    "avg_R": 0.0,
                    "total_R": 0.0,
                    "winrate": 0.0,
                    "avg_pnl": 0.0,
                    "total_pnl": 0.0,
                }
            )
            continue

        r_vals = group["R_multiple"].astype(float)
        pnl_vals = group["pnl_dollars"].astype(float)
        wins = (r_vals > 0).sum()

        rows.append(
            {
                "exit_reason": reason,
                "trade_count": int(len(group)),
                "avg_R": round(float(r_vals.mean()), 4),
                "total_R": round(float(r_vals.sum()), 4),
                "winrate": round(wins / len(group) * 100.0, 2),
                "avg_pnl": round(float(pnl_vals.mean()), 2),
                "total_pnl": round(float(pnl_vals.sum()), 2),
            }
        )

    # Catch any exit reasons not in the standard list
    other = lifecycle[~lifecycle["exit_reason"].isin(reasons)]
    if not other.empty:
        r_vals = other["R_multiple"].astype(float)
        pnl_vals = other["pnl_dollars"].astype(float)
        wins = (r_vals > 0).sum()
        rows.append(
            {
                "exit_reason": "OTHER",
                "trade_count": int(len(other)),
                "avg_R": round(float(r_vals.mean()), 4),
                "total_R": round(float(r_vals.sum()), 4),
                "winrate": round(wins / len(other) * 100.0, 2),
                "avg_pnl": round(float(pnl_vals.mean()), 2),
                "total_pnl": round(float(pnl_vals.sum()), 2),
            }
        )

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 5. Year contribution
# ---------------------------------------------------------------------------
def _build_year_contribution(lifecycle: pd.DataFrame) -> pd.DataFrame:
    years = [2021, 2022, 2023, 2024]
    rows = []
    for year in years:
        group = lifecycle[lifecycle["entry_year"] == year]
        if group.empty:
            rows.append(
                {
                    "year": year,
                    "trade_count": 0,
                    "avg_R": 0.0,
                    "total_R": 0.0,
                    "winrate": 0.0,
                    "avg_pnl": 0.0,
                    "total_pnl": 0.0,
                }
            )
            continue

        r_vals = group["R_multiple"].astype(float)
        pnl_vals = group["pnl_dollars"].astype(float)
        wins = (r_vals > 0).sum()

        rows.append(
            {
                "year": year,
                "trade_count": int(len(group)),
                "avg_R": round(float(r_vals.mean()), 4),
                "total_R": round(float(r_vals.sum()), 4),
                "winrate": round(wins / len(group) * 100.0, 2),
                "avg_pnl": round(float(pnl_vals.mean()), 2),
                "total_pnl": round(float(pnl_vals.sum()), 2),
            }
        )

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    print("=" * 70)
    print("TRADE LIFECYCLE ANALYSIS — RESEARCH ONLY")
    print("Production strategy is NOT modified.")
    print("=" * 70)

    universe = _load_walk_forward_universe()
    print(f"\nUniverse: {universe}")

    print("Loading walk-forward trades...")
    trades = _load_walk_forward_trades(universe=universe)
    if trades.empty:
        print("ERROR: No walk-forward trades found.")
        return
    print(f"  Total test-window trades: {len(trades)}")

    # --- Build lifecycle ---
    lifecycle = _build_lifecycle(trades)

    # === OUTPUT 1: trade_lifecycle_analysis.csv ===
    lifecycle_path = OUTPUT_DIR / "trade_lifecycle_analysis.csv"
    lifecycle.to_csv(lifecycle_path, index=False)
    print(f"\nOUTPUT 1: {lifecycle_path}")
    print(f"  {len(lifecycle)} trades written")

    # === OUTPUT 2: profit_concentration.csv ===
    concentration = _build_profit_concentration(lifecycle)
    concentration_path = OUTPUT_DIR / "profit_concentration.csv"
    concentration.to_csv(concentration_path, index=False)
    print(f"\nOUTPUT 2: {concentration_path}")
    print(concentration.to_string(index=False))

    # === OUTPUT 3: duration_bucket_analysis.csv ===
    duration = _build_duration_buckets(lifecycle)
    duration_path = OUTPUT_DIR / "duration_bucket_analysis.csv"
    duration.to_csv(duration_path, index=False)
    print(f"\nOUTPUT 3: {duration_path}")
    print(duration.to_string(index=False))

    # === OUTPUT 4: exit_reason_contribution.csv ===
    exit_reasons = _build_exit_reason_contribution(lifecycle)
    exit_path = OUTPUT_DIR / "exit_reason_contribution.csv"
    exit_reasons.to_csv(exit_path, index=False)
    print(f"\nOUTPUT 4: {exit_path}")
    print(exit_reasons.to_string(index=False))

    # === BONUS: year_contribution (embedded in lifecycle analysis) ===
    year_contrib = _build_year_contribution(lifecycle)
    year_path = OUTPUT_DIR / "year_contribution.csv"
    year_contrib.to_csv(year_path, index=False)
    print(f"\nBONUS OUTPUT: {year_path}")
    print(year_contrib.to_string(index=False))

    # -------------------------------------------------------------------
    # Verdict
    # -------------------------------------------------------------------
    print(f"\n{'=' * 70}")
    print("RESEARCH CONCLUSIONS")
    print("=" * 70)

    total_pnl = lifecycle["pnl_dollars"].sum()
    total_r = lifecycle["R_multiple"].sum()
    total_trades = len(lifecycle)

    # Concentration verdict
    top5_pnl = lifecycle.nlargest(5, "pnl_dollars")["pnl_dollars"].sum()
    top10_pnl = lifecycle.nlargest(10, "pnl_dollars")["pnl_dollars"].sum()
    top5_pct = (top5_pnl / total_pnl * 100.0) if total_pnl != 0 else 0.0
    top10_pct = (top10_pnl / total_pnl * 100.0) if total_pnl != 0 else 0.0

    print(f"\n  Total trades:     {total_trades}")
    print(f"  Total PnL:        ${total_pnl:,.2f}")
    print(f"  Total R:          {total_r:.4f}R")
    print(f"  Avg R:            {total_r / total_trades:.4f}R")

    print(f"\n  PROFIT CONCENTRATION:")
    print(f"    Top 5 trades  = {top5_pct:.1f}% of total PnL")
    print(f"    Top 10 trades = {top10_pct:.1f}% of total PnL")

    if top5_pct > 80:
        print("    --> HIGHLY CONCENTRATED: Edge depends on a handful of outliers.")
        print("    --> This is FRAGILE. Missing 2-3 trades would destroy returns.")
    elif top5_pct > 50:
        print("    --> MODERATELY CONCENTRATED: Meaningful tail dependency.")
        print("    --> Strategy benefits from trend-riding but has breadth.")
    else:
        print("    --> BROADLY DISTRIBUTED: Edge is spread across many trades.")
        print("    --> This is ROBUST. Missing a few trades would not be fatal.")

    # Best duration bucket
    if not duration.empty:
        best_bucket = duration.loc[duration["avg_R"].idxmax()]
        worst_bucket = duration.loc[duration["avg_R"].idxmin()]
        print(f"\n  DURATION SWEET SPOT:")
        print(
            f"    Best:  {best_bucket['duration_bucket']} bars "
            f"(avg_R={best_bucket['avg_R']}, {int(best_bucket['trade_count'])} trades)"
        )
        print(
            f"    Worst: {worst_bucket['duration_bucket']} bars "
            f"(avg_R={worst_bucket['avg_R']}, {int(worst_bucket['trade_count'])} trades)"
        )

    # Best exit reason
    if not exit_reasons.empty:
        active_exits = exit_reasons[exit_reasons["trade_count"] > 0]
        if not active_exits.empty:
            best_exit = active_exits.loc[active_exits["avg_R"].idxmax()]
            worst_exit = active_exits.loc[active_exits["avg_R"].idxmin()]
            print(f"\n  EXIT REASON EDGE:")
            print(
                f"    Best:  {best_exit['exit_reason']} "
                f"(avg_R={best_exit['avg_R']}, {int(best_exit['trade_count'])} trades)"
            )
            print(
                f"    Worst: {worst_exit['exit_reason']} "
                f"(avg_R={worst_exit['avg_R']}, {int(worst_exit['trade_count'])} trades)"
            )

    # Year analysis
    if not year_contrib.empty:
        active_years = year_contrib[year_contrib["trade_count"] > 0]
        if not active_years.empty:
            best_year = active_years.loc[active_years["avg_R"].idxmax()]
            worst_year = active_years.loc[active_years["avg_R"].idxmin()]
            print(f"\n  YEARLY PERFORMANCE:")
            for _, yr in active_years.iterrows():
                marker = " <-- BEST" if yr["year"] == best_year["year"] else (
                    " <-- WORST" if yr["year"] == worst_year["year"] else ""
                )
                print(
                    f"    {int(yr['year'])}: "
                    f"{int(yr['trade_count'])} trades, "
                    f"avg_R={yr['avg_R']}, "
                    f"winrate={yr['winrate']}%, "
                    f"total_pnl=${yr['total_pnl']:,.2f}"
                    f"{marker}"
                )

    print(f"\n{'=' * 70}")
    print("REMINDER: This is research only. No production code was modified.")
    print("=" * 70)


if __name__ == "__main__":
    main()
