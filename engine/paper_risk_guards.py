from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd


EXPECTED_UNIVERSE_HASH = "BC7879B3830C7327EB0A5779625A347C06826C47488F64326C7D0B2884CC741D"


def frozen_strategy_config() -> dict[str, Any]:
    return {
        "strategy_id": "CSM001xTSM001",
        "csm": {
            "formation_anchor_trading_days": 252,
            "skip_period_trading_days": 21,
            "return_rule": "close_t_minus_21 / close_t_minus_252 - 1",
            "ranking_rule": "cross_sectional_percentile_rank_average_ascending",
            "top_decile_threshold": 0.90,
            "minimum_eligible_count": 50,
        },
        "tsm": {
            "formation_anchor_trading_days": 252,
            "skip_period_trading_days": 21,
            "direction_threshold": 0.0,
            "state_mapping": {"positive": "sign(return_12_1)==1", "neutral": "sign(return_12_1)==0", "negative": "sign(return_12_1)==-1"},
            "volatility_scaling": "excluded",
        },
        "gate": "csm001_top_decile_flag AND tsm001_positive_state",
        "rebalance_rule": "monthly_last_trading_day_signal",
        "weighting_rule": "equal_weight_approved_candidates_else_cash",
        "execution_timing": "no_earlier_than_next_trading_session_after_signal",
    }


def compute_strategy_hash(strategy_config: dict[str, Any] | None = None) -> str:
    canonical = json.dumps(strategy_config or frozen_strategy_config(), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest().upper()


EXPECTED_STRATEGY_HASH = compute_strategy_hash()


@dataclass(frozen=True, slots=True)
class PaperRiskConfig:
    max_single_position_weight: float = 0.20
    max_gross_exposure: float = 1.10
    max_order_notional: float = 100000.0
    max_daily_order_count: int = 50

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not (0 < self.max_single_position_weight <= 1):
            errors.append("INVALID_MAX_SINGLE_POSITION_WEIGHT")
        if not (0 < self.max_gross_exposure <= 2):
            errors.append("INVALID_MAX_GROSS_EXPOSURE")
        if not math.isfinite(self.max_order_notional) or self.max_order_notional <= 0:
            errors.append("INVALID_MAX_ORDER_NOTIONAL")
        if self.max_daily_order_count <= 0:
            errors.append("INVALID_MAX_DAILY_ORDER_COUNT")
        return errors


@dataclass(slots=True)
class RiskCheckResult:
    passed: bool
    errors: list[str] = field(default_factory=list)


class PaperSafetyManager:
    EXPECTED_UNIVERSE_HASH = EXPECTED_UNIVERSE_HASH
    EXPECTED_STRATEGY_HASH = EXPECTED_STRATEGY_HASH

    def __init__(self, risk_config: PaperRiskConfig | None = None) -> None:
        self.risk_config = risk_config or PaperRiskConfig()

    def verify_environment(self, base_url: str) -> bool:
        return base_url.strip().rstrip("/") == "https://paper-api.alpaca.markets"

    def canonical_universe_hash(self, membership_csv_path: Path) -> str:
        if not membership_csv_path.exists():
            raise FileNotFoundError(str(membership_csv_path))
        membership = pd.read_csv(membership_csv_path)
        required = ["source_asset_id", "symbol", "exchange"]
        missing = [col for col in required if col not in membership.columns]
        if missing:
            raise ValueError(f"UNIVERSE_MISSING_COLUMNS:{','.join(missing)}")
        canonical = membership[required].sort_values(required)
        return hashlib.sha256(canonical.to_csv(index=False).encode("utf-8")).hexdigest().upper()

    def verify_universe_hash(self, membership_csv_path: Path) -> bool:
        try:
            membership = pd.read_csv(membership_csv_path)
            if len(membership) != 250:
                return False
            if membership["symbol"].astype(str).str.upper().duplicated().any():
                return False
            if membership["source_asset_id"].astype(str).duplicated().any():
                return False
            return self.canonical_universe_hash(membership_csv_path) == self.EXPECTED_UNIVERSE_HASH
        except Exception:
            return False

    def compute_strategy_hash(self, strategy_config: dict[str, Any] | None = None) -> str:
        return compute_strategy_hash(strategy_config)

    def verify_strategy_hash(self, strategy_config: dict[str, Any] | None = None) -> bool:
        return self.compute_strategy_hash(strategy_config) == self.EXPECTED_STRATEGY_HASH

    def execution_flags_authorize(self, trading_enabled: bool, paper_execution_enabled: bool, environment: str) -> bool:
        return environment.upper() == "PAPER" and trading_enabled is True and paper_execution_enabled is True

    def check_kill_switch(self, trading_enabled: bool, paper_execution_enabled: bool, environment: str) -> bool:
        return self.execution_flags_authorize(trading_enabled, paper_execution_enabled, environment)

    def check_risk_guards(
        self,
        target_weights: dict[str, float],
        order_notionals: list[float] | float,
        daily_order_count: int,
    ) -> RiskCheckResult:
        errors = self.risk_config.validate()
        values = list(target_weights.values())
        gross_exposure = sum(abs(float(w)) for w in values)
        max_weight = max((abs(float(w)) for w in values), default=0.0)
        notionals = [float(order_notionals)] if isinstance(order_notionals, (int, float)) else [float(x) for x in order_notionals]

        if len(target_weights) != len({symbol.upper() for symbol in target_weights}):
            errors.append("DUPLICATE_TARGET_SYMBOL")
        if any((not math.isfinite(w)) for w in values):
            errors.append("INVALID_TARGET_WEIGHT")
        if max_weight > self.risk_config.max_single_position_weight:
            errors.append("MAX_SINGLE_POSITION_WEIGHT_EXCEEDED")
        if gross_exposure > self.risk_config.max_gross_exposure:
            errors.append("MAX_GROSS_EXPOSURE_EXCEEDED")
        if any((not math.isfinite(n) or n < 0) for n in notionals):
            errors.append("INVALID_ORDER_NOTIONAL")
        if any(n > self.risk_config.max_order_notional for n in notionals):
            errors.append("MAX_ORDER_NOTIONAL_EXCEEDED")
        if daily_order_count > self.risk_config.max_daily_order_count:
            errors.append("MAX_DAILY_ORDER_COUNT_EXCEEDED")
        return RiskCheckResult(passed=not errors, errors=errors)

    def check_buying_power(self, required_notional: float, available_buying_power: float) -> bool:
        if not math.isfinite(required_notional) or not math.isfinite(available_buying_power):
            return False
        if required_notional < 0 or available_buying_power < 0:
            return False
        return required_notional <= available_buying_power
