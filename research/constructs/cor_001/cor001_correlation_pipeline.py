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
class COR001Config:
    construct_id: str = "COR-001"
    construct_name: str = "US Equity Market Average Pairwise Correlation State"
    universe_path: str = "sp500_current_universe.csv"
    start_date: str = "2010-01-01"
    end_date: str = "2025-12-31"
    correlation_window: int = 60
    normalization_window: int = 252
    minimum_eligible_count: int = 50
    output_path: str = "output/cor001_correlation_state.csv"
    data_source: str = "yahoo"
    price_column: str = "Close"


OUTPUT_COLUMNS = [
    "date",
    "cor001_avg_pairwise_corr_60d",
    "cor001_zscore_252d",
    "cor001_percentile_252d",
    "cor001_eligible_security_count",
    "cor001_pair_count",
    "cor001_coverage_ratio",
]


def load_config(path: str | Path) -> COR001Config:
    config_path = Path(path)
    values: dict[str, object] = {}

    for raw_line in config_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = _parse_scalar(value.strip())

    return COR001Config(**values)


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


def compute_cor001(close_panel: pd.DataFrame, config: COR001Config) -> pd.DataFrame:
    if close_panel.empty:
        raise ValueError("Close panel is empty.")
    if config.correlation_window != 60:
        raise ValueError("COR-001 CD-001 requires correlation_window == 60.")
    if config.normalization_window != 252:
        raise ValueError("COR-001 CD-001 requires normalization_window == 252.")

    closes = close_panel.copy()
    closes.index = pd.to_datetime(closes.index).tz_localize(None)
    closes = closes.sort_index()
    closes = closes.apply(pd.to_numeric, errors="coerce")
    closes = closes.where(closes > 0)
    closes = closes.reindex(sorted(closes.columns), axis=1)

    total_universe_count = int(closes.shape[1])
    returns = np.log(closes / closes.shift(1))

    raw_values: list[float] = []
    eligible_counts: list[int] = []
    pair_counts: list[int] = []
    coverage_ratios: list[float] = []

    for idx in range(len(returns)):
        if idx + 1 < config.correlation_window:
            eligible_count = 0
            avg_corr = float("nan")
        else:
            window = returns.iloc[idx - config.correlation_window + 1 : idx + 1]
            eligible_window = window.dropna(axis=1, how="any")
            eligible_count = int(eligible_window.shape[1])

            if eligible_count < config.minimum_eligible_count:
                avg_corr = float("nan")
            else:
                corr_matrix = eligible_window.corr(method="pearson")
                avg_corr = _mean_upper_triangle(corr_matrix)

        pair_count = int(eligible_count * (eligible_count - 1) / 2)
        coverage_ratio = (
            float(eligible_count / total_universe_count)
            if total_universe_count
            else float("nan")
        )

        raw_values.append(avg_corr)
        eligible_counts.append(eligible_count)
        pair_counts.append(pair_count)
        coverage_ratios.append(coverage_ratio)

    raw = pd.Series(raw_values, index=closes.index, dtype="float64")
    rolling_mean = raw.rolling(
        config.normalization_window,
        min_periods=config.normalization_window,
    ).mean()
    rolling_std = raw.rolling(
        config.normalization_window,
        min_periods=config.normalization_window,
    ).std()
    zscore = (raw - rolling_mean) / rolling_std.replace(0, np.nan)
    percentile = raw.rolling(
        config.normalization_window,
        min_periods=config.normalization_window,
    ).apply(_current_percentile, raw=False)

    result = pd.DataFrame(
        {
            "date": closes.index,
            "cor001_avg_pairwise_corr_60d": raw.values,
            "cor001_zscore_252d": zscore.values,
            "cor001_percentile_252d": percentile.values,
            "cor001_eligible_security_count": eligible_counts,
            "cor001_pair_count": pair_counts,
            "cor001_coverage_ratio": coverage_ratios,
        }
    )
    return result[OUTPUT_COLUMNS]


def _mean_upper_triangle(corr_matrix: pd.DataFrame) -> float:
    values = corr_matrix.to_numpy(dtype="float64", copy=True)
    mask = np.triu(np.ones(values.shape, dtype=bool), k=1)
    pair_values = values[mask]
    pair_values = pair_values[np.isfinite(pair_values)]
    if pair_values.size == 0:
        return float("nan")
    return float(pair_values.mean())


def _current_percentile(window: pd.Series) -> float:
    current = window.iloc[-1]
    if pd.isna(current):
        return float("nan")
    clean = window.dropna()
    if clean.empty:
        return float("nan")
    return float((clean <= current).sum() / len(clean))


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


def run(config: COR001Config, close_panel_path: str | None = None) -> dict[str, object]:
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

    result = compute_cor001(close_panel, config)
    output_hash = write_output(result, config.output_path)
    valid_count = int(result["cor001_avg_pairwise_corr_60d"].notna().sum())

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
    parser = argparse.ArgumentParser(description="Run COR-001 correlation construct pipeline.")
    parser.add_argument("--config", default="research/constructs/cor_001/config.yaml")
    parser.add_argument("--close-panel", default=None)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    config = load_config(args.config)
    if args.output:
        config = COR001Config(**{**config.__dict__, "output_path": args.output})
    summary = run(config, close_panel_path=args.close_panel)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

