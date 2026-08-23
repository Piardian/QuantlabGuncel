from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from feature_pipeline import MarketRegimeFeaturePipeline
from mr001_hmm_model import HMMResult, TwoStateGaussianHMM, TwoStateGaussianHMMConfig


@dataclass(frozen=True, slots=True)
class RegimeInferenceResult:
    frame: pd.DataFrame
    model_result: HMMResult


def infer_regime_from_close_data(close_data: pd.DataFrame) -> RegimeInferenceResult:
    features = MarketRegimeFeaturePipeline().build(close_data)
    model = TwoStateGaussianHMM(TwoStateGaussianHMMConfig())
    result = model.fit(features[["daily_log_return", "realized_volatility_20d"]])

    regime_frame = features.copy()
    regime_frame["posterior_state_0"] = result.posterior[:, 0]
    regime_frame["posterior_state_1"] = result.posterior[:, 1]
    regime_frame["latent_state"] = result.states

    expansion_state = _expansion_state(result.means)
    regime_frame["regime_label"] = regime_frame["latent_state"].map(
        {expansion_state: "EXPANSION", 1 - expansion_state: "STRESS"}
    )
    regime_frame["state_label"] = regime_frame["regime_label"]
    return RegimeInferenceResult(frame=regime_frame, model_result=result)


def infer_regime_from_close_csv(path: Path | str) -> RegimeInferenceResult:
    frame = pd.read_csv(path, parse_dates=["Datetime"]).set_index("Datetime")
    return infer_regime_from_close_data(frame)


def _expansion_state(means: pd.DataFrame | pd.Series | object) -> int:
    array = pd.DataFrame(means).to_numpy(dtype=float)
    return int(array[:, 0].argmax())

