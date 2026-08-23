from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional


class TrendDirection(IntEnum):
    SHORT = -1
    NONE = 0
    LONG = 1


@dataclass(slots=True)
class SwingPoint:
    price: float
    bar_index: int


@dataclass(slots=True)
class TrendState:
    direction: TrendDirection = TrendDirection.NONE
    bos_direction: TrendDirection = TrendDirection.NONE
    adx_direction: TrendDirection = TrendDirection.NONE
    ema_direction: TrendDirection = TrendDirection.NONE
    adx_value: float = 0.0
    di_plus: float = 0.0
    di_minus: float = 0.0
    ema_value: float = 0.0
    ema_slope: float = 0.0
    is_valid: bool = False
    reject_reason: str = ""
    swing_highs: list[SwingPoint] = field(default_factory=list)
    swing_lows: list[SwingPoint] = field(default_factory=list)


@dataclass(slots=True)
class SetupState:
    has_ob: bool = False
    ob_high: float = 0.0
    ob_low: float = 0.0
    ob_bar_index: Optional[int] = None
    has_sweep: bool = False
    sweep_price: float = 0.0
    sweep_bar_index: Optional[int] = None
    has_displacement: bool = False
    displacement_ratio: float = 0.0
    displacement_bar_index: Optional[int] = None
    has_fvg: bool = False
    fvg_high: float = 0.0
    fvg_low: float = 0.0
    fvg_mid: float = 0.0
    fvg_bar_index: Optional[int] = None
    fvg_bar_age: int = 0
    fvg_valid: bool = False
    setup_ready: bool = False
    setup_direction: TrendDirection = TrendDirection.NONE
    reject_reason: str = ""


@dataclass(slots=True)
class ManagedTradeState:
    entry_order: object | None = None
    stop_order: object | None = None
    tp1_order: object | None = None
    pending_entry_price: float = 0.0
    pending_stop_price: float = 0.0
    pending_tp1_price: float = 0.0
    pending_size: int = 0
    pending_bars: int = 0
    order_direction: TrendDirection = TrendDirection.NONE
    position_direction: TrendDirection = TrendDirection.NONE
    entry_price: float = 0.0
    stop_price: float = 0.0
    initial_stop_price: float = 0.0
    tp1_price: float = 0.0
    tp1_hit: bool = False
    be_active: bool = False
    remaining_size: int = 0
