import json
from pathlib import Path

import pytest

from pressure_evals import generate as generate_mod
from pressure_evals.ollama_client import ChatResult
from pressure_evals.schemas import Condition, Scenario


def _scenario(scenario_id="s01") -> Scenario:
    return Scenario(
        scenario_id=scenario_id,
        domain="notifications",
        organization="Acme",
        requested_action="enable notifications",
        context="ctx",
        relevant_information="info",
        alternative="alt",
        user_prompt="rendered prompt",
        risk_tags=[],
    )


def test_generate_one_success(monkeypatch):
    def fake_chat(model, system_prompt, user_prompt, *, temperature, top_p, max_tokens):
        return ChatResult(text="a persuasive message", latency_seconds=1.5)

    monkeypatch.setattr(generate_mod, "chat", fake_chat)
    record = generate_mod.generate_one(
        _scenario(),
        "qwen3:4b",
        Condition.baseline,
        run_id="run-1",
        experiment_version="0.1.0",
        temperature=0.7,
        top_p=0.9,
        max_tokens=1024,
    )
    assert record.success is True
    assert record.error is None
    assert record.response == "a persuasive message"
    assert len(record.response_hash) == 64


def test_generate_one_preserves_thinking_text(monkeypatch):
    def fake_chat(model, system_prompt, user_prompt, *, temperature, top_p, max_tokens):
        return ChatResult(text="final answer", latency_seconds=2.0, thinking="reasoning trace")

    monkeypatch.setattr(generate_mod, "chat", fake_chat)
    record = generate_mod.generate_one(
        _scenario(),
        "qwen3:4b",
        Condition.baseline,
        run_id="run-1",
        experiment_version="0.1.0",
        temperature=0.7,
        top_p=0.9,
        max_tokens=1024,
    )
    assert record.response == "final answer"
    assert record.thinking == "reasoning trace"


def test_generate_one_thinking_defaults_to_none_for_non_reasoning_models(monkeypatch):
    def fake_chat(model, system_prompt, user_prompt, *, temperature, top_p, max_tokens):
        return ChatResult(text="final answer", latency_seconds=1.0)

    monkeypatch.setattr(generate_mod, "chat", fake_chat)
    record = generate_mod.generate_one(
        _scenario(),
        "gemma3:4b",
        Condition.baseline,
        run_id="run-1",
        experiment_version="0.1.0",
        temperature=0.7,
        top_p=0.9,
        max_tokens=1024,
    )
    assert record.thinking is None


def test_generate_one_treats_empty_response_as_failure(monkeypatch):
    """A reasoning model can spend its whole token budget on hidden
    chain-of-thought and return empty content; that must not be recorded as
    a success, or it would silently enter scoring as an empty "message"."""

    def fake_chat(model, system_prompt, user_prompt, *, temperature, top_p, max_tokens):
        return ChatResult(text="", latency_seconds=60.0, thinking="very long reasoning trace")

    monkeypatch.setattr(generate_mod, "chat", fake_chat)
    record = generate_mod.generate_one(
        _scenario(),
        "qwen3:4b",
        Condition.pressure,
        run_id="run-1",
        experiment_version="0.1.0",
        temperature=0.7,
        top_p=0.9,
        max_tokens=1024,
    )
    assert record.success is False
    assert "EmptyResponseError" in record.error
    assert record.thinking == "very long reasoning trace"


def test_generate_one_records_failure_without_raising(monkeypatch):
    def fake_chat(*args, **kwargs):
        raise RuntimeError("connection refused")

    monkeypatch.setattr(generate_mod, "chat", fake_chat)
    record = generate_mod.generate_one(
        _scenario(),
        "qwen3:4b",
        Condition.pressure,
        run_id="run-1",
        experiment_version="0.1.0",
        temperature=0.7,
        top_p=0.9,
        max_tokens=1024,
    )
    assert record.success is False
    assert "connection refused" in record.error
    assert record.response == ""


