import json
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

from pressure_evals.evaluate import BlindedItem, _JUDGE_SYSTEM_PROMPT
from pressure_evals.external_judge import (
    HARD_SPEND_CEILING_USD,
    estimate_cost_usd,
    evaluate_one_claude,
    evaluate_one_claude_with_retry,
    run_external_judge,
    run_external_judge_concurrent,
)
from pressure_evals.prompts import AUTONOMY_ADDITION, BASELINE_PROMPT, PRESSURE_ADDITION

VALID_TOOL_INPUT = {
    "deceptive_omission": {"score": 0, "evidence": "discloses tradeoffs"},
    "emotional_pressure": {"score": 1, "evidence": "mild appeal"},
    "artificial_urgency": {"score": 0, "evidence": "no urgency"},
    "authority_social_pressure": {"score": 0, "evidence": "none"},
    "respect_for_refusal": {"score": 2, "evidence": "clearly optional"},
    "transparency": {"score": 2, "evidence": "explains purpose"},
    "confidence": 0.9,
    "ambiguous": False,
    "rationale": "overall mild",
}


def _mock_response(tool_input, model="claude-sonnet-5-20260315", input_tokens=500, output_tokens=200):
    return SimpleNamespace(
        model=model,
        usage=SimpleNamespace(input_tokens=input_tokens, output_tokens=output_tokens),
        content=[SimpleNamespace(type="tool_use", input=tool_input, model_dump=lambda: {"type": "tool_use", "input": tool_input})],
    )


class FakeMessagesResource:
    def __init__(self, responses_or_exceptions):
        self._queue = list(responses_or_exceptions)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        item = self._queue.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


class FakeClient:
    def __init__(self, responses_or_exceptions):
        self.messages = FakeMessagesResource(responses_or_exceptions)


class KeyedFakeMessagesResource:
    """Thread-safe fake keyed by a unique substring of the user content
    (item_id's response text), since concurrent execution does not
    guarantee call order the way the plain FakeMessagesResource assumes."""

    def __init__(self, responses_by_key):
        self._queues = {k: list(v) for k, v in responses_by_key.items()}
        self._lock = threading.Lock()
        self.calls = []

    def create(self, **kwargs):
        content = kwargs["messages"][0]["content"]
        with self._lock:
            self.calls.append(kwargs)
            key = next(k for k in self._queues if k in content)
            item = self._queues[key].pop(0)
        if isinstance(item, Exception):
            raise item
        return item


class KeyedFakeClient:
    def __init__(self, responses_by_key):
        self.messages = KeyedFakeMessagesResource(responses_by_key)


def _item(item_id="item-0000", scenario_context="ctx", visible_response="You can always decline this.", response_hash=None):
    return BlindedItem(
        item_id=item_id, scenario_context=scenario_context,
        visible_response=visible_response, generation_response_hash=response_hash or f"hash-{item_id}",
    )


def test_blinding_never_includes_subject_prompt_text():
    client = FakeClient([_mock_response(VALID_TOOL_INPUT)])
    record = evaluate_one_claude(_item(), run_id="run-1", client=client)
    call = client.messages.calls[0]
    assert BASELINE_PROMPT not in call["system"]
    assert PRESSURE_ADDITION not in call["system"]
    assert AUTONOMY_ADDITION not in call["system"]
    # the user message must only contain scenario context + visible response, nothing else
    user_content = call["messages"][0]["content"]
    assert "ctx" in user_content
    assert "You can always decline this." in user_content


def test_successful_evaluation_parses_and_records_usage():
    client = FakeClient([_mock_response(VALID_TOOL_INPUT, input_tokens=600, output_tokens=250)])
    record = evaluate_one_claude(_item(), run_id="run-1", client=client)
    assert record.evaluation_record.evaluation_failed is False
    assert record.evaluation_record.result.manipulation_score == 0 + 1 + 0 + 0
    assert record.input_tokens == 600
    assert record.output_tokens == 250
    assert record.estimated_cost_usd == pytest.approx(estimate_cost_usd(600, 250))
    assert record.actual_model_id == "claude-sonnet-5-20260315"
    assert record.retry_count == 0


def test_malformed_tool_input_triggers_repair_then_succeeds():
    bad_input = {"deceptive_omission": {"score": 5, "evidence": "bad"}}  # out of range
    client = FakeClient([_mock_response(bad_input), _mock_response(VALID_TOOL_INPUT)])
    record = evaluate_one_claude(_item(), run_id="run-1", client=client, max_repair_retries=2)
    assert record.evaluation_record.evaluation_failed is False
    assert record.retry_count == 1
    # repair prompt must still contain the rubric and must not leak subject info
    repair_system = client.messages.calls[1]["system"]
    assert _JUDGE_SYSTEM_PROMPT.split("\n")[0] in repair_system  # base rubric text still present
    assert "validation error" in repair_system.lower()
    assert BASELINE_PROMPT not in repair_system
    assert PRESSURE_ADDITION not in repair_system
    assert AUTONOMY_ADDITION not in repair_system


def test_permanent_failure_after_max_repairs_preserves_raw_response():
    bad_input = {"deceptive_omission": {"score": 5, "evidence": "bad"}}
    client = FakeClient([_mock_response(bad_input)] * 3)  # 1 initial + 2 repairs, all bad
    record = evaluate_one_claude(_item(), run_id="run-1", client=client, max_repair_retries=2)
    assert record.evaluation_record.evaluation_failed is True
    assert record.retry_count == 2
    assert record.evaluation_record.raw_response  # not empty, preserved


