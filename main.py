from __future__ import annotations

import argparse
from dataclasses import asdict
from pathlib import Path

import backtrader as bt
from fastapi import FastAPI

import sys

from config.settings import DEFAULT_CONFIG_PATH, BacktestConfig, load_config
from data.yahoo_data import MarketDataRequest, YahooFinanceDataSource
from engine.backtest_engine import BacktestEngine, BacktestRunResult
from routers import router as api_router
from strategies.leadership_expansion_v1 import LeadershipExpansionV1Strategy
from strategies.mean_reversion_v1 import MeanReversionV1Strategy
from strategies.relative_strength_pullback_v1 import RelativeStrengthPullbackV1Strategy
from strategies.simple_trend import SimpleTrendStrategy
from strategies.sma_crossover import SmaCrossoverStrategy
from strategies.stock_v131.strategy import TrendFlowingStockV131Strategy

app = FastAPI(title="Professional Stock Market Backtesting & PAPER-002 API", version="1.0.0")
app.include_router(api_router)


STRATEGY_REGISTRY = {
    "leadership_expansion_v1": LeadershipExpansionV1Strategy,
    "relative_strength_pullback_v1": RelativeStrengthPullbackV1Strategy,
    "sma_crossover": SmaCrossoverStrategy,
    "simple_trend": SimpleTrendStrategy,
    "mean_reversion_v1": MeanReversionV1Strategy,
    "trendflowing_stock_v131": TrendFlowingStockV131Strategy,
}
SUPPORTED_TIMEFRAMES = {"15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Professional stock market backtesting system")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH, help="Path to config JSON file")
    parser.add_argument("--ticker", type=str, help="Ticker symbol, e.g. AAPL")
    parser.add_argument("--start", dest="start_date", type=str, help="Start date in YYYY-MM-DD format")
    parser.add_argument("--end", dest="end_date", type=str, help="End date in YYYY-MM-DD format")
    parser.add_argument("--timeframe", type=str, help="Yahoo Finance interval, e.g. 15m, 1h, 1d")
    parser.add_argument("--capital", dest="initial_capital", type=float, help="Starting capital")
    parser.add_argument("--risk", dest="risk_per_trade", type=float, help="Risk per trade as a decimal")
    parser.add_argument("--commission", type=float, help="Commission as a decimal, e.g. 0.001 = 0.1%%")
    parser.add_argument("--slippage", type=float, help="Slippage as a decimal, e.g. 0.0005 = 0.05%%")
    parser.add_argument("--fast-period", type=int, help="Fast SMA period")
    parser.add_argument("--slow-period", type=int, help="Slow SMA period")
    parser.add_argument("--stop-loss", dest="stop_loss_pct", type=float, help="Stop loss percent as decimal")
    parser.add_argument("--take-profit", dest="take_profit_pct", type=float, help="Take profit percent as decimal")
    parser.add_argument("--strategy", dest="strategy_name", type=str, help="Strategy name from registry")
    parser.add_argument("--output-dir", type=str, help="Directory for charts and outputs")
    parser.add_argument("--no-plot", action="store_true", help="Disable chart generation")
    parser.add_argument("--price-step", type=float, help="Minimum price increment for stock research strategy")
    parser.add_argument("--ema-period", type=int, help="EMA period for trend strategies")
    parser.add_argument("--atr-period", type=int, help="ATR period for pullback strategy")
    parser.add_argument("--pullback-atr-threshold", type=float, help="Max pullback distance as ATR multiple")
    parser.add_argument("--shallow-pullback-pct", type=float, help="Minimum retracement from recent high")
    parser.add_argument("--swing-lookback", type=int, help="Swing lookback bars for recent low stop placement")
    parser.add_argument("--reward-risk-ratio", type=float, help="Take-profit multiple of initial risk")
    parser.add_argument("--ema-trend-period", type=int, help="Long-term trend filter EMA period")
    parser.add_argument("--ema-exit-period", type=int, help="Mean-reversion exit EMA period")
    parser.add_argument("--rsi-period", type=int, help="RSI period")
    parser.add_argument("--rsi-threshold", type=float, help="RSI oversold threshold")
    parser.add_argument("--bb-period", type=int, help="Bollinger Band period")
    parser.add_argument("--bb-devfactor", type=float, help="Bollinger Band standard deviation multiplier")
    parser.add_argument("--ema20-distance-atr", type=float, help="Required distance below EMA20 in ATRs")
    parser.add_argument("--stop-atr-multiple", type=float, help="ATR multiple for stop placement")
    parser.add_argument("--max-positions", type=int, help="Maximum simultaneous positions")
    parser.add_argument("--ema-pullback-period", type=int, help="EMA50-style pullback filter period")
    parser.add_argument("--ema-signal-period", type=int, help="EMA20-style signal and exit period")
    parser.add_argument("--relative-strength-lookback", type=int, help="Relative strength lookback in bars")
    parser.add_argument("--relative-strength-threshold", type=float, help="Minimum relative strength edge over SPY")
    parser.add_argument("--initial-stop-atr-multiple", type=float, help="Initial stop distance in ATRs")
    parser.add_argument("--trailing-stop-atr-multiple", type=float, help="Trailing stop distance in ATRs")
    parser.add_argument("--max-holding-bars", type=int, help="Maximum holding period in bars")
    parser.add_argument("--breakout-lookback", type=int, help="Highest-close breakout lookback in bars")
    parser.add_argument("--expansion-atr-multiple", type=float, help="True range expansion multiple of ATR")
    parser.add_argument("--consolidation-bars", type=int, help="Consolidation window length in bars")
    parser.add_argument("--compression-threshold", type=float, help="Maximum consolidation range percentage")
    parser.add_argument("--benchmark-ticker", type=str, help="Benchmark ticker for relative strength")
    parser.add_argument("--enable-ema200-filter", type=bool, help="Toggle EMA200 trend filter")
    parser.add_argument("--enable-ema200-slope", type=bool, help="Toggle EMA200 slope filter")
    parser.add_argument("--enable-relative-strength", type=bool, help="Toggle relative strength filter")
    parser.add_argument("--enable-ema50-filter", type=bool, help="Toggle EMA50 quality filter")
    parser.add_argument("--enable-pullback-filter", type=bool, help="Toggle EMA20 pullback filter")
    parser.add_argument("--enable-momentum-trigger", type=bool, help="Toggle bullish momentum trigger")
    parser.add_argument("--enable-leadership-quality", type=bool, help="Toggle RS20/RS120 leadership quality filter")
    return parser.parse_known_args()


