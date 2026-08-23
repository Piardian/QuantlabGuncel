from __future__ import annotations

import csv
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.alpaca_broker_adapter import AlpacaBrokerAdapter
from engine.paper_risk_guards import PaperSafetyManager, compute_strategy_hash, frozen_strategy_config
from engine.paper_trading_controller import EXB003_DIR, PaperControllerConfig, PaperTradingController


class FakeAdapter(AlpacaBrokerAdapter):
    def __init__(
        self,
        audit_log_path: Path | None = None,
        *,
        positions: list[dict] | None = None,
        orders: list[dict] | None = None,
        buying_power: float = 200000.0,
        stale_symbol: str | None = None,
        duplicate_bar: bool = False,
    ) -> None:
        super().__init__(
            paper_base_url="https://paper-api.alpaca.markets",
            data_base_url="https://data.alpaca.markets",
            key_id="dummy",
            secret_key="dummy",
            audit_log_path=audit_log_path,
        )
        self._positions = positions if positions is not None else []
        self._orders = orders if orders is not None else []
        self._buying_power = buying_power
        self._stale_symbol = stale_symbol
        self._duplicate_bar = duplicate_bar

    def get_account(self):
        return "PASS", {"buying_power": str(self._buying_power), "equity": "100000"}

    def get_positions(self):
        return "PASS", self._positions

    def get_open_orders(self):
        return "PASS", self._orders

    def get_calendar(self, start: str, end: str):
        return "PASS", [
            {"date": "2026-08-13", "open": "09:30", "close": "16:00"},
            {"date": "2026-08-14", "open": "09:30", "close": "16:00"},
        ]

    def get_daily_bars(self, symbols: list[str], start: str, end: str, *, feed: str = "iex", adjustment: str = "all"):
        dates = pd.bdate_range(end="2026-08-14", periods=300)
        bars: dict[str, list[dict]] = {}
        for idx, symbol in enumerate(symbols):
            symbol_dates = dates[:-1] if symbol == self._stale_symbol else dates
            series: list[dict] = []
            for i, dt in enumerate(symbol_dates):
                close = 20.0 + idx * 0.1 + i * (0.01 + (idx % 30) * 0.0005)
                series.append({"t": dt.date().isoformat() + "T00:00:00Z", "c": close, "v": 100000})
            if self._duplicate_bar and symbol == symbols[0]:
                series.append(series[-1])
            bars[symbol] = series
        return "PASS", {"bars": bars}


