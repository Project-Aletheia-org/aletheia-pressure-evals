# V2 Pipeline Design: Automated, Config-Driven, Multi-Model Evaluation

Design only — no code written yet. Grounded in concrete gaps V1 hit in practice (cited inline), not a generic wishlist.

## 0. Design goals

1. **Local open-weight models first.** Every stage must run end-to-end on free, locally-hosted models (Ollama) with zero API cost. Cloud judges (Claude, or others later) are an opt-in *additional* judge, never a requirement to run the pipeline.
2. **One command, fully resumable, cost/latency visible before and during the run.**
3. **Never publish automatically.** Generation, judging, analysis, and report-writing are all local-only by construction; publishing (git push, PR, external upload) is a separate command a human runs deliberately, never invoked by the pipeline itself.
4. **Config is the only thing that changes between studies.** No hardcoded model names, judge names, or dimension lists in the pipeline core — V1's `consensus.py` hardcoding `primary = "qwen3:4b"` and `external_judge.py` hardcoding `EXTERNAL_JUDGE_MODEL` is exactly the pattern V2 removes.

## 1. Config schema (`configs/v2_pipeline.yaml`)

```yaml
run_id: null  # auto-generated if omitted; reused to resume
random_seed: 42

subjects:
  - {provider: ollama, name: qwen3:4b}
  - {provider: ollama, name: gemma3:4b}
  - {provider: ollama, name: llama3.2:3b}

judges:
  primary: {provider: ollama, name: qwen3:4b}   # must NOT also be a subject; see §7
  secondary: [{provider: ollama, name: gemma3:4b}, {provider: ollama, name: llama3.2:3b}]
  external: [{provider: anthropic, name: claude-sonnet-4-6, spend_ceiling_usd: 10.0}]

scenarios_path: data/scenarios.jsonl
conditions: [baseline, pressure, autonomy, pressure_autonomy]

generation: {temperature: 0.7, top_p: 0.9, max_tokens: 3072, timeout_s: 60}
evaluation: {temperature: 0, max_tokens: 4096, timeout_s: 60}

execution:
  concurrency: 5
  max_network_retries: 3
  backoff_base_seconds: 2.0
  max_repair_retries: 2

escalation:
  rules: [score_range_gte_2, primary_secondary_manip_diff_gte_3, primary_secondary_auto_diff_gte_2,
          judge_marked_ambiguous, judge_confidence_lt_0_65, deterministic_contradicts_consensus,
          top_5pct_consensus_manipulation]
  known_unreliable_signals:
    # V1 lesson: audit.evidence_is_grounded's quote regex missed straight
    # single quotes, causing ~149/180 false-positive unverifiable_evidence
    # flags against Claude's quoting style. V2 makes any such caveat an
    # explicit, versioned config entry instead of something re-discovered
    # ad hoc mid-analysis.
    - name: unverifiable_evidence
      reason: "quote-detection regex may not match this judge's quoting style; verify before trusting"
      default_excluded_from_escalation_rule: true

adjudication_packet: {n_items: 15, strata: [largest_manipulation: 5, largest_autonomy: 5, moderate: 5]}

analysis: {bootstrap_samples: 5000, confidence_level: 0.95, n_permutations: 10000}

publish: false  # hardcoded false in the pipeline core, not just config -- see §9
```

## 2. Module layout

```
src/pressure_evals/v2/
  discovery.py        # model discovery + compatibility tests (§3)
  providers/
    base.py            # ProviderAdapter protocol: generate(), judge(), model_info()
    ollama_adapter.py   # wraps existing ollama_client.py
    anthropic_adapter.py  # wraps existing external_judge.py call pattern
    # openai_adapter.py, etc. added later behind the same protocol
  pipeline.py          # orchestrates discovery -> generation -> judging -> consensus -> analysis -> reports
  generation.py        # generalizes generate.py across providers
  judging.py           # generalizes evaluate.py + external_judge.py across providers
  consensus_v2.py       # generalizes consensus.py to N configured judges (no hardcoded names)
  analysis_v2.py        # generalizes analyze.py to N models x N judges
  adjudication.py       # generalizes this session's stratified-sampling script into a library function
  reporting.py          # cost/latency/provenance report generation
  manifest_v2.py        # unified per-run manifest (see §6)
cli_v2.py               # `pressure-evals-v2 run --config ...` entry point
```

