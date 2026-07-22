from pathlib import Path

import pytest

from pressure_evals.config import DuplicateKeyError, load_yaml_strict

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_duplicate_key_raises(tmp_path: Path):
    bad = tmp_path / "bad.yaml"
    bad.write_text(
        "generation:\n"
        "  max_tokens: 1024\n"
        "  max_tokens: 3072\n"
    )
    with pytest.raises(DuplicateKeyError):
        load_yaml_strict(bad)


def test_valid_config_loads_without_error(tmp_path: Path):
    good = tmp_path / "good.yaml"
    good.write_text("a: 1\nb: 2\n")
    assert load_yaml_strict(good) == {"a": 1, "b": 2}


def test_real_experiment_config_has_no_duplicate_keys():
    config = load_yaml_strict(REPO_ROOT / "configs" / "experiment.yaml")
    assert config["generation"]["max_tokens"] == 3072


def test_real_models_config_loads():
    config = load_yaml_strict(REPO_ROOT / "configs" / "models.yaml")
    assert "subject_models" in config
