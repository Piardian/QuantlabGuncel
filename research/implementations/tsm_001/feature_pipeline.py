from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


OUTPUT_COLUMNS = [
    "date",
    "ticker",
    "adjusted_close",
    "price_t_minus_21",
    "price_t_minus_252",
    "tsm_return_12_1",
    "tsm001_direction_score",
    "tsm001_state",
    "tsm001_positive_state",
    "tsm001_negative_state",
    "tsm001_valid_observation",
]


@dataclass(frozen=True, slots=True)
class TSM001FeaturePipeline:
    """Deterministic feature builder for frozen TSM-001."""

    formation_anchor_trading_days: int = 252
    skip_period_trading_days: int = 21
    direction_threshold: float = 0.0
    volatility_scaling: str = "excluded"

    def build_features(self, close_panel: pd.DataFrame) -> pd.DataFrame:
        self._validate_frozen_parameters()
        closes = self._prepare_close_panel(close_panel)
        if closes.empty:
            raise ValueError("TSM-001 close panel cannot be empty.")

        price_t_minus_skip = closes.shift(self.skip_period_trading_days)
        price_t_minus_anchor = closes.shift(self.formation_anchor_trading_days)
        tsm_return_12_1 = (price_t_minus_skip / price_t_minus_anchor) - 1.0
        tsm_return_12_1 = tsm_return_12_1.where(np.isfinite(tsm_return_12_1))

        valid_observation = closes.notna() & price_t_minus_skip.notna() & price_t_minus_anchor.notna() & tsm_return_12_1.notna()
        direction_score = np.sign(tsm_return_12_1).where(valid_observation)
        state = pd.DataFrame(np.nan, index=direction_score.index, columns=direction_score.columns, dtype=object)
        state = state.mask(direction_score.eq(1.0) & valid_observation, "POSITIVE")
        state = state.mask(direction_score.eq(0.0) & valid_observation, "NEUTRAL")
        state = state.mask(direction_score.eq(-1.0) & valid_observation, "NEGATIVE")
        positive_state = direction_score.eq(1.0) & valid_observation
        negative_state = direction_score.eq(-1.0) & valid_observation

        records = []
        for ticker in closes.columns:
            frame = pd.DataFrame(
                {
                    "date": closes.index,
                    "ticker": ticker,
                    "adjusted_close": closes[ticker].to_numpy(dtype=float),
                    "price_t_minus_21": price_t_minus_skip[ticker].to_numpy(dtype=float),
                    "price_t_minus_252": price_t_minus_anchor[ticker].to_numpy(dtype=float),
                    "tsm_return_12_1": tsm_return_12_1[ticker].to_numpy(dtype=float),
                    "tsm001_direction_score": direction_score[ticker].to_numpy(dtype=float),
                    "tsm001_state": state[ticker].to_numpy(dtype=object),
                    "tsm001_positive_state": positive_state[ticker].to_numpy(dtype=bool),
                    "tsm001_negative_state": negative_state[ticker].to_numpy(dtype=bool),
                    "tsm001_valid_observation": valid_observation[ticker].to_numpy(dtype=bool),
                }
            )
            records.append(frame)

        result = pd.concat(records, ignore_index=True)
        result = result.sort_values(["date", "ticker"]).reset_index(drop=True)
        return result[OUTPUT_COLUMNS]

    def _validate_frozen_parameters(self) -> None:
        if self.formation_anchor_trading_days != 252:
            raise ValueError("TSM-001 CD-001 requires formation_anchor_trading_days == 252.")
        if self.skip_period_trading_days != 21:
            raise ValueError("TSM-001 CD-001 requires skip_period_trading_days == 21.")
        if not np.isclose(self.direction_threshold, 0.0):
            raise ValueError("TSM-001 CD-001 requires direction_threshold == 0.0.")
        if self.volatility_scaling != "excluded":
            raise ValueError("TSM-001 CD-001 requires volatility_scaling == 'excluded'.")

    def _prepare_close_panel(self, close_panel: pd.DataFrame) -> pd.DataFrame:
        frame = close_panel.copy()
        frame.index = pd.to_datetime(frame.index).tz_localize(None)
        frame = frame.sort_index()
        frame = frame[~frame.index.duplicated(keep="first")]
        frame = frame.reindex(sorted(frame.columns), axis=1)
        frame = frame.apply(pd.to_numeric, errors="coerce")
        return frame.where(frame > 0)
