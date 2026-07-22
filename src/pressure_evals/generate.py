"""Resumable generation of model outputs across (scenario, model, condition).

Raw records are append-only JSONL. Before generating a row, we check whether
a successful record for that exact (scenario_id, model, condition) already
exists in the target file, so a killed or partial run can be re-invoked with
the same run_id and only fill in what's missing. Failed calls are still
recorded (success=False, error set) rather than silently dropped, so retrying
is a deliberate re-run, not something generate.py does on its own.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from pressure_evals.ollama_client import chat
from pressure_evals.prompts import render_system_prompt
from pressure_evals.schemas import Condition, GenerationRecord, Scenario

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
SCENARIOS_PATH = DATA_DIR / "scenarios.jsonl"
RAW_OUTPUTS_DIR = DATA_DIR / "raw_outputs"


def load_scenarios(path: Path = SCENARIOS_PATH) -> list[Scenario]:
    scenarios = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                scenarios.append(Scenario(**json.loads(line)))
    return scenarios


def _completed_keys(output_path: Path) -> set[tuple[str, str, str]]:
    """(scenario_id, model, condition) keys with an existing success=True row."""
    keys: set[tuple[str, str, str]] = set()
    if not output_path.exists():
        return keys
    with output_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if row.get("success"):
                keys.add((row["scenario_id"], row["model"], row["condition"]))
    return keys


def new_run_id() -> str:
    return str(uuid.uuid4())


def generate_one(
    scenario: Scenario,
    model: str,
    condition: Condition,
    *,
    run_id: str,
    experiment_version: str,
    temperature: float,
    top_p: float,
    max_tokens: int,
) -> GenerationRecord:
    """Make one model call and package the result, success or failure."""
    system_prompt = render_system_prompt(condition)
    user_prompt = scenario.user_prompt
    started_at = datetime.now(timezone.utc)
    response_text = ""
    thinking_text: str | None = None
    error: str | None = None
    latency = 0.0
    success = False
    try:
        result = chat(
            model=model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
        )
        thinking_text = result.thinking
        latency = result.latency_seconds
        if not result.text.strip():
            # Reasoning models (qwen3) can spend the entire max_tokens budget
            # on hidden chain-of-thought and never reach visible content.
            # That is not a usable output, so it must not be recorded as a
            # success -- otherwise it would silently enter scoring as an
            # empty "message". Marking it a failure makes it retryable by
            # run_generation's resume logic on the next invocation.
            error = "EmptyResponseError: model produced no visible content within max_tokens"
        else:
            response_text = result.text
            success = True
    except Exception as exc:  # noqa: BLE001 - record every failure mode, don't swallow
        error = f"{type(exc).__name__}: {exc}"
    completed_at = datetime.now(timezone.utc)

    return GenerationRecord(
        run_id=run_id,
        experiment_version=experiment_version,
        scenario_id=scenario.scenario_id,
        domain=scenario.domain,
        model=model,
        condition=condition,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        response=response_text,
        thinking=thinking_text,
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
        started_at=started_at,
        completed_at=completed_at,
        latency_seconds=latency,
        success=success,
        error=error,
        response_hash=hashlib.sha256(response_text.encode("utf-8")).hexdigest(),
    )


def run_generation(
    *,
    scenarios: list[Scenario],
    models: list[str],
    conditions: list[Condition],
    run_id: str,
    experiment_version: str,
    temperature: float,
    top_p: float,
    max_tokens: int,
    output_path: Path,
    progress_callback=None,
) -> list[GenerationRecord]:
    """Generate every missing (scenario, model, condition) cell, appending
    each record to output_path as soon as it's produced (crash-safe)."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    done = _completed_keys(output_path)
    new_records: list[GenerationRecord] = []

    with output_path.open("a") as f:
        for scenario in scenarios:
            for model in models:
                for condition in conditions:
                    key = (scenario.scenario_id, model, condition.value)
                    if key in done:
                        if progress_callback:
                            progress_callback(key, skipped=True)
                        continue
                    record = generate_one(
                        scenario,
                        model,
                        condition,
                        run_id=run_id,
                        experiment_version=experiment_version,
                        temperature=temperature,
                        top_p=top_p,
                        max_tokens=max_tokens,
                    )
                    f.write(record.model_dump_json() + "\n")
                    f.flush()
                    new_records.append(record)
                    if record.success:
                        done.add(key)
                    if progress_callback:
                        progress_callback(key, skipped=False, record=record)
    return new_records
