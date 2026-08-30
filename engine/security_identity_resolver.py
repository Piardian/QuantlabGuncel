from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from engine.alpaca_broker_adapter import AlpacaBrokerAdapter

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY_PATH = REPO_ROOT / "research" / "market_edge_discovery_program" / "fuf_001_free_exploratory_universe_freeze" / "fuf001_identity_event_registry.csv"


class IdentityContinuityStatus(str, Enum):
    VERIFIED_CONTINUITY = "VERIFIED_CONTINUITY"
    VERIFIED_DISCONTINUITY = "VERIFIED_DISCONTINUITY"
    UNRESOLVED = "UNRESOLVED"
    UNCHANGED = "UNCHANGED"


class IdentityEventType(str, Enum):
    TICKER_CHANGE = "TICKER_CHANGE"
    EXCHANGE_TRANSFER = "EXCHANGE_TRANSFER"
    ISSUER_NAME_CHANGE = "ISSUER_NAME_CHANGE"
    BROKER_ASSET_ID_CHANGE = "BROKER_ASSET_ID_CHANGE"
    MERGER = "MERGER"
    SPINOFF = "SPINOFF"
    SPLIT = "SPLIT"
    REVERSE_SPLIT = "REVERSE_SPLIT"
    SECURITY_REPLACEMENT = "SECURITY_REPLACEMENT"
    DELISTING_WITHOUT_SUCCESSOR = "DELISTING_WITHOUT_SUCCESSOR"
    IDENTITY_COLLISION = "IDENTITY_COLLISION"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class ResolvedIdentity:
    frozen_member_id: str
    canonical_symbol: str
    runtime_symbol: str
    runtime_asset_id: str
    continuity_status: str
    event_type: str
    effective_last_old_session: str | None = None
    effective_first_new_session: str | None = None
    data_symbols_required: tuple[str, ...] = ()
    price_series_continuity_required: bool = False
    corporate_action_adjustment_required: str = "NONE"
    resolved: bool = True
    block_reason: str | None = None
    audit_metadata: dict[str, Any] = field(default_factory=dict)