## 3. Model discovery + compatibility tests

- **Discovery**: enumerate locally-installed Ollama models (`ollama list` equivalent, already in `ollama_client.py`'s `missing_models`/`model_digests`) and separately check which cloud judges have a usable API key present (env var check only, never logging the key — same invariant as V1's `external_judge.py`). Produces a `DiscoveryReport`: per configured model, `available: bool`, `digest_or_version`, `reachable_latency_ms` (one health-check call).
- **Compatibility tests**: for every model that discovery reports available, run one smoke cell (1 scenario, 1 condition for subjects; 1 calibration example for judges) verifying: non-empty response, structured-output/JSON-schema compliance for judges, latency under `timeout_s`. This generalizes the existing `run-pilot` / `_run_calibration_check` commands, but runs automatically as a gate before the real run rather than being a separately-invoked command a human might forget.
- **Fail-fast, not silent-skip**: if a *configured* model is unavailable or fails its compatibility test, the pipeline halts with a clear report rather than silently proceeding with a subset — matching the existing `ensure_ready`/`OllamaUnavailableError` pattern in `cli.py`, generalized to all providers.

## 4. Generation and blinded judging

- Generation: same immutable-record-per-call, resumable-by-hash design as `generate.py`, parameterized over the `subjects` list instead of `config["models"]`.
- Judging: **every judge — primary, secondary, or external — implements the exact same blinding contract** already proven in `evaluate.py`/`external_judge.py`: item_id-only, scenario_context + visible_response only, fixed-seed shuffle, no subject/condition/hypothesis/other-judge-score ever in the prompt. This is enforced by a single shared `build_blinded_items()` + `_build_judge_user_prompt()` used by every provider adapter, not reimplemented per-provider (V1 had two near-identical implementations in `evaluate.py` and `external_judge.py` — V2 collapses them to one, with a provider-specific `call()` underneath).
- **Latency tracking, added in V2**: V1's `ExternalJudgeRecord` had no per-call latency field, which meant a mid-run status check in this session couldn't report average/max judge latency at all. V2's judging record includes `latency_seconds` for every call (generation records already had this; judge records now do too), enabling real cost *and* latency reporting mid-run.

## 5. Retry and repair handling

Formalizes the two-tier pattern this session built for the Claude judge and generalizes it to every provider:
1. **Schema-repair retries** (inner): malformed structured output triggers a repair prompt (rubric + validation error, no subject metadata), up to `max_repair_retries`, within one logical evaluation call.
2. **Network/API retries** (outer): connection/timeout/rate-limit errors retry the *whole* logical call with exponential backoff, up to `max_network_retries`, strictly separated from (1) — carried over unchanged from `external_judge.py`'s `evaluate_one_claude_with_retry`, generalized to local providers too (Ollama can also time out or drop connections).
3. Every attempt, successful or not, is preserved in the raw record; only successful evaluations count toward "done" for resumability.

## 6. Provenance manifests

One unified per-run manifest superseding the current split (`RunManifest` for generation, `EvaluationManifest` per judge file):

```json
{
  "run_id": "...", "config_hash": "sha256 of the exact YAML used",
  "git_commit": "...", "started_at_utc": "...", "completed_at_utc": "...",
  "subjects": {"qwen3:4b": {"digest": "...", "cells": {"expected": 60, "successful": 60, "failed": 0}}},
  "judges": {"qwen3:4b": {...}, "claude-sonnet-4-6": {...}},
  "provider_versions": {"anthropic-sdk": "0.118.0", "ollama": "0.24.0"},
  "cost": {"claude-sonnet-4-6": {"input_tokens": ..., "output_tokens": ..., "usd": ...}},
  "latency": {"claude-sonnet-4-6": {"mean_s": ..., "max_s": ..., "p95_s": ...}},
  "status": "completed | completed_with_failures | aborted"
}
```

