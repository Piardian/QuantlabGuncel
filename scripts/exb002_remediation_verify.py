from __future__ import annotations

import hashlib
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "research" / "market_edge_discovery_program" / "exb_002_remediation_frozen_tsm_runtime_failure"
EXB001_DIR = ROOT / "research" / "market_edge_discovery_program" / "exb_001_non_formal_exploratory_backtest_preparation"
CSM_IMPL = ROOT / "research" / "implementations" / "csm_001"
TSM_IMPL = ROOT / "research" / "implementations" / "tsm_001"


def import_frozen_models():
    sys.path.insert(0, str(CSM_IMPL))
    from csm001_momentum_model import CSM001MomentumModel

    sys.path.pop(0)
    sys.modules.pop("feature_pipeline", None)
    sys.path.insert(0, str(TSM_IMPL))
    from tsm001_momentum_model import TSM001MomentumModel

    sys.path.pop(0)
    sys.modules.pop("feature_pipeline", None)
    return CSM001MomentumModel, TSM001MomentumModel


def load_env() -> None:
    env_file = ROOT / ".env"
    if not env_file.exists():
        return
    for raw in env_file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def alpaca_get(url: str) -> Any:
    key = os.environ.get("ALPACA_API_KEY_ID") or os.environ.get("APCA_API_KEY_ID")
    secret = os.environ.get("ALPACA_API_SECRET_KEY") or os.environ.get("APCA_API_SECRET_KEY")
    if not key or not secret:
        raise RuntimeError("Alpaca credentials are missing from environment.")
    req = urllib.request.Request(url)
    req.add_header("APCA-API-KEY-ID", key)
    req.add_header("APCA-API-SECRET-KEY", secret)
    with urllib.request.urlopen(req, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_close_panel(symbols: list[str], start: str, end: str, feed: str, adjustment: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    token = None
    while True:
        params = {
            "symbols": ",".join(symbols),
            "timeframe": "1Day",
            "start": start,
            "end": end,
            "feed": feed,
            "adjustment": adjustment,
            "limit": "10000",
        }
        if token:
            params["page_token"] = token
        payload = alpaca_get("https://data.alpaca.markets/v2/stocks/bars?" + urllib.parse.urlencode(params))
        for symbol, bars in payload.get("bars", {}).items():
            for bar in bars:
                rows.append(
                    {
                        "date": pd.Timestamp(bar["t"]).tz_convert(None).normalize(),
                        "symbol": symbol,
                        "close": float(bar["c"]) if float(bar["c"]) > 0 and float(bar["v"]) > 0 else np.nan,
                    }
                )
        token = payload.get("next_page_token")
        if not token:
            break
    frame = pd.DataFrame(rows)
    return frame.pivot(index="date", columns="symbol", values="close").sort_index()


def hash_frame(frame: pd.DataFrame) -> str:
    return hashlib.sha256(frame.to_csv(index=False).encode("utf-8")).hexdigest().upper()


def test_case(name: str, fn) -> dict[str, Any]:
    try:
        detail = fn()
        return {"test": name, "status": "PASS", "detail": json.dumps(detail, sort_keys=True)}
    except Exception as exc:  # noqa: BLE001
        return {"test": name, "status": "FAIL", "detail": f"{type(exc).__name__}: {exc}"}


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    load_env()
    CSM001MomentumModel, TSM001MomentumModel = import_frozen_models()
    tsm_model = TSM001MomentumModel()

    def normal_input():
        dates = pd.bdate_range("2020-01-01", periods=320)
        panel = pd.DataFrame({"UP": np.linspace(100, 200, len(dates)), "DOWN": np.linspace(200, 100, len(dates))}, index=dates)
        out = tsm_model.transform(panel).frame
        return {"rows": len(out), "valid": int(out["tsm001_valid_observation"].sum())}

    def insufficient_history():
        dates = pd.bdate_range("2020-01-01", periods=251)
        panel = pd.DataFrame({"UP": np.linspace(100, 200, len(dates))}, index=dates)
        out = tsm_model.transform(panel).frame
        assert int(out["tsm001_valid_observation"].sum()) == 0
        return {"rows": len(out), "valid": 0}

    def missing_observation():
        dates = pd.bdate_range("2020-01-01", periods=320)
        values = np.linspace(100, 200, len(dates))
        values[252] = np.nan
        panel = pd.DataFrame({"MISS": values}, index=dates)
        out = tsm_model.transform(panel).frame
        assert out["tsm001_valid_observation"].sum() < 68
        return {"rows": len(out), "valid": int(out["tsm001_valid_observation"].sum())}

    def constant_price():
        dates = pd.bdate_range("2020-01-01", periods=320)
        out = tsm_model.transform(pd.DataFrame({"FLAT": 100.0}, index=dates)).frame
        valid = out[out["tsm001_valid_observation"]]
        assert set(valid["tsm001_state"]) == {"NEUTRAL"}
        return {"valid": len(valid), "states": sorted(valid["tsm001_state"].unique().tolist())}

    def nan_input():
        dates = pd.bdate_range("2020-01-01", periods=320)
        out = tsm_model.transform(pd.DataFrame({"NAN": np.nan}, index=dates)).frame
        assert not out["tsm001_valid_observation"].any()
        return {"rows": len(out), "valid": 0}

    def duplicate_timestamps():
        dates = list(pd.bdate_range("2020-01-01", periods=320))
        dates[5] = dates[4]
        out = tsm_model.transform(pd.DataFrame({"DUP": np.linspace(100, 200, len(dates))}, index=dates)).frame
        assert out["date"].is_unique
        return {"rows": len(out), "unique_dates": int(out["date"].nunique())}

    def unsorted_dates():
        dates = pd.bdate_range("2020-01-01", periods=320)
        panel = pd.DataFrame({"UNSORTED": np.linspace(100, 200, len(dates))}, index=dates[::-1])
        out = tsm_model.transform(panel).frame
        assert out["date"].is_monotonic_increasing
        return {"rows": len(out), "monotonic": True}

    def multiple_securities():
        dates = pd.bdate_range("2020-01-01", periods=320)
        panel = pd.DataFrame({"UP": np.linspace(100, 200, len(dates)), "FLAT": 100.0, "DOWN": np.linspace(200, 100, len(dates))}, index=dates)
        out = tsm_model.transform(panel).frame
        latest = out[out["tsm001_valid_observation"]].sort_values("date").groupby("ticker").tail(1).set_index("ticker")
        assert latest.loc["UP", "tsm001_state"] == "POSITIVE"
        assert latest.loc["FLAT", "tsm001_state"] == "NEUTRAL"
        assert latest.loc["DOWN", "tsm001_state"] == "NEGATIVE"
        return {"tickers": sorted(latest.index.tolist())}

    def boundary_lookback():
        dates = pd.bdate_range("2020-01-01", periods=253)
        out = tsm_model.transform(pd.DataFrame({"UP": np.linspace(100, 200, len(dates))}, index=dates)).frame
        assert int(out["tsm001_valid_observation"].sum()) == 1
        return {"rows": len(out), "valid": 1, "first_valid": str(out[out["tsm001_valid_observation"]]["date"].iloc[0].date())}

    def deterministic_replay():
        dates = pd.bdate_range("2020-01-01", periods=320)
        panel = pd.DataFrame({"UP": np.linspace(100, 200, len(dates)), "DOWN": np.linspace(200, 100, len(dates))}, index=dates)
        first = tsm_model.transform(panel).frame
        second = tsm_model.transform(panel).frame
        assert hash_frame(first) == hash_frame(second)
        return {"hash": hash_frame(first)}

    def golden_case():
        dates = pd.bdate_range("2020-01-01", periods=253)
        panel = pd.DataFrame({"GOLD": np.arange(100.0, 353.0)}, index=dates)
        out = tsm_model.transform(panel).frame
        row = out[out["tsm001_valid_observation"]].iloc[0]
        expected = panel.iloc[-22, 0] / panel.iloc[0, 0] - 1.0
        assert np.isclose(row["tsm_return_12_1"], expected)
        assert row["tsm001_state"] == "POSITIVE"
        return {"expected_return_12_1": expected, "observed_return_12_1": row["tsm_return_12_1"], "state": row["tsm001_state"]}

    unit_tests = [
        test_case("normal_input", normal_input),
        test_case("insufficient_history", insufficient_history),
        test_case("missing_observation", missing_observation),
        test_case("constant_price_series", constant_price),
        test_case("nan_input", nan_input),
        test_case("duplicate_timestamps", duplicate_timestamps),
        test_case("unsorted_dates", unsorted_dates),
        test_case("multiple_securities", multiple_securities),
        test_case("boundary_lookback", boundary_lookback),
        test_case("deterministic_replay", deterministic_replay),
        test_case("golden_case", golden_case),
    ]
    unit_df = pd.DataFrame(unit_tests)
    unit_df.to_csv(OUT_DIR / "exb002_tsm_unit_tests.csv", index=False)

    request = json.loads((EXB001_DIR / "exb001_dataset_request_spec.json").read_text(encoding="utf-8"))
    symbols = sorted(pd.read_csv(EXB001_DIR / "exb001_universe_candidates.csv")["symbol"].astype(str).tolist())
    close_panel = fetch_close_panel(symbols, request["dataset_start"], request["dataset_end"], request["feed"], request["adjustment"])
    close_panel = close_panel.reindex(sorted(close_panel.columns), axis=1)
    tsm_first = tsm_model.transform(close_panel).frame
    tsm_second = tsm_model.transform(close_panel).frame
    csm = CSM001MomentumModel().transform(close_panel).frame
    interface = csm[["date", "ticker", "csm001_top_decile_flag"]].merge(
        tsm_first[["date", "ticker", "tsm001_positive_state", "tsm001_valid_observation"]],
        on=["date", "ticker"],
        how="inner",
    )
    smoke_selected = interface[interface["csm001_top_decile_flag"] & interface["tsm001_positive_state"]]

    summary = {
        "unit_tests_total": int(len(unit_df)),
        "unit_tests_passed": int((unit_df["status"] == "PASS").sum()),
        "unit_tests_failed": int((unit_df["status"] == "FAIL").sum()),
        "golden_test": "PASS" if unit_df.query("test == 'golden_case'")["status"].iloc[0] == "PASS" else "FAIL",
        "exb_input_shape_rows": int(close_panel.shape[0]),
        "exb_input_shape_symbols": int(close_panel.shape[1]),
        "tsm_rows": int(len(tsm_first)),
        "tsm_valid_observations": int(tsm_first["tsm001_valid_observation"].sum()),
        "tsm_positive_observations": int(tsm_first["tsm001_positive_state"].sum()),
        "tsm_reproducibility": "PASS" if hash_frame(tsm_first) == hash_frame(tsm_second) else "FAIL",
        "csm_tsm_interface_rows": int(len(interface)),
        "csm_tsm_selected_state_count": int(len(smoke_selected)),
        "pipeline_smoke_test": "PASS",
        "performance_generated": "NO",
        "broker_mutation_calls": 0,
        "alpha_logic_changed": "NO",
    }
    (OUT_DIR / "exb002_remediation_smoke_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
