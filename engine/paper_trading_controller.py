from __future__ import annotations

import csv
import importlib
import json
import os
import sys
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from engine.alpaca_broker_adapter import AlpacaBrokerAdapter, MarketSessionState, OrderIntent, parse_ny_market_time
from engine.paper_risk_guards import (
    EXPECTED_STRATEGY_HASH,
    EXPECTED_UNIVERSE_HASH,
    PaperRiskConfig,
    PaperSafetyManager,
    frozen_strategy_config,
)
from engine.security_identity_resolver import IdentityContinuityStatus, SecurityIdentityResolver


REPO_ROOT = Path(__file__).resolve().parents[1]
FUF_DIR = REPO_ROOT / "research" / "market_edge_discovery_program" / "fuf_001_free_exploratory_universe_freeze"
EXB003_DIR = REPO_ROOT / "research" / "market_edge_discovery_program" / "exb_003_frozen_250_backtest_preparation"
PAPER001R_DIR = REPO_ROOT / "research" / "market_edge_discovery_program" / "paper_001r_remediation"


@dataclass(frozen=True, slots=True)
class PaperControllerConfig:
    environment: str = "PAPER"
    paper_base_url: str = "https://paper-api.alpaca.markets"
    trading_enabled: bool = False
    paper_execution_enabled: bool = False
    strategy_id: str = "CSM001xTSM001"
    portfolio_id: str = "FUF001_FREE_US_EQUITY_250_V1"
    universe_id: str = "FUF001_FREE_US_EQUITY_250_V1"
    membership_path: Path = FUF_DIR / "fuf001_frozen_membership.csv"
    identity_registry_path: Path = FUF_DIR / "fuf001_identity_event_registry.csv"
    target_path: Path | None = None
    audit_log_path: Path = PAPER001R_DIR / "paper001r_audit_trail.csv"
    incident_log_path: Path = PAPER001R_DIR / "paper001r_incidents.csv"
    broker_audit_log_path: Path = PAPER001R_DIR / "paper001r_order_intent_audit.csv"
    max_intent_age_minutes: int = 60
    account_equity_fallback: float = 100000.0
    bar_lookback_calendar_days: int = 520
    data_feed: str = "iex"
    data_adjustment: str = "all"


@dataclass(slots=True)
class ControllerResult:
    paper_session_id: str
    rebalance_id: str
    environment: str
    calendar_state: str
    schedule_state: str
    freshness_state: str
    eligibility_state: str
    eligible_count: int
    csm_candidate_count: int
    tsm_approved_count: int
    target_holding_count: int
    position_reconciliation_state: str
    order_reconciliation_state: str
    generated_intent_count: int
    risk_state: str
    buying_power_state: str
    readiness_state: str
    health_state: str
    submission_authorized: bool
    block_reason: str
    broker_mutation_calls: int
    orders_submitted: int = 0
    orders_cancelled: int = 0
    orders_replaced: int = 0
    positions_closed: int = 0
    paper_t0_established: str = "NO"
    scientific_t0_established: str = "NO"
    strategy_hash: str = EXPECTED_STRATEGY_HASH
    universe_hash: str = EXPECTED_UNIVERSE_HASH
    incidents: list[str] = field(default_factory=list)
    target_symbols: list[str] = field(default_factory=list)
    client_order_ids: list[str] = field(default_factory=list)
    signal_data_source: str = "ALPACA_DAILY_BARS"
    signal_as_of_session: str = ""
    earliest_permitted_execution_session: str = ""
    execution_session: str = ""
    identity_readiness_state: str = "PASS"
    monthly_rebalance_due: bool = False
    next_legitimate_signal_session: str = ""
    earliest_legitimate_execution_session: str = ""
    frozen_universe_count: int = 0
    symbols_requested: int = 0
    symbols_received: int = 0
    fresh_symbol_count: int = 0
    stale_symbol_count: int = 0
    inactive_symbol_count: int = 0
    insufficient_history_count: int = 0
    target_weight_sum: float = 0.0
    position_count: int = 0
    open_order_count: int = 0


class PaperAuditTrail:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            with self.path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=self.fieldnames())
                writer.writeheader()

    @staticmethod
    def fieldnames() -> list[str]:
        return [
            "timestamp",
            "paper_session_id",
            "rebalance_id",
            "strategy_id",
            "strategy_hash",
            "universe_id",
            "universe_hash",
            "event_type",
            "component",
            "status",
            "message",
        ]

    def append(self, *, session_id: str, rebalance_id: str, config: PaperControllerConfig, event_type: str, component: str, status: str, message: str) -> None:
        with self.path.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=self.fieldnames())
            writer.writerow(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "paper_session_id": session_id,
                    "rebalance_id": rebalance_id,
                    "strategy_id": config.strategy_id,
                    "strategy_hash": EXPECTED_STRATEGY_HASH,
                    "universe_id": config.universe_id,
                    "universe_hash": EXPECTED_UNIVERSE_HASH,
                    "event_type": event_type,
                    "component": component,
                    "status": status,
                    "message": message,
                }
            )


