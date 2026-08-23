# STEP-2 Operational Risk Guard Policy

## Purpose
Operational risk guards exist strictly as software safety ceilings to prevent catastrophic execution or sizing bugs. They are NOT alpha tuning parameters or performance optimization ceilings.

## Defined Ceilings
1. `max_single_position_weight`: `0.20` (20% maximum single position weight)
2. `max_gross_exposure`: `1.10` (110% maximum gross exposure)
3. `max_order_notional`: `$100,000.00` (Maximum notional value for a single order intent)
4. `max_daily_order_count`: `50` (Maximum order intents per rebalance session)
5. `buying_power_guard`: Required `required_notional <= available_buying_power`

## Enforcement
Evaluated locally during portfolio and order intent generation before any broker interaction.
