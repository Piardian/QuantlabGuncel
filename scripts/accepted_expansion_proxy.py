"""Accepted Expansion Proxy Research.

Research-only script. NO filters, NO entry changes, NO optimization.

Goal: Find lookahead-safe proxies for accepted expansion.
Question: Which entry-bar features predict continuation?

Outputs:
    output/accepted_expansion_proxy.csv   - per-trade feature table
    output/accepted_expansion_summary.csv - winner vs loser comparison
"""

from __future__ import annotations

from pathlib import Path
import sys
import time

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from data.yahoo_data import MarketDataRequest, YahooFinanceDataSource

OUTPUT_DIR = ROOT / "output"
UNIVERSE = ["AAPL", "MSFT", "NVDA", "META", "AMZN", "GOOGL", "TSLA", "SPY", "QQQ"]
START = "2018-01-01"
END = "2024-01-01"
TIMEFRAME = "1d"
ATR_PERIOD = 14
SMA_VOLUME_PERIOD = 20


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    data_source = YahooFinanceDataSource()
    rows: list[dict[str, object]] = []

    for ticker in UNIVERSE:
        print(f"[*] Processing {ticker} ...")
        market_data = _fetch_with_retry(data_source=data_source, ticker=ticker)
        enriched = _enrich_market_data(market_data)

        trades_path = _resolve_trades_path(ticker)
        if trades_path is None:
            print(f"    SKIP: no trades.csv found for {ticker}")
            continue

        trades = pd.read_csv(trades_path, parse_dates=["entry_time", "exit_time"])
        print(f"    Found {len(trades)} trades")

        for _, trade in trades.iterrows():
            row = _build_proxy_row(ticker=ticker, trade=trade, market_data=enriched)
            if row is not None:
                rows.append(row)

    if not rows:
        print("[!] No feature rows produced. Exiting.")
        return

    features = pd.DataFrame(rows)

    # ---- Output 1: per-trade proxy features ----
    proxy_path = OUTPUT_DIR / "accepted_expansion_proxy.csv"
    features.to_csv(proxy_path, index=False)
    print(f"\n[OK] {proxy_path}  ({len(features)} rows)")

    # ---- Output 2: winner vs loser summary ----
    summary = _build_summary(features)
    summary_path = OUTPUT_DIR / "accepted_expansion_summary.csv"
    summary.to_csv(summary_path, index=False)
    print(f"[OK] {summary_path}  ({len(summary)} features compared)")

    # ---- Console quick-look ----
    _print_summary(summary)


# ---------------------------------------------------------------------------
# Data enrichment (ATR, SMA volume — all lookback-safe)
# ---------------------------------------------------------------------------


