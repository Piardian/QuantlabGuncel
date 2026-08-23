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
UNIVERSE = ["AAPL", "MSFT", "NVDA", "META", "AMZN", "GOOGL", "TSLA", "SPY", "QQQ"]
START = "2018-01-01"
END = "2024-01-01"
TIMEFRAME = "1d"
ATR_PERIOD = 14
EMA_PERIOD = 200
RS_LOOKBACK = 60
TRADING_DAYS = 252
BENCHMARK = "SPY"


def main() -> None:
    data_source = YahooFinanceDataSource()
    benchmark_data = _add_indicators(_fetch_with_retry(data_source=data_source, ticker=BENCHMARK))
    rows: list[dict[str, float | int | str]] = []

    for ticker in UNIVERSE:
        market_data = benchmark_data if ticker == BENCHMARK else _add_indicators(
            _fetch_with_retry(data_source=data_source, ticker=ticker)
        )
        strategy_metrics = _strategy_metrics(ticker=ticker)
        asset_characteristics = _asset_characteristics(
            market_data=market_data,
            benchmark_data=benchmark_data,
        )
        rows.append({"ticker": ticker, **strategy_metrics, **asset_characteristics})

    attribution = pd.DataFrame(rows)
    attribution_path = OUTPUT_DIR / "asset_attribution.csv"
    attribution.to_csv(attribution_path, index=False)

    correlation_summary = _correlation_summary(attribution)
    correlation_path = OUTPUT_DIR / "asset_correlation_summary.csv"
    correlation_summary.to_csv(correlation_path, index=False)

    print(attribution_path)
    print(correlation_path)


def _fetch_with_retry(data_source: YahooFinanceDataSource, ticker: str) -> pd.DataFrame:
    last_error: Exception | None = None
    for _ in range(3):
        try:
            return data_source.fetch(MarketDataRequest(ticker=ticker, start=START, end=END, timeframe=TIMEFRAME))
        except Exception as exc:
            last_error = exc
            time.sleep(1)
    raise RuntimeError(f"Could not fetch data for {ticker}: {last_error}") from last_error