def merge_config(base_config: BacktestConfig, args: argparse.Namespace) -> BacktestConfig:
    values = asdict(base_config)
    for field_name, field_value in vars(args).items():
        if field_name == "config" or field_value is None:
            continue
        if field_name == "no_plot":
            if field_value:
                values["plot"] = False
            continue
        values[field_name] = field_value

    timeframe = values["timeframe"]
    if timeframe not in SUPPORTED_TIMEFRAMES:
        raise ValueError(
            f"Unsupported timeframe '{timeframe}'. "
            f"Use one of: {', '.join(sorted(SUPPORTED_TIMEFRAMES))}."
        )

    return BacktestConfig(**values)


def print_summary(config: BacktestConfig, result: BacktestRunResult) -> None:
    metrics = result.metrics

    print(f"Ticker: {config.ticker}")
    print(f"Date Range: {config.start_date} -> {config.end_date}")
    print(f"Timeframe: {config.timeframe}")
    print(f"Initial Capital: ${config.initial_capital:,.2f}")
    print(f"Final Portfolio Value: ${result.final_portfolio_value:,.2f}")
    print(f"Total Return: {metrics.total_return_pct:.2f}%")
    print(f"Net Profit: ${metrics.net_profit:,.2f}")
    print(f"Win Rate: {metrics.win_rate_pct:.2f}%")
    print(f"Max Drawdown: {metrics.max_drawdown_pct:.2f}%")
    print(f"Sharpe Ratio: {metrics.sharpe_ratio:.4f}" if metrics.sharpe_ratio is not None else "Sharpe Ratio: N/A")
    print(f"Closed Trades: {metrics.total_trades}")
    print(f"Avg R: {metrics.avg_r:.4f}" if metrics.avg_r is not None else "Avg R: N/A")
    print(f"Expectancy: {metrics.expectancy:.4f}" if metrics.expectancy is not None else "Expectancy: N/A")

    if result.chart_paths:
        print("Charts:")
        for name, path in result.chart_paths.items():
            print(f"  {name}: {path.resolve()}")


