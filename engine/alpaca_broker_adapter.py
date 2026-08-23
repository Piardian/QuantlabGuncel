from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class BrokerMode(str, Enum):
    DRY_RUN = "DRY_RUN"


class MarketSessionState(str, Enum):
    MARKET_OPEN = "MARKET_OPEN"
    MARKET_CLOSED = "MARKET_CLOSED"
    HOLIDAY = "HOLIDAY"
    PRE_OPEN = "PRE_OPEN"
    POST_CLOSE = "POST_CLOSE"
    UNKNOWN = "UNKNOWN"


class ValidationStatus(str, Enum):
    CREATED = "CREATED"
    VALIDATED = "VALIDATED"
    BROKER_ELIGIBLE = "BROKER_ELIGIBLE"
    SUBMISSION_BLOCKED_ALP003 = "SUBMISSION_BLOCKED_ALP003"
    REJECTED_DUPLICATE = "REJECTED_DUPLICATE"
    REJECTED_INVALID = "REJECTED_INVALID"
    REJECTED_STALE_INTENT = "REJECTED_STALE_INTENT"
    REJECTED_MARKET_SESSION = "REJECTED_MARKET_SESSION"
    REJECTED_KILL_SWITCH = "REJECTED_KILL_SWITCH"


class ReconciliationState(str, Enum):
    MATCH = "MATCH"
    MISSING_INTERNAL = "MISSING_INTERNAL"
    MISSING_BROKER = "MISSING_BROKER"
    QUANTITY_MISMATCH = "QUANTITY_MISMATCH"
    SYMBOL_MISMATCH = "SYMBOL_MISMATCH"
    INTENT_ONLY = "INTENT_ONLY"
    BROKER_ACCEPTED = "BROKER_ACCEPTED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    UNKNOWN = "UNKNOWN"


class BrokerMutationDisabled(RuntimeError):
    pass


@dataclass(slots=True)
class RiskGuardConfig:
    max_order_notional: float | None = None
    max_position_notional: float | None = None
    max_gross_exposure: float | None = None
    max_number_positions: int | None = None
    buying_power_guard: bool = True
    duplicate_order_guard: bool = True
    market_session_guard: bool = True
    kill_switch: bool = True


@dataclass(slots=True)
class OrderIntent:
    intent_id: str
    strategy_id: str
    portfolio_id: str
    rebalance_id: str
    symbol: str
    source_asset_id: str
    side: str
    quantity: float | None
    notional: float | None
    order_type: str
    time_in_force: str
    reference_price: float
    signal_timestamp: str
    intent_created_at: str
    client_order_id: str
    reason: str
    status: str = ValidationStatus.CREATED.value
    sequence: int = 1


@dataclass(slots=True)
class ValidationResult:
    intent_id: str
    client_order_id: str
    status: str
    errors: list[str] = field(default_factory=list)


@dataclass(slots=True)
class AuditEvent:
    timestamp: str
    intent_id: str
    client_order_id: str
    symbol: str
    side: str
    quantity: float | None
    notional: float | None
    validation_result: str
    broker_mode: str
    reconciliation_state: str
    error_code: str


