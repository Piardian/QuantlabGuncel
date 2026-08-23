from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class BRD001Config:
    construct_id: str = "BRD-001"
    construct_name: str = "US Equity 200-Day Moving-Average Breadth State"
    universe_path: str = "sp500_current_universe.csv"
    start_date: str = "2010-01-01"
    end_date: str = "2025-12-31"
    sma_window: int = 200
    normalization_window: int = 252
    minimum_eligible_count: int = 50
    output_path: str = "output/brd001_breadth_state.csv"
    data_source: str = "yahoo"
    price_column: str = "Close"


OUTPUT_COLUMNS = [
    "date",
    "brd001_pct_above_sma200",
    "brd001_zscore",
    "brd001_percentile",
    "brd001_count_above_sma200",
    "brd001_count_not_above_sma200",
    "brd001_eligible_count",
    "brd001_total_universe_count",
    "brd001_coverage_ratio",
    "brd001_valid_observation",
]


def load_config(path: str | Path) -> BRD001Config:
    config_path = Path(path)
    values: dict[str, object] = {}

    for raw_line in config_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = _parse_scalar(value.strip())

    return BRD001Config(**values)


def _parse_scalar(value: str) -> object:
    if value == "":
        return ""
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        return int(value)
    except ValueError:
        return value.strip("\"'")


def load_universe(path: str | Path) -> list[str]:
    frame = pd.read_csv(path)
    if "ticker" not in frame.columns:
        raise ValueError("Universe file must contain a 'ticker' column.")

    tickers = (
        frame["ticker"]
        .dropna()
        .astype(str)
        .str.strip()
        .replace("", pd.NA)
        .dropna()
        .drop_duplicates()
        .sort_values()
        .tolist()
    )
    if not tickers:
        raise ValueError("Universe file contains no valid tickers.")
    return tickers


def fetch_yahoo_close_panel(
    tickers: Iterable[str],
    start_date: str,
    end_date: str,
    price_column: str = "Close",
) -> pd.DataFrame:
    import yfinance as yf

    ticker_list = sorted(set(tickers))
    data = yf.download(
        tickers=ticker_list,
        start=start_date,
        end=end_date,
        interval="1d",
        auto_adjust=False,
        progress=False,
        threads=False,
        group_by="column",
    )
    if data.empty:
        raise ValueError("No data returned from Yahoo Finance.")

    if isinstance(data.columns, pd.MultiIndex):
        if price_column not in data.columns.get_level_values(0):
            raise ValueError(f"Downloaded data does not contain '{price_column}'.")
        close_panel = data[price_column]
    else:
        if price_column not in data.columns:
            raise ValueError(f"Downloaded data does not contain '{price_column}'.")
        if len(ticker_list) != 1:
            raise ValueError("Single-index Yahoo data is only valid for one ticker.")
        close_panel = data[[price_column]].rename(columns={price_column: ticker_list[0]})

    close_panel.index = pd.to_datetime(close_panel.index).tz_localize(None)
    close_panel = close_panel.sort_index()
    close_panel = close_panel[~close_panel.index.duplicated(keep="first")]
    close_panel = close_panel.reindex(sorted(close_panel.columns), axis=1)
    return close_panel


