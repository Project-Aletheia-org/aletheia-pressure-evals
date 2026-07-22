# Evaluation Methodology

Companion to `docs/rubric_card.md` (dimension definitions) and
`reports/study_protocol.md` (full protocol). This document describes how
scoring is actually carried out and validated.

## Layer 1: automated judge

- Judge model: `qwen3:4b`, temperature 0 (deterministic), per
  `configs/experiment.yaml`.
- The judge sees only the anonymized response text: subject model identity,
  experimental condition, and the study's hypotheses are withheld. Rows are
  shuffled before scoring (fixed seed) so ordering cannot leak condition.
- Output is a structured Pydantic object (`EvaluationResult`, rubric v0.1):
  six primary dimensions (score + evidence each), three secondary
  measurement-validity dimensions, `confidence`, `ambiguous`, and an overall
  `rationale`.
- Malformed JSON gets up to `max_repair_retries: 3` repair-prompt attempts
  (the validation error is included in the repair prompt). If still
  malformed, the record is flagged `evaluation_failed=True` and preserved,
  not silently dropped or fabricated.
- Every `EvaluationRecord` carries provenance: `judge_model`, `judge_digest`
  (Ollama model digest), `rubric_version`, `evaluation_prompt_hash`,
  `validation_attempts`, and the immutable `raw_response` alongside the
  parsed result.
- **Judge labels are a measurement, not ground truth.** They are validated
  against blinded human annotation (Layer 2) and reported honestly even if
  agreement turns out to be weak.

## Layer 2: human validation

- Stratified blind sample of 60 outputs: 5 per (model x condition)
  combination, randomized order, anonymous item IDs, no model or condition
  column exposed to the annotator (`AnnotationExportRow` schema).
- A second annotator scores at least 20 randomly selected outputs, if
  available, so human-human agreement can be measured before any
  disagreement is adjudicated.
- Reported: exact agreement, weighted Cohen's kappa per dimension, Spearman
  correlation between human and judge composite scores, mean absolute
  error, and the judge's ambiguity rate.

## Measurement-validity checks (run before/alongside primary scoring)

- **Calibration pass**: the judge scores the 12 hand-authored calibration
  examples (`data/calibration_examples.jsonl`) before scoring real data;
  scores are compared to the pre-registered expected ranges as a sanity
  check on the judge, not a formal pass/fail gate.
- **Judge-stability audit**: 20 stratified experimental outputs are scored
  three times each by the primary judge; exact stability and score variance
  are reported per dimension. All three passes are preserved -- the main
  analysis still uses the single primary-pass judgment, never a majority
  vote across the three.
- **Secondary-judge audit**: 30 stratified outputs are additionally scored
  by `gemma3:4b`; composite- and dimension-level agreement with the primary
  judge (`qwen3:4b`) is reported as a diagnostic, not treated as a second
  ground truth.
- **Control Set v0.1**: 2 no-stakes scenarios (`data/control_scenarios.jsonl`)
  check whether models/the judge still produce elevated manipulation scores
  when there is genuinely nothing to be manipulative about. Never merged
  into the 180 primary outputs.

## What is never done

- The judge never sees which model produced a response or which
  experimental condition it came from.
- Reasoning traces (`thinking`, qwen3 only) are never scored and never
  treated as a message sent to a user.
- Outputs are never excluded from analysis because they contradict a
  hypothesis; only empty/malformed/duplicate cells are excluded, and that
  exclusion is reported as a count, not silently applied.
- A response is never rescored to "fix" a result; if a scoring bug is
  found, it is documented as a deviation and results are regenerated
  transparently, not edited in place.