def build_strategy_params(config: BacktestConfig) -> dict:
    if config.strategy_name == "trendflowing_stock_v131":
        return {
            "risk_per_trade": config.risk_per_trade,
            "price_step": config.price_step,
            "adx_period": config.adx_period,
            "adx_threshold": config.adx_threshold,
            "ema_period": config.ema_period,
            "swing_lookback": config.swing_lookback,
            "ob_lookback": config.ob_lookback,
            "disp_multiplier": config.disp_multiplier,
            "disp_avg_bars": config.disp_avg_bars,
            "fvg_max_bars": config.fvg_max_bars,
            "sl_buffer_steps": config.sl_buffer_steps,
            "sl_atr_min_mult": config.sl_atr_min_mult,
            "sl_atr_max_mult": config.sl_atr_max_mult,
            "tp1_rr": config.tp1_rr,
            "be_rr": config.be_rr,
            "trailing_atr_mult": config.trailing_atr_mult,
        }

    if config.strategy_name == "simple_trend":
        return {
            "risk_per_trade": config.risk_per_trade,
            "ema_period": config.ema_period,
            "atr_period": config.atr_period,
            "pullback_atr_threshold": config.pullback_atr_threshold,
            "shallow_pullback_pct": config.shallow_pullback_pct,
            "swing_lookback": config.swing_lookback,
            "reward_risk_ratio": config.reward_risk_ratio,
        }

    if config.strategy_name == "mean_reversion_v1":
        return {
            "risk_per_trade": config.risk_per_trade,
            "ema_trend_period": config.ema_trend_period,
            "ema_exit_period": config.ema_exit_period,
            "rsi_period": config.rsi_period,
            "rsi_threshold": config.rsi_threshold,
            "bb_period": config.bb_period,
            "bb_devfactor": config.bb_devfactor,
            "atr_period": config.atr_period,
            "ema20_distance_atr": config.ema20_distance_atr,
            "stop_atr_multiple": config.stop_atr_multiple,
            "max_positions": config.max_positions,
        }

    if config.strategy_name == "relative_strength_pullback_v1":
        return {
            "risk_per_trade": config.risk_per_trade,
            "ema_trend_period": config.ema_trend_period,
            "ema_pullback_period": config.ema_pullback_period,
            "ema_signal_period": config.ema_signal_period,
            "atr_period": config.atr_period,
            "relative_strength_lookback": config.relative_strength_lookback,
            "relative_strength_threshold": config.relative_strength_threshold,
            "initial_stop_atr_multiple": config.initial_stop_atr_multiple,
            "trailing_stop_atr_multiple": config.trailing_stop_atr_multiple,
            "max_holding_bars": config.max_holding_bars,
            "consolidation_bars": config.consolidation_bars,
            "compression_threshold": config.compression_threshold,
            "max_positions": config.max_positions,
            "skip_relative_strength_filter": config.skip_relative_strength_filter,
            "enable_ema200_filter": config.enable_ema200_filter,
            "enable_ema200_slope": config.enable_ema200_slope,
            "enable_relative_strength": config.enable_relative_strength,
            "enable_ema50_filter": config.enable_ema50_filter,
            "enable_pullback_filter": config.enable_pullback_filter,
        }

    if config.strategy_name == "leadership_expansion_v1":
        return {
            "risk_per_trade": config.risk_per_trade,
            "ema_trend_period": config.ema_trend_period,
            "ema_quality_period": config.ema_pullback_period,
            "atr_period": config.atr_period,
            "relative_strength_lookback": config.relative_strength_lookback,
            "relative_strength_threshold": config.relative_strength_threshold,
            "expansion_atr_multiple": config.expansion_atr_multiple,
            "breakout_lookback": config.breakout_lookback,
            "initial_stop_atr_multiple": config.initial_stop_atr_multiple,
            "trailing_stop_atr_multiple": config.trailing_stop_atr_multiple,
            "max_holding_bars": config.max_holding_bars,
            "max_positions": config.max_positions,
            "skip_relative_strength_filter": config.skip_relative_strength_filter,
            "enable_leadership_quality": config.enable_leadership_quality,
            "enable_relative_strength_filter": config.enable_relative_strength_filter,
            "enable_ema200_filter": config.enable_ema200_filter,
            "enable_ema200_slope_filter": config.enable_ema200_slope_filter,
            "enable_ema50_filter": config.enable_ema50_filter,
            "enable_expansion_filter": config.enable_expansion_filter,
            "enable_breakout_confirmation": config.enable_breakout_confirmation,
            "enable_protective_stop_exit": config.enable_protective_stop_exit,
            "enable_atr_trailing_exit": config.enable_atr_trailing_exit,
            "enable_ema_exit": config.enable_ema_exit,
            "enable_time_exit": config.enable_time_exit,
            "enable_risk_position_sizing": config.enable_risk_position_sizing,
        }

    return {
        "risk_per_trade": config.risk_per_trade,
        "stop_loss_pct": config.stop_loss_pct,
        "take_profit_pct": config.take_profit_pct,
        "fast_period": config.fast_period,
        "slow_period": config.slow_period,
    }


