from __future__ import annotations

from dataclasses import dataclass
from math import log, pi
from typing import NamedTuple

import numpy as np
import pandas as pd


class HMMResult(NamedTuple):
    posterior: np.ndarray
    states: np.ndarray
    log_likelihood: float
    means: np.ndarray
    covariances: np.ndarray
    transition_matrix: np.ndarray
    initial_probabilities: np.ndarray


@dataclass(frozen=True, slots=True)
class TwoStateGaussianHMMConfig:
    max_iter: int = 200
    tol: float = 1e-8
    covariance_floor: float = 1e-8
    sticky_transition: float = 0.95


class TwoStateGaussianHMM:
    """Deterministic two-state Gaussian HMM using EM and scaled forward-backward."""

    def __init__(self, config: TwoStateGaussianHMMConfig | None = None) -> None:
        self.config = config or TwoStateGaussianHMMConfig()

    def fit(self, observations: pd.DataFrame | np.ndarray) -> HMMResult:
        x = self._as_array(observations)
        if x.ndim != 2 or x.shape[0] < 10:
            raise ValueError("Observations must be a 2D array with at least 10 rows.")

        means, covariances, transition, init = self._initialize_parameters(x)
        previous_ll = -np.inf

        for _ in range(self.config.max_iter):
            posterior, xi, ll = self._forward_backward(x, means, covariances, transition, init)
            init = posterior[0]
            transition = self._m_step_transition(posterior, xi)
            means, covariances = self._m_step_gaussian(x, posterior)
            if abs(ll - previous_ll) <= self.config.tol * (1.0 + abs(previous_ll)):
                previous_ll = ll
                break
            previous_ll = ll

        posterior, _, ll = self._forward_backward(x, means, covariances, transition, init)
        states = posterior.argmax(axis=1)
        return HMMResult(
            posterior=posterior,
            states=states,
            log_likelihood=ll,
            means=means,
            covariances=covariances,
            transition_matrix=transition,
            initial_probabilities=init,
        )

    def _initialize_parameters(self, x: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        score = self._standardize(x[:, 0]) - self._standardize(x[:, 1])
        threshold = np.median(score)
        state0 = score <= threshold
        state1 = ~state0
        if state0.sum() == 0 or state1.sum() == 0:
            midpoint = len(x) // 2
            state0 = np.zeros(len(x), dtype=bool)
            state0[:midpoint] = True
            state1 = ~state0

        means = np.vstack([x[state0].mean(axis=0), x[state1].mean(axis=0)])
        covariances = np.vstack([
            self._regularized_covariance(x[state0]),
            self._regularized_covariance(x[state1]),
        ])
        transition = np.array(
            [
                [self.config.sticky_transition, 1.0 - self.config.sticky_transition],
                [1.0 - self.config.sticky_transition, self.config.sticky_transition],
            ],
            dtype=float,
        )
        init = np.array([0.5, 0.5], dtype=float)
        return means, covariances, transition, init

    def _forward_backward(self, x: np.ndarray, means: np.ndarray, covariances: np.ndarray, transition: np.ndarray, init: np.ndarray):
        n = x.shape[0]
        k = 2
        log_emission = np.column_stack([self._log_gaussian_density(x, means[i], covariances[i]) for i in range(k)])

        log_alpha = np.zeros((n, k), dtype=float)
        log_scale = np.zeros(n, dtype=float)
        log_alpha[0] = np.log(init + 1e-300) + log_emission[0]
        log_scale[0] = self._logsumexp(log_alpha[0])
        log_alpha[0] -= log_scale[0]

        log_transition = np.log(transition + 1e-300)
        for t in range(1, n):
            for j in range(k):
                log_alpha[t, j] = log_emission[t, j] + self._logsumexp(log_alpha[t - 1] + log_transition[:, j])
            log_scale[t] = self._logsumexp(log_alpha[t])
            log_alpha[t] -= log_scale[t]

        log_beta = np.zeros((n, k), dtype=float)
        for t in range(n - 2, -1, -1):
            for i in range(k):
                log_beta[t, i] = self._logsumexp(log_transition[i] + log_emission[t + 1] + log_beta[t + 1]) - log_scale[t + 1]

        log_gamma = log_alpha + log_beta
        posterior = self._normalize_rows(np.exp(log_gamma))

        xi = np.zeros((n - 1, k, k), dtype=float)
        for t in range(n - 1):
            log_xi_t = (
                log_alpha[t][:, None]
                + log_transition
                + log_emission[t + 1][None, :]
                + log_beta[t + 1][None, :]
            )
            xi[t] = np.exp(log_xi_t - self._logsumexp(log_xi_t.ravel()))

        ll = float(log_scale.sum())
        return posterior, xi, ll

    def _m_step_transition(self, posterior: np.ndarray, xi: np.ndarray) -> np.ndarray:
        trans = xi.sum(axis=0)
        row_sums = trans.sum(axis=1, keepdims=True)
        with np.errstate(divide="ignore", invalid="ignore"):
            transition = np.divide(trans, row_sums, out=np.full_like(trans, 0.5), where=row_sums > 0)
        transition = np.clip(transition, 1e-12, 1.0)
        transition /= transition.sum(axis=1, keepdims=True)
        return transition

    def _m_step_gaussian(self, x: np.ndarray, posterior: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        means = np.zeros((2, x.shape[1]), dtype=float)
        covariances = np.zeros((2, x.shape[1]), dtype=float)
        for state in range(2):
            weights = posterior[:, state]
            weight_sum = weights.sum()
            if weight_sum <= 0:
                means[state] = x.mean(axis=0)
                covariances[state] = self._regularized_covariance(x)
                continue
            means[state] = (weights[:, None] * x).sum(axis=0) / weight_sum
            diff = x - means[state]
            covariances[state] = (weights[:, None] * diff * diff).sum(axis=0) / weight_sum
            covariances[state] = np.maximum(covariances[state], self.config.covariance_floor)
        return means, covariances

    def _log_gaussian_density(self, x: np.ndarray, mean: np.ndarray, covariance: np.ndarray) -> np.ndarray:
        variance = np.maximum(covariance, self.config.covariance_floor)
        diff = x - mean
        return -0.5 * (
            np.sum(np.log(2.0 * pi * variance))
            + np.sum((diff * diff) / variance, axis=1)
        )

    @staticmethod
    def _regularized_covariance(x: np.ndarray) -> np.ndarray:
        if len(x) == 0:
            return np.array([1.0, 1.0], dtype=float)
        cov = np.var(x, axis=0, ddof=0)
        cov = np.where(np.isfinite(cov), cov, 1.0)
        return np.maximum(cov, 1e-8)

    @staticmethod
    def _as_array(observations: pd.DataFrame | np.ndarray) -> np.ndarray:
        if isinstance(observations, pd.DataFrame):
            return observations.to_numpy(dtype=float)
        return np.asarray(observations, dtype=float)

    @staticmethod
    def _standardize(values: np.ndarray) -> np.ndarray:
        mean = np.nanmean(values)
        std = np.nanstd(values)
        if not np.isfinite(std) or std == 0:
            return np.zeros_like(values, dtype=float)
        return (values - mean) / std

    @staticmethod
    def _logsumexp(values: np.ndarray) -> float:
        maximum = np.max(values)
        if not np.isfinite(maximum):
            return float("-inf")
        return float(maximum + np.log(np.sum(np.exp(values - maximum))))

    @staticmethod
    def _normalize_rows(matrix: np.ndarray) -> np.ndarray:
        totals = matrix.sum(axis=1, keepdims=True)
        totals = np.where(totals == 0, 1.0, totals)
        return matrix / totals

