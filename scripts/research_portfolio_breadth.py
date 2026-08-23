"""Portfolio Breadth Research — Research Only.

Tests the effect of varying max_positions on leadership_expansion_v1
performance. Everything else remains identical: same universe, same entries,
same exits, same risk model.

Configurations tested:
    max_positions = 1, 3, 5, 10

Outputs:
    output/portfolio_breadth_research.csv  — per-window per-config metrics
    output/portfolio_breadth_summary.csv   — aggregated comparison

Production strategy is NEVER modified.
"""

from __future__ import annotations

import math
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config.settings import BacktestConfig  # noqa: E402
from data.yahoo_data import MarketDataRequest, YahooFinanceDataSource  # noqa: E402
from engine.backtest_engine import BacktestEngine  # noqa: E402
from main import build_strategy_params  # noqa: E402
from strategies.leadership_expansion_v1 import LeadershipExpansionV1Strategy  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
OUTPUT_DIR = ROOT / "output"
TIMEFRAME = "1d"
BENCHMARK = "SPY"
DATA_START = "2018-01-01"
DATA_END = "2025-01-01"
FULL_HISTORY_CUTOFF = pd.Timestamp("2018-02-01")
INITIAL_CAPITAL = 10_000.0

WINDOWS = [
    ("W1_2021", "2018-01-01", "2021-01-01", "2022-01-01"),
    ("W2_2022", "2018-01-01", "2022-01-01", "2023-01-01"),
    ("W3_2023", "2018-01-01", "2023-01-01", "2024-01-01"),
    ("W4_2024", "2018-01-01", "2024-01-01", "2025-01-01"),
]

MAX_POSITIONS_CONFIGS = [1, 3, 5, 10]


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
                    ticker=ticker, start=DATA_START, end=DATA_END, timeframe=TIMEFRAME
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


# ---------------------------------------------------------------------------
# Metrics helpers
# ---------------------------------------------------------------------------
def _summarize_trades(trades: pd.DataFrame) -> dict[str, float | int]:
    if trades.empty:
        return {
            "trade_count": 0,
            "avg_R": 0.0,
            "expectancy": 0.0,
            "profit_factor": 0.0,
            "net_pnl": 0.0,
            "winrate": 0.0,
            "max_drawdown": 0.0,
        }

    pnl = pd.to_numeric(trades["pnl_dollars"], errors="coerce").fillna(0.0)
    r_values = pd.to_numeric(trades["R_multiple"], errors="coerce").dropna()
    wins = pnl[pnl > 0]
    losses = pnl[pnl < 0]
    win_rate_dec = float((pnl > 0).mean())
    loss_rate_dec = float((pnl < 0).mean())
    avg_win = float(wins.mean()) if not wins.empty else 0.0
    avg_loss_abs = float(abs(losses.mean())) if not losses.empty else 0.0
    gross_profit = float(wins.sum()) if not wins.empty else 0.0
    gross_loss = float(abs(losses.sum())) if not losses.empty else 0.0
    profit_factor = (
        gross_profit / gross_loss
        if gross_loss > 0
        else (math.inf if gross_profit > 0 else 0.0)
    )

    return {
        "trade_count": int(len(trades)),
        "avg_R": round(float(r_values.mean()), 4) if not r_values.empty else 0.0,
        "expectancy": round(
            (win_rate_dec * avg_win) - (loss_rate_dec * avg_loss_abs), 4
        ),
        "profit_factor": round(profit_factor, 4)
        if math.isfinite(profit_factor)
        else float("inf"),
        "net_pnl": round(float(pnl.sum()), 2),
        "winrate": round(win_rate_dec * 100.0, 2),
        "max_drawdown": round(_trade_level_max_drawdown(pnl), 2),
    }


def _trade_level_max_drawdown(pnl: pd.Series) -> float:
    cumulative = pnl.cumsum()
    running_peak = cumulative.cummax()
    drawdown = cumulative - running_peak
    return float(drawdown.min()) if not drawdown.empty else 0.0


def _compute_cagr_and_sharpe(
    equity_curve: pd.Series, initial_capital: float
) -> tuple[float | None, float | None]:
    """Compute CAGR and annualized Sharpe from daily equity curve."""
    if equity_curve is None or len(equity_curve) < 2:
        return None, None

    final_value = float(equity_curve.iloc[-1])
    n_days = (equity_curve.index[-1] - equity_curve.index[0]).days
    if n_days <= 0 or initial_capital <= 0:
        return None, None

    years = n_days / 365.25
    cagr = ((final_value / initial_capital) ** (1.0 / years) - 1.0) * 100.0 if years > 0 else None

    daily_returns = equity_curve.pct_change().dropna()
    if len(daily_returns) < 2 or float(daily_returns.std()) == 0:
        return cagr, None

    sharpe = float(daily_returns.mean() / daily_returns.std()) * (252 ** 0.5)
    return cagr, sharpe


