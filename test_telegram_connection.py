from __future__ import annotations

from pathlib import Path
from time import sleep
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import argparse
import json

from telegram_notifier import CONFIG_PATH, TelegramNotifier
from telegram_notifier import telegram_ssl_context


REPORT_PATH = Path("validation_report.txt")
BOT_USERNAME = "@Piardian2bot"
SUCCESS_MESSAGE = "✅ Telegram connection successful"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Telegram bot connectivity")
    parser.add_argument("--timeout-seconds", type=int, default=90)
    parser.add_argument("--poll-seconds", type=int, default=5)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report: dict[str, Any] = {
        "bot_username": BOT_USERNAME,
        "discovered_chat_id": "",
        "connection_status": "not_started",
        "message_delivery_status": "not_started",
        "errors": [],
    }

    try:
        config = load_config()
        token = str(config.get("bot_token", "")).strip()
        if not token:
            raise RuntimeError("bot_token is missing from config/telegram_config.json")

        chat_id = str(config.get("chat_id", "")).strip()
        if not chat_id:
            chat_id = discover_chat_id(token, args.timeout_seconds, args.poll_seconds, report)
            if not chat_id:
                raise RuntimeError(f"No Telegram chat found. Send any message to {BOT_USERNAME}, then rerun this test.")
            config["chat_id"] = chat_id
            config["enabled"] = True
            save_config(config)

        report["discovered_chat_id"] = chat_id
        report["connection_status"] = "success"

        notifier = TelegramNotifier()
        delivered = notifier.send(SUCCESS_MESSAGE)
        report["message_delivery_status"] = "success" if delivered else "skipped"
        write_report(report)
        return 0 if delivered else 1
    except Exception as exc:
        report["connection_status"] = "failure"
        report["message_delivery_status"] = "failure"
        report["errors"].append(str(exc))
        write_report(report)
        print(str(exc))
        return 1


def discover_chat_id(token: str, timeout_seconds: int, poll_seconds: int, report: dict[str, Any]) -> str:
    elapsed = 0
    while elapsed <= timeout_seconds:
        updates = telegram_api(token, "getUpdates")
        chat_id = extract_chat_id(updates)
        if chat_id:
            return chat_id

        message = f"No Telegram chat found yet. Send any message to {BOT_USERNAME}; retrying in {poll_seconds}s."
        print(message)
        report["errors"].append(message)
        sleep(poll_seconds)
        elapsed += poll_seconds
    return ""


def extract_chat_id(updates: dict[str, Any]) -> str:
    for update in reversed(updates.get("result", [])):
        message = update.get("message") or update.get("edited_message") or update.get("channel_post")
        if not message:
            continue
        chat = message.get("chat", {})
        chat_id = chat.get("id")
        if chat_id is not None:
            return str(chat_id)
    return ""


def telegram_api(token: str, method: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    url = f"https://api.telegram.org/bot{token}/{method}"
    data = urlencode(payload or {}).encode("utf-8") if payload else None
    request = Request(url, data=data, method="POST" if data else "GET")
    with urlopen(request, timeout=15, context=telegram_ssl_context()) as response:
        body = response.read().decode("utf-8")
    decoded = json.loads(body)
    if not decoded.get("ok"):
        raise RuntimeError(f"Telegram API returned ok=false for {method}: {decoded}")
    return decoded


def load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        raise RuntimeError(f"Missing Telegram config: {CONFIG_PATH}")
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def save_config(config: dict[str, Any]) -> None:
    CONFIG_PATH.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")


def write_report(report: dict[str, Any]) -> None:
    lines = [
        f"Bot username: {report['bot_username']}",
        f"Discovered chat_id: {report['discovered_chat_id']}",
        f"Connection status: {report['connection_status']}",
        f"Message delivery status: {report['message_delivery_status']}",
        "Errors encountered:",
    ]
    errors = report.get("errors") or []
    if errors:
        lines.extend(f"- {error}" for error in errors)
    else:
        lines.append("- None")
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
