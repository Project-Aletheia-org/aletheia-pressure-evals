import hashlib
import json
from pathlib import Path

from pressure_evals.validate import validate_generation_dataset


def _row(scenario_id, model, condition, response="msg", success=True, hash_override=None):
    h = hash_override or hashlib.sha256(response.encode()).hexdigest()
    return {
        "scenario_id": scenario_id,
        "model": model,
        "condition": condition,
        "response": response,
        "response_hash": h,
        "model_digest": "digest-1",
        "success": success,
    }


def test_valid_dataset_passes(tmp_path: Path):
    f = tmp_path / "gen.jsonl"
    rows = [_row("s01", "qwen3:4b", "baseline"), _row("s01", "qwen3:4b", "pressure")]
    f.write_text("\n".join(json.dumps(r) for r in rows) + "\n")

    report = validate_generation_dataset(
        f, expected_successful_cells=2, expected_conditions={"baseline", "pressure"},
        expected_scenario_ids={"s01"},
    )
    assert report.ok
    assert report.problems == []


def test_detects_duplicate_successful_cells(tmp_path: Path):
    f = tmp_path / "gen.jsonl"
    rows = [_row("s01", "qwen3:4b", "baseline"), _row("s01", "qwen3:4b", "baseline")]
    f.write_text("\n".join(json.dumps(r) for r in rows) + "\n")

    report = validate_generation_dataset(
        f, expected_successful_cells=1, expected_conditions={"baseline"},
        expected_scenario_ids={"s01"},
    )
    assert not report.ok
    assert report.duplicate_successful_cells == 1
    assert any("duplicate" in p for p in report.problems)


def test_detects_empty_response(tmp_path: Path):
    f = tmp_path / "gen.jsonl"
    rows = [_row("s01", "qwen3:4b", "baseline", response="")]
    f.write_text("\n".join(json.dumps(r) for r in rows) + "\n")

    report = validate_generation_dataset(
        f, expected_successful_cells=1, expected_conditions={"baseline"},
        expected_scenario_ids={"s01"},
    )
    assert not report.ok
    assert report.empty_successful_responses == 1


def test_detects_hash_mismatch(tmp_path: Path):
    f = tmp_path / "gen.jsonl"
    rows = [_row("s01", "qwen3:4b", "baseline", hash_override="wronghash")]
    f.write_text("\n".join(json.dumps(r) for r in rows) + "\n")

    report = validate_generation_dataset(
        f, expected_successful_cells=1, expected_conditions={"baseline"},
        expected_scenario_ids={"s01"},
    )
    assert not report.ok
    assert len(report.hash_mismatches) == 1


def test_detects_missing_model_digest(tmp_path: Path):
    f = tmp_path / "gen.jsonl"
    row = _row("s01", "qwen3:4b", "baseline")
    row["model_digest"] = None
    f.write_text(json.dumps(row) + "\n")

    report = validate_generation_dataset(
        f, expected_successful_cells=1, expected_conditions={"baseline"},
        expected_scenario_ids={"s01"},
    )
    assert not report.ok
    assert report.missing_model_digest == 1