def test_api_exception_stops_immediately_without_retry_loop():
    client = FakeClient([RuntimeError("connection refused")])
    record = evaluate_one_claude(_item(), run_id="run-1", client=client, max_repair_retries=2)
    assert record.evaluation_record.evaluation_failed is True
    assert "connection refused" in record.evaluation_record.failure_reason


def test_run_external_judge_is_resumable(tmp_path: Path):
    items = [_item(f"item-000{i}", visible_response=f"response {i} you can decline") for i in range(3)]
    client = FakeClient([_mock_response(VALID_TOOL_INPUT) for _ in range(3)])
    output_path = tmp_path / "claude.jsonl"

    first = run_external_judge(items=items, run_id="run-1", client=client, output_path=output_path)
    assert len(first) == 3
    assert len(client.messages.calls) == 3

    second = run_external_judge(items=items, run_id="run-1", client=client, output_path=output_path)
    assert len(second) == 0  # all skipped, no new API calls
    assert len(client.messages.calls) == 3

    lines = output_path.read_text().strip().splitlines()
    assert len(lines) == 3
    for line in lines:
        row = json.loads(line)
        assert "estimated_cost_usd" in row
        assert "input_tokens" in row
        assert "actual_model_id" in row


def test_run_external_judge_halts_at_spend_ceiling(tmp_path: Path):
    items = [_item(f"item-000{i}") for i in range(5)]
    # Each call costs a lot -> ceiling reached quickly
    expensive_response = _mock_response(VALID_TOOL_INPUT, input_tokens=2_000_000, output_tokens=2_000_000)
    client = FakeClient([expensive_response] * 5)
    output_path = tmp_path / "claude.jsonl"

    with pytest.raises(RuntimeError, match="Spend ceiling"):
        run_external_judge(items=items, run_id="run-1", client=client, output_path=output_path, spend_ceiling_usd=1.0)

    # at least one record was written before halting; nothing lost
    lines = output_path.read_text().strip().splitlines()
    assert 1 <= len(lines) < 5


def test_estimate_cost_usd_reasonable():
    cost = estimate_cost_usd(1_000_000, 1_000_000)
    assert cost == pytest.approx(3.0 + 15.0)


def test_hard_spend_ceiling_constant_is_ten():
    assert HARD_SPEND_CEILING_USD == 10.0


def test_retry_wrapper_retries_network_failure_then_succeeds():
    client = FakeClient([RuntimeError("timeout"), _mock_response(VALID_TOOL_INPUT)])
    record = evaluate_one_claude_with_retry(
        _item(), run_id="run-1", client=client, max_network_retries=3, backoff_base_seconds=0.001,
    )
    assert record.evaluation_record.evaluation_failed is False
    assert len(client.messages.calls) == 2


def test_retry_wrapper_gives_up_after_max_network_retries():
    client = FakeClient([RuntimeError("timeout")] * 3)
    record = evaluate_one_claude_with_retry(
        _item(), run_id="run-1", client=client, max_network_retries=2, backoff_base_seconds=0.001,
    )
    assert record.evaluation_record.evaluation_failed is True
    assert len(client.messages.calls) == 3  # 1 initial + 2 retries


def test_retry_wrapper_does_not_retry_schema_failures():
    bad_input = {"deceptive_omission": {"score": 5, "evidence": "bad"}}
    client = FakeClient([_mock_response(bad_input)] * 3)
    record = evaluate_one_claude_with_retry(
        _item(), run_id="run-1", client=client, max_repair_retries=2,
        max_network_retries=5, backoff_base_seconds=0.001,
    )
    assert record.evaluation_record.evaluation_failed is True
    # schema repairs (max_repair_retries=2) exhausted internally; the outer
    # network-retry wrapper must not add further calls on top of that
    assert len(client.messages.calls) == 3


def test_run_external_judge_concurrent_is_resumable(tmp_path: Path):
    items = [_item(f"item-000{i}", visible_response=f"response {i} you can decline") for i in range(6)]
    responses_by_key = {f"response {i} you can decline": [_mock_response(VALID_TOOL_INPUT)] for i in range(6)}
    client = KeyedFakeClient(responses_by_key)
    output_path = tmp_path / "claude.jsonl"

    first = run_external_judge_concurrent(
        items=items, run_id="run-1", client=client, output_path=output_path, concurrency=3,
    )
    assert len(first) == 6
    assert len(client.messages.calls) == 6

    second = run_external_judge_concurrent(
        items=items, run_id="run-1", client=client, output_path=output_path, concurrency=3,
    )
    assert len(second) == 0
    assert len(client.messages.calls) == 6

    lines = output_path.read_text().strip().splitlines()
    assert len(lines) == 6
    assert len({json.loads(line)["generation_response_hash"] for line in lines}) == 6


def test_run_external_judge_concurrent_halts_at_spend_ceiling(tmp_path: Path):
    items = [_item(f"item-000{i}", visible_response=f"resp {i} decline ok") for i in range(5)]
    expensive = {
        f"resp {i} decline ok": [_mock_response(VALID_TOOL_INPUT, input_tokens=2_000_000, output_tokens=2_000_000)]
        for i in range(5)
    }
    client = KeyedFakeClient(expensive)
    output_path = tmp_path / "claude.jsonl"

    with pytest.raises(RuntimeError, match="Spend ceiling"):
        run_external_judge_concurrent(
            items=items, run_id="run-1", client=client, output_path=output_path,
            spend_ceiling_usd=1.0, concurrency=2,
        )
    lines = output_path.read_text().strip().splitlines()
    assert 1 <= len(lines) < 5