This is written incrementally (not just at start/end) so a status check mid-run — exactly the kind of check requested earlier in this session — can always read accurate, current cost/latency/completion numbers directly from one file instead of reconstructing them ad hoc from raw JSONL.

## 7. Statistical analysis (generalized)

- `analysis_v2.py` loops over the **configured judge list** (not hardcoded "qwen"/"claude"), producing the A/B/.../N single-judge analyses automatically, plus all-pairs agreement (C-style), consensus (D-style, median across however many judges are configured, not just mean-of-2), and disagreement-exclusion sensitivity (E-style) — exactly the structure built ad hoc in this session's `full_analysis.py`, but as a library function parameterized by judge count instead of a one-off script.
- **Judge/subject conflation check, built in, not manual.** V1's central finding — that `qwen3:4b` being both a subject and the primary judge explains most of the evaluator-sensitivity — was discovered by hand this session. V2's config schema requires declaring `judges.primary` explicitly and **warns (configurable to hard-fail) if any judge model name also appears in `subjects`**, surfacing this confound at config-validation time instead of after a full run and manual investigation.
- Same scenario-blocked bootstrap / paired permutation primitives from `analyze.py`, unchanged (they're already provider- and judge-count-agnostic).

## 8. Disagreement escalation and blinded human-review packet generation

- `consensus_v2.py`: same escalation-reason machinery as `consensus.py`, but reasons and thresholds come from `escalation.rules` in config, and any heuristic with known reliability caveats (like the evidence-groundedness quote-regex gap) is declared in `escalation.known_unreliable_signals` and excluded from the default disagreement rule automatically, with the reason logged in the run manifest — rather than requiring a human to notice a 149/180 flag rate and manually diagnose it mid-analysis, as happened in V1.
- `adjudication.py`: generalizes this session's stratified-sampling script (`build_adjudication_packet.py`) into a reusable function: configurable strata, greedy scenario-diversification, fixed-seed shuffle, fresh anonymous review IDs decoupled from internal item IDs, separate unblinding-key file never displayed by default. Exposed as `pressure-evals-v2 adjudication-packet --n 15`.
- **Human-rating completion is tracked, not assumed.** V1 hit a real failure mode this session: a packet was generated, opened, and the user believed they'd completed it, but no scores were ever saved to disk. V2's packet format includes a required non-blank sentinel per row (e.g., a `SCORED: yes` field) and the pipeline's "validate ratings" step checks file mtime + sentinel completion + no-blank-fields before treating any comparison as real, refusing to proceed (with a clear diagnostic) if the file is unchanged since generation.

## 9. Cost, latency, and one-command execution

- `pressure-evals-v2 run --config configs/v2_pipeline.yaml` runs: discovery -> compatibility -> generation -> judging (primary, secondary, external, in that order, each resumable) -> consensus/escalation -> analysis -> report writing, printing a running cost/latency ticker and hard-stopping at any configured spend ceiling (same projected-vs-actual hard-stop logic as this session's `run_external_judge_concurrent`).
- Every stage is independently resumable by `run_id`, so the one-command entry point can be interrupted and re-run without redoing completed work — this is not new (already true of every V1 stage) but V2 makes it true of the *orchestration* as a whole, not just each stage in isolation.
- **No automatic publication, enforced structurally, not just by convention.** The pipeline package contains no code path that invokes `git push`, `gh`, or any network-upload call — publishing is a categorically separate script/skill a human invokes deliberately, so there's no config flag to accidentally set that would make the pipeline publish anything.

## 10. What V2 deliberately does not change

- The rubric, six dimensions, manipulation/autonomy composite definitions, and blinding contract are unchanged from V1 — V2 is an execution/orchestration generalization, not a rubric redesign.
- V2 does not retroactively fix V1's data; it's designed so the *next* study doesn't require the same ad hoc scratchpad scripting this session used to stitch a two-judge comparison together after the fact.
