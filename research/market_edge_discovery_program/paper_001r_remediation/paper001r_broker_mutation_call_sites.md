# PAPER-001R Broker Mutation Call-Site Audit

Audit result: no Alpaca broker mutation was executed during PAPER-001R.

## Alpaca adapter mutation-capable methods

| File | Function | Operation | Reachable from Paper controller? | Guarded? | Current execution eligibility |
|---|---|---|---|---|---|
| `engine/alpaca_broker_adapter.py` | `submit_order` | submit order | No | Raises `BrokerMutationDisabled` | Ineligible |
| `engine/alpaca_broker_adapter.py` | `replace_order` | replace order | No | Raises `BrokerMutationDisabled` | Ineligible |
| `engine/alpaca_broker_adapter.py` | `cancel_order` | cancel order | No | Raises `BrokerMutationDisabled` | Ineligible |

## Non-Alpaca strategy/backtrader methods

Several historical/backtest strategy files include functions named `close_position` or `_cancel_order_if_active`. These are Backtrader strategy methods and are not reachable from the PAPER-001R CSM x TSM Paper controller.

## PAPER-001R submission boundary

`PaperTradingController.run_dry_run` computes:

```text
submission_authorized =
    environment_is_paper
    AND TRADING_ENABLED
    AND PAPER_EXECUTION_ENABLED
    AND readiness_pass
    AND timing_valid
```

During PAPER-001R:

```text
TRADING_ENABLED = FALSE
PAPER_EXECUTION_ENABLED = FALSE
submission_authorized = FALSE
```
