from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ComponentDefinition:
    parameter: str
    production_component: str
    decision_stage: str
    alternate_research_semantics: str


COMPONENTS = (
    ComponentDefinition("enable_relative_strength_filter", "Relative Strength Filter", "entry", "Bypass the RS eligibility gate."),
    ComponentDefinition("enable_leadership_quality", "Leadership Quality Gate", "entry", "Bypass the RS20/RS120 quality condition."),
    ComponentDefinition("enable_ema200_filter", "Price Above EMA200", "entry", "Bypass the EMA200 price gate."),
    ComponentDefinition("enable_ema200_slope_filter", "EMA200 Positive Slope", "entry", "Bypass the EMA200 slope gate."),
    ComponentDefinition("enable_ema50_filter", "Price Above EMA50", "entry", "Bypass the EMA50 quality gate."),
    ComponentDefinition("enable_expansion_filter", "ATR Expansion Filter", "entry", "Bypass the TrueRange versus ATR gate."),
    ComponentDefinition("enable_breakout_confirmation", "Breakout Confirmation", "entry", "Bypass the prior-close breakout gate."),
    ComponentDefinition("enable_protective_stop_exit", "Initial Protective Stop Exit", "exit", "Retain ATR risk sizing but do not exit at the unmoved initial stop."),
    ComponentDefinition("enable_atr_trailing_exit", "ATR Trailing Exit", "exit", "Do not raise or execute the ATR trailing stop."),
    ComponentDefinition("enable_ema_exit", "EMA50 Exit", "exit", "Do not exit on EMA50 breakdown."),
    ComponentDefinition("enable_time_exit", "Maximum Holding Exit", "exit", "Do not exit solely because maximum holding time elapsed."),
    ComponentDefinition("enable_risk_position_sizing", "Risk-Based Position Sizing", "sizing", "Use one affordable share instead of risk-budget sizing."),
)


def valid_toggle_names() -> set[str]:
    return {component.parameter for component in COMPONENTS}
