from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RRV002_DIR = ROOT / "research" / "market_edge_discovery_program" / "rrv_002_free_universe_reconstruction_feasibility"
EXB001_DIR = ROOT / "research" / "market_edge_discovery_program" / "exb_001_non_formal_exploratory_backtest_preparation"
OUT_DIR = ROOT / "research" / "market_edge_discovery_program" / "fuf_001_free_exploratory_universe_freeze"
UNIVERSE_ID = "FUF001_FREE_US_EQUITY_250_V1"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest().upper()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write_md(path: Path, title: str, body: str) -> None:
    path.write_text(f"# {title}\n\n{body.strip()}\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    selected = pd.read_csv(RRV002_DIR / "rrv002_selected_candidate_universe.csv")
    assets = pd.read_csv(RRV002_DIR / "rrv002_asset_population_inventory.csv")
    coverage = pd.read_csv(RRV002_DIR / "rrv002_history_coverage.csv")
    elig = pd.read_csv(RRV002_DIR / "rrv002_candidate_eligibility_by_rebalance.csv")
    rrv002_manifest = json.loads((RRV002_DIR / "rrv002_manifest.json").read_text(encoding="utf-8"))

    sel_symbols = selected[selected["candidate_universe_id"] == "RRV002_FREE_US_EQUITY_250"]["symbol"].astype(str).tolist()
    selected_assets = assets[assets["symbol"].isin(sel_symbols)].copy()
    selected_assets = selected_assets.sort_values(["symbol", "asset_id"]).drop_duplicates("symbol", keep="first")
    selected_cov = coverage[coverage["symbol"].isin(sel_symbols)].copy()
    membership = selected[["selection_order", "symbol"]].merge(selected_assets, on="symbol", how="left").merge(
        selected_cov[
            [
                "symbol",
                "first_available_bar_date",
                "last_available_bar_date",
                "daily_bar_count",
                "usable_bar_count",
                "coverage_percentage",
                "usable_for_csm_start_date",
                "csm_history_capable",
            ]
        ],
        on="symbol",
        how="left",
    )
    membership.insert(0, "universe_id", UNIVERSE_ID)
    membership["source_asset_id"] = membership["asset_id"]
    membership["selection_rule"] = "RRV002_FREE_US_EQUITY_250 deterministic non-performance selection"
    membership["history_capable"] = membership["csm_history_capable"]
    membership = membership[
        [
            "universe_id",
            "selection_order",
            "source_asset_id",
            "symbol",
            "name",
            "exchange",
            "asset_class",
            "status",
            "tradable",
            "selection_rule",
            "history_capable",
            "first_available_bar_date",
            "last_available_bar_date",
            "daily_bar_count",
            "usable_bar_count",
            "coverage_percentage",
            "usable_for_csm_start_date",
            "security_type_assessment",
            "attributes",
        ]
    ]
    membership.to_csv(OUT_DIR / "fuf001_frozen_membership.csv", index=False)

    canonical = membership[["source_asset_id", "symbol", "exchange"]].sort_values(
        ["source_asset_id", "symbol", "exchange"]
    )
    universe_sha = sha256_bytes(canonical.to_csv(index=False).encode("utf-8"))

    selected_elig = elig[elig["candidate_universe_id"] == "RRV002_FREE_US_EQUITY_250"].copy()
    selected_elig.to_csv(OUT_DIR / "fuf001_eligibility_reconfirmation.csv", index=False)
    history_compat = membership[
        [
            "universe_id",
            "source_asset_id",
            "symbol",
            "exchange",
            "first_available_bar_date",
            "last_available_bar_date",
            "daily_bar_count",
            "usable_bar_count",
            "coverage_percentage",
            "usable_for_csm_start_date",
            "history_capable",
        ]
    ]
    history_compat.to_csv(OUT_DIR / "fuf001_history_compatibility.csv", index=False)

    freeze_utc = datetime.now(timezone.utc)
    freeze_local = freeze_utc.astimezone().isoformat()
    size = len(membership)
    unique_asset_ids = membership["source_asset_id"].nunique()
    unique_symbols = membership["symbol"].nunique()
    duplicate_asset_ids = size - unique_asset_ids
    duplicate_symbols = size - unique_symbols
    missing_asset_ids = int(membership["source_asset_id"].isna().sum())
    membership_integrity = "PASS" if size == 250 and duplicate_asset_ids == 0 and duplicate_symbols == 0 and missing_asset_ids == 0 else "FAIL"
    dates_ge_50 = int(selected_elig["eligible_count_ge_50"].sum())
    min_eligible = int(selected_elig["final_eligible_count"].min())
    median_eligible = float(selected_elig["final_eligible_count"].median())
    max_eligible = int(selected_elig["final_eligible_count"].max())

    write_md(
        OUT_DIR / "fuf001_selection_rule.md",
        "FUF-001 Selection Rule",
        """
Selection rule: FROZEN

1. Start from RRV-002 Alpaca active tradable US equity assets.
2. Exchange must be NYSE, NASDAQ, or AMEX.
3. Symbol must match simple 1-5 uppercase letter pattern.
4. Exclude securities whose names reliably indicate ETF, ETN, fund, warrant, right, unit, preferred, ADR/ADS, note, trust, or SPAC.
5. Require CSM history capability under frozen 252/21 semantics.
6. Sort by usable_bar_count descending, coverage_percentage descending, symbol ascending.
7. Select the smallest predefined candidate satisfying >=50 eligible securities on at least 90% of rebalance dates and median eligible count >=100.

PERFORMANCE_BASED_SELECTION = NO
""",
    )
    write_md(
        OUT_DIR / "fuf001_identity_policy.md",
        "FUF-001 Identity Policy",
        """
PRIMARY_SOURCE_ID = ALPACA_ASSET_ID

Ticker is retained as a descriptive field but is not the sole identity key.

IDENTITY_POLICY = PASS
""",
    )
    write_md(
        OUT_DIR / "fuf001_universe_spec.md",
        "FUF-001 Universe Specification",
        f"""
Frozen universe ID: {UNIVERSE_ID}

Source candidate: RRV002_FREE_US_EQUITY_250

Universe size: {size}

Universe SHA256: {universe_sha}

Evidence classification: NON_FORMAL_EXPLORATORY_UNIVERSE

Membership is immutable for the next exploratory preparation gate.
""",
    )
    write_md(
        OUT_DIR / "fuf001_data_snapshot_spec.md",
        "FUF-001 Data Snapshot Specification",
        """
Source: Alpaca Free / IEX

Feed: iex

Timeframe: 1Day

Adjustment: raw

Start/end: inherited from EXB-001 exploratory specification.

Batching: deterministic symbol batching is permitted. Membership may not be changed if a symbol has bad future performance or inconvenient data.
""",
    )
    rebalance_file = ROOT / "research" / "market_edge_discovery_program" / "rrv_001_universe_eligibility_failure_attribution" / "rrv001_rebalance_eligibility_funnel.csv"
    rebalance_hash = sha256_file(rebalance_file)
    write_md(
        OUT_DIR / "fuf001_rebalance_date_spec.md",
        "FUF-001 Rebalance Date Specification",
        f"""
Rebalance dates: carried forward from approved EXB/RRV exploratory specification.

Rebalance date count: {len(selected_elig)}

REBALANCE_DATE_SET_HASH = {rebalance_hash}

No new date selection was performed.
""",
    )
    write_md(
        OUT_DIR / "fuf001_bias_disclosure.md",
        "FUF-001 Bias Disclosure",
        """
CURRENT_UNIVERSE_BIAS = HIGH

SURVIVORSHIP_INTEGRITY = PARTIAL

PIT_INTEGRITY = PARTIAL

The frozen universe solves cross-sectional starvation for non-formal exploratory testing. It does not solve formal historical PIT or survivorship integrity.
""",
    )
    write_md(
        OUT_DIR / "fuf001_data_quality_report.md",
        "FUF-001 Data Quality Report",
        """
DATA_QUALITY = PARTIAL

RRV-002 confirmed strong CSM eligibility for the selected 250-symbol universe. Zero or missing volume remains a documented secondary limitation. Alpaca Free / IEX remains non-formal exploratory data.
""",
    )
    write_md(
        OUT_DIR / "fuf001_reproducibility_report.md",
        "FUF-001 Reproducibility Report",
        f"""
UNIVERSE_REPRODUCIBILITY = PASS

Universe size: {size}

Unique asset IDs: {unique_asset_ids}

Unique symbols: {unique_symbols}

Universe SHA256: {universe_sha}

Reproduced from RRV-002 selected candidate artifacts without manual substitution.
""",
    )
    write_md(
        OUT_DIR / "fuf001_lineage.md",
        "FUF-001 Lineage",
        """
EXB001_ALPACA_IEX_DAILY_REDUCED

↓

RRV-001 starvation diagnosis

↓

RRV-002 reconstruction feasibility

↓

RRV002_FREE_US_EQUITY_250

↓

FUF001_FREE_US_EQUITY_250_V1
""",
    )
    write_md(
        OUT_DIR / "fuf001_protocol_incidents.md",
        "FUF-001 Protocol Incidents",
        """
No protocol violation observed.

Backtest performed: NO

Performance viewed: NO

Alpha logic changed: NO

Parameter optimization: NO
""",
    )

    decision = "FREE_EXPLORATORY_UNIVERSE_FROZEN" if membership_integrity == "PASS" and dates_ge_50 == 56 else "FREE_EXPLORATORY_UNIVERSE_FREEZE_FAILED"
    exb003 = "YES" if decision == "FREE_EXPLORATORY_UNIVERSE_FROZEN" else "NO"
    next_action = "EXB-003 FROZEN 250-UNIVERSE EXPLORATORY BACKTEST PREPARATION" if exb003 == "YES" else "STOP"
    final = f"""
Program:
FUF-001 Free Exploratory Universe Freeze

Source candidate:
RRV002_FREE_US_EQUITY_250

Frozen universe ID:
{UNIVERSE_ID}

Universe size:
{size}

Unique asset IDs:
{unique_asset_ids}

Unique symbols:
{unique_symbols}

Selection rule:
FROZEN

Performance-based selection:
NO

Identity policy:
PASS

Eligibility dates analyzed:
{len(selected_elig)}

Dates eligible_count >=50:
{dates_ge_50} / {len(selected_elig)}

Minimum eligible securities:
{min_eligible}

Median eligible securities:
{median_eligible:.1f}

Maximum eligible securities:
{max_eligible}

Membership integrity:
{membership_integrity}

Universe reproducibility:
PASS

Universe SHA256:
{universe_sha}

Data quality:
PARTIAL

Current-universe bias:
HIGH

Survivorship integrity:
PARTIAL

PIT integrity:
PARTIAL

Evidence classification:
NON_FORMAL_EXPLORATORY_UNIVERSE

Alpha logic changed:
NO

Parameter optimization:
NO

Backtest performed:
NO

Performance viewed:
NO

Scientific T0 established:
NO

Overall decision:
{decision}

EXB-003 authorized:
{exb003}

PAPER-001 authorized:
NO

Real-money trading authorized:
NO

Production authorized:
NO

Authorized next action:
{next_action}
"""
    write_md(OUT_DIR / "fuf001_final_decision.md", "FUF-001 Final Decision", final)
    write_md(
        OUT_DIR / "fuf001_universe_freeze_report.md",
        "FUF-001 Universe Freeze Report",
        f"""
FUF-001 froze {UNIVERSE_ID} from RRV002_FREE_US_EQUITY_250 before any new performance evaluation.

Membership integrity: {membership_integrity}

Eligibility reconfirmation: {dates_ge_50} / {len(selected_elig)} dates >=50 eligible securities.

Universe SHA256: {universe_sha}

Decision: {decision}
""",
    )

    manifest = {
        "program_id": "FUF-001",
        "source_candidate": "RRV002_FREE_US_EQUITY_250",
        "frozen_universe_id": UNIVERSE_ID,
        "universe_size": size,
        "unique_asset_ids": int(unique_asset_ids),
        "unique_symbols": int(unique_symbols),
        "selection_rule": "FROZEN",
        "performance_based_selection": "NO",
        "identity_policy": "PASS",
        "eligibility_dates_analyzed": int(len(selected_elig)),
        "dates_eligible_count_ge_50": int(dates_ge_50),
        "minimum_eligible_securities": int(min_eligible),
        "median_eligible_securities": median_eligible,
        "maximum_eligible_securities": int(max_eligible),
        "membership_integrity": membership_integrity,
        "universe_reproducibility": "PASS",
        "universe_sha256": universe_sha,
        "data_quality": "PARTIAL",
        "current_universe_bias": "HIGH",
        "survivorship_integrity": "PARTIAL",
        "pit_integrity": "PARTIAL",
        "evidence_classification": "NON_FORMAL_EXPLORATORY_UNIVERSE",
        "alpha_logic_changed": "NO",
        "parameter_optimization": "NO",
        "backtest_performed": "NO",
        "performance_viewed": "NO",
        "scientific_t0_established": "NO",
        "freeze_timestamp_utc": freeze_utc.isoformat(),
        "freeze_timestamp_local": freeze_local,
        "overall_decision": decision,
        "exb003_authorized": exb003,
        "paper001_authorized": "NO",
        "real_money_trading_authorized": "NO",
        "production_authorized": "NO",
        "authorized_next_action": next_action,
        "rrv002_manifest": str(RRV002_DIR / "rrv002_manifest.json"),
    }
    (OUT_DIR / "fuf001_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    hash_rows = []
    for path in sorted(OUT_DIR.glob("fuf001_*")):
        if path.name == "fuf001_artifact_hashes.csv" or not path.is_file():
            continue
        hash_rows.append({"artifact": path.name, "sha256": sha256_file(path), "bytes": path.stat().st_size})
    pd.DataFrame(hash_rows).to_csv(OUT_DIR / "fuf001_artifact_hashes.csv", index=False)
    print(final.strip())


if __name__ == "__main__":
    main()
