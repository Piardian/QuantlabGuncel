"""Verify Alpaca Paper account access without storing secrets.

Reads credentials from environment variables or an untracked local .env file:
APCA_API_BASE_URL, APCA_API_KEY_ID, APCA_API_SECRET_KEY.

The script prints only non-secret account metadata.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def load_local_env(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    load_local_env(repo_root / ".env")

    base_url = os.environ.get("APCA_API_BASE_URL", "https://paper-api.alpaca.markets").rstrip("/")
    key_id = require_env("APCA_API_KEY_ID")
    secret_key = require_env("APCA_API_SECRET_KEY")

    request = Request(
        f"{base_url}/v2/account",
        headers={
            "APCA-API-KEY-ID": key_id,
            "APCA-API-SECRET-KEY": secret_key,
            "Accept": "application/json",
        },
        method="GET",
    )

    try:
        with urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        print(json.dumps({"status": "FAIL", "http_status": exc.code, "reason": exc.reason}, indent=2))
        return 2
    except URLError as exc:
        print(json.dumps({"status": "FAIL", "reason": str(exc.reason)}, indent=2))
        return 2
    except Exception as exc:  # noqa: BLE001 - CLI diagnostics should be explicit.
        print(json.dumps({"status": "FAIL", "reason": str(exc)}, indent=2))
        return 2

    safe_payload = {
        "status": "PASS",
        "account_id_present": bool(payload.get("id")),
        "account_status": payload.get("status"),
        "currency": payload.get("currency"),
        "pattern_day_trader": payload.get("pattern_day_trader"),
        "trading_blocked": payload.get("trading_blocked"),
        "transfers_blocked": payload.get("transfers_blocked"),
        "account_blocked": payload.get("account_blocked"),
    }
    print(json.dumps(safe_payload, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(json.dumps({"status": "NOT_READY", "reason": str(exc)}, indent=2))
        raise SystemExit(1)