def _add_indicators(dataframe: pd.DataFrame) -> pd.DataFrame:
    data = dataframe.copy()
    previous_close = data["Close"].shift(1)
    true_range = pd.concat(
        [
            data["High"] - data["Low"],
            (data["High"] - previous_close).abs(),
            (data["Low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    data["TrueRange"] = true_range
    data["ATR14"] = _wilder_average(true_range, ATR_PERIOD)
    data["EMA200"] = data["Close"].ewm(span=EMA_PERIOD, adjust=False).mean()
    data["DailyReturn"] = data["Close"].pct_change()
    data["Return60"] = data["Close"].pct_change(RS_LOOKBACK)
    return data


def _wilder_average(series: pd.Series, period: int) -> pd.Series:
    values = series.astype(float)
    averages = pd.Series(index=values.index, dtype=float)
    if len(values) < period:
        return averages

    averages.iloc[period - 1] = values.iloc[:period].mean()
    for index in range(period, len(values)):
        averages.iloc[index] = ((averages.iloc[index - 1] * (period - 1)) + values.iloc[index]) / period
    return averages


def _strategy_metrics(ticker: str) -> dict[str, float | int]:
    trades_path = _resolve_trades_path(ticker)
    if trades_path is None:
        return {
            "trade_count": 0,
            "avg_R": 0.0,
            "expectancy": 0.0,
            "profit_factor": 0.0,
            "winrate": 0.0,
            "net_pnl": 0.0,
        }

    trades = pd.read_csv(trades_path)
    if trades.empty:
        return {
            "trade_count": 0,
            "avg_R": 0.0,
            "expectancy": 0.0,
            "profit_factor": 0.0,
            "winrate": 0.0,
            "net_pnl": 0.0,
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
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else (math.inf if gross_profit > 0 else 0.0)

    return {
        "trade_count": int(len(trades)),
        "avg_R": float(r_values.mean()) if not r_values.empty else 0.0,
        "expectancy": (win_rate_dec * avg_win) - (loss_rate_dec * avg_loss_abs),
        "profit_factor": profit_factor,
        "winrate": win_rate_dec * 100.0,
        "net_pnl": float(pnl.sum()),
    }


def _resolve_trades_path(ticker: str) -> Path | None:
    candidates = [
        OUTPUT_DIR / f"leadership_quality_FULL_SYSTEM_{ticker}" / "trades.csv",
        OUTPUT_DIR / f"leadership_expansion_v1_{ticker}" / "trades.csv",
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def _asset_characteristics(market_data: pd.DataFrame, benchmark_data: pd.DataFrame) -> dict[str, float]:
    aligned = market_data.join(
        benchmark_data[["DailyReturn", "Return60"]].rename(
            columns={"DailyReturn": "BenchmarkDailyReturn", "Return60": "BenchmarkReturn60"}
        ),
        how="inner",
    ).dropna(subset=["DailyReturn", "BenchmarkDailyReturn"])

    daily_returns = aligned["DailyReturn"].dropna()
    benchmark_returns = aligned["BenchmarkDailyReturn"].dropna()
    beta = _beta_vs_benchmark(daily_returns=daily_returns, benchmark_returns=benchmark_returns)

    valid_indicator_data = aligned.dropna(subset=["ATR14", "EMA200", "Return60", "BenchmarkReturn60"])
    rs60 = valid_indicator_data["Return60"] - valid_indicator_data["BenchmarkReturn60"]
    trend_distance = (valid_indicator_data["Close"] - valid_indicator_data["EMA200"]) / valid_indicator_data["EMA200"]

    return {
        "annualized_volatility": float(daily_returns.std(ddof=1) * math.sqrt(TRADING_DAYS)),
        "average_ATR_percent": float((valid_indicator_data["ATR14"] / valid_indicator_data["Close"]).mean()),
        "beta_vs_SPY": beta,
        "average_daily_range_percent": float(((aligned["High"] - aligned["Low"]) / aligned["Close"]).mean()),
        "trend_persistence": float((valid_indicator_data["Close"] > valid_indicator_data["EMA200"]).mean() * 100.0),
        "RS_persistence": float((rs60 > 0).mean() * 100.0),
        "momentum_strength": float(valid_indicator_data["Return60"].mean()),
        "trend_strength": float(trend_distance.mean()),
    }


def _beta_vs_benchmark(daily_returns: pd.Series, benchmark_returns: pd.Series) -> float:
    returns = pd.concat([daily_returns, benchmark_returns], axis=1).dropna()
    if len(returns) < 2:
        return 0.0
    asset = returns.iloc[:, 0]
    benchmark = returns.iloc[:, 1]
    benchmark_var = float(benchmark.var(ddof=1))
    if benchmark_var <= 0:
        return 0.0
    return float(asset.cov(benchmark) / benchmark_var)


def _correlation_summary(attribution: pd.DataFrame) -> pd.DataFrame:
    characteristic_columns = [
        "annualized_volatility",
        "average_ATR_percent",
        "beta_vs_SPY",
        "average_daily_range_percent",
        "trend_persistence",
        "RS_persistence",
        "momentum_strength",
        "trend_strength",
    ]
    rows = []
    for metric in characteristic_columns:
        rows.append(
            {
                "metric": metric,
                "correlation_with_avg_R": _safe_corr(attribution[metric], attribution["avg_R"]),
                "correlation_with_expectancy": _safe_corr(attribution[metric], attribution["expectancy"]),
            }
        )
    return pd.DataFrame(rows)


def _safe_corr(left: pd.Series, right: pd.Series) -> float:
    values = pd.concat([left.astype(float), right.astype(float)], axis=1).replace([math.inf, -math.inf], pd.NA).dropna()
    if len(values) < 2:
        return 0.0
    return float(values.iloc[:, 0].corr(values.iloc[:, 1]))


if __name__ == "__main__":
    main()
