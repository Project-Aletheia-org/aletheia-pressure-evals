"""Typer CLI for the pressure-evals pipeline."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from pressure_evals.config import load_yaml_strict
from pressure_evals.generate import (
    RAW_OUTPUTS_DIR,
    SCENARIOS_PATH,
    load_scenarios,
    new_run_id,
    run_generation,
)
from pressure_evals.manifest import build_manifest, count_cells, write_manifest
from pressure_evals.ollama_client import (
    OllamaUnavailableError,
    ensure_ready,
    health_check_prompt,
    install_instructions,
    is_ollama_reachable,
    missing_models,
    model_digests as fetch_model_digests,
    model_info,
)
from pressure_evals.schemas import CalibrationExample, Condition
from pressure_evals.validate import validate_generation_dataset

app = typer.Typer(help="aletheia-pressure-evals: goal-pressure/manipulation pilot pipeline")
console = Console()

CONFIG_PATH = Path(__file__).resolve().parents[2] / "configs" / "experiment.yaml"

# Versioned research objects (see reports/study_protocol.md Section 2 and 12).
PROTOCOL_VERSION = "v0.1"
SCENARIO_SET_VERSION = "v0.1"
RUBRIC_VERSION = "v0.1"


def _load_config() -> dict:
    return load_yaml_strict(CONFIG_PATH)


@app.command()
def check() -> None:
    """Verify Ollama is reachable and all required models are installed."""
    config = _load_config()
    required = list(config["models"]) + [config["evaluation"]["judge_model"]]
    required = sorted(set(required))

    if not is_ollama_reachable():
        console.print("[red]Ollama is not reachable at localhost:11434.[/red]")
        console.print("Start the Ollama app, or run `ollama serve`, then retry.")
        raise typer.Exit(code=1)
    console.print("[green]Ollama is reachable.[/green]")

    missing = missing_models(required)
    table = Table(title="Required models")
    table.add_column("model")
    table.add_column("status")
    for m in required:
        table.add_row(m, "[red]missing[/red]" if m in missing else "[green]installed[/green]")
    console.print(table)

    if missing:
        console.print("\n[yellow]Install missing models with:[/yellow]")
        console.print(install_instructions(missing))
        raise typer.Exit(code=1)

    console.print("\nRunning health-check prompt on first subject model...")
    probe_model = config["models"][0]
    try:
        result = health_check_prompt(probe_model)
    except Exception as exc:  # noqa: BLE001 - surface any ollama error clearly
        console.print(f"[red]Health-check call to {probe_model} failed: {exc}[/red]")
        raise typer.Exit(code=1)
    console.print(f"[green]{probe_model} responded ({result.latency_seconds:.2f}s):[/green]")
    console.print(result.text.strip())


def _run_generation_job(
    *,
    run_id: str,
    limit_scenarios: Optional[int],
    output_path: Path,
) -> None:
    config = _load_config()
    required = sorted(set(config["models"]) | {config["evaluation"]["judge_model"]})
    try:
        ensure_ready(required)
    except OllamaUnavailableError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1)

    scenarios = load_scenarios()
    if limit_scenarios is not None:
        scenarios = scenarios[:limit_scenarios]
    conditions = [Condition(c) for c in config["conditions"]]
    digests = fetch_model_digests(config["models"])

    total_cells = len(scenarios) * len(config["models"]) * len(conditions)
    console.print(
        f"run_id={run_id} scenarios={len(scenarios)} models={len(config['models'])} "
        f"conditions={len(conditions)} -> up to {total_cells} calls "
        f"(existing successes are skipped)"
    )

    started_at = datetime.now(timezone.utc)
    manifest = build_manifest(
        run_id=run_id,
        protocol_version=PROTOCOL_VERSION,
        scenario_set_version=SCENARIO_SET_VERSION,
        rubric_version=RUBRIC_VERSION,
        models=config["models"],
        generation_config=config["generation"],
        random_seed=config["random_seed"],
        scenarios_path=SCENARIOS_PATH,
        output_path=output_path,
        started_at=started_at,
        completed_at=None,
        expected_cells=total_cells,
        status="running",
    )
    write_manifest(manifest)

    def progress(key, skipped, record=None):
        scenario_id, model, condition, replicate_id = key
        if skipped:
            console.print(f"  [dim]skip  {scenario_id} / {model} / {condition}[/dim]")
        elif record.success:
            console.print(
                f"  [green]ok[/green]    {scenario_id} / {model} / {condition} "
                f"({record.latency_seconds:.1f}s)"
            )
        else:
            console.print(
                f"  [red]fail[/red]  {scenario_id} / {model} / {condition}: {record.error}"
            )

    records = run_generation(
        scenarios=scenarios,
        models=config["models"],
        conditions=conditions,
        run_id=run_id,
        experiment_version=config["experiment_version"],
        temperature=config["generation"]["temperature"],
        top_p=config["generation"]["top_p"],
        max_tokens=config["generation"]["max_tokens"],
        output_path=output_path,
        model_digests=digests,
        progress_callback=progress,
    )
    n_success = sum(1 for r in records if r.success)
    n_fail = len(records) - n_success
    console.print(
        f"\nDone. {len(records)} new records written to {output_path} "
        f"({n_success} success, {n_fail} failed)."
    )

    completed_at = datetime.now(timezone.utc)
    final_manifest = build_manifest(
        run_id=run_id,
        protocol_version=PROTOCOL_VERSION,
        scenario_set_version=SCENARIO_SET_VERSION,
        rubric_version=RUBRIC_VERSION,
        models=config["models"],
        generation_config=config["generation"],
        random_seed=config["random_seed"],
        scenarios_path=SCENARIOS_PATH,
        output_path=output_path,
        started_at=started_at,
        completed_at=completed_at,
        expected_cells=total_cells,
        status="completed" if final_successful_cells_complete(output_path, total_cells) else "completed_with_failures",
    )
    write_manifest(final_manifest)
    console.print(f"Manifest written: {manifest_summary(final_manifest)}")


def final_successful_cells_complete(output_path: Path, expected_cells: int) -> bool:
    return count_cells(output_path)["successful_cells"] >= expected_cells


def manifest_summary(m) -> str:
    return (
        f"{m.successful_cells}/{m.expected_cells} successful cells, "
        f"{m.failed_attempts} failed attempts, {m.retries} retries, status={m.status}"
    )


@app.command()
def generate(
    run_id: Optional[str] = typer.Option(None, help="Reuse to resume a previous run."),
    limit_scenarios: Optional[int] = typer.Option(
        None, help="Only use the first N scenarios (for smoke tests)."
    ),
) -> None:
    """Generate model outputs for every (scenario, model, condition) cell."""
    run_id = run_id or new_run_id()
    output_path = RAW_OUTPUTS_DIR / f"{run_id}.jsonl"
    _run_generation_job(run_id=run_id, limit_scenarios=limit_scenarios, output_path=output_path)


@app.command(name="run-pilot")
def run_pilot() -> None:
    """Two-scenario smoke test across all models and conditions (fixed run_id)."""
    output_path = RAW_OUTPUTS_DIR / "smoke.jsonl"
    _run_generation_job(run_id="smoke", limit_scenarios=2, output_path=output_path)


def _run_calibration_check(judge_model: str, temperature: float, max_tokens: int) -> None:
    from pressure_evals.evaluate import _JUDGE_SYSTEM_PROMPT
    from pressure_evals.ollama_client import chat as ollama_chat

    calib_path = Path(__file__).resolve().parents[2] / "data" / "calibration_examples.jsonl"
    examples = []
    with calib_path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                examples.append(CalibrationExample(**json.loads(line)))

    table = Table(title="Calibration check (Measurement Calibration Set v0.1)")
    table.add_column("id")
    table.add_column("category")
    table.add_column("dimension")
    table.add_column("expected")
    table.add_column("observed")
    table.add_column("in range?")

    outside_range = 0
    for ex in examples:
        prompt = f"Request context:\n(calibration example, no scenario)\n\nAssistant's message to the user:\n{ex.message}"
        try:
            resp = ollama_chat(
                model=judge_model,
                system_prompt=_JUDGE_SYSTEM_PROMPT,
                user_prompt=prompt,
                temperature=temperature,
                top_p=1.0,
                max_tokens=max_tokens,
            )
            observed = json.loads(resp.text)
        except Exception as exc:  # noqa: BLE001
            console.print(f"[red]calibration call failed for {ex.example_id}: {exc}[/red]")
            continue
        for dim, (lo, hi) in ex.expected_scores.items():
            obs_score = observed.get(dim, {}).get("score") if isinstance(observed.get(dim), dict) else None
            in_range = obs_score is not None and lo <= obs_score <= hi
            if not in_range:
                outside_range += 1
            table.add_row(
                ex.example_id, ex.category, dim, f"[{lo},{hi}]", str(obs_score),
                "[green]yes[/green]" if in_range else "[red]NO[/red]",
            )
    console.print(table)
    console.print(
        f"\n{outside_range} (example, dimension) pairs outside the expected range. "
        "This is a sanity check on the judge, not a rubric-tuning gate."
    )


@app.command()
def evaluate(
    run_id: str = typer.Option(..., help="Generation run_id to evaluate, e.g. baseline-v0.1-20260722"),
    skip_calibration: bool = typer.Option(False, help="Skip the calibration check step."),
) -> None:
    """Blinded judge evaluation of a completed generation run."""
    from pressure_evals.evaluate import (
        EVALUATIONS_DIR,
        build_blinded_items,
        build_evaluation_manifest,
        load_successful_generations,
        run_evaluation,
        write_blinding_key,
        write_evaluation_manifest,
    )

    config = _load_config()
    judge_model = config["evaluation"]["judge_model"]
    try:
        ensure_ready([judge_model])
    except OllamaUnavailableError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1)

    generation_path = RAW_OUTPUTS_DIR / f"{run_id}.jsonl"
    if not generation_path.exists():
        console.print(f"[red]No generation dataset at {generation_path}[/red]")
        raise typer.Exit(code=1)

    scenarios = load_scenarios()
    expected_scenario_ids = {s.scenario_id for s in scenarios}
    expected_conditions = {c for c in config["conditions"]}
    expected_cells = len(scenarios) * len(config["models"]) * len(expected_conditions)

    console.print("Step 1: pre-evaluation validation")
    report = validate_generation_dataset(
        generation_path,
        expected_successful_cells=expected_cells,
        expected_conditions=expected_conditions,
        expected_scenario_ids=expected_scenario_ids,
    )
    if not report.ok:
        console.print("[red]Pre-evaluation validation FAILED:[/red]")
        for p in report.problems:
            console.print(f"  - {p}")
        raise typer.Exit(code=1)
    console.print(
        f"[green]OK[/green]: {report.successful_cells} successful unique cells, "
        f"0 empty, 0 duplicates, 0 hash mismatches, all digests present."
    )

    if not skip_calibration:
        console.print("\nStep 7: calibration check")
        _run_calibration_check(
            judge_model, config["evaluation"]["temperature"], config["evaluation"]["max_tokens"]
        )

    console.print("\nStep 2-6: blinding + structured evaluation")
    scenarios_by_id = {s.scenario_id: s for s in scenarios}
    generation_records = load_successful_generations(generation_path)
    items, key = build_blinded_items(generation_records, scenarios_by_id, seed=config["random_seed"])

    key_path = EVALUATIONS_DIR / f"{run_id}.blinding_key.json"
    write_blinding_key(key, key_path)
    console.print(f"Blinded {len(items)} items (seed={config['random_seed']}); key -> {key_path}")

    judge_digest = model_info(judge_model).digest
    output_path = EVALUATIONS_DIR / f"{run_id}.jsonl"

    started_at = datetime.now(timezone.utc)
    manifest = build_evaluation_manifest(
        evaluation_run_id=run_id,
        generation_run_id=run_id,
        generation_dataset_path=generation_path,
        judge_model=judge_model,
        judge_digest=judge_digest,
        random_seed=config["random_seed"],
        output_path=output_path,
        started_at=started_at,
        completed_at=None,
        expected_evaluations=len(items),
        status="running",
    )
    write_evaluation_manifest(manifest, EVALUATIONS_DIR)

    def progress(item, skipped, record=None):
        if skipped:
            console.print(f"  [dim]skip  {item.item_id}[/dim]")
        elif not record.evaluation_failed:
            console.print(f"  [green]ok[/green]    {item.item_id} (attempts={record.validation_attempts})")
        else:
            console.print(f"  [red]fail[/red]  {item.item_id}: {record.failure_reason}")

    records = run_evaluation(
        items=items,
        run_id=run_id,
        judge_model=judge_model,
        judge_digest=judge_digest,
        temperature=config["evaluation"]["temperature"],
        max_tokens=config["evaluation"]["max_tokens"],
        max_repair_retries=config["evaluation"]["max_repair_retries"],
        output_path=output_path,
        progress_callback=progress,
    )
    n_success = sum(1 for r in records if not r.evaluation_failed)
    n_fail = len(records) - n_success
    console.print(f"\nDone. {len(records)} new evaluations ({n_success} success, {n_fail} failed).")

    completed_at = datetime.now(timezone.utc)
    final_manifest = build_evaluation_manifest(
        evaluation_run_id=run_id,
        generation_run_id=run_id,
        generation_dataset_path=generation_path,
        judge_model=judge_model,
        judge_digest=judge_digest,
        random_seed=config["random_seed"],
        output_path=output_path,
        started_at=started_at,
        completed_at=completed_at,
        expected_evaluations=len(items),
        status="completed" if final_manifest_complete(output_path, len(items)) else "completed_with_failures",
    )
    write_evaluation_manifest(final_manifest, EVALUATIONS_DIR)
    console.print(
        f"Manifest: {final_manifest.successful_evaluations}/{final_manifest.expected_evaluations} "
        f"successful, {final_manifest.failed_evaluations} failed, "
        f"{final_manifest.repair_attempts} repair attempts, status={final_manifest.status}"
    )


def final_manifest_complete(output_path: Path, expected: int) -> bool:
    if not output_path.exists():
        return False
    successful = set()
    with output_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if not row.get("evaluation_failed"):
                successful.add(row["generation_response_hash"])
    return len(successful) >= expected


if __name__ == "__main__":
    app()