def build_resample_rules(config: BacktestConfig) -> list[dict[str, int]]:
    if config.strategy_name != "trendflowing_stock_v131":
        return []
    if config.timeframe != "15m":
        raise ValueError("trendflowing_stock_v131 currently requires --timeframe 15m.")
    return [
        {"timeframe": bt.TimeFrame.Minutes, "compression": 60},
        {"timeframe": bt.TimeFrame.Minutes, "compression": 240},
    ]


def main() -> None:
    args, unknown = parse_args()
    base_config = load_config(args.config)
    config = merge_config(base_config, args)

    strategy_class = STRATEGY_REGISTRY.get(config.strategy_name)
    if strategy_class is None:
        raise ValueError(f"Unsupported strategy: {config.strategy_name}")

    data_source = YahooFinanceDataSource()
    market_data = data_source.fetch(
        MarketDataRequest(
            ticker=config.ticker,
            start=config.start_date,
            end=config.end_date,
            timeframe=config.timeframe,
        )
    )
    benchmark_data = None
    if config.strategy_name in {"relative_strength_pullback_v1", "leadership_expansion_v1"}:
        config.skip_relative_strength_filter = config.ticker.upper() == config.benchmark_ticker.upper()
        benchmark_data = data_source.fetch(
            MarketDataRequest(
                ticker=config.benchmark_ticker,
                start=config.start_date,
                end=config.end_date,
                timeframe=config.timeframe,
            )
        )

    engine = BacktestEngine(
        initial_capital=config.initial_capital,
        commission=config.commission,
        slippage_perc=config.slippage,
        output_dir=Path(config.output_dir),
    )

    result = engine.run(
        dataframe=market_data,
        strategy_class=strategy_class,
        strategy_params=build_strategy_params(config),
        extra_dataframes=[benchmark_data] if benchmark_data is not None else None,
        plot_results=config.plot,
        base_timeframe=config.timeframe,
        resample_rules=build_resample_rules(config),
    )

    print_summary(config, result)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "serve":
        import uvicorn
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    else:
        main()
