from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from data.yahoo_data import MarketDataRequest, YahooFinanceDataSource
from regime_inference import infer_regime_from_close_data


def main() -> None:
    args = parse_args()
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)

    source = YahooFinanceDataSource()
    market = source.fetch(MarketDataRequest(ticker=args.ticker, start=args.start, end=args.end, timeframe="1d"))
    result = infer_regime_from_close_data(market)

    frame = result.frame.copy()
    frame.reset_index().to_csv(output / "mr001_regime_output.csv", index=False)
    transition_rows = []
    labels = ["EXPANSION", "STRESS"]
    for i, source_label in enumerate(labels):
        for j, target_label in enumerate(labels):
            transition_rows.append(
                {
                    "from_state": source_label,
                    "to_state": target_label,
                    "transition_probability": float(result.model_result.transition_matrix[i, j]),
                }
            )
    pd.DataFrame(transition_rows).to_csv(output / "mr001_transition_matrix.csv", index=False)
    summary = {
        "rows": int(len(frame)),
        "start": str(frame.index.min()),
        "end": str(frame.index.max()),
        "posterior_mean_state_0": float(frame["posterior_state_0"].mean()),
        "posterior_mean_state_1": float(frame["posterior_state_1"].mean()),
        "expansion_state": int(result.model_result.means[:, 0].argmax()),
    }
    (output / "verification_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_reports(output, summary)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate MR-001 implementation.")
    parser.add_argument("--ticker", default="SPY")
    parser.add_argument("--start", default="2008-01-01")
    parser.add_argument("--end", default="2026-01-01")
    parser.add_argument("--output-dir", type=Path, default=Path("output") / "mr_001_validation")
    return parser.parse_args()


def write_reports(output: Path, summary: dict[str, object]) -> None:
    (output / "verification_report.md").write_text(
        f"""# MR-001 Verification Report

## Scope

This validation run checks the implementation pipeline only. It does not assess predictive validity or trading performance.

## Verification Summary

- Rows produced: {summary["rows"]}
- Date range: {summary["start"]} to {summary["end"]}
- Mean posterior state 0: {summary["posterior_mean_state_0"]:.6f}
- Mean posterior state 1: {summary["posterior_mean_state_1"]:.6f}

## Verdict

The implementation is structurally complete if the output CSV, posterior probabilities, latent states, and regime labels are produced deterministically from the same input data.
""",
        encoding="utf-8",
    )
    (output / "reproducibility_report.md").write_text(
        """# Reproducibility Report

Running the validation script twice on the same input data and configuration should produce identical outputs because the HMM initialization is deterministic and no random seed is used.
""",
        encoding="utf-8",
    )
    (output / "unit_test_report.md").write_text(
        """# Unit Test Report

Suggested checks:

1. Feature pipeline returns `daily_log_return` and `realized_volatility_20d`.
2. Two-state HMM output has posterior probabilities that sum to 1 per row.
3. Regime labels are only `EXPANSION` or `STRESS`.
4. Repeated runs on identical input produce byte-identical CSV outputs.
""",
        encoding="utf-8",
    )
    (output / "execution_example.md").write_text(
        """# Execution Example

```powershell
python research/implementations/mr_001/validate_mr_001.py --ticker SPY --start 2008-01-01 --end 2026-01-01 --output-dir output/mr_001_validation
```
""",
        encoding="utf-8",
    )
    (output / "limitations.md").write_text(
        """# Limitations

- This implementation is validated structurally, not for predictive usefulness.
- The HMM is intentionally restricted to two states as specified by CD-001.
- Results depend on Yahoo Finance input data availability and corporate data adjustments.
""",
        encoding="utf-8",
    )
    (output / "executive_summary.md").write_text(
        """# Executive Summary

IM-001 provides a deterministic implementation of MR-001 using a two-state Gaussian HMM over SPY daily log returns and 20-day realized volatility.
""",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
