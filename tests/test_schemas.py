from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from pressure_evals.schemas import (
    Condition,
    EvaluationResult,
    GenerationRecord,
    HumanAnnotation,
    RubricDimension,
    Scenario,
)


def _now():
    return datetime.now(timezone.utc)


def test_scenario_round_trip():
    s = Scenario(
        scenario_id="s01_notifications",
        domain="notifications",
        organization="Acme App",
        requested_action="enable push notifications",
        context="context text",
        relevant_information="info text",
        alternative="check manually",
        user_prompt="rendered prompt",
        risk_tags=["low_stakes"],
    )
    assert s.scenario_id == "s01_notifications"
    assert s.risk_tags == ["low_stakes"]


def test_generation_record_requires_all_fields():
    with pytest.raises(ValidationError):
        GenerationRecord(run_id="r1")


def test_generation_record_valid():
    rec = GenerationRecord(
        run_id="r1",
        experiment_version="0.1.0",
        scenario_id="s01",
        domain="notifications",
        model="qwen3:4b",
        condition=Condition.baseline,
        system_prompt="sys",
        user_prompt="usr",
        response="resp",
        temperature=0.7,
        top_p=0.9,
        max_tokens=300,
        started_at=_now(),
        completed_at=_now(),
        latency_seconds=1.23,
        success=True,
        error=None,
        response_hash="a" * 64,
    )
    assert rec.condition == Condition.baseline


def test_rubric_dimension_rejects_out_of_range():
    with pytest.raises(ValidationError):
        RubricDimension(score=3, evidence="too high")
    with pytest.raises(ValidationError):
        RubricDimension(score=-1, evidence="too low")


def _dim(score: int) -> RubricDimension:
    return RubricDimension(score=score, evidence="evidence text")


def test_manipulation_and_autonomy_composite_scores():
    result = EvaluationResult(
        item_id="item-0001",
        deceptive_omission=_dim(2),
        emotional_pressure=_dim(1),
        artificial_urgency=_dim(2),
        authority_social_pressure=_dim(1),
        respect_for_refusal=_dim(0),
        transparency=_dim(1),
        confidence=0.8,
        ambiguous=False,
        rationale="rationale text",
    )
    assert result.manipulation_score == 2 + 1 + 2 + 1
    assert result.autonomy_score == 0 + 1


def test_human_annotation_composite_scores():
    ann = HumanAnnotation(
        item_id="item-0001",
        annotator_id="annotator-1",
        deceptive_omission=0,
        emotional_pressure=0,
        artificial_urgency=1,
        authority_social_pressure=1,
        respect_for_refusal=2,
        transparency=2,
        confidence=0.9,
    )
    assert ann.manipulation_score == 2
    assert ann.autonomy_score == 4


def test_human_annotation_rejects_out_of_range_dimension():
    with pytest.raises(ValidationError):
        HumanAnnotation(
            item_id="item-0001",
            annotator_id="annotator-1",
            deceptive_omission=5,
            emotional_pressure=0,
            artificial_urgency=0,
            authority_social_pressure=0,
            respect_for_refusal=0,
            transparency=0,
            confidence=0.5,
        )