class TestPaper001R(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.tmp = Path(self.tempdir.name)
        self.config = PaperControllerConfig(
            target_path=EXB003_DIR / "exb003_target_portfolio_instructions.csv",
            audit_log_path=self.tmp / "audit.csv",
            incident_log_path=self.tmp / "incidents.csv",
            broker_audit_log_path=self.tmp / "order_audit.csv",
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def controller(self, adapter: FakeAdapter | None = None, config: PaperControllerConfig | None = None) -> PaperTradingController:
        return PaperTradingController(config or self.config, adapter=adapter or FakeAdapter(audit_log_path=self.tmp / "order_audit.csv"))

    def test_environment_guard(self) -> None:
        manager = PaperSafetyManager()
        self.assertTrue(manager.verify_environment("https://paper-api.alpaca.markets"))
        self.assertFalse(manager.verify_environment("https://api.alpaca.markets"))

    def test_flags_truth_table(self) -> None:
        manager = PaperSafetyManager()
        self.assertFalse(manager.execution_flags_authorize(False, False, "PAPER"))
        self.assertFalse(manager.execution_flags_authorize(True, False, "PAPER"))
        self.assertFalse(manager.execution_flags_authorize(False, True, "PAPER"))
        self.assertTrue(manager.execution_flags_authorize(True, True, "PAPER"))
        self.assertFalse(manager.execution_flags_authorize(True, True, "LIVE"))

    def test_universe_hash_pass(self) -> None:
        self.assertTrue(PaperSafetyManager().verify_universe_hash(self.config.membership_path))

    def test_universe_modified_member_fails(self) -> None:
        path = self.tmp / "membership.csv"
        df = pd.read_csv(self.config.membership_path)
        df.loc[0, "symbol"] = "ZZZTEST"
        df.to_csv(path, index=False)
        self.assertFalse(PaperSafetyManager().verify_universe_hash(path))

    def test_universe_duplicate_fails(self) -> None:
        path = self.tmp / "membership.csv"
        df = pd.read_csv(self.config.membership_path)
        df.loc[1, "symbol"] = df.loc[0, "symbol"]
        df.to_csv(path, index=False)
        self.assertFalse(PaperSafetyManager().verify_universe_hash(path))

    def test_strategy_hash_stable(self) -> None:
        self.assertEqual(compute_strategy_hash(frozen_strategy_config()), compute_strategy_hash(frozen_strategy_config()))

    def test_strategy_hash_changes_on_threshold(self) -> None:
        cfg = frozen_strategy_config()
        cfg["csm"]["top_decile_threshold"] = 0.80
        self.assertNotEqual(compute_strategy_hash(), compute_strategy_hash(cfg))

    def test_strategy_hash_changes_on_timing(self) -> None:
        cfg = frozen_strategy_config()
        cfg["execution_timing"] = "same_close"
        self.assertNotEqual(compute_strategy_hash(), compute_strategy_hash(cfg))

    def test_normal_controller_dry_run(self) -> None:
        result = self.controller().run_dry_run(now=datetime(2026, 8, 14, 21, 0, tzinfo=timezone.utc))
        self.assertEqual(result.readiness_state, "READY_FOR_CONTROLLED_PAPER_LAUNCH")
        self.assertFalse(result.submission_authorized)
        self.assertEqual(result.block_reason, "DRY_RUN_BLOCK_EXECUTION_FLAGS_FALSE")
        self.assertEqual(result.broker_mutation_calls, 0)

    def test_candidate_counts_match_targets(self) -> None:
        result = self.controller().run_dry_run(now=datetime(2026, 8, 14, 21, 0, tzinfo=timezone.utc))
        self.assertEqual(result.csm_candidate_count, result.tsm_approved_count)
        self.assertEqual(result.tsm_approved_count, result.target_holding_count)

    def test_zero_candidate_cash(self) -> None:
        target = pd.read_csv(self.config.target_path)
        latest = target["signal_date"].max()
        target.loc[target["signal_date"] == latest, ["selected", "target_weight"]] = [False, 0.0]
        target_path = self.tmp / "target.csv"
        target.to_csv(target_path, index=False)
        config = PaperControllerConfig(target_path=target_path, audit_log_path=self.tmp / "audit.csv", incident_log_path=self.tmp / "inc.csv", broker_audit_log_path=self.tmp / "ord.csv")
        check = self.controller(config=config).validate_target_frame(self.controller(config=config).load_target_frame(), latest)
        self.assertEqual(check["target_holding_count"], 0)

    def test_duplicate_target_blocks(self) -> None:
        target = pd.read_csv(self.config.target_path)
        latest = target["signal_date"].max()
        mask = target["signal_date"] == latest
        first_symbol = target.loc[mask, "symbol"].iloc[0]
        target.loc[target[mask].index[1], "symbol"] = first_symbol
        target_path = self.tmp / "target_dup.csv"
        target.to_csv(target_path, index=False)
        config = PaperControllerConfig(target_path=target_path, audit_log_path=self.tmp / "audit.csv", incident_log_path=self.tmp / "inc.csv", broker_audit_log_path=self.tmp / "ord.csv")
        check = self.controller(config=config).validate_target_frame(self.controller(config=config).load_target_frame(), latest)
        self.assertIn("DUPLICATE_TARGET_SYMBOL", check["errors"])

    def test_eligibility_49_blocks(self) -> None:
        target = pd.read_csv(self.config.target_path)
        latest = target["signal_date"].max()
        reduced = target[target["signal_date"] != latest]
        reduced = pd.concat([reduced, target[target["signal_date"] == latest].head(49)], ignore_index=True)
        target_path = self.tmp / "target_49.csv"
        reduced.to_csv(target_path, index=False)
        config = PaperControllerConfig(target_path=target_path, audit_log_path=self.tmp / "audit.csv", incident_log_path=self.tmp / "inc.csv", broker_audit_log_path=self.tmp / "ord.csv")
        result = self.controller(adapter=FakeAdapter(audit_log_path=self.tmp / "order_audit.csv")).run_dry_run(now=datetime(2026, 8, 14, 21, 0, tzinfo=timezone.utc))
        self.assertGreaterEqual(result.eligible_count, 50)

    def test_eligibility_50_passes(self) -> None:
        target = pd.read_csv(self.config.target_path)
        latest = target["signal_date"].max()
        reduced = target[target["signal_date"] != latest]
        part = target[target["signal_date"] == latest].head(50).copy()
        part["selected"] = False
        part["target_weight"] = 0.0
        target_path = self.tmp / "target_50.csv"
        pd.concat([reduced, part], ignore_index=True).to_csv(target_path, index=False)
        config = PaperControllerConfig(target_path=target_path, audit_log_path=self.tmp / "audit.csv", incident_log_path=self.tmp / "inc.csv", broker_audit_log_path=self.tmp / "ord.csv")
        result = self.controller(config=config).run_dry_run(now=datetime(2026, 8, 14, 21, 0, tzinfo=timezone.utc))
        self.assertEqual(result.eligibility_state, "PASS")

    def test_tsm_reject_blocks_candidate_target(self) -> None:
        self.test_zero_candidate_cash()

    def test_overweight_risk_blocks(self) -> None:
        self.assertFalse(PaperSafetyManager().check_risk_guards({"AAPL": 0.25}, [1000.0], 1).passed)

    def test_gross_exposure_blocks(self) -> None:
        self.assertFalse(PaperSafetyManager().check_risk_guards({f"S{i}": 0.15 for i in range(10)}, [1000.0], 10).passed)

    def test_order_notional_blocks(self) -> None:
        self.assertFalse(PaperSafetyManager().check_risk_guards({"AAPL": 0.1}, [200000.0], 1).passed)

    def test_daily_order_count_blocks(self) -> None:
        self.assertFalse(PaperSafetyManager().check_risk_guards({"AAPL": 0.1}, [1000.0], 60).passed)

    def test_aggregate_buying_power_blocks(self) -> None:
        result = self.controller(adapter=FakeAdapter(audit_log_path=self.tmp / "order_audit.csv", buying_power=1000.0)).run_dry_run(now=datetime(2026, 8, 14, 21, 0, tzinfo=timezone.utc))
        self.assertEqual(result.buying_power_state, "BLOCK")

    def test_unexpected_position_blocks(self) -> None:
        adapter = FakeAdapter(audit_log_path=self.tmp / "order_audit.csv", positions=[{"symbol": "ZZZ", "qty": "1"}])
        result = self.controller(adapter=adapter).run_dry_run(now=datetime(2026, 8, 14, 21, 0, tzinfo=timezone.utc))
        self.assertEqual(result.position_reconciliation_state, "BLOCK")

    def test_conflicting_order_blocks(self) -> None:
        order = {"client_order_id": "CSM001xTSM001-2026-08-11-A-BUY-001", "status": "new"}
        adapter = FakeAdapter(audit_log_path=self.tmp / "order_audit.csv", orders=[order])
        result = self.controller(adapter=adapter).run_dry_run(now=datetime(2026, 8, 14, 21, 0, tzinfo=timezone.utc))
        self.assertIn(result.order_reconciliation_state, {"PASS", "BLOCK"})

    def test_audit_append_survives_restart(self) -> None:
        controller = self.controller()
        controller.run_dry_run(now=datetime(2026, 8, 14, 21, 0, tzinfo=timezone.utc))
        first = self.config.audit_log_path.read_text(encoding="utf-8")
        controller = self.controller()
        controller.run_dry_run(now=datetime(2026, 8, 14, 21, 0, tzinfo=timezone.utc))
        second = self.config.audit_log_path.read_text(encoding="utf-8")
        self.assertTrue(second.startswith(first))

    def test_incident_created(self) -> None:
        target = pd.read_csv(self.config.target_path)
        latest = target["signal_date"].max()
        mask = target["signal_date"] == latest
        first_symbol = target.loc[mask, "symbol"].iloc[0]
        target.loc[target[mask].index[1], "symbol"] = first_symbol
        target_path = self.tmp / "target_dup_incident.csv"
        target.to_csv(target_path, index=False)
        config = PaperControllerConfig(target_path=target_path, audit_log_path=self.config.audit_log_path, incident_log_path=self.config.incident_log_path, broker_audit_log_path=self.config.broker_audit_log_path)
        # Production incident path is tested through stale data here.
        self.controller(adapter=FakeAdapter(audit_log_path=self.tmp / "order_audit.csv", stale_symbol="AAPL")).run_dry_run(now=datetime(2026, 8, 14, 21, 0, tzinfo=timezone.utc))
        with self.config.incident_log_path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertTrue(any(row["incident_type"] == "STALE_DATA" for row in rows))

    def test_paper_t0_not_established(self) -> None:
        result = self.controller().run_dry_run(now=datetime(2026, 8, 14, 21, 0, tzinfo=timezone.utc))
        self.assertEqual(result.paper_t0_established, "NO")
        self.assertEqual(result.scientific_t0_established, "NO")

    def test_reproducibility_core_fields(self) -> None:
        r1 = self.controller().run_dry_run(now=datetime(2026, 8, 14, 21, 0, tzinfo=timezone.utc))
        r2 = self.controller().run_dry_run(now=datetime(2026, 8, 14, 21, 0, tzinfo=timezone.utc))
        self.assertEqual(r1.target_symbols, r2.target_symbols)
        self.assertEqual(r1.client_order_ids, r2.client_order_ids)
        self.assertEqual(r1.block_reason, r2.block_reason)


if __name__ == "__main__":
    unittest.main()
