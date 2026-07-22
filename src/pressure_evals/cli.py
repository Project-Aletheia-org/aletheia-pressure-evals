"""Typer CLI for the pressure-evals pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from pressure_evals.config import load_yaml_strict
from pressure_evals.generate import (
    RAW_OUTPUTS_DIR,
    load_scenarios,
    new_run_id,
    run_generation,
)
from pressure_evals.ollama_client import (
    OllamaUnavailableError,
    ensure_ready,
    health_check_prompt,
    install_instructions,
    is_ollama_reachable,
    missing_models,
)
from pressure_evals.schemas import Condition

app = typer.Typer(help="aletheia-pressure-evals: goal-pressure/manipulation pilot pipeline")
console = Console()

CONFIG_PATH = Path(__file__).resolve().parents[2] / "configs" / "experiment.yaml"


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

    total_cells = len(scenarios) * len(config["models"]) * len(conditions)
    console.print(
        f"run_id={run_id} scenarios={len(scenarios)} models={len(config['models'])} "
        f"conditions={len(conditions)} -> up to {total_cells} calls "
        f"(existing successes are skipped)"
    )

    def progress(key, skipped, record=None):
        scenario_id, model, condition = key
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
        progress_callback=progress,
    )
    n_success = sum(1 for r in records if r.success)
    n_fail = len(records) - n_success
    console.print(
        f"\nDone. {len(records)} new records written to {output_path} "
        f"({n_success} success, {n_fail} failed)."
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


if __name__ == "__main__":
    app()
