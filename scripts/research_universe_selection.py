from __future__ import annotations

from pathlib import Path
import math

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output"
ATTRIBUTION_PATH = OUTPUT_DIR / "asset_attribution.csv"


def main() -> None:
    attribution = pd.read_csv(ATTRIBUTION_PATH)
    ranked = _add_ranks(attribution)
    universes = _build_universes(ranked)

    membership = _build_membership(ranked=ranked, universes=universes)
    membership_path = OUTPUT_DIR / "universe_membership.csv"
    membership.to_csv(membership_path, index=False)

    research = _build_universe_research(universes=universes)
    research_path = OUTPUT_DIR / "universe_selection_research.csv"
    research.to_csv(research_path, index=False)

    print(research_path)
    print(membership_path)


def _add_ranks(attribution: pd.DataFrame) -> pd.DataFrame:
    ranked = attribution.copy()
    ranked["volatility_rank"] = ranked["annualized_volatility"].rank(ascending=False, method="min").astype(int)
    ranked["atr_percent_rank"] = ranked["average_ATR_percent"].rank(ascending=False, method="min").astype(int)
    ranked["momentum_rank"] = ranked["momentum_strength"].rank(ascending=False, method="min").astype(int)
    return ranked


def _build_universes(ranked: pd.DataFrame) -> dict[str, list[str]]:
    top_count = math.ceil(len(ranked) * 0.5)
    top_volatility = set(ranked.nsmallest(top_count, "volatility_rank")["ticker"])
    top_atr = set(ranked.nsmallest(top_count, "atr_percent_rank")["ticker"])
    top_momentum = set(ranked.nsmallest(top_count, "momentum_rank")["ticker"])

    return {
        "ALL_ASSETS": sorted(ranked["ticker"].tolist()),
        "TOP_50_VOLATILITY": sorted(top_volatility),
        "TOP_50_ATR_PERCENT": sorted(top_atr),
        "TOP_50_MOMENTUM": sorted(top_momentum),
        "TOP_50_VOLATILITY_AND_MOMENTUM": sorted(top_volatility & top_momentum),
    }


def _build_membership(ranked: pd.DataFrame, universes: dict[str, list[str]]) -> pd.DataFrame:
    rows = []
    rank_lookup = ranked.set_index("ticker")
    for universe_name, assets in universes.items():
        for ticker in assets:
            asset = rank_lookup.loc[ticker]
            rows.append(
                {
                    "universe_name": universe_name,
                    "ticker": ticker,
                    "annualized_volatility": asset["annualized_volatility"],
                    "average_ATR_percent": asset["average_ATR_percent"],
                    "average_daily_range_percent": asset["average_daily_range_percent"],
                    "momentum_strength": asset["momentum_strength"],
                    "beta_vs_SPY": asset["beta_vs_SPY"],
                    "volatility_rank": int(asset["volatility_rank"]),
                    "atr_percent_rank": int(asset["atr_percent_rank"]),
                    "momentum_rank": int(asset["momentum_rank"]),
                }
            )
    return pd.DataFrame(rows)


def _build_universe_research(universes: dict[str, list[str]]) -> pd.DataFrame:
    rows = []
    for universe_name, assets in universes.items():
        trades = _load_trades(assets)
        rows.append({"universe_name": universe_name, "asset_count": len(assets), **_summarize_trades(trades)})
    return pd.DataFrame(rows)


def _load_trades(assets: list[str]) -> pd.DataFrame:
    frames = []
    for ticker in assets:
        trades_path = _resolve_trades_path(ticker)
        if trades_path is None:
            continue
        trades = pd.read_csv(trades_path)
        if trades.empty:
            continue
        trades["ticker"] = ticker
        frames.append(trades)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def _resolve_trades_path(ticker: str) -> Path | None:
    candidates = [
        OUTPUT_DIR / f"leadership_quality_FULL_SYSTEM_{ticker}" / "trades.csv",
        OUTPUT_DIR / f"leadership_expansion_v1_{ticker}" / "trades.csv",
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def _summarize_trades(trades: pd.DataFrame) -> dict[str, float | int]:
    if trades.empty:
        return {
            "trade_count": 0,
            "avg_R": 0.0,
            "expectancy": 0.0,
            "profit_factor": 0.0,
            "net_pnl": 0.0,
            "winrate": 0.0,
        }

    pnl = pd.to_numeric(trades["pnl_dollars"], errors="coerce").fillna(0.0)
    r_values = pd.to_numeric(trades["R_multiple"], errors="coerce").dropna()
    wins = pnl[pnl > 0]
    losses = pnl[pnl < 0]
    win_rate_dec = float((pnl > 0).mean())
    loss_rate_dec = float((pnl < 0).mean())
    avg_win = float(wins.mean()) if not wins.empty else 0.0
    avg_loss_abs = float(abs(losses.mean())) if not losses.empty else 0.0
    gross_profit = float(wins.sum()) if not wins.empty else 0.0
    gross_loss = float(abs(losses.sum())) if not losses.empty else 0.0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else (math.inf if gross_profit > 0 else 0.0)

    return {
        "trade_count": int(len(trades)),
        "avg_R": float(r_values.mean()) if not r_values.empty else 0.0,
        "expectancy": (win_rate_dec * avg_win) - (loss_rate_dec * avg_loss_abs),
        "profit_factor": profit_factor,
        "net_pnl": float(pnl.sum()),
        "winrate": win_rate_dec * 100.0,
    }


if __name__ == "__main__":
    main()
