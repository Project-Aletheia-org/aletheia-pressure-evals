"""Immutable run manifests: full provenance for one generation run.

A manifest answers "what exactly produced this data" without having to
reconstruct it from code history: git commit, model digests, config,
content hashes of the scenario/prompt/rubric definitions, and cell counts.
"""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from pressure_evals.ollama_client import model_digests, ollama_version
from pressure_evals.prompts import PROMPT_VERSION
from pressure_evals.schemas import RunManifest

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFESTS_DIR = REPO_ROOT / "data" / "raw_outputs"


def git_commit(cwd: Path = REPO_ROOT) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True, cwd=cwd
    )
    return result.stdout.strip()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative_to_repo(path: Path) -> str:
    """Store paths relative to the repo root so manifests never embed the
    local machine's absolute filesystem path (e.g. a home directory name)."""
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def count_cells(output_path: Path) -> dict:
    """Cell identity is (scenario_id, model, condition, replicate_id).
    `retries` counts attempts beyond the first for a given cell, whether or
    not that cell ultimately succeeded."""
    if not output_path.exists():
        return dict(successful_cells=0, failed_attempts=0, retries=0)
    attempts_per_key: dict[tuple, int] = {}
    successful_keys: set[tuple] = set()
    failed_attempts = 0
    with output_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            key = (row["scenario_id"], row["model"], row["condition"], row.get("replicate_id", 0))
            attempts_per_key[key] = attempts_per_key.get(key, 0) + 1
            if row["success"]:
                successful_keys.add(key)
            else:
                failed_attempts += 1
    retries = sum(c - 1 for c in attempts_per_key.values() if c > 1)
    return dict(
        successful_cells=len(successful_keys),
        failed_attempts=failed_attempts,
        retries=retries,
    )


def build_manifest(
    *,
    run_id: str,
    protocol_version: str,
    scenario_set_version: str,
    rubric_version: str,
    models: list[str],
    generation_config: dict,
    random_seed: int,
    scenarios_path: Path,
    output_path: Path,
    started_at: datetime,
    completed_at: Optional[datetime],
    expected_cells: int,
    status: str,
) -> RunManifest:
    counts = count_cells(output_path)
    return RunManifest(
        run_id=run_id,
        git_commit=git_commit(),
        protocol_version=protocol_version,
        scenario_set_version=scenario_set_version,
        rubric_version=rubric_version,
        prompt_version=PROMPT_VERSION,
        models=models,
        model_digests=model_digests(models),
        ollama_version=ollama_version(),
        machine_architecture=platform.machine(),
        generation_config=generation_config,
        random_seed=random_seed,
        scenario_file_hash=sha256_file(scenarios_path),
        prompt_definition_hash=sha256_file(REPO_ROOT / "src" / "pressure_evals" / "prompts.py"),
        rubric_definition_hash=sha256_file(REPO_ROOT / "src" / "pressure_evals" / "schemas.py"),
        started_at_utc=started_at,
        completed_at_utc=completed_at,
        expected_cells=expected_cells,
        successful_cells=counts["successful_cells"],
        failed_attempts=counts["failed_attempts"],
        retries=counts["retries"],
        output_path=relative_to_repo(output_path),
        status=status,
    )


def manifest_path(run_id: str, manifests_dir: Path = MANIFESTS_DIR) -> Path:
    return manifests_dir / f"{run_id}.manifest.json"


def write_manifest(manifest: RunManifest, manifests_dir: Path = MANIFESTS_DIR) -> Path:
    manifests_dir.mkdir(parents=True, exist_ok=True)
    path = manifest_path(manifest.run_id, manifests_dir)
    path.write_text(manifest.model_dump_json(indent=2) + "\n")
    return path
