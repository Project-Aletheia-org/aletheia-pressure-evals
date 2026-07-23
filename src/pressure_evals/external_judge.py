"""External sensitivity judge: claude-sonnet-5 via the Anthropic Messages
API, scoring the same 180 blinded items as the local judges.

This is a measurement-validation extension, not a replacement for the
qwen3:4b primary judge. It reuses the exact same blinding (item content,
rubric, prompt structure) as `evaluate.py`'s local-judge path, so results
are directly comparable, but is a separate code path since it calls a
different API (Anthropic, not Ollama) with different auth, rate limits,
and cost tracking requirements.

The API key is read only from the ANTHROPIC_API_KEY environment variable
via the SDK's default client construction; it is never logged, printed, or
written to any output file.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import anthropic
from pydantic import ValidationError

from pressure_evals.evaluate import BlindedItem, _JUDGE_SYSTEM_PROMPT, evaluation_prompt_hash
from pressure_evals.schemas import EvaluationRecord, EvaluationResult, JudgeRawOutput

EXTERNAL_JUDGE_MODEL = "claude-sonnet-5"

# Anthropic Sonnet-class published rates as of this study; not independently
# re-verified per call. Treat cost figures derived from these as estimates,
# not authoritative billing records -- the real total is whatever appears
# on the Anthropic account, not this constant.
ASSUMED_INPUT_RATE_PER_MTOK_USD = 3.0
ASSUMED_OUTPUT_RATE_PER_MTOK_USD = 15.0
HARD_SPEND_CEILING_USD = 10.0

_TOOL_NAME = "record_evaluation"


def _tool_schema() -> dict:
    schema = JudgeRawOutput.model_json_schema()
    return {
        "name": _TOOL_NAME,
        "description": "Record the blinded behavioral evaluation for this item.",
        "input_schema": schema,
    }


def estimate_cost_usd(input_tokens: int, output_tokens: int) -> float:
    return (
        input_tokens / 1_000_000 * ASSUMED_INPUT_RATE_PER_MTOK_USD
        + output_tokens / 1_000_000 * ASSUMED_OUTPUT_RATE_PER_MTOK_USD
    )


@dataclass
class ExternalJudgeRecord:
    """EvaluationRecord plus Anthropic-specific provenance (token usage,
    cost, exact model ID, retry count) not present in the local-judge
    schema (which has no per-call cost concept)."""

    evaluation_record: EvaluationRecord
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float
    actual_model_id: Optional[str]
    retry_count: int
    input_hash: str

    def to_json_dict(self) -> dict:
        d = json.loads(self.evaluation_record.model_dump_json())
        d.update(
            input_tokens=self.input_tokens,
            output_tokens=self.output_tokens,
            estimated_cost_usd=self.estimated_cost_usd,
            actual_model_id=self.actual_model_id,
            retry_count=self.retry_count,
            input_hash=self.input_hash,
        )
        return d


def _build_user_prompt(item: BlindedItem) -> str:
    return (
        f"Request context:\n{item.scenario_context}\n\n"
        f"Assistant's message to the user:\n{item.visible_response}"
    )


def evaluate_one_claude(
    item: BlindedItem,
    *,
    run_id: str,
    client: "anthropic.Anthropic",
    max_tokens: int = 1024,
    max_repair_retries: int = 2,
    timeout: float = 60.0,
) -> ExternalJudgeRecord:
    user_prompt = _build_user_prompt(item)
    input_hash = hashlib.sha256((_JUDGE_SYSTEM_PROMPT + "\n" + user_prompt).encode("utf-8")).hexdigest()
    tool = _tool_schema()

    system_prompt = _JUDGE_SYSTEM_PROMPT
    attempts = 0
    last_error: Optional[str] = None
    last_raw = ""
    result: Optional[JudgeRawOutput] = None
    total_input_tokens = 0
    total_output_tokens = 0
    actual_model_id: Optional[str] = None

    while attempts <= max_repair_retries:
        attempts += 1
        try:
            response = client.messages.create(
                model=EXTERNAL_JUDGE_MODEL,
                max_tokens=max_tokens,
                temperature=0,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
                tools=[tool],
                tool_choice={"type": "tool", "name": _TOOL_NAME},
                timeout=timeout,
            )
        except Exception as exc:  # noqa: BLE001
            last_error = f"{type(exc).__name__}: {exc}"
            break

        actual_model_id = response.model
        total_input_tokens += response.usage.input_tokens
        total_output_tokens += response.usage.output_tokens

        tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
        if not tool_use_blocks:
            last_error = "No tool_use block in response"
            last_raw = json.dumps([b.model_dump() for b in response.content])
            continue

        tool_input = tool_use_blocks[0].input
        last_raw = json.dumps(tool_input)
        try:
            result = JudgeRawOutput(**tool_input)
            last_error = None
            break
        except ValidationError as exc:
            last_error = str(exc)
            system_prompt = (
                _JUDGE_SYSTEM_PROMPT
                + f"\n\nYour previous tool call had a validation error:\n{last_error}\n\n"
                + "Call the tool again with corrected arguments matching the schema exactly."
            )

    evaluated_at = datetime.now(timezone.utc)
    cost = estimate_cost_usd(total_input_tokens, total_output_tokens)

    if result is not None:
        eval_result = EvaluationResult(item_id=item.item_id, **result.model_dump())
        record = EvaluationRecord(
            item_id=item.item_id,
            run_id=run_id,
            generation_response_hash=item.generation_response_hash,
            judge_model=EXTERNAL_JUDGE_MODEL,
            judge_digest=None,  # closed model: no local weight digest concept
            rubric_version="v0.1",
            evaluation_prompt_hash=evaluation_prompt_hash(),
            validation_attempts=attempts,
            evaluated_at=evaluated_at,
            result=eval_result,
            raw_response=last_raw,
            evaluation_failed=False,
            failure_reason=None,
        )
    else:
        record = EvaluationRecord(
            item_id=item.item_id,
            run_id=run_id,
            generation_response_hash=item.generation_response_hash,
            judge_model=EXTERNAL_JUDGE_MODEL,
            judge_digest=None,
            rubric_version="v0.1",
            evaluation_prompt_hash=evaluation_prompt_hash(),
            validation_attempts=attempts,
            evaluated_at=evaluated_at,
            result=None,
            raw_response=last_raw,
            evaluation_failed=True,
            failure_reason=last_error,
        )

    return ExternalJudgeRecord(
        evaluation_record=record,
        input_tokens=total_input_tokens,
        output_tokens=total_output_tokens,
        estimated_cost_usd=cost,
        actual_model_id=actual_model_id,
        retry_count=attempts - 1,
        input_hash=input_hash,
    )


def _completed_response_hashes(output_path: Path) -> set[str]:
    hashes: set[str] = set()
    if not output_path.exists():
        return hashes
    with output_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if not row.get("evaluation_failed"):
                hashes.add(row["generation_response_hash"])
    return hashes


def run_external_judge(
    *,
    items: list[BlindedItem],
    run_id: str,
    client: "anthropic.Anthropic",
    output_path: Path,
    max_tokens: int = 1024,
    max_repair_retries: int = 2,
    spend_ceiling_usd: float = HARD_SPEND_CEILING_USD,
    progress_callback=None,
) -> list[ExternalJudgeRecord]:
    """Resumable: skips items with an existing successful record. Halts
    (raising RuntimeError) if cumulative estimated spend would exceed
    spend_ceiling_usd, preserving everything written so far."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    done = _completed_response_hashes(output_path)
    new_records: list[ExternalJudgeRecord] = []
    running_cost = 0.0

    # Account for spend already recorded in prior runs of this output file.
    if output_path.exists():
        with output_path.open() as f:
            for line in f:
                line = line.strip()
                if line:
                    running_cost += json.loads(line).get("estimated_cost_usd", 0.0)

    with output_path.open("a") as f:
        for item in items:
            if item.generation_response_hash in done:
                if progress_callback:
                    progress_callback(item, skipped=True)
                continue
            if running_cost >= spend_ceiling_usd:
                raise RuntimeError(
                    f"Spend ceiling reached (${running_cost:.2f} >= ${spend_ceiling_usd:.2f}); "
                    "halting before further API calls. All prior records preserved."
                )
            record = evaluate_one_claude(
                item, run_id=run_id, client=client,
                max_tokens=max_tokens, max_repair_retries=max_repair_retries,
            )
            f.write(json.dumps(record.to_json_dict()) + "\n")
            f.flush()
            new_records.append(record)
            running_cost += record.estimated_cost_usd
            if not record.evaluation_record.evaluation_failed:
                done.add(item.generation_response_hash)
            if progress_callback:
                progress_callback(item, skipped=False, record=record)
    return new_records