class SecurityIdentityResolver:
    def __init__(self, registry_path: Path | str | None = None) -> None:
        self.registry_path = Path(registry_path) if registry_path else DEFAULT_REGISTRY_PATH
        self._registry_cache: pd.DataFrame | None = None

    def load_registry(self) -> pd.DataFrame:
        if self._registry_cache is not None:
            return self._registry_cache
        if not self.registry_path.exists():
            df = pd.DataFrame(
                columns=[
                    "frozen_member_id",
                    "original_symbol",
                    "original_source_asset_id",
                    "event_type",
                    "effective_last_old_session",
                    "effective_first_new_session",
                    "new_symbol",
                    "new_source_asset_id",
                    "identity_continuity_status",
                    "evidence_source",
                    "evidence_reference",
                    "evidence_date",
                    "price_series_continuity_required",
                    "corporate_action_adjustment_required",
                    "review_status",
                ]
            )
            self._registry_cache = df
            return df

        df = pd.read_csv(self.registry_path, dtype=str).fillna("")
        self._registry_cache = df
        return df

    def registry_hash(self) -> str:
        if not self.registry_path.exists():
            return hashlib.sha256(b"").hexdigest().upper()
        return hashlib.sha256(self.registry_path.read_bytes()).hexdigest().upper()

    def resolve_member(
        self,
        member: pd.Series | dict[str, Any],
        as_of_session: str,
        broker: AlpacaBrokerAdapter | None = None,
    ) -> ResolvedIdentity:
        member_dict = member.to_dict() if isinstance(member, pd.Series) else dict(member)
        canonical_symbol = str(member_dict.get("symbol", "")).upper()
        source_asset_id = str(member_dict.get("source_asset_id", ""))
        frozen_member_id = str(member_dict.get("frozen_member_id", source_asset_id or canonical_symbol))

        registry = self.load_registry()
        events = registry[
            (registry["original_source_asset_id"].str.upper() == source_asset_id.upper())
            & (registry["original_symbol"].str.upper() == canonical_symbol)
        ]

        if events.empty:
            if broker is not None:
                status, payload = broker.get_asset(canonical_symbol)
                if status in {"HTTP_404", "NOT_FOUND"} or (isinstance(status, str) and status.startswith("HTTP_404")):
                    id_status, id_payload = broker.get_asset(source_asset_id) if source_asset_id else ("HTTP_404", {})
                    if id_status == "PASS" and isinstance(id_payload, dict) and id_payload.get("symbol", "").upper() != canonical_symbol:
                        return ResolvedIdentity(
                            frozen_member_id=frozen_member_id,
                            canonical_symbol=canonical_symbol,
                            runtime_symbol=canonical_symbol,
                            runtime_asset_id=source_asset_id,
                            continuity_status=IdentityContinuityStatus.UNRESOLVED.value,
                            event_type=IdentityEventType.IDENTITY_COLLISION.value,
                            data_symbols_required=(canonical_symbol,),
                            resolved=False,
                            block_reason="BLOCK_IDENTITY_MISMATCH",
                            audit_metadata={"broker_payload": id_payload},
                        )
                    return ResolvedIdentity(
                        frozen_member_id=frozen_member_id,
                        canonical_symbol=canonical_symbol,
                        runtime_symbol=canonical_symbol,
                        runtime_asset_id=source_asset_id,
                        continuity_status=IdentityContinuityStatus.VERIFIED_DISCONTINUITY.value,
                        event_type=IdentityEventType.DELISTING_WITHOUT_SUCCESSOR.value,
                        data_symbols_required=(canonical_symbol,),
                        resolved=True,
                        audit_metadata={"broker_status": "404_NOT_FOUND"},
                    )

                if status == "PASS" and isinstance(payload, dict):
                    broker_asset_id = str(payload.get("id", ""))
                    tradable = bool(payload.get("tradable", False))
                    asset_active = payload.get("status") == "active"
                    if broker_asset_id and source_asset_id and broker_asset_id != source_asset_id and tradable:
                        return ResolvedIdentity(
                            frozen_member_id=frozen_member_id,
                            canonical_symbol=canonical_symbol,
                            runtime_symbol=canonical_symbol,
                            runtime_asset_id=broker_asset_id,
                            continuity_status=IdentityContinuityStatus.UNRESOLVED.value,
                            event_type=IdentityEventType.IDENTITY_COLLISION.value,
                            data_symbols_required=(canonical_symbol,),
                            resolved=False,
                            block_reason="BLOCK_IDENTITY_MISMATCH",
                            audit_metadata={"broker_asset_id": broker_asset_id, "source_asset_id": source_asset_id},
                        )
                    if not asset_active or not tradable:
                        return ResolvedIdentity(
                            frozen_member_id=frozen_member_id,
                            canonical_symbol=canonical_symbol,
                            runtime_symbol=canonical_symbol,
                            runtime_asset_id=source_asset_id,
                            continuity_status=IdentityContinuityStatus.VERIFIED_DISCONTINUITY.value,
                            event_type=IdentityEventType.DELISTING_WITHOUT_SUCCESSOR.value,
                            data_symbols_required=(canonical_symbol,),
                            resolved=True,
                            audit_metadata={"broker_status": payload.get("status")},
                        )

            return ResolvedIdentity(
                frozen_member_id=frozen_member_id,
                canonical_symbol=canonical_symbol,
                runtime_symbol=canonical_symbol,
                runtime_asset_id=source_asset_id,
                continuity_status=IdentityContinuityStatus.UNCHANGED.value,
                event_type="NONE",
                data_symbols_required=(canonical_symbol,),
                resolved=True,
                audit_metadata={"registry_version": self.registry_hash()[:16]},
            )

        event = events.iloc[-1]
        continuity_status = str(event.get("identity_continuity_status", "")).strip().upper()
        event_type = str(event.get("event_type", "")).strip().upper()
        last_old = str(event.get("effective_last_old_session", "")).strip()
        first_new = str(event.get("effective_first_new_session", "")).strip()
        new_symbol = str(event.get("new_symbol", "")).strip().upper()
        new_asset_id = str(event.get("new_source_asset_id", "")).strip()
        price_cont_req = str(event.get("price_series_continuity_required", "")).strip().upper() in {"1", "TRUE", "YES"}
        corp_adj = str(event.get("corporate_action_adjustment_required", "NONE")).strip().upper()

        if continuity_status == IdentityContinuityStatus.UNRESOLVED.value:
            return ResolvedIdentity(
                frozen_member_id=frozen_member_id,
                canonical_symbol=canonical_symbol,
                runtime_symbol=canonical_symbol,
                runtime_asset_id=source_asset_id,
                continuity_status=continuity_status,
                event_type=event_type,
                effective_last_old_session=last_old or None,
                effective_first_new_session=first_new or None,
                data_symbols_required=(canonical_symbol,),
                resolved=False,
                block_reason="BLOCK_IDENTITY_CONTINUITY_UNRESOLVED",
                audit_metadata={"registry_event": event.to_dict()},
            )

        if continuity_status == IdentityContinuityStatus.VERIFIED_DISCONTINUITY.value:
            return ResolvedIdentity(
                frozen_member_id=frozen_member_id,
                canonical_symbol=canonical_symbol,
                runtime_symbol=canonical_symbol,
                runtime_asset_id=source_asset_id,
                continuity_status=continuity_status,
                event_type=event_type,
                effective_last_old_session=last_old or None,
                effective_first_new_session=first_new or None,
                data_symbols_required=(canonical_symbol,),
                resolved=True,
                block_reason=None,
                audit_metadata={"registry_event": event.to_dict()},
            )

        if continuity_status == IdentityContinuityStatus.VERIFIED_CONTINUITY.value:
            if corp_adj not in {"NONE", "BROKER_ADJUSTED_SERIES_SUFFICIENT"}:
                return ResolvedIdentity(
                    frozen_member_id=frozen_member_id,
                    canonical_symbol=canonical_symbol,
                    runtime_symbol=new_symbol if as_of_session >= first_new else canonical_symbol,
                    runtime_asset_id=new_asset_id if as_of_session >= first_new else source_asset_id,
                    continuity_status=continuity_status,
                    event_type=event_type,
                    effective_last_old_session=last_old or None,
                    effective_first_new_session=first_new or None,
                    data_symbols_required=(canonical_symbol, new_symbol),
                    price_series_continuity_required=price_cont_req,
                    corporate_action_adjustment_required=corp_adj,
                    resolved=False,
                    block_reason="BLOCK_CORPORATE_ACTION_UNRESOLVED",
                    audit_metadata={"registry_event": event.to_dict()},
                )

            is_new_era = bool(first_new and as_of_session >= first_new)
            runtime_symbol = new_symbol if is_new_era else canonical_symbol
            runtime_asset_id = new_asset_id if is_new_era else source_asset_id

            if is_new_era and broker is not None:
                status, payload = broker.get_asset(new_symbol)
                if status == "PASS" and isinstance(payload, dict):
                    b_id = str(payload.get("id", ""))
                    if new_asset_id and b_id and b_id != new_asset_id:
                        return ResolvedIdentity(
                            frozen_member_id=frozen_member_id,
                            canonical_symbol=canonical_symbol,
                            runtime_symbol=new_symbol,
                            runtime_asset_id=b_id,
                            continuity_status=continuity_status,
                            event_type=event_type,
                            resolved=False,
                            block_reason="BLOCK_IDENTITY_MISMATCH",
                            audit_metadata={"expected_new_id": new_asset_id, "broker_id": b_id},
                        )

            required_symbols = (canonical_symbol, new_symbol) if (is_new_era and new_symbol != canonical_symbol) else (canonical_symbol,)
            return ResolvedIdentity(
                frozen_member_id=frozen_member_id,
                canonical_symbol=canonical_symbol,
                runtime_symbol=runtime_symbol,
                runtime_asset_id=runtime_asset_id,
                continuity_status=continuity_status,
                event_type=event_type,
                effective_last_old_session=last_old or None,
                effective_first_new_session=first_new or None,
                data_symbols_required=required_symbols,
                price_series_continuity_required=price_cont_req,
                corporate_action_adjustment_required=corp_adj,
                resolved=True,
                block_reason=None,
                audit_metadata={"registry_event": event.to_dict()},
            )

        return ResolvedIdentity(
            frozen_member_id=frozen_member_id,
            canonical_symbol=canonical_symbol,
            runtime_symbol=canonical_symbol,
            runtime_asset_id=source_asset_id,
            continuity_status=IdentityContinuityStatus.UNRESOLVED.value,
            event_type="UNKNOWN",
            data_symbols_required=(canonical_symbol,),
            resolved=False,
            block_reason="BLOCK_IDENTITY_CONTINUITY_UNRESOLVED",
        )

    def resolve_universe(
        self,
        membership: pd.DataFrame,
        as_of_session: str,
        broker: AlpacaBrokerAdapter | None = None,
    ) -> dict[str, ResolvedIdentity]:
        resolutions: dict[str, ResolvedIdentity] = {}
        for row in membership.itertuples():
            res = self.resolve_member(pd.Series(row._asdict()), as_of_session, broker=broker)
            resolutions[res.canonical_symbol] = res
        return resolutions

    def stitch_price_series(
        self,
        bars_df: pd.DataFrame,
        resolution: ResolvedIdentity,
        as_of_session: str,
        *,
        calendar_payload: list[dict[str, Any]] | None = None,
    ) -> tuple[str, pd.DataFrame]:
        if bars_df.empty:
            return "MARKET_DATA_FAILURE", pd.DataFrame()

        sym_bars = bars_df.copy()
        sym_bars["date"] = pd.to_datetime(sym_bars["date"]).dt.date.astype(str)

        if resolution.continuity_status != IdentityContinuityStatus.VERIFIED_CONTINUITY.value:
            filtered = sym_bars[sym_bars["symbol"] == resolution.canonical_symbol].copy()
            filtered = filtered[filtered["date"] <= as_of_session]
            if filtered.empty:
                return "MARKET_DATA_FAILURE", pd.DataFrame()

            # Check duplicate dates
            if int(filtered.duplicated(subset=["date"]).sum()) > 0:
                return "BLOCK_PRICE_SERIES_CONTINUITY", pd.DataFrame()

            filtered = filtered.sort_values("date").reset_index(drop=True)

            # Strictly increasing chronology
            dates = list(filtered["date"])
            if not all(dates[i] < dates[i + 1] for i in range(len(dates) - 1)):
                return "BLOCK_PRICE_SERIES_CONTINUITY", pd.DataFrame()

            # Price validation: finite and strictly positive
            close_numeric = pd.to_numeric(filtered["close"], errors="coerce")
            if close_numeric.isna().any() or not np.isfinite(close_numeric).all():
                return "BLOCK_PRICE_SERIES_CONTINUITY", pd.DataFrame()
            if (close_numeric <= 0).any():
                return "BLOCK_PRICE_SERIES_CONTINUITY", pd.DataFrame()

            filtered["close"] = close_numeric
            return "PASS", filtered

        # Handle VERIFIED_CONTINUITY
        old_sym = resolution.canonical_symbol
        new_sym = resolution.runtime_symbol
        last_old = resolution.effective_last_old_session
        first_new = resolution.effective_first_new_session

        if not last_old or not first_new:
            return "BLOCK_PRICE_SERIES_CONTINUITY", pd.DataFrame()

        # If transition has not occurred yet (as_of_session <= last_old), operate on old symbol alone
        if as_of_session <= last_old:
            old_bars = sym_bars[(sym_bars["symbol"] == old_sym) & (sym_bars["date"] <= as_of_session)].copy()
            if old_bars.empty:
                return "MARKET_DATA_FAILURE", pd.DataFrame()
            if int(old_bars.duplicated(subset=["date"]).sum()) > 0:
                return "BLOCK_PRICE_SERIES_CONTINUITY", pd.DataFrame()
            old_bars = old_bars.sort_values("date").reset_index(drop=True)
            dates = list(old_bars["date"])
            if not all(dates[i] < dates[i + 1] for i in range(len(dates) - 1)):
                return "BLOCK_PRICE_SERIES_CONTINUITY", pd.DataFrame()
            close_numeric = pd.to_numeric(old_bars["close"], errors="coerce")
            if close_numeric.isna().any() or not np.isfinite(close_numeric).all() or (close_numeric <= 0).any():
                return "BLOCK_PRICE_SERIES_CONTINUITY", pd.DataFrame()
            old_bars["close"] = close_numeric
            old_bars["symbol"] = resolution.canonical_symbol
            return "PASS", old_bars

        # Filter old and new bars
        old_bars = sym_bars[(sym_bars["symbol"] == old_sym) & (sym_bars["date"] <= last_old)].copy()
        new_bars = sym_bars[(sym_bars["symbol"] == new_sym) & (sym_bars["date"] >= first_new) & (sym_bars["date"] <= as_of_session)].copy()

        # Boundary checks:
        # 1. Old-symbol history must reach last_old
        if old_bars.empty or str(old_bars["date"].max()) != last_old:
            return "BLOCK_PRICE_SERIES_CONTINUITY", pd.DataFrame()

        # 2. New-symbol history must start at first_new
        if new_bars.empty or str(new_bars["date"].min()) != first_new:
            return "BLOCK_PRICE_SERIES_CONTINUITY", pd.DataFrame()

        # 3. Calendar continuity: no unexpected trading sessions between last_old and first_new
        if calendar_payload is not None and isinstance(calendar_payload, list):
            calendar_dates = [str(item.get("date")) for item in calendar_payload]
            gap_sessions = [d for d in calendar_dates if last_old < d < first_new]
            if gap_sessions:
                return "BLOCK_PRICE_SERIES_CONTINUITY", pd.DataFrame()
        else:
            if first_new <= last_old:
                return "BLOCK_PRICE_SERIES_CONTINUITY", pd.DataFrame()

        # 4. Overlap check
        old_dates = set(old_bars["date"])
        new_dates = set(new_bars["date"])
        if old_dates & new_dates:
            return "BLOCK_PRICE_SERIES_CONTINUITY", pd.DataFrame()

        # Combine
        combined = pd.concat([old_bars, new_bars], ignore_index=True)
        if combined.empty:
            return "MARKET_DATA_FAILURE", pd.DataFrame()

        # 5. Duplicate dates
        if int(combined.duplicated(subset=["date"]).sum()) > 0:
            return "BLOCK_PRICE_SERIES_CONTINUITY", pd.DataFrame()

        # 6. Strictly increasing chronology
        combined = combined.sort_values("date").reset_index(drop=True)
        dates = list(combined["date"])
        if not all(dates[i] < dates[i + 1] for i in range(len(dates) - 1)):
            return "BLOCK_PRICE_SERIES_CONTINUITY", pd.DataFrame()

        # 7. Price validation: finite and strictly positive
        close_numeric = pd.to_numeric(combined["close"], errors="coerce")
        if close_numeric.isna().any() or not np.isfinite(close_numeric).all():
            return "BLOCK_PRICE_SERIES_CONTINUITY", pd.DataFrame()
        if (close_numeric <= 0).any():
            return "BLOCK_PRICE_SERIES_CONTINUITY", pd.DataFrame()

        combined["close"] = close_numeric
        combined["symbol"] = resolution.canonical_symbol
        return "PASS", combined
