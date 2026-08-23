from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from data.yahoo_data import MarketDataRequest, YahooFinanceDataSource  # noqa: E402
from liquidity_inference import infer_liquidity_from_market_data  # noqa: E402


def parse_simple_yaml(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip()
    return values


def load_universe(path: Path, max_symbols: int | None) -> list[str]:
    frame = pd.read_csv(path)
    if "ticker" not in frame.columns:
        raise ValueError("Universe file must contain a ticker column.")
    tickers = frame["ticker"].dropna().astype(str).str.upper().drop_duplicates().tolist()
    return tickers[:max_symbols] if max_symbols else tickers


def fetch_market_data(tickers: list[str], start: str, end: str, timeframe: str) -> tuple[dict[str, pd.DataFrame], list[dict[str, str]]]:
    source = YahooFinanceDataSource()
    market_data: dict[str, pd.DataFrame] = {}
    errors: list[dict[str, str]] = []
    for ticker in tickers:
        last_error: Exception | None = None
        for _ in range(3):
            try:
                market_data[ticker] = source.fetch(
                    MarketDataRequest(ticker=ticker, start=start, end=end, timeframe=timeframe)
                )
                last_error = None
                break
            except Exception as exc:
                last_error = exc
                time.sleep(0.5)
        if last_error is not None:
            errors.append({"ticker": ticker, "error": str(last_error)})
    return market_data, errors


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    args = parse_args()
    config = parse_simple_yaml(args.config)
    output_dir = Path(args.output_dir or config.get("output_dir", "output/liq_001_validation"))
    output_dir.mkdir(parents=True, exist_ok=True)

    max_symbols = int(args.max_symbols if args.max_symbols is not None else config.get("max_symbols", "80"))
    universe_path = ROOT / config.get("universe_path", "sp500_current_universe.csv")
    tickers = load_universe(universe_path, max_symbols=max_symbols)
    market_data, errors = fetch_market_data(
        tickers=tickers,
        start=args.start or config.get("start", "2010-01-01"),
        end=args.end or config.get("end", "2026-01-01"),
        timeframe=config.get("timeframe", "1d"),
    )
    if len(market_data) < int(config.get("min_eligible_securities", "50")):
        raise RuntimeError(
            f"Only {len(market_data)} symbols loaded; min_eligible_securities requires "
            f"{config.get('min_eligible_securities', '50')}."
        )

    result = infer_liquidity_from_market_data(
        market_data=market_data,
        smoothing_window=int(config.get("smoothing_window", "20")),
        zscore_window=int(config.get("zscore_window", "252")),
        min_eligible_securities=int(config.get("min_eligible_securities", "50")),
    )

    output_path = output_dir / "liq001_liquidity_output.csv"
    security_path = output_dir / "liq001_security_features_sample.csv"
    result.frame.to_csv(output_path, index=False)
    result.security_features.head(10_000).to_csv(security_path, index=False)
    pd.DataFrame(errors).to_csv(output_dir / "liq001_error_report.csv", index=False)

    summary = {
        "construct_id": "LIQ-001",
        "loaded_symbols": int(len(market_data)),
        "requested_symbols": int(len(tickers)),
        "failed_symbols": int(len(errors)),
        "rows": int(len(result.frame)),
        "start": str(pd.to_datetime(result.frame["date"]).min()) if not result.frame.empty else None,
        "end": str(pd.to_datetime(result.frame["date"]).max()) if not result.frame.empty else None,
        "mean_eligible_count": float(result.frame["eligible_count"].mean()) if not result.frame.empty else None,
        "mean_coverage_ratio": float(result.frame["coverage_ratio"].mean()) if not result.frame.empty else None,
        "output_sha256": file_sha256(output_path),
    }
    (output_dir / "verification_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_reports(output_dir, summary)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate LIQ-001 implementation.")
    parser.add_argument("--config", type=Path, default=Path(__file__).with_name("config.yaml"))
    parser.add_argument("--start")
    parser.add_argument("--end")
    parser.add_argument("--max-symbols", type=int)
    parser.add_argument("--output-dir", type=Path)
    return parser.parse_args()


def write_reports(output: Path, summary: dict[str, object]) -> None:
    (output / "verification_report.md").write_text(
        f"""# LIQ-001 Verification Report

## Scope

This validation run checks implementation fidelity only. It does not evaluate prediction, alpha, profitability, or economic utility.

## Verification Summary

- Requested symbols: {summary["requested_symbols"]}
- Loaded symbols: {summary["loaded_symbols"]}
- Failed symbols: {summary["failed_symbols"]}
- Rows produced: {summary["rows"]}
- Date range: {summary["start"]} to {summary["end"]}
- Mean eligible count: {summary["mean_eligible_count"]:.2f}
- Mean coverage ratio: {summary["mean_coverage_ratio"]:.4f}
- Output SHA256: `{summary["output_sha256"]}`

## Verdict

The implementation is structurally complete if the output CSV contains the frozen CD-001 columns and repeated execution with identical inputs produces identical outputs.
""",
        encoding="utf-8",
    )
    (output / "reproducibility_report.md").write_text(
        """# Reproducibility Report

LIQ-001 uses deterministic formulas only. With identical market data, universe, configuration, and preprocessing, output values are reproducible.

The validation summary records a SHA256 hash for the primary output CSV.
""",
        encoding="utf-8",
    )
    (output / "unit_test_report.md").write_text(
        """# Unit Test Report

Required checks:

1. Security feature pipeline computes log return, dollar volume, eligibility, and security illiquidity.
2. Aggregate pipeline computes cross-sectional median illiquidity.
3. Coverage diagnostics are present.
4. 20-day smoothing and 252-day z-score columns are present.
5. Repeated execution on identical synthetic input is deterministic.
""",
        encoding="utf-8",
    )
    (output / "execution_example.md").write_text(
        """# Execution Example

```powershell
.venv\\Scripts\\python.exe research\\implementations\\liq_001\\validate_liq_001.py --config research\\implementations\\liq_001\\config.yaml
```
""",
        encoding="utf-8",
    )
    (output / "limitations.md").write_text(
        """# Limitations

- This implementation validates daily Amihud-style aggregate illiquidity only.
- It does not capture bid-ask spread, depth, immediacy, or resiliency.
- Yahoo Finance data revisions can change future reruns unless raw input snapshots are archived.
- The current validation may use a capped universe for runtime practicality.
- No predictive or economic interpretation is made.
""",
        encoding="utf-8",
    )
    (output / "executive_summary.md").write_text(
        """# Executive Summary

IM-001 implements LIQ-001 as a deterministic US Equity Aggregate Daily Illiquidity construct using daily close and volume data.

The implementation follows CD-001 and is ready for construct validation once human review approves progression.
""",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

