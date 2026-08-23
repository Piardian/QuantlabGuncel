"""Portfolio Stability Analysis — Research Only.

Analyzes the out-of-sample portfolio equity curve of leadership_expansion_v1
under the selected configuration (max_positions = 3, 1% risk per trade, default costs)
across walk-forward windows.

Outputs:
    output/portfolio_stability_analysis.csv  — monthly/quarterly/yearly returns & distributions
    output/portfolio_recovery_analysis.csv   — drawdown and recovery period details
    output/portfolio_quality_metrics.csv     — UI, MAR, Calmar, Gain-to-Pain, CAGR, Sharpe

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
MAX_POSITIONS = 3
INITIAL_CAPITAL = 10_000.0

WINDOWS = [
    ("W1_2021", "2018-01-01", "2021-01-01", "2022-01-01"),
    ("W2_2022", "2018-01-01", "2022-01-01", "2023-01-01"),
    ("W3_2023", "2018-01-01", "2023-01-01", "2024-01-01"),
    ("W4_2024", "2018-01-01", "2024-01-01", "2025-01-01"),
]


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
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    print("=" * 70)
    print("PORTFOLIO STABILITY ANALYSIS — RESEARCH ONLY")
    print("leadership_expansion_v1, max_positions = 3")
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
    # Run backtests for each window and collect out-of-sample daily returns
    # -------------------------------------------------------------------
    window_returns_list: list[pd.Series] = []

    for window_name, train_start, test_start, test_end in WINDOWS:
        print(f"\nRunning {window_name} out-of-sample...")
        window_equity_df = pd.DataFrame()

        for ticker in validated_universe:
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
                max_positions=MAX_POSITIONS,
                output_dir=str(OUTPUT_DIR / "_stability_tmp"),
                plot=False,
            )
            config.skip_relative_strength_filter = ticker.upper() == BENCHMARK

            run_dir = OUTPUT_DIR / "_stability_tmp"
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
                eq = result.equity_curve
                # Slice to out-of-sample test period
                eq_test = eq.loc[
                    (eq.index >= pd.Timestamp(test_start))
                    & (eq.index < pd.Timestamp(test_end))
                ]
                if not eq_test.empty:
                    window_equity_df[ticker] = eq_test
            except Exception as exc:
                print(f"    Skipped {ticker} {window_name}: {exc}")
                continue

        if not window_equity_df.empty:
            # Sum the equity of all tickers to get the combined window equity curve
            # Forward fill to handle any alignment gaps
            combined_window_equity = window_equity_df.ffill().sum(axis=1)
            # Calculate daily percentage returns
            window_returns = combined_window_equity.pct_change().fillna(0.0)
            window_returns_list.append(window_returns)

    # Cleanup temp directory
    tmp_dir = OUTPUT_DIR / "_stability_tmp"
    if tmp_dir.exists():
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)

    if not window_returns_list:
        print("\nError: No returns data collected.")
        return

    # Concatenate daily returns across all windows chronologically
    portfolio_daily_returns = pd.concat(window_returns_list).sort_index()
    # Remove duplicate index entries if any (keep last)
    portfolio_daily_returns = portfolio_daily_returns[~portfolio_daily_returns.index.duplicated(keep="last")]

    # Construct continuous equity curve
    portfolio_equity = (1.0 + portfolio_daily_returns).cumprod() * INITIAL_CAPITAL
    portfolio_equity.name = "equity"

    # Save daily equity for reference
    daily_path = OUTPUT_DIR / "portfolio_daily_equity.csv"
    pd.DataFrame({
        "returns": portfolio_daily_returns,
        "equity": portfolio_equity
    }).to_csv(daily_path)
    print(f"\nContinuous daily equity curve saved to: {daily_path}")

    # -------------------------------------------------------------------
    # Calculate returns over monthly, quarterly, yearly intervals
    # -------------------------------------------------------------------
    # Prep helper series with initial capital at start for return calculation
    start_date = portfolio_equity.index[0] - pd.Timedelta(days=1)
    base_series = pd.Series([INITIAL_CAPITAL], index=[start_date])
    full_equity = pd.concat([base_series, portfolio_equity])

    monthly_returns = full_equity.resample("ME").last().pct_change().dropna()
    quarterly_returns = full_equity.resample("QE").last().pct_change().dropna()
    yearly_returns = full_equity.resample("YE").last().pct_change().dropna()

    # Worst & Best Metrics
    worst_month = monthly_returns.min()
    best_month = monthly_returns.max()
    worst_quarter = quarterly_returns.min()
    best_quarter = quarterly_returns.max()
    worst_year = yearly_returns.min()
    best_year = yearly_returns.max()

    # Distribution Metrics
    pos_months_pct = (monthly_returns > 0).mean() * 100.0
    neg_months_pct = (monthly_returns < 0).mean() * 100.0
    pos_quarters_pct = (quarterly_returns > 0).mean() * 100.0
    neg_quarters_pct = (quarterly_returns < 0).mean() * 100.0

    # -------------------------------------------------------------------
    # Recovery Analysis
    # -------------------------------------------------------------------
    running_peak = portfolio_equity.cummax()
    drawdown = (portfolio_equity - running_peak) / running_peak
    max_dd = drawdown.min()
    avg_dd = drawdown[drawdown < 0].mean() if not drawdown[drawdown < 0].empty else 0.0

    # Parse drawdown recovery periods
    is_in_dd = drawdown < 0
    dd_periods: list[dict] = []
    start_date_dd = None
    peak_dd_val = 0.0

    for date, val in is_in_dd.items():
        if val:
            if start_date_dd is None:
                start_date_dd = date
                peak_dd_val = drawdown.loc[date]
            else:
                peak_dd_val = min(peak_dd_val, drawdown.loc[date])
        else:
            if start_date_dd is not None:
                end_date_dd = date
                duration = (end_date_dd - start_date_dd).days
                dd_periods.append({
                    "start_date": start_date_dd,
                    "end_date": end_date_dd,
                    "duration_days": duration,
                    "peak_drawdown": round(peak_dd_val * 100, 2)
                })
                start_date_dd = None
                peak_dd_val = 0.0

    # If the backtest ends while still in drawdown
    if start_date_dd is not None:
        end_date_dd = drawdown.index[-1]
        duration = (end_date_dd - start_date_dd).days
        dd_periods.append({
            "start_date": start_date_dd,
            "end_date": end_date_dd,
            "duration_days": duration,
            "peak_drawdown": round(peak_dd_val * 100, 2)
        })

    dd_df = pd.DataFrame(dd_periods)
    if not dd_df.empty:
        longest_recovery = int(dd_df["duration_days"].max())
        avg_recovery = round(float(dd_df["duration_days"].mean()), 2)
    else:
        longest_recovery = 0
        avg_recovery = 0.0

    # -------------------------------------------------------------------
    # Portfolio Quality
    # -------------------------------------------------------------------
    # CAGR
    n_days = (portfolio_equity.index[-1] - portfolio_equity.index[0]).days
    years = n_days / 365.25
    cagr = ((portfolio_equity.iloc[-1] / INITIAL_CAPITAL) ** (1.0 / years) - 1.0) if years > 0 else 0.0

    # Sharpe (annualized)
    daily_std = portfolio_daily_returns.std()
    sharpe = (portfolio_daily_returns.mean() / daily_std * math.sqrt(252)) if daily_std > 0 else 0.0

    # Ulcer Index
    ulcer_index = math.sqrt((drawdown * 100).pow(2).mean())

    # MAR & Calmar
    mar_ratio = cagr / abs(max_dd) if max_dd != 0 else 0.0
    calmar_ratio = mar_ratio  # equivalent over the full period

    # Gain-to-Pain Ratio (Schwager)
    neg_month_sum = abs(monthly_returns[monthly_returns < 0].sum())
    gpr = monthly_returns.sum() / neg_month_sum if neg_month_sum > 0 else float("inf")

    # -------------------------------------------------------------------
    # Save Outputs
    # -------------------------------------------------------------------
    # 1. portfolio_stability_analysis.csv
    stability_summary = [
        {"metric": "Worst Month Return", "value": f"{worst_month * 100:.2f}%"},
        {"metric": "Best Month Return", "value": f"{best_month * 100:.2f}%"},
        {"metric": "Worst Quarter Return", "value": f"{worst_quarter * 100:.2f}%"},
        {"metric": "Best Quarter Return", "value": f"{best_quarter * 100:.2f}%"},
        {"metric": "Worst Year Return", "value": f"{worst_year * 100:.2f}%"},
        {"metric": "Best Year Return", "value": f"{best_year * 100:.2f}%"},
        {"metric": "Positive Months %", "value": f"{pos_months_pct:.2f}%"},
        {"metric": "Negative Months %", "value": f"{neg_months_pct:.2f}%"},
        {"metric": "Positive Quarters %", "value": f"{pos_quarters_pct:.2f}%"},
        {"metric": "Negative Quarters %", "value": f"{neg_quarters_pct:.2f}%"},
    ]
    stability_df = pd.DataFrame(stability_summary)
    stability_path = OUTPUT_DIR / "portfolio_stability_analysis.csv"
    stability_df.to_csv(stability_path, index=False)
    print(f"OUTPUT 1: {stability_path}")
    print(stability_df.to_string(index=False))

    # Also save monthly returns details for the user
    monthly_details = pd.DataFrame({
        "Month": monthly_returns.index.strftime("%Y-%m"),
        "Return": monthly_returns.values * 100
    })
    monthly_details_path = OUTPUT_DIR / "portfolio_monthly_returns.csv"
    monthly_details.to_csv(monthly_details_path, index=False)

    # 2. portfolio_recovery_analysis.csv
    recovery_summary = [
        {"metric": "Maximum Drawdown", "value": f"{max_dd * 100:.2f}%"},
        {"metric": "Average Drawdown (when in DD)", "value": f"{avg_dd * 100:.2f}%"},
        {"metric": "Longest Recovery Period (days)", "value": str(longest_recovery)},
        {"metric": "Average Recovery Period (days)", "value": str(avg_recovery)},
    ]
    recovery_df = pd.DataFrame(recovery_summary)
    recovery_path = OUTPUT_DIR / "portfolio_recovery_analysis.csv"
    recovery_df.to_csv(recovery_path, index=False)
    print(f"\nOUTPUT 2: {recovery_path}")
    print(recovery_df.to_string(index=False))

    # Save detailed drawdown periods
    dd_df.to_csv(OUTPUT_DIR / "portfolio_drawdown_periods.csv", index=False)

    # 3. portfolio_quality_metrics.csv
    quality_summary = [
        {"metric": "CAGR", "value": f"{cagr * 100:.2f}%"},
        {"metric": "Annualized Sharpe Ratio", "value": f"{sharpe:.4f}"},
        {"metric": "Ulcer Index", "value": f"{ulcer_index:.4f}"},
        {"metric": "MAR Ratio", "value": f"{mar_ratio:.4f}"},
        {"metric": "Calmar Ratio", "value": f"{calmar_ratio:.4f}"},
        {"metric": "Gain-to-Pain Ratio", "value": f"{gpr:.4f}"},
    ]
    quality_df = pd.DataFrame(quality_summary)
    quality_path = OUTPUT_DIR / "portfolio_quality_metrics.csv"
    quality_df.to_csv(quality_path, index=False)
    print(f"\nOUTPUT 3: {quality_path}")
    print(quality_df.to_string(index=False))

    # -------------------------------------------------------------------
    # Verdict analysis
    # -------------------------------------------------------------------
    print(f"\n{'=' * 70}")
    print("PORTFOLIO STABILITY VERDICT")
    print("=" * 70)
    print(f"  CAGR: {cagr * 100:.2f}%  |  Max DD: {max_dd * 100:.2f}%")
    print(f"  MAR Ratio: {mar_ratio:.4f}  |  Sharpe: {sharpe:.4f}")
    print(f"  Ulcer Index: {ulcer_index:.4f}  |  Gain-to-Pain: {gpr:.4f}")
    print(f"  Longest Recovery: {longest_recovery} days")
    print(f"  Positive Months: {pos_months_pct:.1f}% ({len(monthly_returns[monthly_returns > 0])}/{len(monthly_returns)})")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
