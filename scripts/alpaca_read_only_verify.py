"""ALP-002 read-only Alpaca integration verification.

This script performs GET-only requests against Alpaca Paper/trading and
market-data endpoints. It never submits, cancels, replaces, or closes orders.

Secrets are read from environment variables or an untracked local .env file.
Secret values are never printed or written to artifacts.
"""

from __future__ import annotations

import csv
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "research" / "market_edge_discovery_program" / "alp_002_read_only_integration_verification"
SPEC_PATH = OUT_DIR / "alp002_test_spec.json"
OBSERVED_PATH = OUT_DIR / "alp002_observed_results.json"
ENDPOINT_CSV = OUT_DIR / "alp002_endpoint_verification.csv"


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


def infer_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "str"
    if isinstance(value, list):
        return "list"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def schema_from_payload(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        sample = payload[0] if payload else {}
    elif isinstance(payload, dict):
        if "bars" in payload and isinstance(payload["bars"], dict):
            first_list = next((v for v in payload["bars"].values() if isinstance(v, list) and v), [])
            sample = first_list[0] if first_list else {}
        elif "corporate_actions" in payload and isinstance(payload["corporate_actions"], list):
            sample = payload["corporate_actions"][0] if payload["corporate_actions"] else {}
        else:
            sample = payload
    else:
        sample = {}

    if not isinstance(sample, dict):
        return []

    return [
        {
            "field": key,
            "type": infer_type(value),
            "nullable_observed": value is None,
        }
        for key, value in sorted(sample.items())
    ]


class ReadOnlyAlpacaClient:
    def __init__(self, paper_base_url: str, data_base_url: str, key_id: str, secret_key: str) -> None:
        self.paper_base_url = paper_base_url.rstrip("/")
        self.data_base_url = data_base_url.rstrip("/")
        self.headers = {
            "APCA-API-KEY-ID": key_id,
            "APCA-API-SECRET-KEY": secret_key,
            "Accept": "application/json",
        }
        self.order_mutation_calls = 0

    def get_json(self, base_url: str, path: str, params: dict[str, Any] | None = None) -> tuple[str, Any]:
        query = f"?{urlencode(params, doseq=True)}" if params else ""
        url = f"{base_url}{path}{query}"
        request = Request(url, headers=self.headers, method="GET")

        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                with urlopen(request, timeout=30) as response:
                    body = response.read().decode("utf-8")
                    return "PASS", json.loads(body) if body else None
            except HTTPError as exc:
                status = exc.code
                if status in {401, 403, 404}:
                    return f"HTTP_{status}", {"error": exc.reason}
                if status == 429 and attempt < max_attempts:
                    time.sleep(attempt)
                    continue
                return f"HTTP_{status}", {"error": exc.reason}
            except (URLError, TimeoutError) as exc:
                if attempt < max_attempts:
                    time.sleep(attempt)
                    continue
                return "NETWORK_FAIL", {"error": str(exc)}
        return "FAIL", {"error": "unreachable"}

    def get_account(self) -> tuple[str, Any]:
        return self.get_json(self.paper_base_url, "/v2/account")

    def get_assets(self) -> tuple[str, Any]:
        return self.get_json(self.paper_base_url, "/v2/assets", {"status": "active", "asset_class": "us_equity"})

    def get_asset(self, symbol: str) -> tuple[str, Any]:
        return self.get_json(self.paper_base_url, f"/v2/assets/{symbol}")

    def get_calendar(self, start: str, end: str) -> tuple[str, Any]:
        return self.get_json(self.paper_base_url, "/v2/calendar", {"start": start, "end": end})

    def get_positions(self) -> tuple[str, Any]:
        return self.get_json(self.paper_base_url, "/v2/positions")

    def get_daily_bars(self, symbols: list[str], timeframe: str, start: str, end: str, feed: str, adjustment: str) -> tuple[str, Any]:
        params = {
            "symbols": ",".join(symbols),
            "timeframe": timeframe,
            "start": start,
            "end": end,
            "feed": feed,
            "adjustment": adjustment,
        }
        return self.get_json(self.data_base_url, "/v2/stocks/bars", params)

    def get_corporate_actions(self, spec: dict[str, Any]) -> tuple[str, Any]:
        params = {
            "ca_types": ",".join(spec["ca_types"]),
            "since": spec["since"],
            "until": spec["until"],
            "symbols": ",".join(spec["symbols"]),
        }
        return self.get_json(self.paper_base_url, "/v2/corporate_actions", params)


def summarize_count(payload: Any) -> int:
    if isinstance(payload, list):
        return len(payload)
    if isinstance(payload, dict) and "bars" in payload and isinstance(payload["bars"], dict):
        return sum(len(v) for v in payload["bars"].values() if isinstance(v, list))
    if isinstance(payload, dict) and "corporate_actions" in payload and isinstance(payload["corporate_actions"], list):
        return len(payload["corporate_actions"])
    if isinstance(payload, dict):
        return 1
    return 0


def status_to_result(status: str, allow_empty: bool, count: int) -> str:
    if status == "PASS" and (allow_empty or count > 0):
        return "PASS"
    if status == "PASS" and count == 0:
        return "PARTIAL"
    if status in {"HTTP_403"}:
        return "NOT_ENTITLED"
    return "FAIL"


def write_endpoint_csv(rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "endpoint",
        "method",
        "http_result",
        "verification_result",
        "record_count",
        "secret_written",
        "mutation_call",
        "notes",
    ]
    with ENDPOINT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    load_local_env(REPO_ROOT / ".env")
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))

    paper_base = os.environ.get("APCA_API_BASE_URL", spec["paper_base_url"]).rstrip("/")
    if paper_base != "https://paper-api.alpaca.markets":
        observed = {
            "overall_status": "ALP002_WRONG_ENVIRONMENT",
            "paper_base_url_is_paper": False,
            "order_mutation_calls": 0,
        }
        OBSERVED_PATH.write_text(json.dumps(observed, indent=2), encoding="utf-8")
        print(json.dumps(observed, indent=2))
        return 3

    client = ReadOnlyAlpacaClient(
        paper_base_url=paper_base,
        data_base_url=spec["market_data_base_url"],
        key_id=require_env("APCA_API_KEY_ID"),
        secret_key=require_env("APCA_API_SECRET_KEY"),
    )

    checks: dict[str, dict[str, Any]] = {}
    endpoint_rows: list[dict[str, Any]] = []

    def record(name: str, endpoint: str, status: str, payload: Any, allow_empty: bool = False, notes: str = "") -> None:
        count = summarize_count(payload)
        result = status_to_result(status, allow_empty=allow_empty, count=count)
        checks[name] = {
            "http_result": status,
            "verification_result": result,
            "record_count": count,
            "schema": schema_from_payload(payload),
            "notes": notes,
        }
        endpoint_rows.append(
            {
                "endpoint": endpoint,
                "method": "GET",
                "http_result": status,
                "verification_result": result,
                "record_count": count,
                "secret_written": "NO",
                "mutation_call": "NO",
                "notes": notes,
            }
        )

    status, payload = client.get_account()
    record("account", "/v2/account", status, payload, notes="safe account metadata only")

    status, payload = client.get_assets()
    record("assets", "/v2/assets", status, payload, notes="active us_equity list")

    status, payload = client.get_asset(spec["single_asset_symbol"])
    record("single_asset", "/v2/assets/{symbol}", status, payload, notes=spec["single_asset_symbol"])

    status, payload = client.get_calendar(spec["calendar"]["start"], spec["calendar"]["end"])
    record("calendar", "/v2/calendar", status, payload, notes="frozen date range")

    bars_spec = spec["historical_bars"]
    status, payload = client.get_daily_bars(
        symbols=bars_spec["symbols"],
        timeframe=bars_spec["timeframe"],
        start=bars_spec["start"],
        end=bars_spec["end"],
        feed=bars_spec["feed"],
        adjustment=bars_spec["adjustment"],
    )
    record("historical_bars", "/v2/stocks/bars", status, payload, notes="non-formal integration schema/count only")

    status, payload = client.get_positions()
    record("positions", "/v2/positions", status, payload, allow_empty=True, notes="zero positions acceptable")

    status, payload = client.get_corporate_actions(spec["corporate_actions"])
    record("corporate_actions", "/v2/corporate_actions", status, payload, allow_empty=True, notes="optional/non-blocking if not entitled")

    observed = {
        "program_id": "ALP-002",
        "execution_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "environment": "PAPER",
        "authentication": "PASS" if checks["account"]["verification_result"] == "PASS" else "FAIL",
        "order_mutation_calls": client.order_mutation_calls,
        "alpha_execution_performed": "NO",
        "backtest_performed": "NO",
        "performance_evaluation_performed": "NO",
        "scientific_t0_established": "NO",
        "checks": checks,
    }
    OBSERVED_PATH.write_text(json.dumps(observed, indent=2), encoding="utf-8")
    write_endpoint_csv(endpoint_rows)

    print(json.dumps({
        "status": "COMPLETE",
        "environment": observed["environment"],
        "order_mutation_calls": client.order_mutation_calls,
        "checks": {k: v["verification_result"] for k, v in checks.items()},
    }, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(json.dumps({"status": "NOT_READY", "reason": str(exc)}, indent=2))
        raise SystemExit(1)