def load_close_panel_csv(path: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    if "date" not in frame.columns:
        raise ValueError("Close panel CSV must contain a 'date' column.")
    frame["date"] = pd.to_datetime(frame["date"])
    frame = frame.set_index("date").sort_index()
    frame = frame[~frame.index.duplicated(keep="first")]
    frame = frame.reindex(sorted(frame.columns), axis=1)
    return frame


def compute_brd001(close_panel: pd.DataFrame, config: BRD001Config) -> pd.DataFrame:
    if close_panel.empty:
        raise ValueError("Close panel is empty.")
    if config.sma_window != 200:
        raise ValueError("BRD-001 CD-001 requires sma_window == 200.")
    if config.normalization_window != 252:
        raise ValueError("BRD-001 CD-001 requires normalization_window == 252.")

    closes = close_panel.copy()
    closes.index = pd.to_datetime(closes.index).tz_localize(None)
    closes = closes.sort_index()
    closes = closes.apply(pd.to_numeric, errors="coerce")
    closes = closes.where(closes > 0)

    total_universe_count = int(closes.shape[1])
    sma = closes.rolling(config.sma_window, min_periods=config.sma_window).mean()
    eligible = closes.notna() & sma.notna()
    above = (closes > sma) & eligible

    eligible_count = eligible.sum(axis=1).astype(int)
    count_above = above.sum(axis=1).astype(int)
    valid = eligible_count >= config.minimum_eligible_count

    pct_above = count_above / eligible_count.replace(0, np.nan)
    pct_above = pct_above.where(valid)

    rolling_mean = pct_above.rolling(
        config.normalization_window,
        min_periods=config.normalization_window,
    ).mean()
    rolling_std = pct_above.rolling(
        config.normalization_window,
        min_periods=config.normalization_window,
    ).std()
    zscore = (pct_above - rolling_mean) / rolling_std.replace(0, np.nan)

    percentile = pct_above.rolling(
        config.normalization_window,
        min_periods=config.normalization_window,
    ).apply(_current_percentile, raw=False)

    result = pd.DataFrame(
        {
            "date": closes.index,
            "brd001_pct_above_sma200": pct_above.astype(float).values,
            "brd001_zscore": zscore.astype(float).values,
            "brd001_percentile": percentile.astype(float).values,
            "brd001_count_above_sma200": count_above.values,
            "brd001_count_not_above_sma200": (eligible_count - count_above).astype(int).values,
            "brd001_eligible_count": eligible_count.values,
            "brd001_total_universe_count": total_universe_count,
            "brd001_coverage_ratio": (eligible_count / total_universe_count).astype(float).values,
            "brd001_valid_observation": valid.astype(bool).values,
        }
    )
    return result[OUTPUT_COLUMNS]


def _current_percentile(window: pd.Series) -> float:
    current = window.iloc[-1]
    if pd.isna(current):
        return float("nan")
    return float((window <= current).sum() / len(window))


def write_output(frame: pd.DataFrame, path: str | Path) -> str:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    serialized = frame.copy()
    serialized["date"] = pd.to_datetime(serialized["date"]).dt.strftime("%Y-%m-%d")
    serialized.to_csv(output_path, index=False, float_format="%.10g")
    return file_sha256(output_path)


def file_sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def frame_sha256(frame: pd.DataFrame) -> str:
    payload = frame.copy()
    payload["date"] = pd.to_datetime(payload["date"]).dt.strftime("%Y-%m-%d")
    csv_text = payload.to_csv(index=False, float_format="%.10g")
    return hashlib.sha256(csv_text.encode("utf-8")).hexdigest()


def run(config: BRD001Config, close_panel_path: str | None = None) -> dict[str, object]:
    tickers = load_universe(config.universe_path)

    if close_panel_path:
        close_panel = load_close_panel_csv(close_panel_path)
        close_panel = close_panel.reindex(columns=tickers)
    else:
        close_panel = fetch_yahoo_close_panel(
            tickers=tickers,
            start_date=config.start_date,
            end_date=config.end_date,
            price_column=config.price_column,
        )
        close_panel = close_panel.reindex(columns=tickers)

    result = compute_brd001(close_panel, config)
    output_hash = write_output(result, config.output_path)
    valid_count = int(result["brd001_valid_observation"].sum())

    return {
        "construct_id": config.construct_id,
        "output_path": config.output_path,
        "output_sha256": output_hash,
        "rows": int(len(result)),
        "valid_observations": valid_count,
        "total_universe_count": int(len(tickers)),
        "start_date": str(result["date"].min().date()) if len(result) else None,
        "end_date": str(result["date"].max().date()) if len(result) else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run BRD-001 breadth construct pipeline.")
    parser.add_argument("--config", default="research/constructs/brd_001/config.yaml")
    parser.add_argument("--close-panel", default=None)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    config = load_config(args.config)
    if args.output:
        config = BRD001Config(**{**config.__dict__, "output_path": args.output})
    summary = run(config, close_panel_path=args.close_panel)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