def test_run_generation_is_resumable(monkeypatch, tmp_path: Path):
    calls = []

    def fake_chat(model, system_prompt, user_prompt, *, temperature, top_p, max_tokens):
        calls.append((model, system_prompt))
        return ChatResult(text="msg", latency_seconds=0.1)

    monkeypatch.setattr(generate_mod, "chat", fake_chat)
    output_path = tmp_path / "run.jsonl"
    scenarios = [_scenario("s01"), _scenario("s02")]
    models = ["qwen3:4b"]
    conditions = [Condition.baseline, Condition.pressure]

    first = generate_mod.run_generation(
        scenarios=scenarios,
        models=models,
        conditions=conditions,
        run_id="run-1",
        experiment_version="0.1.0",
        temperature=0.7,
        top_p=0.9,
        max_tokens=1024,
        output_path=output_path,
    )
    assert len(first) == 4  # 2 scenarios x 1 model x 2 conditions
    assert len(calls) == 4

    # Second invocation with the same output_path should skip everything.
    second = generate_mod.run_generation(
        scenarios=scenarios,
        models=models,
        conditions=conditions,
        run_id="run-1",
        experiment_version="0.1.0",
        temperature=0.7,
        top_p=0.9,
        max_tokens=1024,
        output_path=output_path,
    )
    assert len(second) == 0
    assert len(calls) == 4  # no new model calls made

    lines = output_path.read_text().strip().splitlines()
    assert len(lines) == 4


def test_run_generation_records_model_digest_and_replicate_id(monkeypatch, tmp_path: Path):
    def fake_chat(model, system_prompt, user_prompt, *, temperature, top_p, max_tokens):
        return ChatResult(text="msg", latency_seconds=0.1)

    monkeypatch.setattr(generate_mod, "chat", fake_chat)
    output_path = tmp_path / "run.jsonl"

    records = generate_mod.run_generation(
        scenarios=[_scenario("s01")],
        models=["qwen3:4b"],
        conditions=[Condition.baseline],
        run_id="run-1",
        experiment_version="0.1.0",
        temperature=0.7,
        top_p=0.9,
        max_tokens=1024,
        output_path=output_path,
        model_digests={"qwen3:4b": "abc123"},
        replicate_id=0,
    )
    assert records[0].model_digest == "abc123"
    assert records[0].replicate_id == 0
    assert records[0].prompt_version == "v0.1"


def test_run_generation_resumes_after_failure(monkeypatch, tmp_path: Path):
    attempt = {"n": 0}

    def flaky_chat(model, system_prompt, user_prompt, *, temperature, top_p, max_tokens):
        attempt["n"] += 1
        if attempt["n"] == 1:
            raise RuntimeError("boom")
        return ChatResult(text="msg", latency_seconds=0.1)

    monkeypatch.setattr(generate_mod, "chat", flaky_chat)
    output_path = tmp_path / "run.jsonl"
    scenarios = [_scenario("s01")]
    models = ["qwen3:4b"]
    conditions = [Condition.baseline]

    first = generate_mod.run_generation(
        scenarios=scenarios,
        models=models,
        conditions=conditions,
        run_id="run-1",
        experiment_version="0.1.0",
        temperature=0.7,
        top_p=0.9,
        max_tokens=1024,
        output_path=output_path,
    )
    assert first[0].success is False

    # Re-running should retry the failed cell (not marked done) rather than skip it.
    second = generate_mod.run_generation(
        scenarios=scenarios,
        models=models,
        conditions=conditions,
        run_id="run-1",
        experiment_version="0.1.0",
        temperature=0.7,
        top_p=0.9,
        max_tokens=1024,
        output_path=output_path,
    )
    assert len(second) == 1
    assert second[0].success is True

    lines = output_path.read_text().strip().splitlines()
    assert len(lines) == 2  # failed attempt + successful retry, both preserved
