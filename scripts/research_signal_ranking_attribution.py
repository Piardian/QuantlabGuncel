from __future__ import annotations

from pathlib import Path
import math
import sys
import time

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from data.yahoo_data import MarketDataRequest, YahooFinanceDataSource

OUTPUT_DIR = ROOT / "output"
MISSED_SIGNAL_ANALYSIS_PATH = OUTPUT_DIR / "missed_signal_analysis.csv"
FORWARD_SIGNALS_PATH = OUTPUT_DIR / "forward_simulation_readiness.csv"
MAX_POSITIONS = 3
START = "2018-01-01"
END = "2025-01-01"
TIMEFRAME = "1d"
EMA_PERIOD = 200


def main() -> None:
    if not MISSED_SIGNAL_ANALYSIS_PATH.exists():
        raise RuntimeError("Missing missed_signal_analysis.csv. Run missed signal attribution first.")
    if not FORWARD_SIGNALS_PATH.exists():
        raise RuntimeError("Missing forward_simulation_readiness.csv. Run forward simulation readiness first.")

    signals = pd.read_csv(MISSED_SIGNAL_ANALYSIS_PATH, parse_dates=["signal_date", "entry_date"])
    forward = pd.read_csv(FORWARD_SIGNALS_PATH, parse_dates=["signal_date", "entry_date"])
    signals = _attach_capacity_context(signals=signals, forward=forward)
    signals = _attach_distance_above_ema200(signals)
    conflict_days = signals[signals["signals_generated"] > signals["available_slots"]]["signal_date"].drop_duplicates()
    conflicts = signals[signals["signal_date"].isin(conflict_days)].copy()

    research_rows = []
    conflict_rows = []
    ranking_methods = {
        "ACTUAL_EXECUTED": None,
        "RANK_RS60": "RS60",
        "RANK_ATR_PERCENT": "ATR_percent",
        "RANK_MOMENTUM": "momentum",
        "RANK_VOLATILITY": "volatility",
        "RANK_DISTANCE_ABOVE_EMA200": "distance_above_ema200",
    }

    for signal_date, day_signals in conflicts.groupby("signal_date"):
        available_slots = int(day_signals["available_slots"].iloc[0])
        selected_count = max(min(available_slots, len(day_signals)), 0)
        actual_selected = day_signals[day_signals["executed"]].copy()

        conflict_rows.append(
            {
                "signal_date": signal_date,
                "signals_generated": int(len(day_signals)),
                "available_slots": available_slots,
                "actual_executed": int(len(actual_selected)),
                "actual_net_R": float(actual_selected["R_multiple"].sum()) if not actual_selected.empty else 0.0,
                "best_possible_net_R": float(day_signals.nlargest(selected_count, "R_multiple")["R_multiple"].sum())
                if selected_count > 0
                else 0.0,
                "worst_possible_net_R": float(day_signals.nsmallest(selected_count, "R_multiple")["R_multiple"].sum())
                if selected_count > 0
                else 0.0,
                "tickers": ", ".join(day_signals["ticker"].astype(str).tolist()),
            }
        )

        for method_name, rank_column in ranking_methods.items():
            if method_name == "ACTUAL_EXECUTED":
                selected = actual_selected
            elif selected_count <= 0:
                selected = day_signals.iloc[0:0]
            else:
                selected = day_signals.sort_values(rank_column, ascending=False).head(selected_count)

            for _, signal in selected.iterrows():
                research_rows.append(
                    {
                        "signal_date": signal_date,
                        "ranking_method": method_name,
                        "ticker": signal["ticker"],
                        "R_multiple": signal["R_multiple"],
                        "RS60": signal["RS60"],
                        "ATR_percent": signal["ATR_percent"],
                        "momentum": signal["momentum"],
                        "volatility": signal["volatility"],
                        "distance_above_ema200": signal["distance_above_ema200"],
                        "was_actual_executed": bool(signal["executed"]),
                    }
                )

    research = pd.DataFrame(research_rows)
    research_path = OUTPUT_DIR / "signal_ranking_research.csv"
    research.to_csv(research_path, index=False)

    comparison = _build_method_comparison(research)
    comparison_path = OUTPUT_DIR / "ranking_method_comparison.csv"
    comparison.to_csv(comparison_path, index=False)

    conflict_analysis = pd.DataFrame(conflict_rows)
    conflict_path = OUTPUT_DIR / "conflict_day_analysis.csv"
    conflict_analysis.to_csv(conflict_path, index=False)

    print(research_path)
    print(comparison_path)
    print(conflict_path)


