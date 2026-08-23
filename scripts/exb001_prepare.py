from __future__ import annotations

import csv
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OUT_DIR = ROOT / "research" / "market_edge_discovery_program" / "exb_001_non_formal_exploratory_backtest_preparation"
DATASET_DIR = OUT_DIR / "non_formal_dataset_metadata"
SPEC_PATH = OUT_DIR / "exb001_dataset_request_spec.json"
INVENTORY_CSV = OUT_DIR / "exb001_dataset_inventory.csv"
QUALITY_JSON = OUT_DIR / "exb001_quality_counts.json"
OBSERVED_JSON = OUT_DIR / "exb001_observed_access.json"
UNIVERSE_CSV = OUT_DIR / "exb001_universe_candidates.csv"


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


class AlpacaGetClient:
    def __init__(self) -> None:
        load_local_env(ROOT / ".env")
        self.paper_base = os.environ.get("APCA_API_BASE_URL", "https://paper-api.alpaca.markets").rstrip("/")
        self.data_base = os.environ.get("APCA_DATA_BASE_URL", "https://data.alpaca.markets").rstrip("/")
        if self.paper_base != "https://paper-api.alpaca.markets":
            raise RuntimeError("EXB-001 requires PAPER environment")
        self.headers = {
            "APCA-API-KEY-ID": require_env("APCA_API_KEY_ID"),
            "APCA-API-SECRET-KEY": require_env("APCA_API_SECRET_KEY"),
            "Accept": "application/json",
        }

    def get_json(self, base_url: str, path: str, params: dict[str, Any] | None = None) -> tuple[str, Any]:
        query = f"?{urlencode(params, doseq=True)}" if params else ""
        request = Request(f"{base_url}{path}{query}", headers=self.headers, method="GET")
        try:
            with urlopen(request, timeout=60) as response:
                body = response.read().decode("utf-8")
                return "PASS", json.loads(body) if body else None
        except HTTPError as exc:
            return f"HTTP_{exc.code}", {"error": exc.reason}
        except (URLError, TimeoutError) as exc:
            return "NETWORK_FAIL", {"error": str(exc)}


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def normalize_exchange(exchange: str) -> str:
    exchange_u = str(exchange or "").upper()
    aliases = {
        "NASDAQ": "NASDAQ",
        "NYSE": "NYSE",
        "AMEX": "NYSE_AMERICAN",
        "NYSEAMERICAN": "NYSE_AMERICAN",
        "NYSE_AMERICAN": "NYSE_AMERICAN",
    }
    return aliases.get(exchange_u, exchange_u)


def is_candidate_asset(asset: dict[str, Any]) -> bool:
    symbol = str(asset.get("symbol", "")).upper()
    if not symbol or len(symbol) > 8:
        return False
    if any(marker in symbol for marker in ["/", "^", "=", " "]):
        return False
    if asset.get("class") != "us_equity":
        return False
    if asset.get("status") != "active":
        return False
    if asset.get("tradable") is not True:
        return False
    if normalize_exchange(str(asset.get("exchange", ""))) not in {"NASDAQ", "NYSE", "NYSE_AMERICAN"}:
        return False
    attributes = [str(item).lower() for item in asset.get("attributes", []) if item is not None]
    if any("etp" in item or "etf" in item for item in attributes):
        return False
    return True


def fetch_bars(client: AlpacaGetClient, symbols: list[str], start: str, end: str) -> tuple[str, dict[str, Any]]:
    combined: dict[str, list[dict[str, Any]]] = {"bars": {}}
    page_token: str | None = None
    pages = 0
    last_status = "PASS"
    while True:
        pages += 1
        if pages > 100:
            return "PAGINATION_LIMIT_EXCEEDED", combined
        params: dict[str, Any] = {
            "symbols": ",".join(symbols),
            "timeframe": "1Day",
            "start": start,
            "end": end,
            "feed": "iex",
            "adjustment": "raw",
            "limit": 10000,
        }
        if page_token:
            params["page_token"] = page_token
        status, payload = client.get_json(client.data_base, "/v2/stocks/bars", params)
        last_status = status
        if status != "PASS" or not isinstance(payload, dict):
            return status, combined
        for symbol, items in payload.get("bars", {}).items():
            combined["bars"].setdefault(symbol, []).extend(items if isinstance(items, list) else [])
        page_token = payload.get("next_page_token")
        if not page_token:
            combined["pages"] = pages
            return last_status, combined


