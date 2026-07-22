import numpy as np
import pytest

from pressure_evals.analyze import (
    mann_whitney_secondary,
    paired_permutation_test,
    scenario_blocked_bootstrap_ci,
    scenario_clustered_regression,
)


def _synthetic_paired(n_scenarios=15, seed=0):
    rng = np.random.default_rng(seed)
    scenario_ids = [f"s{i:02d}" for i in range(n_scenarios)]
    baseline = rng.normal(2.0, 0.5, size=n_scenarios)
    pressure = baseline + 1.5 + rng.normal(0, 0.3, size=n_scenarios)  # true effect +1.5
    return scenario_ids, baseline, pressure


def test_scenario_blocked_bootstrap_ci_detects_real_effect():
    scenario_ids, baseline, pressure = _synthetic_paired()
    result = scenario_blocked_bootstrap_ci(pressure, baseline, scenario_ids, n_resamples=2000, seed=1)
    assert result.n_pairs == 15
    assert result.mean_diff > 1.0  # true effect is +1.5
    assert result.ci_low > 0  # CI should exclude zero given a strong effect
    assert result.ci_low < result.mean_diff < result.ci_high


def test_scenario_blocked_bootstrap_ci_null_effect_includes_zero():
    scenario_ids = [f"s{i:02d}" for i in range(15)]
    rng = np.random.default_rng(2)
    a = rng.normal(2.0, 0.5, size=15)
    b = a.copy()  # identical -> true difference is exactly zero
    result = scenario_blocked_bootstrap_ci(a, b, scenario_ids, n_resamples=2000, seed=3)
    assert result.mean_diff == 0.0
    assert result.ci_low <= 0.0 <= result.ci_high


def test_bootstrap_requires_paired_equal_length():
    with pytest.raises(ValueError):
        scenario_blocked_bootstrap_ci([1, 2, 3], [1, 2], ["a", "b", "c"])


def test_paired_permutation_test_detects_real_effect():
    scenario_ids, baseline, pressure = _synthetic_paired()
    result = paired_permutation_test(pressure, baseline, scenario_ids, n_permutations=5000, seed=1)
    assert result.observed_diff > 1.0
    assert result.p_value < 0.05  # strong synthetic effect should be significant


def test_paired_permutation_test_null_effect_not_significant():
    scenario_ids = [f"s{i:02d}" for i in range(15)]
    rng = np.random.default_rng(4)
    a = rng.normal(2.0, 0.5, size=15)
    b = a + rng.normal(0, 0.01, size=15)  # negligible difference
    result = paired_permutation_test(a, b, scenario_ids, n_permutations=5000, seed=5)
    assert result.p_value > 0.05


def test_mann_whitney_secondary_returns_stat_and_pvalue():
    rng = np.random.default_rng(6)
    a = rng.normal(5, 1, size=30)
    b = rng.normal(2, 1, size=30)
    stat, p = mann_whitney_secondary(a, b)
    assert p < 0.05
    assert stat > 0


def test_scenario_clustered_regression_recovers_pressure_effect():
    rng = np.random.default_rng(7)
    n_scenarios = 15
    scenario_ids = []
    manipulation = []
    pressure_col = []
    autonomy_col = []
    model_dummy = []
    for s in range(n_scenarios):
        for p in (0, 1):
            for a in (0, 1):
                scenario_ids.append(f"s{s:02d}")
                pressure_col.append(p)
                autonomy_col.append(a)
                model_dummy.append(0)
                true = 2.0 + 2.0 * p - 1.0 * a + rng.normal(0, 0.2)
                manipulation.append(true)

    result = scenario_clustered_regression(
        np.array(manipulation),
        np.array(pressure_col),
        np.array(autonomy_col),
        np.array(model_dummy).reshape(-1, 1),
        scenario_ids,
    )
    # coefficient order: const, pressure, autonomy, interaction, model_dummy
    assert result.params[1] == pytest.approx(2.0, abs=0.5)