def _attach_capacity_context(signals: pd.DataFrame, forward: pd.DataFrame) -> pd.DataFrame:
    context = (
        forward.groupby("signal_date")
        .agg(
            signals_generated=("ticker", "size"),
            active_positions_before_day=("active_positions_before_signal", "min"),
        )
        .reset_index()
    )
    context["available_slots"] = (MAX_POSITIONS - context["active_positions_before_day"]).clip(lower=0)
    merged = signals.merge(context, on="signal_date", how="left")
    merged["signals_generated"] = merged["signals_generated"].fillna(1).astype(int)
    merged["available_slots"] = merged["available_slots"].fillna(MAX_POSITIONS).astype(int)
    return merged


def _attach_distance_above_ema200(signals: pd.DataFrame) -> pd.DataFrame:
    data_source = YahooFinanceDataSource()
    enriched = signals.copy()
    enriched["distance_above_ema200"] = 0.0

    for ticker in enriched["ticker"].dropna().astype(str).unique():
        market_data = _add_ema200(_fetch_with_retry(data_source=data_source, ticker=ticker))
        distances = {}
        for index, row in market_data.dropna(subset=["EMA200"]).iterrows():
            ema200 = float(row["EMA200"])
            distances[index.normalize()] = ((float(row["Close"]) - ema200) / ema200) if ema200 > 0 else 0.0

        ticker_mask = enriched["ticker"].astype(str) == ticker
        enriched.loc[ticker_mask, "distance_above_ema200"] = (
            enriched.loc[ticker_mask, "signal_date"].dt.normalize().map(distances).fillna(0.0)
        )

    return enriched


def _fetch_with_retry(data_source: YahooFinanceDataSource, ticker: str) -> pd.DataFrame:
    last_error: Exception | None = None
    for _ in range(3):
        try:
            return data_source.fetch(MarketDataRequest(ticker=ticker, start=START, end=END, timeframe=TIMEFRAME))
        except Exception as exc:
            last_error = exc
            time.sleep(1)
    raise RuntimeError(f"Could not fetch data for {ticker}: {last_error}") from last_error


def _add_ema200(dataframe: pd.DataFrame) -> pd.DataFrame:
    data = dataframe.copy()
    data["EMA200"] = data["Close"].ewm(span=EMA_PERIOD, adjust=False).mean()
    return data


def _build_method_comparison(research: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for method_name, group in research.groupby("ranking_method"):
        rows.append({"ranking_method": method_name, **_summarize_r(group["R_multiple"])})
    return pd.DataFrame(rows).sort_values("net_R", ascending=False)


def _summarize_r(r_values: pd.Series) -> dict[str, float | int]:
    r = pd.to_numeric(r_values, errors="coerce").dropna()
    if r.empty:
        return {
            "trade_count": 0,
            "avg_R": 0.0,
            "profit_factor": 0.0,
            "winrate": 0.0,
            "net_R": 0.0,
        }
    wins = r[r > 0]
    losses = r[r < 0]
    gross_profit = float(wins.sum()) if not wins.empty else 0.0
    gross_loss = float(abs(losses.sum())) if not losses.empty else 0.0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else (math.inf if gross_profit > 0 else 0.0)
    return {
        "trade_count": int(len(r)),
        "avg_R": float(r.mean()),
        "profit_factor": profit_factor,
        "winrate": float((r > 0).mean() * 100.0),
        "net_R": float(r.sum()),
    }


if __name__ == "__main__":
    main()
