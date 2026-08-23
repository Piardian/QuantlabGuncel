from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import json


@dataclass(slots=True)
class BacktestConfig:
    ticker: str = "AAPL"
    start_date: str = "2020-01-01"
    end_date: str = "2024-01-01"
    timeframe: str = "1d"
    initial_capital: float = 10_000.0
    risk_per_trade: float = 0.01
    commission: float = 0.001
    slippage: float = 0.0005
    strategy_name: str = "sma_crossover"
    fast_period: int = 50
    slow_period: int = 200
    stop_loss_pct: float = 0.05
    take_profit_pct: float = 0.10
    adx_period: int = 14
    adx_threshold: float = 20.0
    ema_period: int = 50
    atr_period: int = 14
    pullback_atr_threshold: float = 0.5
    shallow_pullback_pct: float = 0.01
    swing_lookback: int = 3
    reward_risk_ratio: float = 2.0
    ema_trend_period: int = 200
    ema_exit_period: int = 20
    rsi_period: int = 2
    rsi_threshold: float = 10.0
    bb_period: int = 20
    bb_devfactor: float = 2.0
    ema20_distance_atr: float = 1.0
    stop_atr_multiple: float = 1.5
    max_positions: int = 3
    ema_pullback_period: int = 50
    ema_signal_period: int = 20
    relative_strength_lookback: int = 60
    relative_strength_threshold: float = 0.05
    initial_stop_atr_multiple: float = 1.5
    trailing_stop_atr_multiple: float = 2.0
    max_holding_bars: int = 40
    breakout_lookback: int = 20
    expansion_atr_multiple: float = 1.5
    consolidation_bars: int = 5
    compression_threshold: float = 0.04
    benchmark_ticker: str = "SPY"
    skip_relative_strength_filter: bool = False
    enable_ema200_filter: bool = True
    enable_ema200_slope: bool = True
    enable_relative_strength: bool = True
    enable_ema50_filter: bool = True
    enable_pullback_filter: bool = True
    enable_momentum_trigger: bool = True
    enable_leadership_quality: bool = True
    enable_relative_strength_filter: bool = True
    enable_ema200_slope_filter: bool = True
    enable_expansion_filter: bool = True
    enable_breakout_confirmation: bool = True
    enable_protective_stop_exit: bool = True
    enable_atr_trailing_exit: bool = True
    enable_ema_exit: bool = True
    enable_time_exit: bool = True
    enable_risk_position_sizing: bool = True
    ob_lookback: int = 20
    disp_multiplier: float = 1.5
    disp_avg_bars: int = 5
    fvg_max_bars: int = 16
    sl_buffer_steps: int = 5
    sl_atr_min_mult: float = 1.0
    sl_atr_max_mult: float = 4.0
    tp1_rr: float = 1.5
    be_rr: float = 1.5
    trailing_atr_mult: float = 2.0
    price_step: float = 0.01
    output_dir: str = "output"
    plot: bool = True


DEFAULT_CONFIG_PATH = Path(__file__).with_name("backtest_config.json")


def load_config(config_path: Path | None = None) -> BacktestConfig:
    resolved_path = config_path or DEFAULT_CONFIG_PATH
    payload: dict[str, Any] = {}

    if resolved_path.exists():
        payload = json.loads(resolved_path.read_text(encoding="utf-8"))

    return BacktestConfig(**payload)


def save_default_config(config_path: Path | None = None) -> Path:
    resolved_path = config_path or DEFAULT_CONFIG_PATH
    resolved_path.write_text(
        json.dumps(asdict(BacktestConfig()), indent=2),
        encoding="utf-8",
    )
    return resolved_path