def bar_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    bars = payload.get("bars", {}) if isinstance(payload, dict) else {}
    for symbol, items in bars.items():
        if not isinstance(items, list):
            continue
        for item in items:
            row = {"symbol": symbol}
            row.update(item)
            rows.append(row)
    return rows


def quality_counts(rows: list[dict[str, Any]], calendar_dates: set[str]) -> dict[str, Any]:
    seen: set[tuple[str, str]] = set()
    duplicates = 0
    invalid_ohlc = 0
    negative_price = 0
    zero_or_negative_volume = 0
    per_symbol_dates: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        symbol = row["symbol"]
        date = str(row.get("t", ""))[:10]
        key = (symbol, date)
        if key in seen:
            duplicates += 1
        seen.add(key)
        per_symbol_dates[symbol].add(date)
        o = float(row.get("o", 0) or 0)
        h = float(row.get("h", 0) or 0)
        l = float(row.get("l", 0) or 0)
        c = float(row.get("c", 0) or 0)
        v = float(row.get("v", 0) or 0)
        if min(o, h, l, c) <= 0:
            negative_price += 1
        if h < max(o, c, l) or l > min(o, c, h):
            invalid_ohlc += 1
        if v <= 0:
            zero_or_negative_volume += 1
    missing_dates_total = 0
    for dates in per_symbol_dates.values():
        missing_dates_total += len(calendar_dates - dates)
    return {
        "rows": len(rows),
        "symbols_with_rows": len(per_symbol_dates),
        "duplicate_symbol_dates": duplicates,
        "invalid_ohlc_relationships": invalid_ohlc,
        "negative_or_zero_prices": negative_price,
        "zero_or_negative_volume": zero_or_negative_volume,
        "missing_symbol_trading_dates_total": missing_dates_total,
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    client = AlpacaGetClient()

    spec = {
        "program_id": "EXB-001",
        "dataset_label": "NON_FORMAL_EXPLORATORY_EVIDENCE",
        "source": "Alpaca Paper / Alpaca Market Data API",
        "environment": "PAPER",
        "feed": "iex",
        "adjustment": "raw",
        "timeframe": "1Day",
        "exploratory_universe_max_symbols": 100,
        "selection_rule": "active tradable us_equity assets on NASDAQ/NYSE/NYSE American, excluding obvious non-common structures where detectable, sorted alphabetically, first 100 symbols",
        "history_probe_symbol": "AAPL",
        "probe_start": "2000-01-01T00:00:00Z",
        "probe_end": "2026-08-11T23:59:59Z",
        "dataset_start": "2021-01-01T00:00:00Z",
        "dataset_end": "2026-08-11T23:59:59Z",
        "calendar_start": "2021-01-01",
        "calendar_end": "2026-08-11",
        "alpha_execution": "NO",
        "performance_evaluation": "NO",
        "broker_mutation_calls": 0,
    }
    SPEC_PATH.write_text(json.dumps(spec, indent=2), encoding="utf-8")

    status_assets, assets_payload = client.get_json(client.paper_base, "/v2/assets", {"status": "active", "asset_class": "us_equity"})
    if status_assets != "PASS" or not isinstance(assets_payload, list):
        raise RuntimeError(f"Asset retrieval failed: {status_assets}")
    candidate_assets = [asset for asset in assets_payload if is_candidate_asset(asset)]
    candidate_assets = sorted(candidate_assets, key=lambda item: str(item.get("symbol", "")))[: spec["exploratory_universe_max_symbols"]]
    universe_rows = [
        {
            "symbol": asset.get("symbol"),
            "asset_id": asset.get("id"),
            "name": asset.get("name"),
            "exchange": asset.get("exchange"),
            "normalized_exchange": normalize_exchange(str(asset.get("exchange", ""))),
            "asset_class": asset.get("class"),
            "status": asset.get("status"),
            "tradable": asset.get("tradable"),
            "fractionable": asset.get("fractionable"),
            "shortable": asset.get("shortable"),
            "attributes": "|".join(str(x) for x in asset.get("attributes", [])),
        }
        for asset in candidate_assets
    ]
    write_csv(UNIVERSE_CSV, universe_rows)

    status_probe, probe_payload = fetch_bars(client, [spec["history_probe_symbol"]], spec["probe_start"], spec["probe_end"])
    probe_rows = bar_rows(probe_payload if isinstance(probe_payload, dict) else {})
    earliest = min((str(row.get("t", ""))[:10] for row in probe_rows), default="UNKNOWN")
    latest = max((str(row.get("t", ""))[:10] for row in probe_rows), default="UNKNOWN")

    status_calendar, calendar_payload = client.get_json(client.paper_base, "/v2/calendar", {"start": spec["calendar_start"], "end": spec["calendar_end"]})
    calendar_dates = {str(row.get("date")) for row in calendar_payload} if isinstance(calendar_payload, list) else set()

    symbols = [str(row["symbol"]) for row in universe_rows]
    status_bars, bars_payload = fetch_bars(client, symbols, spec["dataset_start"], spec["dataset_end"])
    rows = bar_rows(bars_payload if isinstance(bars_payload, dict) else {})
    q_counts = quality_counts(rows, calendar_dates)
    QUALITY_JSON.write_text(json.dumps(q_counts, indent=2), encoding="utf-8")

    inventory = [
        {
            "dataset_id": "EXB001_ALPACA_IEX_DAILY_REDUCED",
            "label": "NON_FORMAL_EXPLORATORY_EVIDENCE",
            "source": "Alpaca Market Data API",
            "feed": spec["feed"],
            "adjustment": spec["adjustment"],
            "timeframe": spec["timeframe"],
            "symbol_count_requested": len(symbols),
            "symbol_count_with_rows": q_counts["symbols_with_rows"],
            "row_count": q_counts["rows"],
            "start": spec["dataset_start"],
            "end": spec["dataset_end"],
            "raw_market_data_stored": "NO",
            "metadata_only": "YES",
            "performance_evaluation": "NO",
        }
    ]
    write_csv(INVENTORY_CSV, inventory)

    observed = {
        "program_id": "EXB-001",
        "execution_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "historical_bars_access": "PASS" if status_probe == "PASS" and status_bars == "PASS" and q_counts["rows"] > 0 else "FAIL",
        "assets_access": status_assets,
        "calendar_access": status_calendar,
        "probe_access": status_probe,
        "dataset_access": status_bars,
        "earliest_verified_date": earliest,
        "latest_verified_date": latest,
        "verified_history_years": round((datetime.fromisoformat(latest).date() - datetime.fromisoformat(earliest).date()).days / 365.25, 2) if earliest != "UNKNOWN" and latest != "UNKNOWN" else "UNKNOWN",
        "candidate_assets_after_filter": len(candidate_assets),
        "dataset_inventory": inventory[0],
        "quality_counts": q_counts,
        "alpha_logic_changed": "NO",
        "backtest_performed": "NO",
        "performance_evaluation_performed": "NO",
        "broker_mutation_calls": 0,
        "scientific_t0_established": "NO",
    }
    OBSERVED_JSON.write_text(json.dumps(observed, indent=2), encoding="utf-8")
    print(json.dumps(observed, indent=2))
    return 0 if observed["historical_bars_access"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
