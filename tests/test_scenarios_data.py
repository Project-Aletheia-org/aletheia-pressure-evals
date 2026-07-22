import json
from pathlib import Path

from pressure_evals.prompts import render_user_prompt
from pressure_evals.schemas import Scenario

SCENARIOS_PATH = Path(__file__).resolve().parents[1] / "data" / "scenarios.jsonl"


def _load_scenarios() -> list[Scenario]:
    scenarios = []
    with SCENARIOS_PATH.open() as f:
        for line in f:
            scenarios.append(Scenario(**json.loads(line)))
    return scenarios


def test_exactly_fifteen_scenarios():
    assert len(_load_scenarios()) == 15


def test_scenario_ids_and_domains_are_unique():
    scenarios = _load_scenarios()
    ids = [s.scenario_id for s in scenarios]
    domains = [s.domain for s in scenarios]
    assert len(ids) == len(set(ids))
    assert len(domains) == len(set(domains))


def test_no_scenario_has_dangerous_risk_tags():
    banned = {"medical", "political", "illegal", "self_harm", "dangerous"}
    for s in _load_scenarios():
        assert not (banned & set(s.risk_tags)), s.scenario_id


def test_stored_user_prompt_matches_current_template():
    """Catches drift if prompts.py's template changes without regenerating data."""
    for s in _load_scenarios():
        assert s.user_prompt == render_user_prompt(s), s.scenario_id


def test_word_limit_instruction_present():
    for s in _load_scenarios():
        assert "150 words" in s.user_prompt
