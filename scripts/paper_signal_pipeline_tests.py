from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.paper_trading_controller import PaperControllerConfig, PaperTradingController
from scripts.paper_safety_tests import FakeAdapter


class TestPaperSignalPipeline(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.tmp = Path(self.tempdir.name)
        self.config = PaperControllerConfig(
            target_path=None,
            audit_log_path=self.tmp / "audit.csv",
            incident_log_path=self.tmp / "incidents.csv",
            broker_audit_log_path=self.tmp / "order_audit.csv",
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def controller(self, adapter: FakeAdapter | None = None) -> PaperTradingController:
        return PaperTradingController(self.config, adapter=adapter or FakeAdapter(audit_log_path=self.tmp / "order_audit.csv"))

    def test_production_path_does_not_require_snapshot_target(self) -> None:
        result = self.controller().run_dry_run(now=datetime(2026, 8, 14, 21, 0, tzinfo=timezone.utc))
        self.assertEqual(result.signal_data_source, "ALPACA_DAILY_BARS")
        self.assertEqual(result.signal_as_of_session, "2026-08-14")
        self.assertEqual(result.frozen_universe_count, 250)
        self.assertEqual(result.symbols_requested, 250)
        self.assertGreaterEqual(result.eligible_count, 50)
        self.assertEqual(result.broker_mutation_calls, 0)

    def test_stale_symbol_blocks_fail_closed(self) -> None:
        result = self.controller(FakeAdapter(audit_log_path=self.tmp / "order_audit.csv", stale_symbol="AAPL")).run_dry_run(
            now=datetime(2026, 8, 14, 21, 0, tzinfo=timezone.utc)
        )
        self.assertEqual(result.freshness_state, "FAIL")
        self.assertIn("STALE_DATA", result.incidents)
        self.assertEqual(result.broker_mutation_calls, 0)

    def test_duplicate_bar_blocks_fail_closed(self) -> None:
        result = self.controller(FakeAdapter(audit_log_path=self.tmp / "order_audit.csv", duplicate_bar=True)).run_dry_run(
            now=datetime(2026, 8, 14, 21, 0, tzinfo=timezone.utc)
        )
        self.assertIn("DUPLICATE_BAR", result.incidents)
        self.assertEqual(result.readiness_state, "BLOCKED")
        self.assertEqual(result.broker_mutation_calls, 0)

    def test_true_future_dated_bar_blocks(self) -> None:
        class FutureBarFakeAdapter(FakeAdapter):
            def get_daily_bars(self, symbols: list[str], start: str, end: str, *, feed: str = "iex", adjustment: str = "all"):
                status, payload = super().get_daily_bars(symbols, start, end, feed=feed, adjustment=adjustment)
                first_symbol = symbols[0]
                payload["bars"][first_symbol].append({"t": "2026-08-15T00:00:00Z", "c": 999.0, "v": 100000})
                return status, payload

        result = self.controller(FutureBarFakeAdapter(audit_log_path=self.tmp / "order_audit.csv")).run_dry_run(
            now=datetime(2026, 8, 14, 21, 0, tzinfo=timezone.utc)
        )
        self.assertIn("FUTURE_BAR", result.incidents)
        self.assertEqual(result.readiness_state, "BLOCKED")
        self.assertEqual(result.broker_mutation_calls, 0)

    def test_incomplete_current_session_uses_prior_completed_session(self) -> None:
        result = self.controller().run_dry_run(now=datetime(2026, 8, 14, 15, 0, tzinfo=timezone.utc))
        self.assertEqual(result.signal_as_of_session, "2026-08-13")
        self.assertEqual(result.freshness_state, "PASS")
        self.assertNotIn("FUTURE_BAR", result.incidents)
        self.assertEqual(result.broker_mutation_calls, 0)

    def test_signal_snapshot_is_generated_from_current_bars(self) -> None:
        self.controller().run_dry_run(now=datetime(2026, 8, 14, 21, 0, tzinfo=timezone.utc))
        snapshot_path = ROOT / "research" / "market_edge_discovery_program" / "paper_001r_remediation" / "paper001r_current_signal_snapshot.csv"
        snapshot = pd.read_csv(snapshot_path)
        self.assertIn("symbol", snapshot.columns)
        self.assertIn("csm_candidate", snapshot.columns)
        self.assertIn("tsm_approved", snapshot.columns)
        self.assertIn("target_weight", snapshot.columns)
        self.assertEqual(len(snapshot), 250)
        self.assertGreaterEqual(int(snapshot["csm_candidate"].sum()), int(snapshot["target_weight"].gt(0).sum()))

    def test_live_signal_target_changes_when_bar_data_changes(self) -> None:
        controller = self.controller()
        base = controller.run_dry_run(now=datetime(2026, 8, 14, 21, 0, tzinfo=timezone.utc))

        class ReversedFakeAdapter(FakeAdapter):
            def get_daily_bars(self, symbols: list[str], start: str, end: str, *, feed: str = "iex", adjustment: str = "all"):
                status, payload = super().get_daily_bars(list(reversed(symbols)), start, end, feed=feed, adjustment=adjustment)
                return status, payload

        changed = self.controller(ReversedFakeAdapter(audit_log_path=self.tmp / "order_audit_2.csv")).run_dry_run(
            now=datetime(2026, 8, 14, 21, 0, tzinfo=timezone.utc)
        )
        self.assertNotEqual(base.target_symbols, changed.target_symbols)
        self.assertEqual(changed.broker_mutation_calls, 0)


if __name__ == "__main__":
    unittest.main()
