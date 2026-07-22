"""Pre-flight validation of a generation dataset before it is scored.

Used before evaluation begins so a structural problem (missing digests,
wrong cell count, an accidentally-empty "successful" response) is caught
before spending judge calls on a dataset that can't support the analysis.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ValidationReport:
    ok: bool
    total_rows: int
    successful_cells: int
    empty_successful_responses: int
    duplicate_successful_cells: int
    hash_mismatches: list
    missing_model_digest: int
    conditions_present: set
    scenarios_present: set
    problems: list = field(default_factory=list)


def validate_generation_dataset(
    output_path: Path,
    *,
    expected_successful_cells: int,
    expected_conditions: set,
    expected_scenario_ids: set,
) -> ValidationReport:
    rows = []
    with output_path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))

    success = [r for r in rows if r.get("success")]
    keys = [(r["scenario_id"], r["model"], r["condition"]) for r in success]
    dup = len(keys) - len(set(keys))
    empty = [r for r in success if not r["response"].strip()]
    bad_hashes = [
        (r["scenario_id"], r["model"], r["condition"])
        for r in success
        if hashlib.sha256(r["response"].encode("utf-8")).hexdigest() != r["response_hash"]
    ]
    missing_digest = sum(1 for r in success if not r.get("model_digest"))
    conditions_present = {r["condition"] for r in success}
    scenarios_present = {r["scenario_id"] for r in success}

    problems = []
    if len(set(keys)) != expected_successful_cells:
        problems.append(
            f"expected {expected_successful_cells} successful unique cells, found {len(set(keys))}"
        )
    if dup:
        problems.append(f"{dup} duplicate successful cells")
    if empty:
        problems.append(f"{len(empty)} successful rows with empty response")
    if bad_hashes:
        problems.append(f"{len(bad_hashes)} response_hash mismatches")
    if missing_digest:
        problems.append(f"{missing_digest} successful rows missing model_digest")
    if conditions_present != expected_conditions:
        problems.append(
            f"condition mismatch: expected {expected_conditions}, found {conditions_present}"
        )
    if scenarios_present != expected_scenario_ids:
        missing = expected_scenario_ids - scenarios_present
        extra = scenarios_present - expected_scenario_ids
        problems.append(f"scenario mismatch: missing={missing} extra={extra}")

    return ValidationReport(
        ok=not problems,
        total_rows=len(rows),
        successful_cells=len(set(keys)),
        empty_successful_responses=len(empty),
        duplicate_successful_cells=dup,
        hash_mismatches=bad_hashes,
        missing_model_digest=missing_digest,
        conditions_present=conditions_present,
        scenarios_present=scenarios_present,
        problems=problems,
    )
