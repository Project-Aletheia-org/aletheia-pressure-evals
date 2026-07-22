import json
from datetime import datetime, timezone
from pathlib import Path

from pressure_evals import manifest as manifest_mod
from pressure_evals.manifest import build_manifest, count_cells, sha256_file


def test_sha256_file_deterministic(tmp_path: Path):
    f = tmp_path / "a.txt"
    f.write_text("hello")
    assert sha256_file(f) == sha256_file(f)
    assert len(sha256_file(f)) == 64


def test_sha256_file_changes_with_content(tmp_path: Path):
    f = tmp_path / "a.txt"
    f.write_text("hello")
    h1 = sha256_file(f)
    f.write_text("hello world")
    h2 = sha256_file(f)
    assert h1 != h2


def _row(scenario_id, model, condition, success, replicate_id=0):
    return {
        "scenario_id": scenario_id,
        "model": model,
        "condition": condition,
        "replicate_id": replicate_id,
        "success": success,
    }


def test_count_cells_no_file(tmp_path: Path):
    counts = count_cells(tmp_path / "missing.jsonl")
    assert counts == {"successful_cells": 0, "failed_attempts": 0, "retries": 0}


def test_count_cells_counts_unique_successes_and_retries(tmp_path: Path):
    f = tmp_path / "run.jsonl"
    rows = [
        _row("s01", "qwen3:4b", "baseline", False),
        _row("s01", "qwen3:4b", "baseline", True),  # retry that succeeded
        _row("s01", "qwen3:4b", "pressure", True),  # succeeded first try
        _row("s02", "gemma3:4b", "baseline", False),  # never succeeded
    ]
    f.write_text("\n".join(json.dumps(r) for r in rows) + "\n")

    counts = count_cells(f)
    assert counts["successful_cells"] == 2  # s01/baseline, s01/pressure
    assert counts["failed_attempts"] == 2  # the two success=False rows
    assert counts["retries"] == 1  # one extra attempt on the s01/baseline cell


def test_count_cells_rejects_no_duplicate_successes(tmp_path: Path):
    """Two successful rows for the same cell would indicate a duplicate-cell
    bug; successful_cells must count unique keys, not raw rows."""
    f = tmp_path / "run.jsonl"
    rows = [
        _row("s01", "qwen3:4b", "baseline", True),
        _row("s01", "qwen3:4b", "baseline", True),  # would be a duplicate
    ]
    f.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    counts = count_cells(f)
    assert counts["successful_cells"] == 1


def test_build_manifest_uses_mocked_provenance(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(manifest_mod, "git_commit", lambda: "deadbeef")
    monkeypatch.setattr(manifest_mod, "model_digests", lambda models: {m: f"digest-{m}" for m in models})
    monkeypatch.setattr(manifest_mod, "ollama_version", lambda: "ollama version is 0.24.0")

    scenarios_path = tmp_path / "scenarios.jsonl"
    scenarios_path.write_text('{"a": 1}\n')
    output_path = tmp_path / "run.jsonl"
    output_path.write_text(json.dumps(_row("s01", "qwen3:4b", "baseline", True)) + "\n")

    m = build_manifest(
        run_id="test-run",
        protocol_version="v0.1",
        scenario_set_version="v0.1",
        rubric_version="v0.1",
        models=["qwen3:4b"],
        generation_config={"temperature": 0.7},
        random_seed=42,
        scenarios_path=scenarios_path,
        output_path=output_path,
        started_at=datetime.now(timezone.utc),
        completed_at=None,
        expected_cells=180,
        status="running",
    )
    assert m.git_commit == "deadbeef"
    assert m.model_digests == {"qwen3:4b": "digest-qwen3:4b"}
    assert m.successful_cells == 1
    assert m.status == "running"
    assert len(m.scenario_file_hash) == 64


def test_build_manifest_output_path_is_repo_relative(monkeypatch):
    """Manifests must never embed the local machine's absolute filesystem
    path (e.g. a home directory username)."""
    monkeypatch.setattr(manifest_mod, "git_commit", lambda: "deadbeef")
    monkeypatch.setattr(manifest_mod, "model_digests", lambda models: {m: "d" for m in models})
    monkeypatch.setattr(manifest_mod, "ollama_version", lambda: "0.24.0")

    output_path = manifest_mod.REPO_ROOT / "data" / "raw_outputs" / "abs_test.jsonl"
    m = build_manifest(
        run_id="abs-test",
        protocol_version="v0.1",
        scenario_set_version="v0.1",
        rubric_version="v0.1",
        models=["qwen3:4b"],
        generation_config={},
        random_seed=42,
        scenarios_path=manifest_mod.REPO_ROOT / "data" / "scenarios.jsonl",
        output_path=output_path,
        started_at=datetime.now(timezone.utc),
        completed_at=None,
        expected_cells=1,
        status="running",
    )
    assert not m.output_path.startswith("/")
    assert "raw_outputs" in m.output_path
