from __future__ import annotations

from pathlib import Path

import pandas as pd

from opt001_options_implied_model import fetch_fred_series_csv, load_fred_csv


def load_opt001_input(source_series: str = "VIXCLS", input_csv: Path | None = None) -> tuple[pd.DataFrame, dict[str, str]]:
    """Load OPT-001 source input without modifying the frozen construct."""

    if input_csv:
        frame = load_fred_csv(input_csv, source_series)
        source = str(input_csv)
    else:
        frame = fetch_fred_series_csv(source_series)
        source = "fred_download"

    if "DATE" not in frame.columns and "observation_date" in frame.columns:
        frame = frame.rename(columns={"observation_date": "DATE"})
    if "DATE" not in frame.columns:
        raise ValueError("OPT-001 FRED input must contain DATE or observation_date.")
    frame["DATE"] = pd.to_datetime(frame["DATE"])
    frame = frame.sort_values("DATE").drop_duplicates(subset=["DATE"], keep="first")
    return frame[["DATE", source_series]], {"source_series": source_series, "input_source": source}

