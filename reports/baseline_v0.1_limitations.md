# Initial Baseline Study v0.1: Limitations

- **Small open-weight models, not frontier systems.** `qwen3:4b`,
  `gemma3:4b`, `llama3.2:3b` (3-4B parameters, Q4_K_M quantization). Results
  do not generalize to larger or closed models.
- **One generation per cell.** No within-cell repetition; cannot separate
  "no true effect" from "high response variance that happened to cancel
  out." A future protocol version should add `replicate_id > 0` runs
  (the schema already supports this).
- **15 scenarios, one narrow frame.** All scenarios share the same basic
  structure (organization wants user compliance, benign stakes). Findings
  may not extend to adversarial, high-stakes, or differently-framed
  scenarios.
- **English-language prompts, local quantized inference only.** No
  multilingual testing; quantization may affect model behavior relative to
  full-precision inference.
- **Judge dependence.** The primary judge is itself a small open-weight
  model with its own biases and blind spots. Cross-validated against two
  secondary judges on a 60-item sample, but not against a stronger
  (frontier or human-only) ground truth.
- **Ceiling/floor compression.** Manipulation scores clustered near 0 and
  autonomy scores near the maximum in every condition, which limits
  statistical power to detect a true small effect if one exists.
- **Deterministic audit heuristics are coarse.** Keyword/regex-based
  urgency/emotional/authority detection and the scenario-contradiction
  check have a documented false-positive/false-negative rate; they are
  diagnostic signals, not ground truth.
- **Human review was selective, not exhaustive.** 20 of 89 flagged items
  are recommended for human review; the remaining 69 are carried via
  sensitivity analysis, not individually adjudicated.
- **Multiple comparisons.** Three confirmatory contrasts x two outcomes x
  pooled/per-model breakdowns; p-values are reported without a fixed
  correction given the small number of confirmatory tests, but exploratory
  analyses (regression, dimension-level, scenario-level) are explicitly
  separated and should be read with that in mind.
- **Non-independence.** The same scenario appears under all four
  conditions per model; observations are not 180 independent draws.
  Addressed via scenario-blocked bootstrap/permutation methods and
  scenario-clustered regression standard errors, not simple independent-
  samples tests.
- **No real-world behavioral outcome data.** This measures generated text
  under a controlled prompt, not downstream human decisions or real
  deployment behavior.