def load_local_env(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


class AlpacaReadOnlyTransport:
    def __init__(self, paper_base_url: str, data_base_url: str, key_id: str, secret_key: str) -> None:
        self.paper_base_url = paper_base_url.rstrip("/")
        self.data_base_url = data_base_url.rstrip("/")
        self.headers = {
            "APCA-API-KEY-ID": key_id,
            "APCA-API-SECRET-KEY": secret_key,
            "Accept": "application/json",
        }

    def get_json(self, base_url: str, path: str, params: dict[str, Any] | None = None) -> tuple[str, Any]:
        query = f"?{urlencode(params, doseq=True)}" if params else ""
        request = Request(f"{base_url}{path}{query}", headers=self.headers, method="GET")
        for attempt in range(1, 4):
            try:
                with urlopen(request, timeout=30) as response:
                    body = response.read().decode("utf-8")
                    return "PASS", json.loads(body) if body else None
            except HTTPError as exc:
                if exc.code in {401, 403, 404}:
                    return f"HTTP_{exc.code}", {"error": exc.reason}
                if exc.code == 429 and attempt < 3:
                    time.sleep(attempt)
                    continue
                return f"HTTP_{exc.code}", {"error": exc.reason}
            except (URLError, TimeoutError) as exc:
                if attempt < 3:
                    time.sleep(attempt)
                    continue
                return "NETWORK_FAIL", {"error": str(exc)}
        return "FAIL", {"error": "unreachable"}


class AlpacaBrokerAdapter:
    """Dry-run Alpaca Paper adapter for canonical order intents.

    ALP-003 intentionally blocks every mutation method. Only GET/read and local
    payload construction/validation/reconciliation are supported.
    """

    CLIENT_ORDER_ID_MAX_LEN = 48

    def __init__(
        self,
        *,
        paper_base_url: str,
        data_base_url: str,
        key_id: str,
        secret_key: str,
        broker_mode: BrokerMode = BrokerMode.DRY_RUN,
        trading_enabled: bool = False,
        max_intent_age_minutes: int = 60,
        audit_log_path: Path | None = None,
    ) -> None:
        if paper_base_url.rstrip("/") != "https://paper-api.alpaca.markets":
            raise ValueError("ALP-003 requires Alpaca PAPER environment")
        self.paper_base_url = paper_base_url.rstrip("/")
        self.data_base_url = data_base_url.rstrip("/")
        self.broker_mode = broker_mode
        self.trading_enabled = trading_enabled
        self.max_intent_age = timedelta(minutes=max_intent_age_minutes)
        self.transport = AlpacaReadOnlyTransport(self.paper_base_url, self.data_base_url, key_id, secret_key)
        self.risk_guards = RiskGuardConfig()
        self.known_client_order_ids: set[str] = set()
        self.broker_mutation_calls = 0
        self.audit_log_path = audit_log_path
        if self.audit_log_path:
            self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
            if not self.audit_log_path.exists():
                with self.audit_log_path.open("w", newline="", encoding="utf-8") as handle:
                    writer = csv.DictWriter(handle, fieldnames=list(asdict(AuditEvent("", "", "", "", "", None, None, "", "", "", "")).keys()))
                    writer.writeheader()

    @classmethod
    def from_environment(cls, audit_log_path: Path | None = None) -> "AlpacaBrokerAdapter":
        repo_root = Path(__file__).resolve().parents[1]
        load_local_env(repo_root / ".env")
        return cls(
            paper_base_url=os.environ.get("APCA_API_BASE_URL", "https://paper-api.alpaca.markets"),
            data_base_url=os.environ.get("APCA_DATA_BASE_URL", "https://data.alpaca.markets"),
            key_id=require_env("APCA_API_KEY_ID"),
            secret_key=require_env("APCA_API_SECRET_KEY"),
            audit_log_path=audit_log_path,
        )

    def get_account(self) -> tuple[str, Any]:
        return self.transport.get_json(self.paper_base_url, "/v2/account")

    def get_positions(self) -> tuple[str, Any]:
        return self.transport.get_json(self.paper_base_url, "/v2/positions")

    def get_open_orders(self) -> tuple[str, Any]:
        return self.transport.get_json(self.paper_base_url, "/v2/orders", {"status": "open", "limit": 50})

    def get_asset(self, symbol: str) -> tuple[str, Any]:
        return self.transport.get_json(self.paper_base_url, f"/v2/assets/{symbol.upper()}")

    def get_calendar(self, start: str, end: str) -> tuple[str, Any]:
        return self.transport.get_json(self.paper_base_url, "/v2/calendar", {"start": start, "end": end})

    def get_daily_bars(self, symbols: list[str], start: str, end: str, *, feed: str = "iex", adjustment: str = "all") -> tuple[str, Any]:
        return self.transport.get_json(
            self.data_base_url,
            "/v2/stocks/bars",
            {
                "symbols": ",".join(symbols),
                "timeframe": "1Day",
                "start": start,
                "end": end,
                "feed": feed,
                "adjustment": adjustment,
                "limit": 10000,
            },
        )

    def generate_client_order_id(self, strategy_id: str, rebalance_id: str, symbol: str, side: str, sequence: int = 1) -> str:
        prefix = f"{strategy_id}-{rebalance_id}-{symbol.upper()}-{side.upper()}-{sequence:03d}"
        sanitized = re.sub(r"[^A-Za-z0-9_-]", "-", prefix)
        if len(sanitized) <= self.CLIENT_ORDER_ID_MAX_LEN:
            return sanitized
        digest = hashlib.sha256(sanitized.encode("utf-8")).hexdigest()[:12]
        return f"{sanitized[:35]}-{digest}"[: self.CLIENT_ORDER_ID_MAX_LEN]

    def build_order_intent(
        self,
        *,
        strategy_id: str,
        portfolio_id: str,
        rebalance_id: str,
        symbol: str,
        source_asset_id: str,
        side: str,
        quantity: float | None,
        notional: float | None,
        order_type: str,
        time_in_force: str,
        reference_price: float,
        signal_timestamp: str,
        reason: str,
        sequence: int = 1,
    ) -> OrderIntent:
        client_order_id = self.generate_client_order_id(strategy_id, rebalance_id, symbol, side, sequence)
        intent_id = hashlib.sha256(
            "|".join([strategy_id, portfolio_id, rebalance_id, symbol.upper(), side.upper(), str(sequence)]).encode("utf-8")
        ).hexdigest()[:16]
        return OrderIntent(
            intent_id=intent_id,
            strategy_id=strategy_id,
            portfolio_id=portfolio_id,
            rebalance_id=rebalance_id,
            symbol=symbol.upper(),
            source_asset_id=source_asset_id,
            side=side.lower(),
            quantity=quantity,
            notional=notional,
            order_type=order_type.lower(),
            time_in_force=time_in_force.lower(),
            reference_price=reference_price,
            signal_timestamp=signal_timestamp,
            intent_created_at=datetime.now(timezone.utc).isoformat(),
            client_order_id=client_order_id,
            reason=reason,
            sequence=sequence,
        )

    def validate_order_intent(
        self,
        intent: OrderIntent,
        *,
        asset: dict[str, Any] | None,
        market_session_state: MarketSessionState,
        now: datetime | None = None,
    ) -> ValidationResult:
        errors: list[str] = []
        now = now or datetime.now(timezone.utc)

        if not intent.symbol or not re.match(r"^[A-Z0-9._-]+$", intent.symbol):
            errors.append("INVALID_SYMBOL")
        if asset is None:
            errors.append("UNKNOWN_ASSET")
        else:
            if asset.get("status") != "active":
                errors.append("ASSET_NOT_ACTIVE")
            if asset.get("tradable") is not True:
                errors.append("ASSET_NOT_TRADABLE")
        if intent.side not in {"buy", "sell"}:
            errors.append("INVALID_SIDE")
        if intent.order_type not in {"market", "limit"}:
            errors.append("UNSUPPORTED_ORDER_TYPE")
        if intent.time_in_force not in {"day", "gtc", "opg", "cls", "ioc", "fok"}:
            errors.append("UNSUPPORTED_TIME_IN_FORCE")
        if not math.isfinite(intent.reference_price) or intent.reference_price <= 0:
            errors.append("INVALID_REFERENCE_PRICE")
        if intent.quantity is None and intent.notional is None:
            errors.append("MISSING_QUANTITY_OR_NOTIONAL")
        if intent.quantity is not None and (not math.isfinite(intent.quantity) or intent.quantity <= 0):
            errors.append("INVALID_QUANTITY")
        if intent.notional is not None and (not math.isfinite(intent.notional) or intent.notional <= 0):
            errors.append("INVALID_NOTIONAL")
        if intent.client_order_id in self.known_client_order_ids:
            errors.append("DUPLICATE_CLIENT_ORDER_ID")
        if market_session_state not in {MarketSessionState.MARKET_OPEN, MarketSessionState.PRE_OPEN}:
            errors.append("MARKET_SESSION_NOT_ELIGIBLE")
        if self._is_stale(intent.signal_timestamp, now):
            errors.append("STALE_INTENT")
        if self.broker_mode != BrokerMode.DRY_RUN:
            errors.append("BROKER_MODE_NOT_DRY_RUN")
        if self.trading_enabled:
            errors.append("TRADING_ENABLED_NOT_ALLOWED_IN_ALP003")

        if "STALE_INTENT" in errors:
            status = ValidationStatus.REJECTED_STALE_INTENT.value
        elif "DUPLICATE_CLIENT_ORDER_ID" in errors:
            status = ValidationStatus.REJECTED_DUPLICATE.value
        elif "MARKET_SESSION_NOT_ELIGIBLE" in errors:
            status = ValidationStatus.REJECTED_MARKET_SESSION.value
        elif errors:
            status = ValidationStatus.REJECTED_INVALID.value
        else:
            status = ValidationStatus.SUBMISSION_BLOCKED_ALP003.value
            self.known_client_order_ids.add(intent.client_order_id)

        self._write_audit_event(intent, status, ReconciliationState.INTENT_ONLY.value, ",".join(errors))
        return ValidationResult(intent.intent_id, intent.client_order_id, status, errors)

    def _is_stale(self, timestamp: str, now: datetime) -> bool:
        try:
            parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError:
            return True
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return now - parsed > self.max_intent_age

    def market_session_from_calendar(self, calendar_rows: list[dict[str, Any]], current_time: datetime) -> MarketSessionState:
        current_date = current_time.date().isoformat()
        row = next((item for item in calendar_rows if str(item.get("date")) == current_date), None)
        if row is None:
            return MarketSessionState.HOLIDAY
        try:
            open_time = datetime.fromisoformat(f"{row['date']}T{row['open']}:00-04:00").astimezone(timezone.utc)
            close_time = datetime.fromisoformat(f"{row['date']}T{row['close']}:00-04:00").astimezone(timezone.utc)
        except Exception:
            return MarketSessionState.UNKNOWN
        if current_time < open_time:
            return MarketSessionState.PRE_OPEN
        if open_time <= current_time <= close_time:
            return MarketSessionState.MARKET_OPEN
        return MarketSessionState.POST_CLOSE

    def reconcile_positions(self, internal_positions: dict[str, float], broker_positions: list[dict[str, Any]]) -> dict[str, str]:
        states: dict[str, str] = {}
        broker_map = {str(pos.get("symbol", "")).upper(): float(pos.get("qty", 0) or 0) for pos in broker_positions}
        for symbol, qty in internal_positions.items():
            symbol_u = symbol.upper()
            if symbol_u not in broker_map:
                states[symbol_u] = ReconciliationState.MISSING_BROKER.value
            elif abs(float(qty) - broker_map[symbol_u]) < 1e-9:
                states[symbol_u] = ReconciliationState.MATCH.value
            else:
                states[symbol_u] = ReconciliationState.QUANTITY_MISMATCH.value
        for symbol in broker_map:
            if symbol not in {key.upper() for key in internal_positions}:
                states[symbol] = ReconciliationState.MISSING_INTERNAL.value
        return states or {"__EMPTY__": ReconciliationState.MATCH.value}

    def reconcile_orders(self, intents: list[OrderIntent], broker_orders: list[dict[str, Any]]) -> dict[str, str]:
        broker_by_client_id = {str(order.get("client_order_id", "")): order for order in broker_orders}
        states: dict[str, str] = {}
        for intent in intents:
            broker_order = broker_by_client_id.get(intent.client_order_id)
            if broker_order is None:
                states[intent.client_order_id] = ReconciliationState.INTENT_ONLY.value
                continue
            status = str(broker_order.get("status", "")).lower()
            states[intent.client_order_id] = {
                "new": ReconciliationState.BROKER_ACCEPTED.value,
                "accepted": ReconciliationState.BROKER_ACCEPTED.value,
                "partially_filled": ReconciliationState.PARTIALLY_FILLED.value,
                "filled": ReconciliationState.FILLED.value,
                "canceled": ReconciliationState.CANCELED.value,
                "rejected": ReconciliationState.REJECTED.value,
                "expired": ReconciliationState.EXPIRED.value,
            }.get(status, ReconciliationState.UNKNOWN.value)
        return states

    def submit_order(self, *_: Any, **__: Any) -> None:
        raise BrokerMutationDisabled("submit_order disabled in ALP-003")

    def replace_order(self, *_: Any, **__: Any) -> None:
        raise BrokerMutationDisabled("replace_order disabled in ALP-003")

    def cancel_order(self, *_: Any, **__: Any) -> None:
        raise BrokerMutationDisabled("cancel_order disabled in ALP-003")

    def _write_audit_event(self, intent: OrderIntent, validation_result: str, reconciliation_state: str, error_code: str) -> None:
        if not self.audit_log_path:
            return
        event = AuditEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            intent_id=intent.intent_id,
            client_order_id=intent.client_order_id,
            symbol=intent.symbol,
            side=intent.side,
            quantity=intent.quantity,
            notional=intent.notional,
            validation_result=validation_result,
            broker_mode=self.broker_mode.value,
            reconciliation_state=reconciliation_state,
            error_code=error_code,
        )
        with self.audit_log_path.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(asdict(event).keys()))
            writer.writerow(asdict(event))
