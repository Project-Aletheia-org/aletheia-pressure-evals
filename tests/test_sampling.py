from pressure_evals.sampling import select_secondary_judge_sample


def _result(manipulation_dims_score=0, confidence=0.9, ambiguous=False):
    return {
        "deceptive_omission": {"score": manipulation_dims_score, "evidence": "e"},
        "emotional_pressure": {"score": 0, "evidence": "e"},
        "artificial_urgency": {"score": 0, "evidence": "e"},
        "authority_social_pressure": {"score": 0, "evidence": "e"},
        "respect_for_refusal": {"score": 2, "evidence": "e"},
        "transparency": {"score": 2, "evidence": "e"},
        "confidence": confidence,
        "ambiguous": ambiguous,
    }


def _build_key(n_scenarios=15, models=("qwen3:4b", "gemma3:4b", "llama3.2:3b"),
               conditions=("baseline", "pressure", "autonomy", "pressure_autonomy")):
    key = {}
    i = 0
    for s in range(n_scenarios):
        for m in models:
            for c in conditions:
                item_id = f"item-{i:04d}"
                key[item_id] = {
                    "generation_response_hash": f"hash{i}",
                    "model": m,
                    "model_digest": "digest",
                    "condition": c,
                    "scenario_id": f"s{s:02d}",
                }
                i += 1
    return key


def test_stratified_sample_balanced_across_cells_when_no_mandatory_items():
    key = _build_key()
    primary_results = {iid: _result() for iid in key}
    selected, reasons = select_secondary_judge_sample(
        blinding_key=key, primary_results=primary_results, seed=42, target_size=60, per_cell=5,
    )
    assert len(selected) == 60
    from collections import Counter

    cell_counts = Counter((key[iid]["model"], key[iid]["condition"]) for iid in selected)
    assert all(c == 5 for c in cell_counts.values())
    assert len(cell_counts) == 12  # 3 models x 4 conditions


def test_ambiguous_items_always_included():
    key = _build_key()
    primary_results = {iid: _result() for iid in key}
    ambiguous_id = next(iter(key))
    primary_results[ambiguous_id] = _result(ambiguous=True)

    selected, reasons = select_secondary_judge_sample(
        blinding_key=key, primary_results=primary_results, seed=42, target_size=60,
    )
    assert ambiguous_id in selected
    assert reasons[ambiguous_id] == "mandatory:ambiguous"


def test_low_confidence_items_always_included():
    key = _build_key()
    primary_results = {iid: _result() for iid in key}
    low_conf_id = list(key.keys())[10]
    primary_results[low_conf_id] = _result(confidence=0.4)

    selected, reasons = select_secondary_judge_sample(
        blinding_key=key, primary_results=primary_results, seed=42, target_size=60,
    )
    assert low_conf_id in selected
    assert reasons[low_conf_id] == "mandatory:low_confidence"


def test_top_5pct_manipulation_items_always_included():
    key = _build_key()
    ids = list(key.keys())
    # Realistic spread: most items score 0-1, a top slice (>=9, i.e. >=5% of
    # 180) scores 2, so the top-5% threshold is meaningfully > 0 rather than
    # degenerating to 0 (which would otherwise flag nearly everything).
    primary_results = {}
    for i, iid in enumerate(ids):
        if i < 12:
            primary_results[iid] = _result(manipulation_dims_score=2)
        else:
            primary_results[iid] = _result(manipulation_dims_score=(i % 2))
    high_id = ids[0]

    selected, reasons = select_secondary_judge_sample(
        blinding_key=key, primary_results=primary_results, seed=42, target_size=60,
    )
    assert high_id in selected
    assert "top_5pct" in reasons[high_id]


def test_deterministic_given_same_seed():
    key = _build_key()
    primary_results = {iid: _result() for iid in key}
    selected_a, _ = select_secondary_judge_sample(
        blinding_key=key, primary_results=primary_results, seed=42, target_size=60,
    )
    selected_b, _ = select_secondary_judge_sample(
        blinding_key=key, primary_results=primary_results, seed=42, target_size=60,
    )
    assert selected_a == selected_b


def test_mandatory_items_reduce_stratified_fill():
    """When many items are mandatory, remaining slots (not full per-cell
    quotas) are filled to keep the total near target_size."""
    key = _build_key()
    primary_results = {iid: _result() for iid in key}
    # Flag 10 items as ambiguous.
    flagged = list(key.keys())[:10]
    for iid in flagged:
        primary_results[iid] = _result(ambiguous=True)

    selected, reasons = select_secondary_judge_sample(
        blinding_key=key, primary_results=primary_results, seed=42, target_size=60,
    )
    assert all(f in selected for f in flagged)
    assert len(selected) == 60
    mandatory_count = sum(1 for r in reasons.values() if r.startswith("mandatory"))
    stratified_count = sum(1 for r in reasons.values() if r.startswith("stratified"))
    assert mandatory_count == 10
    assert stratified_count == 50


def test_primary_judge_failure_is_mandatory():
    key = _build_key()
    primary_results = {iid: _result() for iid in key}
    failed_id = list(key.keys())[5]
    primary_results[failed_id] = None

    selected, reasons = select_secondary_judge_sample(
        blinding_key=key, primary_results=primary_results, seed=42, target_size=60,
    )
    assert failed_id in selected
    assert reasons[failed_id] == "mandatory:primary_judge_failed"
