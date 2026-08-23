from __future__ import annotations

from pathlib import Path

import pandas as pd

from fund001_funding_stress_model import fetch_fred_series_csv, load_fred_csv


def load_fund001_inputs(
    cp_series: str = "DCPF3M",
    tbill_series: str = "DTB3",
    cp_csv: Path | None = None,
    tbill_csv: Path | None = None,
) -> tuple[pd.DataFrame, dict[str, str]]:
    """Load and exact-date merge FUND-001 source inputs."""

    if cp_csv:
        cp_frame = load_fred_csv(cp_csv, cp_series)
        cp_source = str(cp_csv)
    else:
        cp_frame = fetch_fred_series_csv(cp_series)
        cp_source = "fred_download"

    if tbill_csv:
        tbill_frame = load_fred_csv(tbill_csv, tbill_series)
        tbill_source = str(tbill_csv)
    else:
        tbill_frame = fetch_fred_series_csv(tbill_series)
        tbill_source = "fred_download"

    cp_frame = _standardize_date_column(cp_frame)
    tbill_frame = _standardize_date_column(tbill_frame)
    cp_frame["DATE"] = pd.to_datetime(cp_frame["DATE"])
    tbill_frame["DATE"] = pd.to_datetime(tbill_frame["DATE"])
    merged = pd.merge(cp_frame[["DATE", cp_series]], tbill_frame[["DATE", tbill_series]], on="DATE", how="outer")
    merged = merged.sort_values("DATE").drop_duplicates(subset=["DATE"], keep="first")

    metadata = {
        "cp_series": cp_series,
        "tbill_series": tbill_series,
        "cp_source": cp_source,
        "tbill_source": tbill_source,
    }
    return merged, metadata


def _standardize_date_column(frame: pd.DataFrame) -> pd.DataFrame:
    if "DATE" in frame.columns:
        return frame
    if "observation_date" in frame.columns:
        return frame.rename(columns={"observation_date": "DATE"})
    raise ValueError("FUND-001 FRED input must contain DATE or observation_date.")