def _enrich_market_data(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()

    prev_close = data["Close"].shift(1)

    # True Range
    tr = pd.concat(
        [
            data["High"] - data["Low"],
            (data["High"] - prev_close).abs(),
            (data["Low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    data["TrueRange"] = tr

    # ATR-14 (Wilder)
    data["ATR14"] = _wilder_average(tr, ATR_PERIOD)

    # SMA-20 of volume
    data["VolSMA20"] = data["Volume"].rolling(window=SMA_VOLUME_PERIOD, min_periods=SMA_VOLUME_PERIOD).mean()

    # Previous close
    data["PrevClose"] = prev_close

    # Previous high
    data["PrevHigh"] = data["High"].shift(1)

    # Typical price as VWAP proxy
    data["TypicalPrice"] = (data["High"] + data["Low"] + data["Close"]) / 3.0

    return data


# ---------------------------------------------------------------------------
# Resolve trade logs
# ---------------------------------------------------------------------------


def _resolve_trades_path(ticker: str) -> Path | None:
    candidates = [
        OUTPUT_DIR / f"leadership_quality_FULL_SYSTEM_{ticker}" / "trades.csv",
        OUTPUT_DIR / f"leadership_expansion_v1_{ticker}" / "trades.csv",
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


# ---------------------------------------------------------------------------
# Per-trade feature extraction
# ---------------------------------------------------------------------------


def _build_proxy_row(
    ticker: str,
    trade: pd.Series,
    market_data: pd.DataFrame,
) -> dict[str, object] | None:
    """Extract all proxy features from the ENTRY BAR only. No lookahead."""

    entry_time = pd.Timestamp(trade["entry_time"]).normalize()
    dates = market_data.index.normalize()
    matching = [i for i, d in enumerate(dates) if d == entry_time]
    if not matching:
        return None

    entry_idx = matching[0]
    # Signal bar is the bar BEFORE entry (signal fires at close, entry next open)
    signal_idx = entry_idx - 1
    if signal_idx < 1:
        return None

    bar = market_data.iloc[signal_idx]

    high = float(bar["High"])
    low = float(bar["Low"])
    open_price = float(bar["Open"])
    close = float(bar["Close"])
    volume = float(bar["Volume"])
    tr = float(bar["TrueRange"])
    atr14 = float(bar["ATR14"])
    vol_sma20 = bar.get("VolSMA20", np.nan)
    prev_close = bar.get("PrevClose", np.nan)
    prev_high = bar.get("PrevHigh", np.nan)
    typical_price = bar.get("TypicalPrice", np.nan)

    # Safety checks
    if high <= low or tr <= 0 or atr14 <= 0:
        return None
    if pd.isna(vol_sma20) or vol_sma20 <= 0:
        return None

    # ---- Trade outcome (target variable — from realized trade) ----
    trade_r = float(trade["R_multiple"])
    if trade_r > 0:
        outcome = "winner"
    elif trade_r < 0:
        outcome = "loser"
    else:
        outcome = "flat"

    # ==================================================================
    # EXISTING features (carried forward from research_expansion_features)
    # ==================================================================
    close_location = (close - low) / (high - low)
    body_pct = abs(close - open_price) / tr
    upper_wick_pct = (high - max(open_price, close)) / tr
    lower_wick_pct = (min(open_price, close) - low) / tr
    gap_pct = (open_price - float(prev_close)) / float(prev_close) if not pd.isna(prev_close) and float(prev_close) > 0 else np.nan
    close_vs_prev_high = 1.0 if not pd.isna(prev_high) and close > float(prev_high) else 0.0
    range_expansion_ratio = tr / atr14

    # ==================================================================
    # NEW PROXY FEATURES (1–7)
    # ==================================================================

    # 1. volume_ratio — Was expansion sponsored by volume?
    volume_ratio = volume / float(vol_sma20)

    # 2. close_distance_from_high — Did expansion finish weak?
    #    (high - close) / true_range → 0 = closed at high, 1 = closed at low
    close_distance_from_high = (high - close) / tr

    # 3. close_distance_from_low — Acceptance strength
    #    (close - low) / true_range → 1 = closed at high, 0 = closed at low
    close_distance_from_low = (close - low) / tr

    # 4. expansion_efficiency — Directional expansion quality
    #    abs(close - open) / ATR14 → large body relative to normal range
    expansion_efficiency = abs(close - open_price) / atr14

    # 5. gap_fill_pct — Did session fade the gap?
    #    If gap up: gap_fill = how much of the gap was retraced intraday
    #    If gap down or no gap: NaN (not applicable for long expansion)
    gap_fill_pct = np.nan
    if not pd.isna(prev_close):
        pc = float(prev_close)
        if pc > 0:
            gap_size = open_price - pc
            if gap_size > 0:
                # Gap up: how much did price retrace INTO the gap?
                intraday_retrace = open_price - low
                gap_fill_pct = min(intraday_retrace / gap_size, 1.0) if gap_size > 0 else 0.0
            elif gap_size < 0:
                # Gap down on a long expansion — unusual, mark as full fill
                gap_fill_pct = 1.0
            else:
                gap_fill_pct = 0.0  # No gap

    # 6. close_vs_vwap_proxy — Daily VWAP approximation
    #    TypicalPrice = (H+L+C)/3 as VWAP proxy
    #    Ratio: close / typical_price
    #    > 1 means close above VWAP proxy (bullish acceptance)
    close_vs_vwap_proxy = close / float(typical_price) if not pd.isna(typical_price) and float(typical_price) > 0 else np.nan

    # 7. intraday_acceptance_score — Composite research metric
    #    close_location * body_pct * (1 - upper_wick_pct)
    #    High score = closed near high, big body, small upper wick → strong acceptance
    intraday_acceptance_score = close_location * body_pct * (1.0 - upper_wick_pct)

    return {
        "ticker": ticker,
        "entry_time": trade["entry_time"],
        "signal_time": market_data.index[signal_idx],
        "trade_outcome": outcome,
        "trade_R": trade_r,
        "exit_reason": trade.get("exit_reason", "UNKNOWN"),
        # --- Existing features ---
        "close_location": round(close_location, 6),
        "body_pct": round(body_pct, 6),
        "upper_wick_pct": round(upper_wick_pct, 6),
        "lower_wick_pct": round(lower_wick_pct, 6),
        "gap_pct": round(gap_pct, 6) if not pd.isna(gap_pct) else np.nan,
        "close_vs_prev_high": close_vs_prev_high,
        "range_expansion_ratio": round(range_expansion_ratio, 6),
        # --- NEW PROXY FEATURES ---
        "volume_ratio": round(volume_ratio, 6),
        "close_distance_from_high": round(close_distance_from_high, 6),
        "close_distance_from_low": round(close_distance_from_low, 6),
        "expansion_efficiency": round(expansion_efficiency, 6),
        "gap_fill_pct": round(gap_fill_pct, 6) if not pd.isna(gap_fill_pct) else np.nan,
        "close_vs_vwap_proxy": round(close_vs_vwap_proxy, 6) if not pd.isna(close_vs_vwap_proxy) else np.nan,
        "intraday_acceptance_score": round(intraday_acceptance_score, 6),
        # --- Raw signal bar data (for manual inspection) ---
        "signal_open": round(open_price, 4),
        "signal_high": round(high, 4),
        "signal_low": round(low, 4),
        "signal_close": round(close, 4),
        "signal_volume": int(volume),
        "signal_tr": round(tr, 4),
        "signal_atr14": round(atr14, 4),
    }


# ---------------------------------------------------------------------------
# Summary: winner vs loser comparison
# ---------------------------------------------------------------------------

PROXY_FEATURES = [
    # Existing
    "close_location",
    "body_pct",
    "upper_wick_pct",
    "lower_wick_pct",
    "gap_pct",
    "close_vs_prev_high",
    "range_expansion_ratio",
    # NEW proxies
    "volume_ratio",
    "close_distance_from_high",
    "close_distance_from_low",
    "expansion_efficiency",
    "gap_fill_pct",
    "close_vs_vwap_proxy",
    "intraday_acceptance_score",
]


def _build_summary(features: pd.DataFrame) -> pd.DataFrame:
    winners = features[features["trade_outcome"] == "winner"]
    losers = features[features["trade_outcome"] == "loser"]

    rows = []
    for feat in PROXY_FEATURES:
        if feat not in features.columns:
            continue

        w_vals = winners[feat].dropna()
        l_vals = losers[feat].dropna()

        w_mean = float(w_vals.mean()) if len(w_vals) > 0 else np.nan
        l_mean = float(l_vals.mean()) if len(l_vals) > 0 else np.nan
        diff = w_mean - l_mean if not (pd.isna(w_mean) or pd.isna(l_mean)) else np.nan

        w_median = float(w_vals.median()) if len(w_vals) > 0 else np.nan
        l_median = float(l_vals.median()) if len(l_vals) > 0 else np.nan

        w_std = float(w_vals.std()) if len(w_vals) > 1 else np.nan
        l_std = float(l_vals.std()) if len(l_vals) > 1 else np.nan

        # Effect size (Cohen's d) — practical significance
        pooled_std = np.nan
        cohens_d = np.nan
        if not (pd.isna(w_std) or pd.isna(l_std)):
            n_w, n_l = len(w_vals), len(l_vals)
            if n_w + n_l > 2:
                pooled_std = np.sqrt(
                    ((n_w - 1) * w_std**2 + (n_l - 1) * l_std**2) / (n_w + n_l - 2)
                )
                if pooled_std > 0:
                    cohens_d = diff / pooled_std

        rows.append(
            {
                "feature": feat,
                "winner_count": len(w_vals),
                "loser_count": len(l_vals),
                "winner_mean": round(w_mean, 6) if not pd.isna(w_mean) else np.nan,
                "loser_mean": round(l_mean, 6) if not pd.isna(l_mean) else np.nan,
                "difference": round(diff, 6) if not pd.isna(diff) else np.nan,
                "winner_median": round(w_median, 6) if not pd.isna(w_median) else np.nan,
                "loser_median": round(l_median, 6) if not pd.isna(l_median) else np.nan,
                "winner_std": round(w_std, 6) if not pd.isna(w_std) else np.nan,
                "loser_std": round(l_std, 6) if not pd.isna(l_std) else np.nan,
                "cohens_d": round(cohens_d, 4) if not pd.isna(cohens_d) else np.nan,
            }
        )

    summary = pd.DataFrame(rows)

    # Sort by absolute Cohen's d descending — strongest separators first
    if "cohens_d" in summary.columns:
        summary["abs_cohens_d"] = summary["cohens_d"].abs()
        summary = summary.sort_values("abs_cohens_d", ascending=False).drop(columns=["abs_cohens_d"])

    return summary.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Console quick-look
# ---------------------------------------------------------------------------


def _print_summary(summary: pd.DataFrame) -> None:
    print("\n" + "=" * 80)
    print("ACCEPTED EXPANSION PROXY — WINNER vs LOSER COMPARISON")
    print("=" * 80)

    for _, row in summary.iterrows():
        feat = row["feature"]
        w = row["winner_mean"]
        l = row["loser_mean"]
        d = row["difference"]
        cd = row["cohens_d"]
        w_n = row["winner_count"]
        l_n = row["loser_count"]

        w_str = f"{w:.4f}" if not pd.isna(w) else "N/A"
        l_str = f"{l:.4f}" if not pd.isna(l) else "N/A"
        d_str = f"{d:+.4f}" if not pd.isna(d) else "N/A"
        cd_str = f"{cd:+.4f}" if not pd.isna(cd) else "N/A"

        # Signal strength indicator
        signal = ""
        if not pd.isna(cd):
            abs_cd = abs(cd)
            if abs_cd >= 0.5:
                signal = " *** STRONG"
            elif abs_cd >= 0.3:
                signal = " **  MODERATE"
            elif abs_cd >= 0.15:
                signal = " *   WEAK"
            else:
                signal = "     NOISE"

        print(
            f"  {feat:<30s}  "
            f"W={w_str:>8s} (n={w_n:>3})  "
            f"L={l_str:>8s} (n={l_n:>3})  "
            f"D={d_str:>8s}  "
            f"d={cd_str:>7s}{signal}"
        )

    print("=" * 80)
    print("Cohen's d interpretation: |d|>=0.5 STRONG, >=0.3 MODERATE, >=0.15 WEAK, <0.15 NOISE")
    print("=" * 80)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _wilder_average(series: pd.Series, period: int) -> pd.Series:
    values = series.astype(float)
    averages = pd.Series(index=values.index, dtype=float)
    if len(values) < period:
        return averages

    averages.iloc[period - 1] = values.iloc[:period].mean()
    for idx in range(period, len(values)):
        averages.iloc[idx] = ((averages.iloc[idx - 1] * (period - 1)) + values.iloc[idx]) / period
    return averages


def _fetch_with_retry(data_source: YahooFinanceDataSource, ticker: str) -> pd.DataFrame:
    last_error: Exception | None = None
    for _ in range(3):
        try:
            return data_source.fetch(
                MarketDataRequest(ticker=ticker, start=START, end=END, timeframe=TIMEFRAME)
            )
        except Exception as exc:
            last_error = exc
            time.sleep(1)
    raise RuntimeError(f"Could not fetch data for {ticker}: {last_error}") from last_error


if __name__ == "__main__":
    main()