# ---------------------------------------------------------------------------
# Run single configuration across all windows
# ---------------------------------------------------------------------------
def _run_configuration(
    max_pos: int,
    universe: list[str],
    market_cache: dict[str, pd.DataFrame],
    benchmark_data: pd.DataFrame,
) -> tuple[list[dict], dict]:
    """Run walk-forward backtest with a specific max_positions value.

    Returns (per_window_rows, aggregate_row).
    """
    per_window_rows: list[dict] = []
    all_test_trades: list[pd.DataFrame] = []

    for window_name, train_start, test_start, test_end in WINDOWS:
        window_trades: list[pd.DataFrame] = []

        for ticker in universe:
            if ticker not in market_cache:
                continue

            market_data = market_cache[ticker].loc[
                (market_cache[ticker].index >= pd.Timestamp(train_start))
                & (market_cache[ticker].index < pd.Timestamp(test_end))
            ]
            benchmark_slice = benchmark_data.loc[
                (benchmark_data.index >= pd.Timestamp(train_start))
                & (benchmark_data.index < pd.Timestamp(test_end))
            ]
            if market_data.empty or benchmark_slice.empty:
                continue

            config = BacktestConfig(
                ticker=ticker,
                start_date=train_start,
                end_date=test_end,
                timeframe=TIMEFRAME,
                strategy_name="leadership_expansion_v1",
                max_positions=max_pos,
                output_dir=str(OUTPUT_DIR / "_breadth_tmp"),
                plot=False,
            )
            config.skip_relative_strength_filter = ticker.upper() == BENCHMARK

            run_dir = OUTPUT_DIR / "_breadth_tmp"
            run_dir.mkdir(exist_ok=True)

            engine = BacktestEngine(
                initial_capital=config.initial_capital,
                commission=config.commission,
                slippage_perc=config.slippage,
                output_dir=run_dir,
            )

            try:
                result = engine.run(
                    dataframe=market_data,
                    strategy_class=LeadershipExpansionV1Strategy,
                    strategy_params=build_strategy_params(config),
                    extra_dataframes=[benchmark_slice],
                    plot_results=False,
                    base_timeframe=TIMEFRAME,
                    resample_rules=[],
                )
            except Exception as exc:
                print(f"    Skipped {ticker} {window_name}: {exc}")
                continue

            trades_path = run_dir / "trades.csv"
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
            test_trades["ticker"] = ticker
            window_trades.append(test_trades)

        combined = (
            pd.concat(window_trades, ignore_index=True)
            if window_trades
            else pd.DataFrame()
        )
        metrics = _summarize_trades(combined)
        per_window_rows.append(
            {
                "max_positions": max_pos,
                "window": window_name,
                **metrics,
            }
        )
        if not combined.empty:
            all_test_trades.append(combined)

    # Aggregate across all windows
    all_trades = (
        pd.concat(all_test_trades, ignore_index=True)
        if all_test_trades
        else pd.DataFrame()
    )
    aggregate = _summarize_trades(all_trades)

    aggregate_row = {
        "max_positions": max_pos,
        **aggregate,
    }

    return per_window_rows, aggregate_row


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    print("=" * 70)
    print("PORTFOLIO BREADTH RESEARCH — RESEARCH ONLY")
    print("Same universe, entries, exits, risk model.")
    print("Only max_positions varies.")
    print("Production strategy is NOT modified.")
    print("=" * 70)

    data_source = YahooFinanceDataSource()
    universe = _load_walk_forward_universe()
    print(f"\nUniverse: {universe}")

    print("Loading market data...")
    benchmark_data = _fetch_with_retry(data_source=data_source, ticker=BENCHMARK)
    market_cache: dict[str, pd.DataFrame] = {BENCHMARK: benchmark_data}

    validated_universe: list[str] = []
    for ticker in universe:
        try:
            md = (
                benchmark_data
                if ticker == BENCHMARK
                else _fetch_with_retry(data_source=data_source, ticker=ticker)
            )
        except Exception:
            print(f"  SKIP {ticker}: data fetch failed")
            continue
        if md.index.min() <= FULL_HISTORY_CUTOFF:
            market_cache[ticker] = md
            validated_universe.append(ticker)
            print(f"  {ticker}: {len(md)} bars loaded")
        else:
            print(f"  SKIP {ticker}: insufficient history")

    print(f"\nValidated universe: {validated_universe} ({len(validated_universe)} tickers)")

    # -------------------------------------------------------------------
    # Run each max_positions configuration
    # -------------------------------------------------------------------
    all_window_rows: list[dict] = []
    summary_rows: list[dict] = []

    for max_pos in MAX_POSITIONS_CONFIGS:
        print(f"\n{'=' * 50}")
        print(f"  RUNNING: max_positions = {max_pos}")
        print(f"{'=' * 50}")

        per_window, aggregate = _run_configuration(
            max_pos=max_pos,
            universe=validated_universe,
            market_cache=market_cache,
            benchmark_data=benchmark_data,
        )
        all_window_rows.extend(per_window)
        summary_rows.append(aggregate)

        print(f"  Result: {aggregate['trade_count']} trades, "
              f"avg_R={aggregate['avg_R']}, "
              f"net_pnl=${aggregate['net_pnl']}, "
              f"max_dd={aggregate['max_drawdown']}")

    # -------------------------------------------------------------------
    # OUTPUT 1: portfolio_breadth_research.csv (per-window detail)
    # -------------------------------------------------------------------
    col_order = [
        "max_positions", "window", "trade_count", "avg_R", "expectancy",
        "profit_factor", "winrate", "net_pnl", "max_drawdown",
    ]
    research_df = pd.DataFrame(all_window_rows)[col_order]
    research_path = OUTPUT_DIR / "portfolio_breadth_research.csv"
    research_df.to_csv(research_path, index=False)
    print(f"\nOUTPUT 1: {research_path}")
    print(research_df.to_string(index=False))

    # -------------------------------------------------------------------
    # OUTPUT 2: portfolio_breadth_summary.csv (aggregate comparison)
    # -------------------------------------------------------------------
    summary_cols = [
        "max_positions", "trade_count", "avg_R", "expectancy",
        "profit_factor", "winrate", "net_pnl", "max_drawdown",
    ]
    summary_df = pd.DataFrame(summary_rows)[summary_cols]
    summary_path = OUTPUT_DIR / "portfolio_breadth_summary.csv"
    summary_df.to_csv(summary_path, index=False)
    print(f"\nOUTPUT 2: {summary_path}")
    print(summary_df.to_string(index=False))

    # -------------------------------------------------------------------
    # Verdict
    # -------------------------------------------------------------------
    print(f"\n{'=' * 70}")
    print("RESEARCH CONCLUSIONS")
    print("=" * 70)

    if not summary_df.empty:
        best_pnl = summary_df.loc[summary_df["net_pnl"].idxmax()]
        best_avgr = summary_df.loc[summary_df["avg_R"].idxmax()]
        best_pf = summary_df.loc[
            summary_df["profit_factor"]
            .replace([float("inf")], 0)
            .idxmax()
        ]

        print("\n  COMPARISON TABLE:")
        for _, row in summary_df.iterrows():
            mp = int(row["max_positions"])
            print(
                f"    max_positions={mp:>2}: "
                f"{int(row['trade_count']):>4} trades, "
                f"avg_R={row['avg_R']:>7}, "
                f"PF={row['profit_factor']:>7}, "
                f"winrate={row['winrate']:>6}%, "
                f"net_pnl=${row['net_pnl']:>10}, "
                f"max_dd=${row['max_drawdown']:>10}"
            )

        print(f"\n  BEST NET PNL:        max_positions={int(best_pnl['max_positions'])} (${best_pnl['net_pnl']:,.2f})")
        print(f"  BEST AVG R:          max_positions={int(best_avgr['max_positions'])} ({best_avgr['avg_R']})")
        print(f"  BEST PROFIT FACTOR:  max_positions={int(best_pf['max_positions'])} ({best_pf['profit_factor']})")

        # Assess concentration vs diversification
        sorted_by_pnl = summary_df.sort_values("net_pnl", ascending=False)
        top_config = sorted_by_pnl.iloc[0]
        if int(top_config["max_positions"]) <= 3:
            print("\n  --> CONCENTRATION WINS: Fewer positions produce better results.")
            print("  --> Capital is diluted by holding too many simultaneous positions.")
        elif int(top_config["max_positions"]) >= 5:
            print("\n  --> DIVERSIFICATION WINS: More positions capture more of the edge.")
            print("  --> The strategy benefits from breadth without diluting quality.")
        else:
            print("\n  --> MODERATE BREADTH OPTIMAL: max_positions=3 balances concentration and diversification.")

    # Cleanup temp directory
    tmp_dir = OUTPUT_DIR / "_breadth_tmp"
    if tmp_dir.exists():
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)

    print(f"\n{'=' * 70}")
    print("REMINDER: This is research only. No production code was modified.")
    print("=" * 70)


if __name__ == "__main__":
    main()
