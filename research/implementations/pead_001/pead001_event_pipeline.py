from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


REQUIRED_COLUMNS = [
    "security_id",
    "ticker",
    "announcement_date",
    "announcement_time_or_session",
    "fiscal_period_end",
    "actual_eps",
    "consensus_expected_eps",
    "consensus_timestamp",
    "price_reference",
]

OUTPUT_COLUMNS = [
    *REQUIRED_COLUMNS,
    "standardized_earnings_surprise",
    "pead_state",
    "first_valid_decision_timestamp",
    "pead001_valid_observation",
    "exclusion_reason",
]

SESSION_VALUES = {
    "before_market_open",
    "during_market",
    "after_market_close",
    "unknown",
}


@dataclass(frozen=True, slots=True)
class PEAD001EventPipeline:
    """Deterministic PEAD-001 event-state builder following frozen CD-001."""

    def load_events(self, path: Path) -> pd.DataFrame:
        if not path.exists():
            raise FileNotFoundError(f"Missing required PEAD-001 event dataset: {path}")
        return pd.read_csv(path)

    def build_features(self, events: pd.DataFrame) -> pd.DataFrame:
        frame = events.copy()
        self._validate_columns(frame)
        frame = self._normalize(frame)

        frame["standardized_earnings_surprise"] = (
            (frame["actual_eps"] - frame["consensus_expected_eps"]) / frame["price_reference"].abs()
        )
        frame["standardized_earnings_surprise"] = frame["standardized_earnings_surprise"].where(
            np.isfinite(frame["standardized_earnings_surprise"])
        )
        frame["pead_state"] = np.select(
            [
                frame["standardized_earnings_surprise"] > 0,
                frame["standardized_earnings_surprise"] < 0,
                frame["standardized_earnings_surprise"].eq(0),
            ],
            ["POSITIVE", "NEGATIVE", "NEUTRAL"],
            default=pd.NA,
        )
        frame["first_valid_decision_timestamp"] = frame.apply(self._first_valid_decision_timestamp, axis=1)
        frame["exclusion_reason"] = frame.apply(self._exclusion_reason, axis=1)
        frame["pead001_valid_observation"] = frame["exclusion_reason"].eq("")
        return frame[OUTPUT_COLUMNS]

    def _validate_columns(self, frame: pd.DataFrame) -> None:
        missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
        if missing:
            raise ValueError(f"Missing required PEAD-001 columns: {missing}")

    def _normalize(self, frame: pd.DataFrame) -> pd.DataFrame:
        normalized = frame.copy()
        for column in ["announcement_date", "fiscal_period_end", "consensus_timestamp"]:
            normalized[column] = pd.to_datetime(normalized[column], errors="coerce")
        normalized["announcement_time_or_session"] = (
            normalized["announcement_time_or_session"].astype(str).str.strip().str.lower()
        )
        for column in ["actual_eps", "consensus_expected_eps", "price_reference"]:
            normalized[column] = pd.to_numeric(normalized[column], errors="coerce")
        return normalized

    def _first_valid_decision_timestamp(self, row: pd.Series) -> pd.Timestamp | pd.NaT:
        announcement_date = row["announcement_date"]
        if pd.isna(announcement_date):
            return pd.NaT
        session = row["announcement_time_or_session"]
        if session == "before_market_open":
            return pd.Timestamp(announcement_date.date()) + pd.Timedelta(hours=9, minutes=30)
        if session in {"during_market", "after_market_close", "unknown"}:
            return pd.Timestamp(announcement_date.date()) + pd.offsets.BDay(1) + pd.Timedelta(hours=9, minutes=30)
        return pd.NaT

    def _exclusion_reason(self, row: pd.Series) -> str:
        reasons: list[str] = []
        if pd.isna(row["announcement_date"]):
            reasons.append("missing_announcement_date")
        if row["announcement_time_or_session"] not in SESSION_VALUES:
            reasons.append("invalid_announcement_time_or_session")
        if pd.isna(row["actual_eps"]):
            reasons.append("missing_actual_eps")
        if pd.isna(row["consensus_expected_eps"]):
            reasons.append("missing_consensus_expected_eps")
        if pd.isna(row["consensus_timestamp"]):
            reasons.append("missing_consensus_timestamp")
        elif pd.notna(row["announcement_date"]) and row["consensus_timestamp"] >= row["announcement_date"]:
            reasons.append("consensus_not_before_announcement")
        if pd.isna(row["price_reference"]) or row["price_reference"] <= 0:
            reasons.append("missing_or_nonpositive_price_reference")
        if pd.isna(row["standardized_earnings_surprise"]):
            reasons.append("invalid_standardized_earnings_surprise")
        if pd.isna(row["first_valid_decision_timestamp"]):
            reasons.append("invalid_first_valid_decision_timestamp")
        if pd.isna(row["security_id"]) or str(row["security_id"]).strip() == "":
            reasons.append("missing_security_id")
        if pd.isna(row["ticker"]) or str(row["ticker"]).strip() == "":
            reasons.append("missing_ticker")
        return ";".join(reasons)
