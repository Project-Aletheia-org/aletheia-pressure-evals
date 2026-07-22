"""Paired statistical analysis for condition contrasts.

Every scenario is evaluated under all four conditions by the same model, so
observations are not independent across conditions -- they are paired within
scenario. All primary contrasts here resample or permute at the scenario
level (not the individual-observation level) to respect that structure,
rather than treating 180 outputs as 180 independent draws.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats
from statsmodels.regression.linear_model import OLS
from statsmodels.tools import add_constant


@dataclass
class PairedContrastResult:
    n_pairs: int
    mean_diff: float
    ci_low: float
    ci_high: float
    confidence_level: float


@dataclass
class PermutationTestResult:
    observed_diff: float
    p_value: float
    n_permutations: int


def _paired_diffs(scores_a: np.ndarray, scores_b: np.ndarray) -> np.ndarray:
    if len(scores_a) != len(scores_b):
        raise ValueError("scores_a and scores_b must be paired (same length, same scenario order)")
    return np.asarray(scores_a, dtype=float) - np.asarray(scores_b, dtype=float)


def scenario_blocked_bootstrap_ci(
    scores_a: np.ndarray,
    scores_b: np.ndarray,
    scenario_ids: list,
    *,
    n_resamples: int = 5000,
    confidence_level: float = 0.95,
    seed: int = 42,
) -> PairedContrastResult:
    """Bootstrap CI for mean(scores_a - scores_b), resampling whole scenarios
    (with replacement) rather than individual paired differences, since
    scenarios -- not individual observations -- are the independent unit
    here (each scenario contributes one paired difference per model)."""
    diffs = _paired_diffs(scores_a, scores_b)
    unique_scenarios = np.array(sorted(set(scenario_ids)))
    scenario_to_diffs: dict = {s: [] for s in unique_scenarios}
    for s, d in zip(scenario_ids, diffs):
        scenario_to_diffs[s].append(d)

    rng = np.random.default_rng(seed)
    boot_means = np.empty(n_resamples)
    n_scenarios = len(unique_scenarios)
    for i in range(n_resamples):
        sampled = rng.choice(unique_scenarios, size=n_scenarios, replace=True)
        boot_means[i] = np.mean([d for s in sampled for d in scenario_to_diffs[s]])

    alpha = 1 - confidence_level
    ci_low, ci_high = np.percentile(boot_means, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return PairedContrastResult(
        n_pairs=len(diffs),
        mean_diff=float(np.mean(diffs)),
        ci_low=float(ci_low),
        ci_high=float(ci_high),
        confidence_level=confidence_level,
    )


def paired_permutation_test(
    scores_a: np.ndarray,
    scores_b: np.ndarray,
    scenario_ids: list,
    *,
    n_permutations: int = 10000,
    seed: int = 42,
) -> PermutationTestResult:
    """Sign-flip permutation test on paired differences, appropriate for
    paired (not independent-samples) data: under the null, the sign of each
    scenario's (a - b) difference is exchangeable, so we randomly flip signs
    rather than reshuffle group labels across independent observations."""
    diffs = _paired_diffs(scores_a, scores_b)
    observed = float(np.mean(diffs))

    rng = np.random.default_rng(seed)
    n = len(diffs)
    signs = rng.choice([-1.0, 1.0], size=(n_permutations, n))
    perm_means = (signs * diffs).mean(axis=1)
    p_value = float(np.mean(np.abs(perm_means) >= abs(observed)))

    return PermutationTestResult(
        observed_diff=observed, p_value=p_value, n_permutations=n_permutations
    )


def mann_whitney_secondary(scores_a: np.ndarray, scores_b: np.ndarray) -> tuple[float, float]:
    """Secondary, non-paired check (treats the two groups as independent
    samples). Reported alongside, never in place of, the paired analyses
    above, since it ignores the scenario-pairing structure."""
    result = stats.mannwhitneyu(scores_a, scores_b, alternative="two-sided")
    return float(result.statistic), float(result.pvalue)


def scenario_clustered_regression(
    manipulation_score: np.ndarray,
    pressure: np.ndarray,
    autonomy: np.ndarray,
    model_dummies: np.ndarray,
    scenario_ids: list,
):
    """Exploratory OLS: manipulation_score ~ pressure + autonomy +
    pressure:autonomy + model, with standard errors clustered by scenario_id
    to account for repeated scenarios across conditions and models. This is
    exploratory, not confirmatory -- it is not one of the primary H1-H5
    contrasts."""
    pressure = np.asarray(pressure, dtype=float)
    autonomy = np.asarray(autonomy, dtype=float)
    interaction = pressure * autonomy
    X = np.column_stack([pressure, autonomy, interaction, model_dummies])
    X = add_constant(X)
    y = np.asarray(manipulation_score, dtype=float)

    groups = np.asarray(scenario_ids)
    model = OLS(y, X)
    return model.fit(cov_type="cluster", cov_kwds={"groups": groups})
