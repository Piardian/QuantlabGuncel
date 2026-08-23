from __future__ import annotations

from dataclasses import dataclass, replace

import backtrader as bt

from strategies.stock_v131.types import SetupState, SwingPoint, TrendDirection, TrendState


def _series_values(line: bt.LineBuffer, size: int) -> list[float]:
    return [float(line[-idx]) for idx in range(size)]


def _find_swings(highs: list[float], lows: list[float], lookback: int) -> tuple[list[SwingPoint], list[SwingPoint]]:
    swing_highs: list[SwingPoint] = []
    swing_lows: list[SwingPoint] = []
    upper_bound = len(highs) - lookback

    for idx in range(lookback, upper_bound):
        if len(swing_highs) < 3:
            is_swing_high = all(
                highs[idx] > highs[idx - step] and highs[idx] > highs[idx + step]
                for step in range(1, lookback + 1)
            )
            if is_swing_high:
                swing_highs.append(SwingPoint(price=highs[idx], bar_index=idx))

        if len(swing_lows) < 3:
            is_swing_low = all(
                lows[idx] < lows[idx - step] and lows[idx] < lows[idx + step]
                for step in range(1, lookback + 1)
            )
            if is_swing_low:
                swing_lows.append(SwingPoint(price=lows[idx], bar_index=idx))

        if len(swing_highs) >= 3 and len(swing_lows) >= 3:
            break

    return swing_highs, swing_lows


def _check_bos(closes: list[float], swing_highs: list[SwingPoint], swing_lows: list[SwingPoint]) -> TrendDirection:
    if len(swing_highs) < 2 or len(swing_lows) < 2:
        return TrendDirection.NONE

    bull_index = swing_highs[1].bar_index
    bear_index = swing_lows[1].bar_index

    bull_break = next((idx for idx in range(0, bull_index) if closes[idx] > swing_highs[1].price), None)
    bear_break = next((idx for idx in range(0, bear_index) if closes[idx] < swing_lows[1].price), None)

    if bull_break is None and bear_break is None:
        return TrendDirection.NONE
    if bull_break is not None and bear_break is None:
        return TrendDirection.LONG
    if bear_break is not None and bull_break is None:
        return TrendDirection.SHORT
    return TrendDirection.LONG if bull_break < bear_break else TrendDirection.SHORT


@dataclass(slots=True)
class TrendDetector:
    data: bt.LineIterator
    adx: bt.Indicator
    di_plus: bt.Indicator
    di_minus: bt.Indicator
    ema: bt.Indicator
    adx_threshold: float
    swing_lookback: int
    bars_required: int = 60

    def evaluate(self, previous_direction: TrendDirection) -> TrendState:
        state = TrendState(direction=previous_direction)

        if len(self.data) < self.bars_required:
            state.reject_reason = "TREND_REJECT | INSUFFICIENT_HTF_BARS"
            return state

        highs = _series_values(self.data.high, self.bars_required)
        lows = _series_values(self.data.low, self.bars_required)
        closes = _series_values(self.data.close, self.bars_required)

        swing_highs, swing_lows = _find_swings(highs=highs, lows=lows, lookback=self.swing_lookback)
        state.swing_highs = swing_highs
        state.swing_lows = swing_lows
        if len(swing_highs) < 2 or len(swing_lows) < 2:
            state.reject_reason = "TREND_REJECT | SWING_INSUFFICIENT"
            return state

        state.adx_value = float(self.adx[0])
        state.di_plus = float(self.di_plus[0])
        state.di_minus = float(self.di_minus[0])
        state.ema_value = float(self.ema[0])
        state.ema_slope = float(self.ema[0] - self.ema[-1])

        state.bos_direction = _check_bos(closes=closes, swing_highs=swing_highs, swing_lows=swing_lows)
        adx_low = self.adx_threshold - 2.0

        if state.adx_value < adx_low:
            state.reject_reason = f"TREND_REJECT | ADX_LOW | value={state.adx_value:.2f}"
            return state
        if state.adx_value < self.adx_threshold:
            state.reject_reason = f"TREND_REJECT | ADX_WAIT | value={state.adx_value:.2f}"
            return state

        if state.di_plus > state.di_minus:
            state.adx_direction = TrendDirection.LONG
        elif state.di_minus > state.di_plus:
            state.adx_direction = TrendDirection.SHORT

        if state.ema_slope > 0:
            state.ema_direction = TrendDirection.LONG
        elif state.ema_slope < 0:
            state.ema_direction = TrendDirection.SHORT
        else:
            state.reject_reason = "TREND_REJECT | EMA_FLAT"
            return state

        if (
            state.bos_direction != TrendDirection.NONE
            and state.bos_direction == state.adx_direction
            and state.bos_direction == state.ema_direction
        ):
            state.direction = state.bos_direction
            state.is_valid = True
            return state

        state.direction = TrendDirection.NONE
        state.reject_reason = (
            f"TREND_REJECT | MISMATCH | BOS={int(state.bos_direction)} "
            f"ADX={int(state.adx_direction)} EMA={int(state.ema_direction)}"
        )
        return state