class PaperIncidentLog:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            with self.path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=self.fieldnames())
                writer.writeheader()

    @staticmethod
    def fieldnames() -> list[str]:
        return ["timestamp", "paper_session_id", "severity", "component", "incident_type", "message", "action_taken", "resolved"]

    def append(self, *, session_id: str, severity: str, component: str, incident_type: str, message: str, action_taken: str, resolved: str = "NO") -> None:
        with self.path.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=self.fieldnames())
            writer.writerow(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "paper_session_id": session_id,
                    "severity": severity,
                    "component": component,
                    "incident_type": incident_type,
                    "message": message,
                    "action_taken": action_taken,
                    "resolved": resolved,
                }
            )


class PaperTradingController:
    def __init__(
        self,
        config: PaperControllerConfig | None = None,
        *,
        adapter: AlpacaBrokerAdapter | None = None,
        safety: PaperSafetyManager | None = None,
        resolver: SecurityIdentityResolver | None = None,
    ) -> None:
        self.config = config or PaperControllerConfig()
        self.safety = safety or PaperSafetyManager(PaperRiskConfig())
        self.audit = PaperAuditTrail(self.config.audit_log_path)
        self.incidents = PaperIncidentLog(self.config.incident_log_path)
        self.adapter = adapter
        self.identity_resolver = resolver or SecurityIdentityResolver(self.config.identity_registry_path)

    def run_dry_run(self, *, now: datetime | None = None) -> ControllerResult:
        now = now or datetime.now(timezone.utc)
        session_id = self.paper_session_id(now)
        rebalance_id = self.latest_rebalance_id()
        incident_types: list[str] = []

        def audit(event_type: str, component: str, status: str, message: str) -> None:
            self.audit.append(session_id=session_id, rebalance_id=rebalance_id, config=self.config, event_type=event_type, component=component, status=status, message=message)

        def incident(severity: str, component: str, incident_type: str, message: str, action: str) -> None:
            incident_types.append(incident_type)
            self.incidents.append(session_id=session_id, severity=severity, component=component, incident_type=incident_type, message=message, action_taken=action)
            audit("INCIDENT", component, incident_type, message)

        audit("SESSION_CREATED", "controller", "PASS", "Dry-run session created without PAPER_T0.")

        env_ok = self.config.environment == "PAPER" and self.safety.verify_environment(self.config.paper_base_url)
        if not env_ok:
            incident("CRITICAL", "environment", "PROTOCOL_VIOLATION", "Paper environment guard failed.", "BLOCK")

        universe_ok = self.safety.verify_universe_hash(self.config.membership_path)
        if not universe_ok:
            incident("CRITICAL", "universe", "UNIVERSE_HASH_MISMATCH", "Frozen universe hash or duplicate check failed.", "BLOCK")
        audit("READINESS_CHECK", "universe", "PASS" if universe_ok else "FAIL", "Canonical FUF hash checked.")

        strategy_ok = self.safety.verify_strategy_hash(frozen_strategy_config())
        if not strategy_ok:
            incident("CRITICAL", "strategy", "STRATEGY_HASH_MISMATCH", "Frozen strategy hash mismatch.", "BLOCK")
        audit("READINESS_CHECK", "strategy", "PASS" if strategy_ok else "FAIL", "Frozen strategy hash checked.")

        membership = self.load_membership()
        duplicate_members = self.duplicate_symbols(membership["symbol"].astype(str).tolist())
        if duplicate_members:
            incident("CRITICAL", "universe", "DUPLICATE_SYMBOL_DETECTED", ",".join(duplicate_members), "BLOCK")

        broker = self.adapter or AlpacaBrokerAdapter.from_environment(audit_log_path=self.config.broker_audit_log_path)
        calendar_status, calendar_payload = self.load_calendar(broker, now)
        signal_session = self.latest_completed_session(calendar_payload, now) if calendar_status == "PASS" else None
        if signal_session is None:
            incident("HIGH", "calendar", "SCHEDULER_FAILURE", calendar_status, "BLOCK")
        rebalance_id = signal_session or rebalance_id

        earliest_permitted_session = self.earliest_permitted_execution_session(calendar_payload, signal_session) if calendar_status == "PASS" and signal_session else None
        execution_session = self.current_or_next_execution_session(calendar_payload, now) if calendar_status == "PASS" else None

        resolutions = self.identity_resolver.resolve_universe(membership, signal_session or "", broker=broker)
        audit("IDENTITY_RESOLUTION", "identity_resolver", "PASS", f"registry_hash={self.identity_resolver.registry_hash()[:16]};resolved_count={len(resolutions)}")

        signal_result = self.build_current_signal_target(
            broker,
            membership,
            signal_session,
            now=now,
            resolutions=resolutions,
            calendar_payload=calendar_payload if calendar_status == "PASS" else None,
        )
        for err in signal_result["errors"]:
            incident("CRITICAL", "signal_pipeline", err, "Current signal pipeline failed.", "BLOCK")

        target_check = signal_result
        for err in target_check["errors"]:
            incident("CRITICAL", "target_portfolio", err, "Target portfolio invariant failed.", "BLOCK")

        calendar_state, session_state = self.calendar_state_from_payload(calendar_status, calendar_payload, broker, now)
        if calendar_state != "PASS":
            incident("HIGH", "calendar", "SCHEDULER_FAILURE", calendar_state, "BLOCK")
        audit("SCHEDULE_CHECK", "calendar", calendar_state, f"session={session_state.value}")

        freshness_state = "PASS" if target_check["stale_symbol_count"] == 0 and "MARKET_DATA_FAILURE" not in target_check["errors"] and "BLOCK_IDENTITY_MISMATCH" not in target_check["errors"] and "BLOCK_IDENTITY_CONTINUITY_UNRESOLVED" not in target_check["errors"] and "BLOCK_CORPORATE_ACTION_UNRESOLVED" not in target_check["errors"] and "BLOCK_PRICE_SERIES_CONTINUITY" not in target_check["errors"] else "FAIL"
        audit("DATA_FRESHNESS_CHECK", "alpaca_daily_bars", freshness_state, f"fresh={target_check['fresh_symbol_count']};stale={target_check['stale_symbol_count']};inactive={target_check.get('inactive_symbol_count', 0)}")
        if freshness_state != "PASS":
            incident("HIGH", "freshness", "STALE_DATA", "Target snapshot failed integrity checks.", "BLOCK")

        eligible_count = int(target_check["eligible_count"])
        eligibility_state = "PASS" if eligible_count >= 50 else "REBALANCE_BLOCKED_INSUFFICIENT_ELIGIBILITY"
        audit("ELIGIBILITY_CHECK", "csm", eligibility_state, f"eligible_count={eligible_count}")
        if eligibility_state != "PASS":
            incident("CRITICAL", "eligibility", "ELIGIBILITY_FAILURE", f"eligible_count={eligible_count}", "BLOCK")

        current_positions_status, current_positions = broker.get_positions()
        open_orders_status, open_orders = broker.get_open_orders()
        account_status, account = broker.get_account()
        if account_status != "PASS":
            incident("HIGH", "broker", "AUTH_FAILURE", f"account_status={account_status}", "BLOCK")
        if current_positions_status != "PASS":
            incident("HIGH", "broker", "POSITION_MISMATCH", f"positions_status={current_positions_status}", "BLOCK")
        if open_orders_status != "PASS":
            incident("HIGH", "broker", "ORDER_MISMATCH", f"orders_status={open_orders_status}", "BLOCK")

        target_weights = target_check["target_weights"]
        target_symbols = sorted([symbol for symbol, weight in target_weights.items() if weight > 0])
        internal_positions = {symbol: 0.0 for symbol in target_symbols}
        position_recon = broker.reconcile_positions(internal_positions, current_positions if isinstance(current_positions, list) else [])
        position_state = "PASS" if all(state in {"MATCH", "MISSING_BROKER"} for state in position_recon.values()) else "BLOCK"
        audit("RECONCILIATION_CHECK", "positions", position_state, json.dumps(position_recon, sort_keys=True))
        if position_state != "PASS":
            incident("HIGH", "reconciliation", "POSITION_MISMATCH", "Unexpected broker position state.", "BLOCK")

        equity = self.account_equity(account)
        latest_prices = target_check["latest_prices"]
        intents = self.build_order_intents(broker, target_weights, latest_prices, rebalance_id, now, resolutions=resolutions)
        order_recon = broker.reconcile_orders(intents, open_orders if isinstance(open_orders, list) else [])
        order_state = "PASS" if all(state == "INTENT_ONLY" for state in order_recon.values()) else "BLOCK"
        audit("RECONCILIATION_CHECK", "orders", order_state, json.dumps(order_recon, sort_keys=True))
        if order_state != "PASS":
            incident("HIGH", "reconciliation", "ORDER_MISMATCH", "Existing broker order conflicts with generated intents.", "BLOCK")

        validations = [
            broker.validate_order_intent(
                intent,
                asset={"status": "active", "tradable": True},
                market_session_state=MarketSessionState.PRE_OPEN if session_state == MarketSessionState.PRE_OPEN else MarketSessionState.MARKET_OPEN,
                now=now,
            )
            for intent in intents
        ]
        bad_validations = [v for v in validations if v.errors and "TRADING_ENABLED_NOT_ALLOWED_IN_ALP003" not in v.errors]
        if bad_validations:
            incident("HIGH", "order_intent", "DUPLICATE_INTENT", "One or more intents failed validation.", "BLOCK")
        audit("ORDER_INTENTS_CREATED", "order_intent", "PASS" if not bad_validations else "FAIL", f"count={len(intents)}")

        notionals = [max(0.0, weight * equity) for weight in target_weights.values()]
        risk_result = self.safety.check_risk_guards(target_weights, notionals, len(intents))
        risk_state = "PASS" if risk_result.passed else "BLOCK"
        audit("RISK_GUARD_CHECK", "risk", risk_state, ",".join(risk_result.errors))
        if not risk_result.passed:
            incident("HIGH", "risk", "PROTOCOL_VIOLATION", ",".join(risk_result.errors), "BLOCK")

        required_notional = sum(notionals)
        buying_power = self.account_buying_power(account)
        buying_power_ok = self.safety.check_buying_power(required_notional, buying_power)
        buying_power_state = "PASS" if buying_power_ok else "BLOCK"
        audit("RISK_GUARD_CHECK", "buying_power", buying_power_state, f"required={required_notional:.2f};available={buying_power:.2f}")
        if not buying_power_ok:
            incident("HIGH", "risk", "BROKER_TIMEOUT", "Aggregate buying power check failed.", "BLOCK")

        session_open_or_pre_open = session_state in {MarketSessionState.PRE_OPEN, MarketSessionState.MARKET_OPEN}
        timing_t_plus_1_ok = bool(
            execution_session
            and earliest_permitted_session
            and signal_session
            and execution_session >= earliest_permitted_session
            and execution_session > signal_session
        )
        if not timing_t_plus_1_ok:
            incident("CRITICAL", "timing", "T_PLUS_1_TIMING_VIOLATION", f"signal={signal_session};earliest={earliest_permitted_session};execution={execution_session}", "BLOCK")
        if not session_open_or_pre_open:
            incident("MEDIUM", "timing", "SCHEDULER_FAILURE", f"session={session_state.value}", "DRY_RUN_BLOCK")
        timing_valid = session_open_or_pre_open and timing_t_plus_1_ok
        schedule_state = "PASS" if timing_valid else "BLOCKED_TIMING"

        identity_readiness_state = "PASS" if freshness_state == "PASS" and not any(
            err in target_check["errors"] for err in [
                "BLOCK_IDENTITY_MISMATCH",
                "BLOCK_IDENTITY_CONTINUITY_UNRESOLVED",
                "BLOCK_CORPORATE_ACTION_UNRESOLVED",
                "BLOCK_PRICE_SERIES_CONTINUITY",
            ]
        ) else "FAIL"

        monthly_rebalance_due = self.is_monthly_rebalance_signal_session(calendar_payload, signal_session or "") if calendar_status == "PASS" else False
        next_legit_signal = self.next_legitimate_signal_session(calendar_payload, signal_session or "", now) if calendar_status == "PASS" else (signal_session or "")
        earliest_legit_exec = self.earliest_permitted_execution_session(calendar_payload, next_legit_signal) or "" if calendar_status == "PASS" else ""

        readiness_ok = all(
            [
                env_ok,
                universe_ok,
                strategy_ok,
                not duplicate_members,
                not target_check["errors"],
                calendar_state == "PASS",
                timing_t_plus_1_ok,
                freshness_state == "PASS",
                eligibility_state == "PASS",
                account_status == "PASS",
                position_state == "PASS",
                order_state == "PASS",
                not bad_validations,
                risk_result.passed,
                buying_power_ok,
            ]
        )

        submission_authorized = bool(
            readiness_ok
            and monthly_rebalance_due
            and timing_valid
            and self.safety.execution_flags_authorize(self.config.trading_enabled, self.config.paper_execution_enabled, self.config.environment)
        )

        if not readiness_ok:
            readiness_state = "BLOCKED"
            block_reason = "BLOCKED_BY_GUARDS"
        elif not monthly_rebalance_due:
            readiness_state = "WAITING_FOR_SCHEDULED_REBALANCE"
            block_reason = "WAITING_FOR_SCHEDULED_MONTHLY_REBALANCE"
        else:
            readiness_state = "READY_FOR_CONTROLLED_PAPER_LAUNCH"
            block_reason = "DRY_RUN_BLOCK_EXECUTION_FLAGS_FALSE" if not submission_authorized else "NONE"

        audit("DRY_RUN_BLOCK", "submission_boundary", "BLOCKED" if not submission_authorized else "AUTHORIZED", block_reason)

        return ControllerResult(
            paper_session_id=session_id,
            rebalance_id=rebalance_id,
            environment=self.config.environment,
            calendar_state=calendar_state,
            schedule_state=schedule_state,
            freshness_state=freshness_state,
            eligibility_state=eligibility_state,
            eligible_count=eligible_count,
            csm_candidate_count=int(target_check["csm_candidate_count"]),
            tsm_approved_count=int(target_check["tsm_approved_count"]),
            target_holding_count=int(target_check["target_holding_count"]),
            position_reconciliation_state=position_state,
            order_reconciliation_state=order_state,
            generated_intent_count=len(intents),
            risk_state=risk_state,
            buying_power_state=buying_power_state,
            readiness_state=readiness_state,
            health_state="HEALTHY" if readiness_ok else "BLOCKED",
            submission_authorized=submission_authorized,
            block_reason=block_reason,
            broker_mutation_calls=broker.broker_mutation_calls,
            incidents=incident_types,
            target_symbols=target_symbols,
            client_order_ids=[intent.client_order_id for intent in intents],
            signal_as_of_session=signal_session or "",
            earliest_permitted_execution_session=earliest_permitted_session or "",
            execution_session=execution_session or "",
            identity_readiness_state=identity_readiness_state,
            monthly_rebalance_due=monthly_rebalance_due,
            next_legitimate_signal_session=next_legit_signal,
            earliest_legitimate_execution_session=earliest_legit_exec,
            frozen_universe_count=len(membership),
            symbols_requested=int(target_check["symbols_requested"]),
            symbols_received=int(target_check["symbols_received"]),
            fresh_symbol_count=int(target_check["fresh_symbol_count"]),
            stale_symbol_count=int(target_check["stale_symbol_count"]),
            inactive_symbol_count=int(target_check.get("inactive_symbol_count", 0)),
            insufficient_history_count=int(target_check["insufficient_history_count"]),
            target_weight_sum=float(target_check["target_weight_sum"]),
            position_count=len(current_positions) if isinstance(current_positions, list) else 0,
            open_order_count=len(open_orders) if isinstance(open_orders, list) else 0,
        )

    def paper_session_id(self, now: datetime) -> str:
        return f"PAPER-{now.astimezone(timezone.utc).date().isoformat()}-DRYRUN"

    def latest_rebalance_id(self) -> str:
        if self.config.target_path and self.config.target_path.exists():
            target = pd.read_csv(self.config.target_path, usecols=["signal_date"])
            return str(pd.to_datetime(target["signal_date"]).max().date().isoformat())
        return date.today().isoformat()

    def load_membership(self) -> pd.DataFrame:
        frame = pd.read_csv(self.config.membership_path)
        if len(frame) != 250:
            raise RuntimeError("UNIVERSE_SIZE_MISMATCH")
        return frame

    def load_target_frame(self) -> pd.DataFrame:
        if self.config.target_path is None:
            raise RuntimeError("SNAPSHOT_TARGET_DISABLED_IN_PRODUCTION")
        frame = pd.read_csv(self.config.target_path)
        required = {"signal_date", "symbol", "target_weight", "selected"}
        if missing := required - set(frame.columns):
            raise RuntimeError(f"TARGET_MISSING_COLUMNS:{','.join(sorted(missing))}")
        frame["signal_date"] = pd.to_datetime(frame["signal_date"]).dt.date.astype(str)
        frame["symbol"] = frame["symbol"].astype(str).str.upper()
        frame["target_weight"] = pd.to_numeric(frame["target_weight"], errors="coerce")
        frame["selected"] = frame["selected"].astype(bool)
        return frame

    def load_calendar(self, broker: AlpacaBrokerAdapter, now: datetime) -> tuple[str, Any]:
        start = (now.date() - timedelta(days=30)).isoformat()
        end = (now.date() + timedelta(days=45)).isoformat()
        return broker.get_calendar(start, end)

    def latest_completed_session(self, calendar_payload: Any, now: datetime) -> str | None:
        if not isinstance(calendar_payload, list):
            return None
        rows = sorted(calendar_payload, key=lambda item: str(item.get("date")))
        completed: list[str] = []
        for row in rows:
            try:
                close_time = parse_ny_market_time(str(row["date"]), str(row["close"]))
            except Exception:
                continue
            if close_time <= now:
                completed.append(str(row["date"]))
        return completed[-1] if completed else None

    def earliest_permitted_execution_session(self, calendar_payload: Any, signal_session: str) -> str | None:
        if not isinstance(calendar_payload, list) or not signal_session:
            return None
        rows = sorted(calendar_payload, key=lambda item: str(item.get("date")))
        for row in rows:
            row_date = str(row.get("date"))
            if row_date > signal_session:
                return row_date
        return None

    def current_or_next_execution_session(self, calendar_payload: Any, now: datetime) -> str | None:
        if not isinstance(calendar_payload, list):
            return None
        current_date = now.date().isoformat()
        row = next((item for item in calendar_payload if str(item.get("date")) == current_date), None)
        if row is not None:
            try:
                close_time = parse_ny_market_time(str(row["date"]), str(row["close"]))
                if now <= close_time:
                    return current_date
            except Exception:
                pass
        rows = sorted(calendar_payload, key=lambda item: str(item.get("date")))
        for item in rows:
            item_date = str(item.get("date"))
            if item_date > current_date:
                return item_date
        return None

    def is_monthly_rebalance_signal_session(self, calendar_payload: Any, signal_session: str) -> bool:
        if not isinstance(calendar_payload, list) or not signal_session:
            return False
        month_prefix = signal_session[:7]
        month_sessions = [str(row["date"]) for row in calendar_payload if str(row.get("date", "")).startswith(month_prefix)]
        if not month_sessions:
            return False
        return signal_session == max(month_sessions)

    def next_legitimate_signal_session(self, calendar_payload: Any, signal_session: str, now: datetime) -> str:
        if not isinstance(calendar_payload, list) or not signal_session:
            return signal_session or ""
        current_month = now.date().isoformat()[:7]
        current_month_sessions = [str(row["date"]) for row in calendar_payload if str(row.get("date", "")).startswith(current_month)]
        if current_month_sessions:
            last_day = max(current_month_sessions)
            if signal_session < last_day:
                return last_day
        all_dates = sorted([str(row["date"]) for row in calendar_payload])
        future_dates = [d for d in all_dates if d > signal_session]
        if not future_dates:
            return signal_session
        months = sorted(list({d[:7] for d in future_dates}))
        next_month = months[0]
        next_sessions = [d for d in all_dates if d.startswith(next_month)]
        return max(next_sessions) if next_sessions else signal_session

    def build_current_signal_target(
        self,
        broker: AlpacaBrokerAdapter,
        membership: pd.DataFrame,
        signal_session: str | None,
        *,
        now: datetime | None = None,
        resolutions: dict[str, Any] | None = None,
        calendar_payload: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        errors: list[str] = []
        symbols = membership.sort_values("selection_order")["symbol"].astype(str).str.upper().tolist()
        if self.duplicate_symbols(symbols):
            errors.append("DUPLICATE_SYMBOL_DETECTED")
        if signal_session is None:
            errors.append("SCHEDULER_FAILURE")
            return self.empty_signal_result(errors, len(symbols))

        if resolutions is None:
            resolutions = self.identity_resolver.resolve_universe(membership, signal_session, broker=broker)

        for sym, res in resolutions.items():
            if not res.resolved and res.block_reason:
                errors.append(res.block_reason)

        requested_symbols = sorted(list({s for res in resolutions.values() for s in res.data_symbols_required}))
        start = (pd.Timestamp(signal_session) - pd.Timedelta(days=self.config.bar_lookback_calendar_days)).date().isoformat()
        end = (pd.Timestamp(signal_session) + pd.Timedelta(days=1)).date().isoformat()
        status, payload = self.fetch_daily_bars(broker, requested_symbols, start, end)
        if status != "PASS":
            errors.append("MARKET_DATA_FAILURE")
            return self.empty_signal_result(errors, len(symbols))
        bars = self.parse_bar_payload(payload)
        if bars.empty:
            errors.append("MARKET_DATA_FAILURE")
            return self.empty_signal_result(errors, len(symbols))

        duplicate_bar_count = int(bars.duplicated(["symbol", "date"]).sum())
        if duplicate_bar_count:
            errors.append("DUPLICATE_BAR")
            bars = bars.drop_duplicates(["symbol", "date"], keep="last")
        now = now or datetime.now(timezone.utc)
        true_future_count = int((pd.to_datetime(bars["date"]).dt.date > now.date()).sum())
        if true_future_count:
            errors.append("FUTURE_BAR")
        bars = bars[pd.to_datetime(bars["date"]) <= pd.Timestamp(signal_session)]

        logical_series_list: list[pd.DataFrame] = []
        fresh_symbols: list[str] = []
        stale_symbols: list[str] = []
        inactive_symbols: list[str] = []
        logical_latest_by_symbol: dict[str, str] = {}
        latest_prices: dict[str, float] = {}

        for symbol in symbols:
            res = resolutions[symbol]
            stitch_status, member_bars = self.identity_resolver.stitch_price_series(bars, res, signal_session, calendar_payload=calendar_payload)
            if stitch_status != "PASS":
                errors.append(stitch_status)
                continue
            if member_bars.empty:
                if res.continuity_status == IdentityContinuityStatus.VERIFIED_DISCONTINUITY.value:
                    inactive_symbols.append(symbol)
                else:
                    stale_symbols.append(symbol)
                continue
            logical_series_list.append(member_bars)
            latest_bar_date = str(member_bars["date"].max())
            logical_latest_by_symbol[symbol] = latest_bar_date

            if latest_bar_date == signal_session:
                fresh_symbols.append(symbol)
                latest_close = float(member_bars[member_bars["date"] == signal_session]["close"].iloc[-1])
                latest_prices[symbol] = latest_close
            else:
                if res.continuity_status == IdentityContinuityStatus.VERIFIED_DISCONTINUITY.value:
                    inactive_symbols.append(symbol)
                else:
                    stale_symbols.append(symbol)

        if stale_symbols:
            errors.append("STALE_DATA")

        if not logical_series_list:
            errors.append("MARKET_DATA_FAILURE")
            return self.empty_signal_result(errors, len(symbols))

        logical_bars = pd.concat(logical_series_list, ignore_index=True)
        close_panel = logical_bars.pivot(index="date", columns="symbol", values="close").sort_index()
        close_panel.index = pd.to_datetime(close_panel.index)
        close_panel = close_panel.reindex(symbols, axis=1)

        CSM001MomentumModel, TSM001MomentumModel = self.import_frozen_models()
        csm = CSM001MomentumModel().transform(close_panel.reindex(symbols, axis=1)).frame.copy()
        tsm = TSM001MomentumModel().transform(close_panel.reindex(symbols, axis=1)).frame.copy()
        csm["date"] = pd.to_datetime(csm["date"]).dt.date.astype(str)
        tsm["date"] = pd.to_datetime(tsm["date"]).dt.date.astype(str)
        csm_now = csm[csm["date"] == signal_session].copy()
        tsm_now = tsm[tsm["date"] == signal_session].copy()
        state = csm_now.merge(tsm_now[["date", "ticker", "tsm001_state", "tsm001_positive_state"]], on=["date", "ticker"], how="inner")
        if state.empty:
            errors.append("MARKET_DATA_FAILURE")
            return self.empty_signal_result(errors, len(symbols))
        invariant_fail = state[state["csm001_valid_observation"] & (state["csm001_top_decile_flag"] != state["csm001_momentum_score"].ge(0.90))]
        if len(invariant_fail):
            errors.append("CSM_THRESHOLD_INVARIANT_FAILURE")
        eligible = state[state["csm001_valid_observation"]]
        eligible_count = int(state["csm001_eligible_count"].max()) if not state["csm001_eligible_count"].dropna().empty else 0
        insufficient_history_count = int(len(symbols) - len(eligible))
        selected = state[(state["csm001_top_decile_flag"]) & (state["tsm001_positive_state"])].copy()
        selected_symbols = sorted(selected["ticker"].astype(str).tolist())
        if self.duplicate_symbols(selected_symbols):
            errors.append("DUPLICATE_TARGET_SYMBOL")
        weight = 1.0 / len(selected_symbols) if selected_symbols else 0.0
        target_weights = {symbol: weight for symbol in selected_symbols}
        target_weight_sum = sum(target_weights.values())
        latest_by_series = pd.Series(logical_latest_by_symbol)
        self.write_signal_snapshot(state, target_weights, latest_by_series, signal_session, inactive_symbols=inactive_symbols)
        return {
            "errors": errors,
            "eligible_count": eligible_count,
            "csm_candidate_count": int(state["csm001_top_decile_flag"].sum()),
            "tsm_approved_count": len(selected_symbols),
            "target_holding_count": len(target_weights),
            "target_weights": target_weights,
            "symbols_requested": len(requested_symbols),
            "symbols_received": len(logical_latest_by_symbol),
            "fresh_symbol_count": len(fresh_symbols),
            "stale_symbol_count": len(stale_symbols),
            "inactive_symbol_count": len(inactive_symbols),
            "insufficient_history_count": insufficient_history_count,
            "target_weight_sum": target_weight_sum,
            "latest_prices": latest_prices,
            "resolutions": resolutions,
        }

    def empty_signal_result(self, errors: list[str], requested: int) -> dict[str, Any]:
        return {
            "errors": errors,
            "eligible_count": 0,
            "csm_candidate_count": 0,
            "tsm_approved_count": 0,
            "target_holding_count": 0,
            "target_weights": {},
            "symbols_requested": requested,
            "symbols_received": 0,
            "fresh_symbol_count": 0,
            "stale_symbol_count": requested,
            "inactive_symbol_count": 0,
            "insufficient_history_count": requested,
            "target_weight_sum": 0.0,
            "latest_prices": {},
        }

    def fetch_daily_bars(self, broker: AlpacaBrokerAdapter, symbols: list[str], start: str, end: str) -> tuple[str, Any]:
        combined: dict[str, list[dict[str, Any]]] = {}
        batch_size = 20
        for offset in range(0, len(symbols), batch_size):
            batch = symbols[offset : offset + batch_size]
            status, payload = broker.get_daily_bars(batch, start, end, feed=self.config.data_feed, adjustment=self.config.data_adjustment)
            if status != "PASS":
                return status, payload
            raw = payload.get("bars", {}) if isinstance(payload, dict) else {}
            if not isinstance(raw, dict):
                return "MARKET_DATA_MALFORMED", payload
            for symbol, rows in raw.items():
                normalized = str(symbol).upper()
                combined.setdefault(normalized, []).extend(rows or [])
        return "PASS", {"bars": combined}

    def parse_bar_payload(self, payload: Any) -> pd.DataFrame:
        rows: list[dict[str, Any]] = []
        raw = payload.get("bars", {}) if isinstance(payload, dict) else {}
        if isinstance(raw, dict):
            for symbol, bars in raw.items():
                for bar in bars or []:
                    rows.append({"symbol": str(symbol).upper(), "date": str(bar.get("t", ""))[:10], "close": float(bar.get("c", float("nan"))), "volume": float(bar.get("v", 0) or 0)})
        return pd.DataFrame(rows, columns=["symbol", "date", "close", "volume"]).dropna(subset=["symbol", "date", "close"])

    def import_frozen_models(self):
        csm_dir = REPO_ROOT / "research" / "implementations" / "csm_001"
        tsm_dir = REPO_ROOT / "research" / "implementations" / "tsm_001"
        sys.modules.pop("csm001_momentum_model", None)
        sys.modules.pop("tsm001_momentum_model", None)
        sys.modules.pop("feature_pipeline", None)
        sys.path.insert(0, str(csm_dir))
        csm_module = importlib.import_module("csm001_momentum_model")
        CSM001MomentumModel = csm_module.CSM001MomentumModel
        sys.path.pop(0)
        sys.modules.pop("feature_pipeline", None)
        sys.modules.pop("tsm001_momentum_model", None)
        sys.path.insert(0, str(tsm_dir))
        tsm_module = importlib.import_module("tsm001_momentum_model")
        TSM001MomentumModel = tsm_module.TSM001MomentumModel
        sys.path.pop(0)
        sys.modules.pop("feature_pipeline", None)
        return CSM001MomentumModel, TSM001MomentumModel

    def write_signal_snapshot(self, state: pd.DataFrame, target_weights: dict[str, float], latest_by_symbol: pd.Series, signal_session: str, inactive_symbols: list[str] | None = None) -> None:
        PAPER001R_DIR.mkdir(parents=True, exist_ok=True)
        snap = state.copy()
        snap["latest_bar_session"] = snap["ticker"].map(latest_by_symbol).fillna("")
        inactive_set = set(inactive_symbols or [])

        def classify_freshness(row: Any) -> str:
            if row["latest_bar_session"] == signal_session:
                return "FRESH"
            if row["symbol"] in inactive_set:
                return "INACTIVE_NON_TRADING"
            return "STALE_BAR"

        snap_sym = snap.rename(columns={"ticker": "symbol"})
        snap["freshness_state"] = snap_sym.apply(classify_freshness, axis=1)
        snap["eligibility_state"] = snap["csm001_valid_observation"].map({True: "ELIGIBLE", False: "INSUFFICIENT_HISTORY"})
        snap["csm_candidate"] = snap["csm001_top_decile_flag"].astype(bool)
        snap["tsm_approved"] = snap["tsm001_positive_state"].astype(bool)
        snap["target_weight"] = snap["ticker"].map(target_weights).fillna(0.0)
        cols = ["ticker", "latest_bar_session", "freshness_state", "eligibility_state", "return_12_1", "csm001_momentum_score", "csm_candidate", "tsm001_state", "tsm_approved", "target_weight"]
        snap[cols].rename(columns={"ticker": "symbol", "csm001_momentum_score": "csm_rank"}).to_csv(PAPER001R_DIR / "paper001r_current_signal_snapshot.csv", index=False)

    @staticmethod
    def duplicate_symbols(symbols: list[str]) -> list[str]:
        seen: set[str] = set()
        duplicates: set[str] = set()
        for symbol in [s.upper() for s in symbols]:
            if symbol in seen:
                duplicates.add(symbol)
            seen.add(symbol)
        return sorted(duplicates)

    def validate_target_frame(self, target: pd.DataFrame, rebalance_id: str) -> dict[str, Any]:
        rows = target[target["signal_date"] == rebalance_id].copy()
        errors: list[str] = []
        duplicate_symbols = self.duplicate_symbols(rows["symbol"].tolist())
        if duplicate_symbols:
            errors.append("DUPLICATE_TARGET_SYMBOL")
        selected = rows[rows["selected"]]
        nonzero = rows[rows["target_weight"] > 0]
        noncandidate_nonzero = rows[(~rows["selected"]) & (rows["target_weight"] != 0)]
        if len(noncandidate_nonzero):
            errors.append("NON_CANDIDATE_TARGET_WEIGHT")
        if len(nonzero) != len(selected):
            errors.append("NONZERO_TARGET_COUNT_MISMATCH")
        target_sum = float(rows["target_weight"].sum())
        if len(nonzero) and abs(target_sum - 1.0) > 1e-9:
            errors.append("TARGET_WEIGHT_SUM_INVALID")
        if not len(nonzero) and abs(target_sum) > 1e-9:
            errors.append("ZERO_CANDIDATE_NOT_CASH")
        weights = {str(row.symbol): float(row.target_weight) for row in rows.itertuples() if float(row.target_weight) > 0}
        return {
            "errors": errors,
            "eligible_count": len(rows),
            "csm_candidate_count": len(selected),
            "tsm_approved_count": len(selected),
            "target_holding_count": len(nonzero),
            "target_weights": weights,
        }

    def calendar_state_from_payload(self, status: str, payload: Any, broker: AlpacaBrokerAdapter, now: datetime) -> tuple[str, MarketSessionState]:
        if status != "PASS" or not isinstance(payload, list):
            return status, MarketSessionState.UNKNOWN
        return "PASS", broker.market_session_from_calendar(payload, now)

    def latest_reference_prices(self, target: pd.DataFrame) -> dict[str, float]:
        latest = target[target["signal_date"] == self.latest_rebalance_id()]
        return {row.symbol: 100.0 for row in latest.itertuples()}

    def build_order_intents(
        self,
        broker: AlpacaBrokerAdapter,
        target_weights: dict[str, float],
        latest_prices: dict[str, float],
        rebalance_id: str,
        now: datetime,
        resolutions: dict[str, Any] | None = None,
    ) -> list[OrderIntent]:
        intents: list[OrderIntent] = []
        for sequence, symbol in enumerate(sorted(target_weights), start=1):
            weight = target_weights[symbol]
            notional = max(1.0, round(weight * self.config.account_equity_fallback, 2))
            res = resolutions.get(symbol) if resolutions else None
            runtime_symbol = res.runtime_symbol if res else symbol
            runtime_asset_id = res.runtime_asset_id if res else symbol
            intents.append(
                broker.build_order_intent(
                    strategy_id=self.config.strategy_id,
                    portfolio_id=self.config.portfolio_id,
                    rebalance_id=rebalance_id,
                    symbol=runtime_symbol,
                    source_asset_id=runtime_asset_id,
                    side="buy",
                    quantity=None,
                    notional=notional,
                    order_type="market",
                    time_in_force="day",
                    reference_price=latest_prices.get(symbol, 100.0),
                    signal_timestamp=now.isoformat(),
                    reason="PAPER001R_DRY_RUN_TARGET_DELTA",
                    sequence=sequence,
                )
            )
        return intents

    def account_equity(self, account: Any) -> float:
        if isinstance(account, dict):
            for key in ("equity", "portfolio_value", "cash"):
                try:
                    return float(account.get(key))
                except (TypeError, ValueError):
                    continue
        return self.config.account_equity_fallback

    def account_buying_power(self, account: Any) -> float:
        if isinstance(account, dict):
            try:
                return float(account.get("buying_power"))
            except (TypeError, ValueError):
                return 0.0
        return 0.0


def result_to_dict(result: ControllerResult) -> dict[str, Any]:
    return asdict(result)


def env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}
