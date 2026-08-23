from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


REQUIRED_COLUMNS = [
    "security_id",
    "ticker",
    "fiscal_period_end",
    "revenue",
    "cost_of_goods_sold",
    "total_assets",
]

OPTIONAL_COLUMNS = ["filing_date"]

OUTPUT_COLUMNS = [
    "security_id",
    "ticker",
    "fiscal_period_end",
    "filing_date",
    "accounting_availability_date",
    "revenue",
    "cost_of_goods_sold",
    "total_assets",
    "gross_profit",
    "gross_profitability",
    "prof001_state",
    "prof001_valid_observation",
    "exclusion_reason",
]


@dataclass(frozen=True, slots=True)
class PROF001AccountingPipeline:
    """Deterministic builder for frozen PROF-001."""

    conservative_lag_calendar_days: int = 180

    def load_accounting(self, path: Path) -> pd.DataFrame:
        if not path.exists():
            raise FileNotFoundError(f"Missing required PROF-001 accounting dataset: {path}")
        return pd.read_csv(path)

    def build_features(self, accounting: pd.DataFrame) -> pd.DataFrame:
        self._validate_frozen_parameters()
        frame = accounting.copy()
        self._validate_columns(frame)
        frame = self._normalize(frame)
        frame["accounting_availability_date"] = frame.apply(self._availability_date, axis=1)
        frame["gross_profit"] = frame["revenue"] - frame["cost_of_goods_sold"]
        frame["gross_profitability"] = frame["gross_profit"] / frame["total_assets"]
        frame["gross_profitability"] = frame["gross_profitability"].where(np.isfinite(frame["gross_profitability"]))
        frame["prof001_state"] = np.select(
            [
                frame["gross_profitability"] > 0,
                frame["gross_profitability"] < 0,
                frame["gross_profitability"].eq(0),
            ],
            ["PROFITABLE", "UNPROFITABLE", "NEUTRAL"],
            default="INVALID",
        )
        frame["exclusion_reason"] = frame.apply(self._exclusion_reason, axis=1)
        frame["prof001_valid_observation"] = frame["exclusion_reason"].eq("")
        return frame[OUTPUT_COLUMNS]

    def _validate_frozen_parameters(self) -> None:
        if self.conservative_lag_calendar_days != 180:
            raise ValueError("PROF-001 CD-001 requires conservative_lag_calendar_days == 180.")

    def _validate_columns(self, frame: pd.DataFrame) -> None:
        missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
        if missing:
            raise ValueError(f"Missing required PROF-001 columns: {missing}")

    def _normalize(self, frame: pd.DataFrame) -> pd.DataFrame:
        normalized = frame.copy()
        if "filing_date" not in normalized.columns:
            normalized["filing_date"] = pd.NaT
        normalized["fiscal_period_end"] = pd.to_datetime(normalized["fiscal_period_end"], errors="coerce")
        normalized["filing_date"] = pd.to_datetime(normalized["filing_date"], errors="coerce")
        for column in ["revenue", "cost_of_goods_sold", "total_assets"]:
            normalized[column] = pd.to_numeric(normalized[column], errors="coerce")
        return normalized

    def _availability_date(self, row: pd.Series) -> pd.Timestamp | pd.NaT:
        if pd.notna(row["filing_date"]):
            return pd.Timestamp(row["filing_date"].date()) + pd.offsets.BDay(1)
        if pd.notna(row["fiscal_period_end"]):
            return pd.Timestamp(row["fiscal_period_end"].date()) + pd.Timedelta(days=self.conservative_lag_calendar_days)
        return pd.NaT

    def _exclusion_reason(self, row: pd.Series) -> str:
        reasons: list[str] = []
        if pd.isna(row["security_id"]) or str(row["security_id"]).strip() == "":
            reasons.append("missing_security_id")
        if pd.isna(row["ticker"]) or str(row["ticker"]).strip() == "":
            reasons.append("missing_ticker")
        if pd.isna(row["fiscal_period_end"]):
            reasons.append("missing_fiscal_period_end")
        if pd.isna(row["revenue"]):
            reasons.append("missing_revenue")
        if pd.isna(row["cost_of_goods_sold"]):
            reasons.append("missing_cost_of_goods_sold")
        if pd.isna(row["total_assets"]) or row["total_assets"] <= 0:
            reasons.append("missing_or_nonpositive_total_assets")
        if pd.isna(row["accounting_availability_date"]):
            reasons.append("missing_accounting_availability_date")
        if pd.isna(row["gross_profitability"]):
            reasons.append("invalid_gross_profitability")
        return ";".join(reasons)
