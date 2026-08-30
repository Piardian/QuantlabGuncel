from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.paper_risk_guards import EXPECTED_UNIVERSE_HASH, PaperSafetyManager
from engine.paper_trading_controller import PaperControllerConfig, PaperTradingController
from engine.security_identity_resolver import (
    IdentityContinuityStatus,
    ResolvedIdentity,
    SecurityIdentityResolver,
)
from scripts.paper_safety_tests import FakeAdapter


class TestSecurityIdentityResolver(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.tmp = Path(self.tempdir.name)
        self.registry_path = self.tmp / "test_registry.csv"

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_unchanged_active_symbol_resolves_normally(self) -> None:
        resolver = SecurityIdentityResolver(self.registry_path)
        member = {"symbol": "AAPL", "source_asset_id": "b0b6dd9d-8b7b-48a9-ba46-4556b674ceb3"}
        res = resolver.resolve_member(member, "2026-08-24")
        self.assertTrue(res.resolved)
        self.assertEqual(res.canonical_symbol, "AAPL")
        self.assertEqual(res.runtime_symbol, "AAPL")
        self.assertEqual(res.continuity_status, IdentityContinuityStatus.UNCHANGED.value)
        self.assertIsNone(res.block_reason)

    def test_verified_ticker_change_stitches_logical_security(self) -> None:
        csv_content = """frozen_member_id,original_symbol,original_source_asset_id,event_type,effective_last_old_session,effective_first_new_session,new_symbol,new_source_asset_id,identity_continuity_status,evidence_source,evidence_reference,evidence_date,price_series_continuity_required,corporate_action_adjustment_required,review_status
34479ce5-4d55-4d85-8ff4-25d08f908979,BBBY,34479ce5-4d55-4d85-8ff4-25d08f908979,TICKER_CHANGE;EXCHANGE_TRANSFER;ISSUER_NAME_CHANGE,2026-08-14,2026-08-17,NXH,96a49f53-6ed9-4900-b92a-44814b21cf92,VERIFIED_CONTINUITY,SEC_8K_NASDAQ_LISTING_NOTICE,SEC Form 8-K Certificate of Amendment / Nasdaq Listing Notice DTN2026-17 NXH (CIK 0001130713 / CUSIP 690370101),2026-08-17,TRUE,NONE,VERIFIED
"""
        self.registry_path.write_text(csv_content.strip() + "\n", encoding="utf-8")
        resolver = SecurityIdentityResolver(self.registry_path)
        member = {"symbol": "BBBY", "source_asset_id": "34479ce5-4d55-4d85-8ff4-25d08f908979"}

        res_new = resolver.resolve_member(member, "2026-08-24")
        self.assertTrue(res_new.resolved)
        self.assertEqual(res_new.runtime_symbol, "NXH")
        self.assertEqual(res_new.runtime_asset_id, "96a49f53-6ed9-4900-b92a-44814b21cf92")
        self.assertEqual(res_new.continuity_status, IdentityContinuityStatus.VERIFIED_CONTINUITY.value)

        dates_old = [f"2026-08-{i:02d}" for i in range(3, 15)]
        dates_new = [f"2026-08-{i:02d}" for i in range(17, 25)]
        bars_old = pd.DataFrame({"symbol": ["BBBY"] * len(dates_old), "date": dates_old, "close": [4.0 + i * 0.1 for i in range(len(dates_old))]})
        bars_new = pd.DataFrame({"symbol": ["NXH"] * len(dates_new), "date": dates_new, "close": [5.0 + i * 0.1 for i in range(len(dates_new))]})
        all_bars = pd.concat([bars_old, bars_new], ignore_index=True)

        calendar = [{"date": d, "open": "09:30", "close": "16:00"} for d in dates_old + dates_new]
        status, stitched = resolver.stitch_price_series(all_bars, res_new, "2026-08-24", calendar_payload=calendar)
        self.assertEqual(status, "PASS")
        self.assertEqual(len(stitched), len(dates_old) + len(dates_new))
        self.assertEqual(stitched["symbol"].nunique(), 1)
        self.assertEqual(stitched["symbol"].iloc[0], "BBBY")

    def test_old_ticker_missing_expected_final_session_blocks(self) -> None:
        csv_content = """frozen_member_id,original_symbol,original_source_asset_id,event_type,effective_last_old_session,effective_first_new_session,new_symbol,new_source_asset_id,identity_continuity_status,evidence_source,evidence_reference,evidence_date,price_series_continuity_required,corporate_action_adjustment_required,review_status
TEST-UUID,OLDCO,TEST-UUID,TICKER_CHANGE,2026-08-14,2026-08-17,NEWCO,NEW-UUID,VERIFIED_CONTINUITY,SEC,8K,2026-08-17,TRUE,NONE,VERIFIED
"""
        self.registry_path.write_text(csv_content.strip() + "\n", encoding="utf-8")
        resolver = SecurityIdentityResolver(self.registry_path)
        member = {"symbol": "OLDCO", "source_asset_id": "TEST-UUID"}
        res = resolver.resolve_member(member, "2026-08-24")

        # Old bars stop on 2026-08-13 (missing final session 2026-08-14)
        bars_old = pd.DataFrame({"symbol": ["OLDCO", "OLDCO"], "date": ["2026-08-12", "2026-08-13"], "close": [10.0, 10.5]})
        bars_new = pd.DataFrame({"symbol": ["NEWCO", "NEWCO"], "date": ["2026-08-17", "2026-08-18"], "close": [11.0, 11.5]})
        all_bars = pd.concat([bars_old, bars_new], ignore_index=True)

        status, _ = resolver.stitch_price_series(all_bars, res, "2026-08-24")
        self.assertEqual(status, "BLOCK_PRICE_SERIES_CONTINUITY")

    def test_successor_ticker_missing_expected_first_session_blocks(self) -> None:
        csv_content = """frozen_member_id,original_symbol,original_source_asset_id,event_type,effective_last_old_session,effective_first_new_session,new_symbol,new_source_asset_id,identity_continuity_status,evidence_source,evidence_reference,evidence_date,price_series_continuity_required,corporate_action_adjustment_required,review_status
TEST-UUID,OLDCO,TEST-UUID,TICKER_CHANGE,2026-08-14,2026-08-17,NEWCO,NEW-UUID,VERIFIED_CONTINUITY,SEC,8K,2026-08-17,TRUE,NONE,VERIFIED
"""
        self.registry_path.write_text(csv_content.strip() + "\n", encoding="utf-8")
        resolver = SecurityIdentityResolver(self.registry_path)
        member = {"symbol": "OLDCO", "source_asset_id": "TEST-UUID"}
        res = resolver.resolve_member(member, "2026-08-24")

        # New bars only start on 2026-08-18 (missing first session 2026-08-17)
        bars_old = pd.DataFrame({"symbol": ["OLDCO", "OLDCO"], "date": ["2026-08-13", "2026-08-14"], "close": [10.0, 10.5]})
        bars_new = pd.DataFrame({"symbol": ["NEWCO", "NEWCO"], "date": ["2026-08-18", "2026-08-19"], "close": [11.0, 11.5]})
        all_bars = pd.concat([bars_old, bars_new], ignore_index=True)

        status, _ = resolver.stitch_price_series(all_bars, res, "2026-08-24")
        self.assertEqual(status, "BLOCK_PRICE_SERIES_CONTINUITY")

    def test_unexpected_trading_session_gap_blocks(self) -> None:
        # Event declared with a multi-day weekday gap without holiday exemption
        csv_content = """frozen_member_id,original_symbol,original_source_asset_id,event_type,effective_last_old_session,effective_first_new_session,new_symbol,new_source_asset_id,identity_continuity_status,evidence_source,evidence_reference,evidence_date,price_series_continuity_required,corporate_action_adjustment_required,review_status
TEST-UUID,OLDCO,TEST-UUID,TICKER_CHANGE,2026-08-11,2026-08-17,NEWCO,NEW-UUID,VERIFIED_CONTINUITY,SEC,8K,2026-08-17,TRUE,NONE,VERIFIED
"""
        self.registry_path.write_text(csv_content.strip() + "\n", encoding="utf-8")
        resolver = SecurityIdentityResolver(self.registry_path)
        member = {"symbol": "OLDCO", "source_asset_id": "TEST-UUID"}
        res = resolver.resolve_member(member, "2026-08-24")

        bars_old = pd.DataFrame({"symbol": ["OLDCO"], "date": ["2026-08-11"], "close": [10.0]})
        bars_new = pd.DataFrame({"symbol": ["NEWCO"], "date": ["2026-08-17"], "close": [11.0]})
        all_bars = pd.concat([bars_old, bars_new], ignore_index=True)

        # Calendar shows 2026-08-12, 2026-08-13, 2026-08-14 were active trading sessions
        calendar = [
            {"date": "2026-08-11", "open": "09:30", "close": "16:00"},
            {"date": "2026-08-12", "open": "09:30", "close": "16:00"},
            {"date": "2026-08-13", "open": "09:30", "close": "16:00"},
            {"date": "2026-08-14", "open": "09:30", "close": "16:00"},
            {"date": "2026-08-17", "open": "09:30", "close": "16:00"},
        ]
        status, _ = resolver.stitch_price_series(all_bars, res, "2026-08-24", calendar_payload=calendar)
        self.assertEqual(status, "BLOCK_PRICE_SERIES_CONTINUITY")

    def test_valid_weekend_transition_passes(self) -> None:
        csv_content = """frozen_member_id,original_symbol,original_source_asset_id,event_type,effective_last_old_session,effective_first_new_session,new_symbol,new_source_asset_id,identity_continuity_status,evidence_source,evidence_reference,evidence_date,price_series_continuity_required,corporate_action_adjustment_required,review_status
TEST-UUID,OLDCO,TEST-UUID,TICKER_CHANGE,2026-08-14,2026-08-17,NEWCO,NEW-UUID,VERIFIED_CONTINUITY,SEC,8K,2026-08-17,TRUE,NONE,VERIFIED
"""
        self.registry_path.write_text(csv_content.strip() + "\n", encoding="utf-8")
        resolver = SecurityIdentityResolver(self.registry_path)
        member = {"symbol": "OLDCO", "source_asset_id": "TEST-UUID"}
        res = resolver.resolve_member(member, "2026-08-24")

        bars_old = pd.DataFrame({"symbol": ["OLDCO"], "date": ["2026-08-14"], "close": [10.0]})
        bars_new = pd.DataFrame({"symbol": ["NEWCO"], "date": ["2026-08-17"], "close": [11.0]})
        all_bars = pd.concat([bars_old, bars_new], ignore_index=True)

        calendar = [
            {"date": "2026-08-14", "open": "09:30", "close": "16:00"},
            {"date": "2026-08-17", "open": "09:30", "close": "16:00"},
        ]
        status, _ = resolver.stitch_price_series(all_bars, res, "2026-08-24", calendar_payload=calendar)
        self.assertEqual(status, "PASS")

    def test_valid_market_holiday_transition_passes(self) -> None:
        # Thursday July 2 to Monday July 6 across Friday July 3 market holiday
        csv_content = """frozen_member_id,original_symbol,original_source_asset_id,event_type,effective_last_old_session,effective_first_new_session,new_symbol,new_source_asset_id,identity_continuity_status,evidence_source,evidence_reference,evidence_date,price_series_continuity_required,corporate_action_adjustment_required,review_status
TEST-UUID,OLDCO,TEST-UUID,TICKER_CHANGE,2026-07-02,2026-07-06,NEWCO,NEW-UUID,VERIFIED_CONTINUITY,SEC,8K,2026-07-06,TRUE,NONE,VERIFIED
"""
        self.registry_path.write_text(csv_content.strip() + "\n", encoding="utf-8")
        resolver = SecurityIdentityResolver(self.registry_path)
        member = {"symbol": "OLDCO", "source_asset_id": "TEST-UUID"}
        res = resolver.resolve_member(member, "2026-07-10")

        bars_old = pd.DataFrame({"symbol": ["OLDCO"], "date": ["2026-07-02"], "close": [10.0]})
        bars_new = pd.DataFrame({"symbol": ["NEWCO"], "date": ["2026-07-06"], "close": [11.0]})
        all_bars = pd.concat([bars_old, bars_new], ignore_index=True)

        calendar = [
            {"date": "2026-07-02", "open": "09:30", "close": "16:00"},
            # 2026-07-03 is exchange holiday (not in calendar)
            {"date": "2026-07-06", "open": "09:30", "close": "16:00"},
        ]
        status, _ = resolver.stitch_price_series(all_bars, res, "2026-07-10", calendar_payload=calendar)
        self.assertEqual(status, "PASS")

    def test_overlapping_old_new_bars_blocks(self) -> None:
        csv_content = """frozen_member_id,original_symbol,original_source_asset_id,event_type,effective_last_old_session,effective_first_new_session,new_symbol,new_source_asset_id,identity_continuity_status,evidence_source,evidence_reference,evidence_date,price_series_continuity_required,corporate_action_adjustment_required,review_status
OVERLAP-UUID,OOLD,OVERLAP-UUID,TICKER_CHANGE,2026-08-17,2026-08-17,ONEW,ONEW-UUID,VERIFIED_CONTINUITY,SEC,8K,2026-08-17,TRUE,NONE,VERIFIED
"""
        self.registry_path.write_text(csv_content.strip() + "\n", encoding="utf-8")
        resolver = SecurityIdentityResolver(self.registry_path)
        member = {"symbol": "OOLD", "source_asset_id": "OVERLAP-UUID"}
        res = resolver.resolve_member(member, "2026-08-24")

        overlap_bars = pd.DataFrame([
            {"symbol": "OOLD", "date": "2026-08-17", "close": 10.0},
            {"symbol": "ONEW", "date": "2026-08-17", "close": 11.0},
        ])
        status, _ = resolver.stitch_price_series(overlap_bars, res, "2026-08-24")
        self.assertEqual(status, "BLOCK_PRICE_SERIES_CONTINUITY")

    def test_duplicate_dates_in_series_blocks(self) -> None:
        resolver = SecurityIdentityResolver(self.registry_path)
        member = {"symbol": "AAPL", "source_asset_id": "b0b6dd9d-8b7b-48a9-ba46-4556b674ceb3"}
        res = resolver.resolve_member(member, "2026-08-24")

        dup_bars = pd.DataFrame([
            {"symbol": "AAPL", "date": "2026-08-20", "close": 150.0},
            {"symbol": "AAPL", "date": "2026-08-20", "close": 151.0},
        ])
        status, _ = resolver.stitch_price_series(dup_bars, res, "2026-08-24")
        self.assertEqual(status, "BLOCK_PRICE_SERIES_CONTINUITY")

    def test_zero_close_price_blocks(self) -> None:
        resolver = SecurityIdentityResolver(self.registry_path)
        member = {"symbol": "AAPL", "source_asset_id": "b0b6dd9d-8b7b-48a9-ba46-4556b674ceb3"}
        res = resolver.resolve_member(member, "2026-08-24")

        bars = pd.DataFrame([
            {"symbol": "AAPL", "date": "2026-08-20", "close": 0.0},
        ])
        status, _ = resolver.stitch_price_series(bars, res, "2026-08-24")
        self.assertEqual(status, "BLOCK_PRICE_SERIES_CONTINUITY")

    def test_negative_close_price_blocks(self) -> None:
        resolver = SecurityIdentityResolver(self.registry_path)
        member = {"symbol": "AAPL", "source_asset_id": "b0b6dd9d-8b7b-48a9-ba46-4556b674ceb3"}
        res = resolver.resolve_member(member, "2026-08-24")

        bars = pd.DataFrame([
            {"symbol": "AAPL", "date": "2026-08-20", "close": -5.25},
        ])
        status, _ = resolver.stitch_price_series(bars, res, "2026-08-24")
        self.assertEqual(status, "BLOCK_PRICE_SERIES_CONTINUITY")

    def test_nan_non_finite_close_price_blocks(self) -> None:
        resolver = SecurityIdentityResolver(self.registry_path)
        member = {"symbol": "AAPL", "source_asset_id": "b0b6dd9d-8b7b-48a9-ba46-4556b674ceb3"}
        res = resolver.resolve_member(member, "2026-08-24")

        bars_nan = pd.DataFrame([{"symbol": "AAPL", "date": "2026-08-20", "close": np.nan}])
        status_nan, _ = resolver.stitch_price_series(bars_nan, res, "2026-08-24")
        self.assertEqual(status_nan, "BLOCK_PRICE_SERIES_CONTINUITY")

        bars_inf = pd.DataFrame([{"symbol": "AAPL", "date": "2026-08-20", "close": np.inf}])
        status_inf, _ = resolver.stitch_price_series(bars_inf, res, "2026-08-24")
        self.assertEqual(status_inf, "BLOCK_PRICE_SERIES_CONTINUITY")

    def test_exchange_transfer_with_same_security_resolves(self) -> None:
        csv_content = """frozen_member_id,original_symbol,original_source_asset_id,event_type,effective_last_old_session,effective_first_new_session,new_symbol,new_source_asset_id,identity_continuity_status,evidence_source,evidence_reference,evidence_date,price_series_continuity_required,corporate_action_adjustment_required,review_status
TEST-UUID,OLDEX,TEST-UUID,EXCHANGE_TRANSFER,2026-08-14,2026-08-17,OLDEX,TEST-UUID,VERIFIED_CONTINUITY,NYSE_NOTICE,Transfer,2026-08-17,TRUE,NONE,VERIFIED
"""
        self.registry_path.write_text(csv_content.strip() + "\n", encoding="utf-8")
        resolver = SecurityIdentityResolver(self.registry_path)
        member = {"symbol": "OLDEX", "source_asset_id": "TEST-UUID"}
        res = resolver.resolve_member(member, "2026-08-24")
        self.assertTrue(res.resolved)
        self.assertEqual(res.runtime_symbol, "OLDEX")
        self.assertEqual(res.continuity_status, IdentityContinuityStatus.VERIFIED_CONTINUITY.value)

    def test_broker_asset_id_changes_with_official_continuity_resolves(self) -> None:
        csv_content = """frozen_member_id,original_symbol,original_source_asset_id,event_type,effective_last_old_session,effective_first_new_session,new_symbol,new_source_asset_id,identity_continuity_status,evidence_source,evidence_reference,evidence_date,price_series_continuity_required,corporate_action_adjustment_required,review_status
OLD-BROKER-UUID,SYM,OLD-BROKER-UUID,BROKER_ASSET_ID_CHANGE,2026-08-14,2026-08-17,SYM,NEW-BROKER-UUID,VERIFIED_CONTINUITY,BROKER_NOTICE,ID Change,2026-08-17,TRUE,NONE,VERIFIED
"""
        self.registry_path.write_text(csv_content.strip() + "\n", encoding="utf-8")
        resolver = SecurityIdentityResolver(self.registry_path)
        member = {"symbol": "SYM", "source_asset_id": "OLD-BROKER-UUID"}
        res = resolver.resolve_member(member, "2026-08-24")
        self.assertTrue(res.resolved)
        self.assertEqual(res.runtime_asset_id, "NEW-BROKER-UUID")

    def test_different_new_ticker_no_evidence_blocks(self) -> None:
        csv_content = """frozen_member_id,original_symbol,original_source_asset_id,event_type,effective_last_old_session,effective_first_new_session,new_symbol,new_source_asset_id,identity_continuity_status,evidence_source,evidence_reference,evidence_date,price_series_continuity_required,corporate_action_adjustment_required,review_status
UNRESOLVED-UUID,UNR,UNRESOLVED-UUID,TICKER_CHANGE,2026-08-14,2026-08-17,NEWUNR,NEW-UUID,UNRESOLVED,NONE,Unverified,2026-08-17,TRUE,NONE,PENDING
"""
        self.registry_path.write_text(csv_content.strip() + "\n", encoding="utf-8")
        resolver = SecurityIdentityResolver(self.registry_path)
        member = {"symbol": "UNR", "source_asset_id": "UNRESOLVED-UUID"}
        res = resolver.resolve_member(member, "2026-08-24")
        self.assertFalse(res.resolved)
        self.assertEqual(res.block_reason, "BLOCK_IDENTITY_CONTINUITY_UNRESOLVED")

    def test_ticker_reuse_by_unrelated_issuer_blocks(self) -> None:
        resolver = SecurityIdentityResolver(self.registry_path)
        member = {"symbol": "REUSED", "source_asset_id": "EXPECTED-UUID-AAA"}

        class MismatchAdapter(FakeAdapter):
            def get_asset(self, symbol: str):
                if symbol == "REUSED":
                    return "PASS", {"id": "UNRELATED-NEW-ISSUER-UUID", "symbol": "REUSED", "status": "active", "tradable": True}
                return super().get_asset(symbol)

        res = resolver.resolve_member(member, "2026-08-24", broker=MismatchAdapter())
        self.assertFalse(res.resolved)
        self.assertEqual(res.block_reason, "BLOCK_IDENTITY_MISMATCH")

    def test_delisting_with_no_successor_legitimate_lifecycle(self) -> None:
        csv_content = """frozen_member_id,original_symbol,original_source_asset_id,event_type,effective_last_old_session,effective_first_new_session,new_symbol,new_source_asset_id,identity_continuity_status,evidence_source,evidence_reference,evidence_date,price_series_continuity_required,corporate_action_adjustment_required,review_status
DELIST-UUID,DELISTED,DELIST-UUID,DELISTING_WITHOUT_SUCCESSOR,2026-08-14,,,,VERIFIED_DISCONTINUITY,SEC,Form 25,2026-08-14,FALSE,NONE,VERIFIED
"""
        self.registry_path.write_text(csv_content.strip() + "\n", encoding="utf-8")
        resolver = SecurityIdentityResolver(self.registry_path)
        member = {"symbol": "DELISTED", "source_asset_id": "DELIST-UUID"}
        res = resolver.resolve_member(member, "2026-08-24")
        self.assertTrue(res.resolved)
        self.assertEqual(res.continuity_status, IdentityContinuityStatus.VERIFIED_DISCONTINUITY.value)
        self.assertIsNone(res.block_reason)

    def test_split_requiring_unresolved_adjustment_blocks(self) -> None:
        csv_content = """frozen_member_id,original_symbol,original_source_asset_id,event_type,effective_last_old_session,effective_first_new_session,new_symbol,new_source_asset_id,identity_continuity_status,evidence_source,evidence_reference,evidence_date,price_series_continuity_required,corporate_action_adjustment_required,review_status
SPLIT-UUID,SPLITCO,SPLIT-UUID,REVERSE_SPLIT,2026-08-14,2026-08-17,SPLITCO,SPLIT-UUID,VERIFIED_CONTINUITY,SEC,8K,2026-08-17,TRUE,EXPLICIT_ADJUSTMENT_REQUIRED,VERIFIED
"""
        self.registry_path.write_text(csv_content.strip() + "\n", encoding="utf-8")
        resolver = SecurityIdentityResolver(self.registry_path)
        member = {"symbol": "SPLITCO", "source_asset_id": "SPLIT-UUID"}
        res = resolver.resolve_member(member, "2026-08-24")
        self.assertFalse(res.resolved)
        self.assertEqual(res.block_reason, "BLOCK_CORPORATE_ACTION_UNRESOLVED")

    def test_identity_registry_modification_changes_hash(self) -> None:
        self.registry_path.write_text("v1", encoding="utf-8")
        resolver = SecurityIdentityResolver(self.registry_path)
        hash1 = resolver.registry_hash()
        self.registry_path.write_text("v2", encoding="utf-8")
        resolver_v2 = SecurityIdentityResolver(self.registry_path)
        hash2 = resolver_v2.registry_hash()
        self.assertNotEqual(hash1, hash2)

    def test_frozen_universe_canonical_hash_remains_unchanged(self) -> None:
        safety = PaperSafetyManager()
        membership_path = ROOT / "research" / "market_edge_discovery_program" / "fuf_001_free_exploratory_universe_freeze" / "fuf001_frozen_membership.csv"
        self.assertTrue(safety.verify_universe_hash(membership_path))
        self.assertEqual(safety.canonical_universe_hash(membership_path), EXPECTED_UNIVERSE_HASH)

    def test_canonical_and_artifact_registry_hash_equality(self) -> None:
        canonical_path = ROOT / "research" / "market_edge_discovery_program" / "fuf_001_free_exploratory_universe_freeze" / "fuf001_identity_event_registry.csv"
        artifact_path = ROOT / "research" / "market_edge_discovery_program" / "paper_001r_identity_remediation" / "identity_event_registry.csv"
        self.assertTrue(canonical_path.exists())
        self.assertTrue(artifact_path.exists())
        canonical_hash = hashlib.sha256(canonical_path.read_bytes()).hexdigest().upper()
        artifact_hash = hashlib.sha256(artifact_path.read_bytes()).hexdigest().upper()
        self.assertEqual(canonical_hash, artifact_hash)

    def test_rebalance_readiness_waiting_when_not_due(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = PaperControllerConfig(
                target_path=None,
                audit_log_path=Path(tmp) / "audit.csv",
                incident_log_path=Path(tmp) / "incidents.csv",
                broker_audit_log_path=Path(tmp) / "order_audit.csv",
            )
            adapter = FakeAdapter(audit_log_path=Path(tmp) / "order_audit.csv")
            # Signal session on mid-month date 2026-08-17 (signal_session = 2026-08-14)
            result_mid = PaperTradingController(config, adapter=adapter).run_dry_run(now=datetime(2026, 8, 17, 14, 0, tzinfo=timezone.utc))
            self.assertEqual(result_mid.identity_readiness_state, "PASS")
            self.assertFalse(result_mid.monthly_rebalance_due)
            self.assertEqual(result_mid.readiness_state, "WAITING_FOR_SCHEDULED_REBALANCE")
            self.assertEqual(result_mid.block_reason, "WAITING_FOR_SCHEDULED_MONTHLY_REBALANCE")

            # Signal session on month-end date (signal_session = 2026-08-31) evaluated on 2026-09-01
            result_end = PaperTradingController(config, adapter=adapter).run_dry_run(now=datetime(2026, 9, 1, 14, 0, tzinfo=timezone.utc))
            self.assertEqual(result_end.identity_readiness_state, "PASS")
            self.assertTrue(result_end.monthly_rebalance_due)
            self.assertEqual(result_end.readiness_state, "READY_FOR_CONTROLLED_PAPER_LAUNCH")
            self.assertEqual(result_end.block_reason, "DRY_RUN_BLOCK_EXECUTION_FLAGS_FALSE")

    def test_golden_signal_equivalence(self) -> None:
        csm_dir = ROOT / "research" / "implementations" / "csm_001"
        tsm_dir = ROOT / "research" / "implementations" / "tsm_001"
        sys.modules.pop("csm001_momentum_model", None)
        sys.modules.pop("tsm001_momentum_model", None)
        sys.modules.pop("feature_pipeline", None)
        sys.path.insert(0, str(csm_dir))
        import csm001_momentum_model

        sys.path.pop(0)
        sys.modules.pop("feature_pipeline", None)
        sys.modules.pop("tsm001_momentum_model", None)
        sys.path.insert(0, str(tsm_dir))
        import tsm001_momentum_model

        sys.path.pop(0)
        sys.modules.pop("feature_pipeline", None)

        dates = pd.bdate_range(end="2026-08-24", periods=300)
        symbols = [f"SYM{i:03d}" for i in range(60)]

        np.random.seed(42)
        price_dict = {}
        for s in symbols:
            returns = np.random.normal(0.0005, 0.015, size=len(dates))
            prices = 100.0 * np.exp(np.cumsum(returns))
            price_dict[s] = prices

        single_panel = pd.DataFrame(price_dict, index=dates)

        split_date = dates[280].date().isoformat()
        next_date = dates[281].date().isoformat()

        rows = []
        for s in symbols:
            if s == "SYM000":
                for dt, p in zip(dates[:281], price_dict[s][:281]):
                    rows.append({"symbol": "SYM000", "date": dt.date().isoformat(), "close": p})
                for dt, p in zip(dates[281:], price_dict[s][281:]):
                    rows.append({"symbol": "NEWSYM000", "date": dt.date().isoformat(), "close": p})
            else:
                for dt, p in zip(dates, price_dict[s]):
                    rows.append({"symbol": s, "date": dt.date().isoformat(), "close": p})

        raw_bars = pd.DataFrame(rows)

        csv_content = f"""frozen_member_id,original_symbol,original_source_asset_id,event_type,effective_last_old_session,effective_first_new_session,new_symbol,new_source_asset_id,identity_continuity_status,evidence_source,evidence_reference,evidence_date,price_series_continuity_required,corporate_action_adjustment_required,review_status
SYM000-UUID,SYM000,SYM000-UUID,TICKER_CHANGE,{split_date},{next_date},NEWSYM000,NEWSYM000-UUID,VERIFIED_CONTINUITY,SEC,8K,{next_date},TRUE,NONE,VERIFIED
"""
        self.registry_path.write_text(csv_content.strip() + "\n", encoding="utf-8")
        resolver = SecurityIdentityResolver(self.registry_path)

        membership_df = pd.DataFrame([{"symbol": s, "source_asset_id": f"{s}-UUID", "frozen_member_id": f"{s}-UUID"} for s in symbols])
        as_of = dates[-1].date().isoformat()
        resolutions = resolver.resolve_universe(membership_df, as_of)

        stitched_series_list = []
        for s in symbols:
            res = resolutions[s]
            status, stitched_member = resolver.stitch_price_series(raw_bars, res, as_of)
            self.assertEqual(status, "PASS")
            stitched_series_list.append(stitched_member)

        stitched_bars = pd.concat(stitched_series_list, ignore_index=True)
        stitched_panel = stitched_bars.pivot(index="date", columns="symbol", values="close").sort_index()
        stitched_panel.index = pd.to_datetime(stitched_panel.index)
        stitched_panel = stitched_panel.reindex(symbols, axis=1)

        csm_single = csm001_momentum_model.CSM001MomentumModel().transform(single_panel).frame
        tsm_single = tsm001_momentum_model.TSM001MomentumModel().transform(single_panel).frame

        csm_stitched = csm001_momentum_model.CSM001MomentumModel().transform(stitched_panel).frame
        tsm_stitched = tsm001_momentum_model.TSM001MomentumModel().transform(stitched_panel).frame

        csm_single["date"] = pd.to_datetime(csm_single["date"]).dt.date.astype(str)
        csm_stitched["date"] = pd.to_datetime(csm_stitched["date"]).dt.date.astype(str)
        tsm_single["date"] = pd.to_datetime(tsm_single["date"]).dt.date.astype(str)
        tsm_stitched["date"] = pd.to_datetime(tsm_stitched["date"]).dt.date.astype(str)

        single_as_of = csm_single[csm_single["date"] == as_of].sort_values("ticker").reset_index(drop=True)
        stitched_as_of = csm_stitched[csm_stitched["date"] == as_of].sort_values("ticker").reset_index(drop=True)

        pd.testing.assert_series_equal(single_as_of["return_12_1"], stitched_as_of["return_12_1"], check_names=False)
        pd.testing.assert_series_equal(single_as_of["csm001_momentum_score"], stitched_as_of["csm001_momentum_score"], check_names=False)
        pd.testing.assert_series_equal(single_as_of["csm001_top_decile_flag"], stitched_as_of["csm001_top_decile_flag"], check_names=False)

        tsm_single_as_of = tsm_single[tsm_single["date"] == as_of].sort_values("ticker").reset_index(drop=True)
        tsm_stitched_as_of = tsm_stitched[tsm_stitched["date"] == as_of].sort_values("ticker").reset_index(drop=True)
        pd.testing.assert_series_equal(tsm_single_as_of["tsm001_state"], tsm_stitched_as_of["tsm001_state"], check_names=False)
        pd.testing.assert_series_equal(tsm_single_as_of["tsm001_positive_state"], tsm_stitched_as_of["tsm001_positive_state"], check_names=False)


if __name__ == "__main__":
    unittest.main(verbosity=2)