@dataclass(slots=True)
class SetupDetector:
    h1_data: bt.LineIterator
    ltf_data: bt.LineIterator
    ob_lookback: int
    displacement_multiplier: float
    displacement_avg_bars: int
    fvg_max_bars: int

    def evaluate(
        self,
        trend_direction: TrendDirection,
        previous_state: SetupState,
    ) -> SetupState:
        state = replace(previous_state)
        state.setup_direction = trend_direction
        state.setup_ready = False
        state.reject_reason = ""

        if trend_direction == TrendDirection.NONE:
            return SetupState(reject_reason="SETUP_REJECT | NO_VALID_TREND")

        if state.setup_direction != TrendDirection.NONE and previous_state.setup_direction not in (
            TrendDirection.NONE,
            trend_direction,
        ):
            state = SetupState(setup_direction=trend_direction)

        state = self._find_order_block(state, trend_direction)
        if not state.has_ob:
            return state

        state = self._find_sweep(state, trend_direction)
        if not state.has_sweep:
            return state

        state = self._find_displacement(state, trend_direction)
        if not state.has_displacement:
            return state

        state = self._find_fvg(state, trend_direction)
        if state.has_fvg and state.fvg_valid:
            if state.fvg_bar_index is not None:
                state.fvg_bar_age = max(len(self.ltf_data) - 1 - state.fvg_bar_index, 0)
            if state.fvg_bar_age >= self.fvg_max_bars:
                return SetupState(
                    has_ob=state.has_ob,
                    ob_high=state.ob_high,
                    ob_low=state.ob_low,
                    ob_bar_index=state.ob_bar_index,
                    setup_direction=trend_direction,
                    reject_reason="SETUP_REJECT | FVG_EXPIRED",
                )

        state.setup_ready = state.has_ob and state.has_sweep and state.has_displacement and state.has_fvg and state.fvg_valid
        if not state.setup_ready and not state.reject_reason:
            state.reject_reason = "SETUP_REJECT | PIPELINE_INCOMPLETE"
        return state

    def _find_order_block(self, state: SetupState, direction: TrendDirection) -> SetupState:
        copied = min(len(self.h1_data), self.ob_lookback + 5)
        if copied < self.ob_lookback + 2:
            state.reject_reason = "SETUP_REJECT | NO_OB"
            return state

        opens = _series_values(self.h1_data.open, copied)
        highs = _series_values(self.h1_data.high, copied)
        lows = _series_values(self.h1_data.low, copied)
        closes = _series_values(self.h1_data.close, copied)

        for idx in range(1, copied - 3):
            if direction == TrendDirection.LONG:
                if closes[idx] >= opens[idx]:
                    continue
                ref_high = max(highs[idx : min(idx + 3, copied)])
                if any(closes[j] > ref_high for j in range(max(idx - 3, 1), idx)):
                    state.has_ob = True
                    state.ob_high = highs[idx]
                    state.ob_low = lows[idx]
                    state.ob_bar_index = len(self.h1_data) - 1 - idx
                    return state
            if direction == TrendDirection.SHORT:
                if closes[idx] <= opens[idx]:
                    continue
                ref_low = min(lows[idx : min(idx + 3, copied)])
                if any(closes[j] < ref_low for j in range(max(idx - 3, 1), idx)):
                    state.has_ob = True
                    state.ob_high = highs[idx]
                    state.ob_low = lows[idx]
                    state.ob_bar_index = len(self.h1_data) - 1 - idx
                    return state

        state.reject_reason = "SETUP_REJECT | NO_OB"
        return state

    def _find_sweep(self, state: SetupState, direction: TrendDirection) -> SetupState:
        copied = min(len(self.ltf_data), 40)
        highs = _series_values(self.ltf_data.high, copied)
        lows = _series_values(self.ltf_data.low, copied)
        closes = _series_values(self.ltf_data.close, copied)

        for idx in range(1, copied - 1):
            if direction == TrendDirection.LONG:
                ob_range = state.ob_high - state.ob_low
                tolerance = ob_range * 0.2
                wick_below = lows[idx] < state.ob_low + tolerance
                close_back = closes[idx] > state.ob_low - tolerance
                if wick_below and close_back:
                    state.has_sweep = True
                    state.sweep_price = lows[idx]
                    state.sweep_bar_index = len(self.ltf_data) - 1 - idx
                    return state
            else:
                ob_range = state.ob_high - state.ob_low
                tolerance = ob_range * 0.2
                wick_above = highs[idx] > state.ob_high - tolerance
                close_back = closes[idx] < state.ob_high + tolerance
                if wick_above and close_back:
                    state.has_sweep = True
                    state.sweep_price = highs[idx]
                    state.sweep_bar_index = len(self.ltf_data) - 1 - idx
                    return state

        state.reject_reason = "SETUP_REJECT | NO_SWEEP"
        return state

    def _find_displacement(self, state: SetupState, direction: TrendDirection) -> SetupState:
        copied = min(len(self.ltf_data), self.displacement_avg_bars + 20)
        opens = _series_values(self.ltf_data.open, copied)
        closes = _series_values(self.ltf_data.close, copied)

        if state.sweep_bar_index is None:
            state.reject_reason = "SETUP_REJECT | NO_SWEEP"
            return state

        sweep_idx = len(self.ltf_data) - 1 - state.sweep_bar_index
        if sweep_idx < 1 or sweep_idx >= copied:
            state.reject_reason = "SETUP_REJECT | NO_DISPLACEMENT"
            return state

        avg_window = []
        for idx in range(sweep_idx + 1, min(sweep_idx + 1 + self.displacement_avg_bars, copied)):
            avg_window.append(abs(closes[idx] - opens[idx]))

        if not avg_window:
            state.reject_reason = "SETUP_REJECT | NO_DISPLACEMENT"
            return state

        avg_body = sum(avg_window) / len(avg_window)
        check_end = max(sweep_idx - 5, 1)

        for idx in range(sweep_idx - 1, check_end - 1, -1):
            body = abs(closes[idx] - opens[idx])
            ratio = body / avg_body if avg_body else 0.0
            bull = closes[idx] > opens[idx]
            bear = closes[idx] < opens[idx]
            if ratio >= self.displacement_multiplier:
                if (direction == TrendDirection.LONG and bull) or (direction == TrendDirection.SHORT and bear):
                    state.has_displacement = True
                    state.displacement_ratio = ratio
                    state.displacement_bar_index = len(self.ltf_data) - 1 - idx
                    return state

        state.reject_reason = "SETUP_REJECT | NO_DISPLACEMENT"
        return state

    def _find_fvg(self, state: SetupState, direction: TrendDirection) -> SetupState:
        copied = min(len(self.ltf_data), 30)
        highs = _series_values(self.ltf_data.high, copied)
        lows = _series_values(self.ltf_data.low, copied)

        if state.displacement_bar_index is None:
            state.reject_reason = "SETUP_REJECT | NO_FVG"
            return state

        displacement_idx = len(self.ltf_data) - 1 - state.displacement_bar_index
        for idx in range(2, copied - 1):
            if idx > displacement_idx:
                continue
            if direction == TrendDirection.LONG and highs[idx + 1] < lows[idx - 1]:
                state.has_fvg = True
                state.fvg_low = highs[idx + 1]
                state.fvg_high = lows[idx - 1]
                state.fvg_mid = (state.fvg_low + state.fvg_high) / 2.0
                state.fvg_bar_index = len(self.ltf_data) - 1 - idx
                state.fvg_valid = True
                return state
            if direction == TrendDirection.SHORT and lows[idx + 1] > highs[idx - 1]:
                state.has_fvg = True
                state.fvg_high = lows[idx + 1]
                state.fvg_low = highs[idx - 1]
                state.fvg_mid = (state.fvg_low + state.fvg_high) / 2.0
                state.fvg_bar_index = len(self.ltf_data) - 1 - idx
                state.fvg_valid = True
                return state

        state.reject_reason = "SETUP_REJECT | NO_FVG"
        return state
