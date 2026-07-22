from pressure_evals.prompts import (
    AUTONOMY_ADDITION,
    BASELINE_PROMPT,
    PRESSURE_ADDITION,
    render_system_prompt,
    render_user_prompt,
)
from pressure_evals.schemas import Condition, Scenario


def _scenario() -> Scenario:
    return Scenario(
        scenario_id="s01_notifications",
        domain="notifications",
        organization="FocusFlow",
        requested_action="enable notifications",
        context="context text",
        relevant_information="info text",
        alternative="check the app manually",
        user_prompt="placeholder",
        risk_tags=["low_stakes"],
    )


def test_baseline_condition_has_no_additions():
    prompt = render_system_prompt(Condition.baseline)
    assert prompt == BASELINE_PROMPT
    assert PRESSURE_ADDITION not in prompt
    assert AUTONOMY_ADDITION not in prompt


def test_pressure_condition_adds_only_pressure_text():
    prompt = render_system_prompt(Condition.pressure)
    assert BASELINE_PROMPT in prompt
    assert PRESSURE_ADDITION in prompt
    assert AUTONOMY_ADDITION not in prompt


def test_autonomy_condition_adds_only_autonomy_text():
    prompt = render_system_prompt(Condition.autonomy)
    assert BASELINE_PROMPT in prompt
    assert AUTONOMY_ADDITION in prompt
    assert PRESSURE_ADDITION not in prompt


def test_pressure_autonomy_condition_adds_both():
    prompt = render_system_prompt(Condition.pressure_autonomy)
    assert BASELINE_PROMPT in prompt
    assert PRESSURE_ADDITION in prompt
    assert AUTONOMY_ADDITION in prompt


def test_four_conditions_produce_four_distinct_prompts():
    prompts = {render_system_prompt(c) for c in Condition}
    assert len(prompts) == 4


def test_user_prompt_renders_all_scenario_fields():
    rendered = render_user_prompt(_scenario())
    assert "FocusFlow" in rendered
    assert "enable notifications" in rendered
    assert "context text" in rendered
    assert "info text" in rendered
    assert "check the app manually" in rendered
    assert "150 words" in rendered
