# Research Log

Chronological record of what was done, why, and what happened. Times are
approximate UTC/local as recorded in commit history and run manifests;
exact timestamps for generation/evaluation runs are in the corresponding
`.manifest.json` files, which are authoritative.

## 2026-07-22: Repository scaffold and Day 1 pipeline

- Scaffolded `aletheia-pressure-evals` (pyproject, configs, schemas,
  generation pipeline, CLI) and pulled `qwen3:4b`, `gemma3:4b`,
  `llama3.2:3b` via Ollama.
- Wrote 15 scenarios (scenario-set v0.1) and the four condition system
  prompts (baseline/pressure/autonomy/pressure_autonomy).
- Ran a 24-output technical smoke test (2 scenarios x 3 models x 4
  conditions). Found and fixed two real bugs:
  1. `think=True` was sent unconditionally to all models; gemma3/llama3.2
     don't support Ollama's thinking parameter and errored out on every
     call. Fixed by only enabling `think` for qwen3-family models.
  2. qwen3 can spend its entire `max_tokens` budget on hidden
     chain-of-thought and return empty visible content; this was being
     recorded as a false success. Fixed by treating an empty response as a
     retryable failure, and raised `generation.max_tokens` 1024 -> 3072.
- Repository was moved between locations twice during setup (a nested
  `research/pressure-evals/` under project-aletheia was tried and reverted;
  settled on a standalone repo `Project-Aletheia-org/aletheia-pressure-evals`).

## 2026-07-22: Preregistration -> living study protocol

- Initial `reports/preregistration.md` used "FROZEN" framing and described
  the work as a one-time pilot. Replaced with `reports/study_protocol.md`,
  a versioned living protocol (protocol v0.1), reflecting that this is an
  ongoing research program, not a single experiment. See
  `study_protocol.md`'s own changelog for version history.
- Added `reports/experiment_registry.csv` to track every run's version
  metadata immutably.

## 2026-07-22: Measurement-validity layer (before main generation)

- Added, before Initial Baseline Study v0.1 generation began: Control Set
  v0.1 (2 no-stakes scenarios), Measurement Calibration Set v0.1 (12
  hand-authored examples), three secondary evaluation dimensions
  (scenario_realism, evaluation_validity, evaluation_awareness, never in
  the composites), the `high_manipulation` secondary threshold, and
  structured scenario metadata (privacy_stakes, financial_stakes, etc.),
  backfilled onto the 15 scenarios without altering their `user_prompt`
  text (verified by test).
- Added run manifests (`RunManifest` schema) and experimental-cell identity
  `(scenario_id, model_digest, condition, prompt_version, replicate_id)`.

## 2026-07-22: Initial Baseline Study v0.1 generation

- Launched `uv run pressure-evals generate --run-id baseline-v0.1-20260722`.
- 180/180 successful, 0 failed attempts, 0 retries, 0 empty responses, 0
  duplicate cells. Runtime 63.4 minutes. See
  `data/raw_outputs/baseline-v0.1-20260722.manifest.json`.

## 2026-07-22: Evaluation pipeline and primary judge (qwen3:4b)

- Built the blinded structured evaluation pipeline (`evaluate.py`): the
  judge never sees subject model identity, condition, or hypotheses; item
  order is shuffled with a fixed seed; malformed JSON gets up to 3
  repair-prompt retries.
- Live-tested the calibration-check helper and found it was missing
  `format=schema` (unlike the main evaluation call path), causing 7/12
  calibration examples to fail with empty responses that a properly
  schema-constrained call would not have produced. Fixed.
- Found the same token-exhaustion pattern from generation recurring in
  evaluation: `evaluation.max_tokens: 2048` produced 2 permanent failures
  (empty response after all repair attempts) in the first 4 items scored.
  Raised to 4096.
- Ran the full 180-item primary evaluation. One item, `item-0049`,
  permanently failed even at 4096 tokens (empty response, all 4 attempts,
  ~200s+ each). Diagnosed as token-exhaustion, not a timeout, not
  malformed-but-parseable JSON, not an Ollama error.
- Rescued `item-0049` with a one-off script (not a global config change):
  identical blinded content, judge, digest, rubric, prompt hash, and
  temperature; only `max_tokens` raised to 8192 for that single item.
  Succeeded on the first attempt (200.6s). All 4 historical failed rows
  (2 for item-0001/item-0003 pre-fix, 2 for item-0049) preserved, never
  overwritten.
- Final state: 180/180 unique successful primary evaluations.

## 2026-07-22: Human-validation plan replaced

- Replaced the originally-planned fixed 60-row manual human-annotation
  sample, and the smaller 30-item secondary-judge audit plan, with a
  scalable automated multi-judge validation + selective-escalation
  framework (see `study_protocol.md` Section 9/16 and its changelog). This
  change was made before any human annotation began.
- Built `sampling.py` (stratified + flagged-item sample selection),
  `audit.py` (deterministic, code-only text audit), and `consensus.py`
  (per-item consensus, escalation flags, dimension- and composite-level
  agreement statistics).

## 2026-07-22: Stratified 60-item secondary-judge sample

- Selected via `select_secondary_judge_sample` (seed 42): 14 items
  mandatory (all from the top-5%-consensus-manipulation criterion; 0
  ambiguous, 0 low-confidence primary-judge items), 46 stratified
  (5 per model x condition cell, adjusted for the mandatory items already
  claiming some cells' slots).
- Scored the sample with `gemma3:4b`: 60/60 successful, 0 failures,
  ~15-20s/item (no reasoning overhead). One data-quality finding: item-0058
  has empty evidence fields on 2 dimensions from gemma3 (schema-valid but
  not meaningfully grounded) -- flagged for escalation, not discarded.
- Found and fixed an evidence-groundedness heuristic bug during a dry run:
  `evidence_is_grounded` originally checked only the evidence's first 6
  words against the response, causing systematic false positives whenever
  a judge paraphrased ("Message explicitly states...") rather than quoting
  verbatim. Rewrote to check content-word overlap across the whole
  evidence string (excluding judge-commentary words), and to only apply
  groundedness checking to positive claims (score > 0), since a score=0
  justification ("no guilt, fear, or shame present") is describing an
  absence and has no reason to textually overlap with the response.
- Scored the same sample with `llama3.2:3b` (in progress as of this log
  entry; see `computational_costs.md` for timing once complete).

## 2026-07-22: Agreement-metric infrastructure

- Extended `consensus.py` with majority agreement rate, mean absolute
  disagreement, pairwise Spearman correlation (dimension-level), and
  composite (manipulation/autonomy) pairwise Pearson/Spearman/MAE/
  percent-within-1/percent-within-2 statistics.
- Added `to_json_safe`: NaN/Infinity are converted to `None` before any
  JSON export (Python's `json.dumps` otherwise emits non-standard `NaN`/
  `Infinity` tokens by default), and numpy scalar types are unwrapped to
  native Python int/float so no numpy type reaches a saved JSON file.
