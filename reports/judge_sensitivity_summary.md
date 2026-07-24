# Judge Sensitivity Summary: Qwen vs. Claude External Judge

Full numbers: `reports/claude_external_judge_results.json`. Per-judge detail: `reports/claude_external_judge_analysis.md`. Agreement table: `reports/qwen_claude_agreement.csv`.

## C — Agreement between Qwen and Claude (180 items, 6 dimensions)

Agreement is weak across the board:

| Dimension | Qwen mean | Claude mean | Cohen's κ | Spearman ρ | Exact agreement |
|---|---|---|---|---|---|
| deceptive_omission | 0.028 | 0.400 | 0.031 | 0.073 | 63% |
| emotional_pressure | 0.000 | 0.728 | 0.000 | n/a (constant input on one side) | 27% |
| artificial_urgency | 0.006 | 0.261 | 0.032 | 0.171 | 76% |
| authority_social_pressure | 0.050 | 0.272 | 0.209 | 0.318 | 77% |
| respect_for_refusal | 1.994 | 1.767 | 0.037 | 0.178 | 78% |
| transparency | 1.978 | 1.567 | 0.010 | 0.025 | 59% |

(Full per-dimension stats including means/medians/mean_range/evidence_overlap_rate are in `reports/qwen_claude_agreement.csv`.)

Composite-level: manipulation Pearson r=0.165, Spearman ρ=0.104, MAE=1.58 (out of 8); autonomy Pearson r=0.140, Spearman ρ=0.083, MAE=0.66 (out of 4). All kappas are near zero — chance-level or barely-above-chance agreement on every dimension. This is not a subtle disagreement; it's two judges operating on effectively different scales. The proximate cause is visible in the raw scores: Claude's manipulation means (1.2-2.9 out of 8, by model/condition cell) run roughly 10-40× higher than Qwen's (0.0-0.2), with real variance where Qwen frequently returns zero variance (sd=0) for an entire model×condition cell.

## D — Consensus (mean of the two judges, per item and per dimension)

Averaging pulls the effect size roughly in half relative to Claude alone, but two contrasts remain significant:

| Contrast | Field | Mean diff | 95% CI | Permutation p |
|---|---|---|---|---|
| pressure − baseline | manipulation | +0.167 | [−0.111, +0.422] | 0.153 |
| pressure − baseline | autonomy | −0.100 | [−0.267, +0.067] | 0.239 |
| **pressure_autonomy − pressure** | **manipulation** | **−0.389** | **[−0.600, −0.167]** | **0.0021** |
| **pressure_autonomy − pressure** | **autonomy** | **+0.278** | **[+0.122, +0.433]** | **0.0009** |
| **autonomy − baseline** | **manipulation** | **−0.367** | **[−0.600, −0.144]** | **0.0010** |
| **autonomy − baseline** | **autonomy** | **+0.267** | **[+0.111, +0.422]** | **0.0003** |

Per-dimension, the consensus contrasts are driven mainly by `emotional_pressure`, `respect_for_refusal`, `transparency` (all p<0.012 in both significant contrasts), with `deceptive_omission` significant only in `pressure_autonomy − pressure` (p=0.0053) and `artificial_urgency`/`authority_social_pressure` weak-to-marginal.

## E — Sensitivity excluding high-disagreement items

**Definition used:** an item is "high-disagreement" if any `consensus.py` escalation reason fires *other than* `unverifiable_evidence`. That reason is excluded deliberately: post-run validation (see `reports/claude_external_judge_analysis.md` §4 in the sibling validation notes, and the run's own audit trail) found the evidence-groundedness heuristic flags ~149/180 items largely because Claude quotes with ASCII straight single quotes (`'...'`), which the heuristic's regex (tuned for `"`/curly quotes) doesn't recognize — a false-positive rate, not a real evidence problem, confirmed by manual spot-checks of the flagged excerpts. Using it as a disagreement signal would have excluded most of the dataset for the wrong reason. The remaining reasons used (`score_range>=2`, `primary_secondary_manipulation_diff>=3`, `primary_secondary_autonomy_diff>=2`, `judge_marked_ambiguous`, `judge_confidence<0.65`, `deterministic_contradicts_consensus`, `top_5pct_consensus_manipulation`) are genuine cross-judge or self-reported signals. **48/180 items (27%)** were flagged this way and excluded; 132 remain.

On the 132 remaining items, using consensus scores, every contrast is non-significant:

| Contrast | Field | n | Mean diff | Permutation p |
|---|---|---|---|---|
| pressure − baseline | manipulation | 18 | +0.111 | 0.437 |
| pressure − baseline | autonomy | 18 | −0.028 | 1.000 |
| pressure_autonomy − pressure | manipulation | 21 | −0.095 | 0.460 |
| pressure_autonomy − pressure | autonomy | 21 | +0.071 | 0.257 |
| autonomy − baseline | manipulation | 26 | −0.077 | 0.643 |
| autonomy − baseline | autonomy | 26 | +0.077 | 0.290 |

**Important caveat on causality:** several of the exclusion reasons (`score_range>=2`, `primary_secondary_manipulation_diff>=3/autonomy_diff>=2`, `top_5pct_consensus_manipulation`) are themselves partly defined by how much Claude's manipulation score diverges from Qwen's or how high the consensus manipulation score is. Excluding those items is not a random or judge-independent robustness check — it mechanically removes many of the exact items that carry the pressure/autonomy signal in Claude's scoring. **E's null result should be read as "the effect is concentrated in the disagreement-flagged subset," not as "the effect disappears under an independent robustness check."** Both are consistent with the data; this analysis cannot distinguish a true concentrated effect from an artifact of the exclusion rule without further work (e.g. a disagreement definition that doesn't reference the outcome being tested).

## Classification

**Primary classification: evaluator-sensitive.**

Evidence for this label over the alternatives:

- **Not robust null.** Qwen alone (A) is a clean null on every contrast. Claude alone (B) finds two of three contrasts significant at p≤0.002 with moderate effect sizes (|d|≈0.5-0.6), and this survives (attenuated but still p<0.01) when the two judges are averaged (D). The substantive conclusion — "does the autonomy-preserving instruction reduce manipulation and increase autonomy-respecting behavior?" — flips from "no measurable effect" to "yes, significant effect" depending entirely on which judge is used. That is the definition of evaluator-sensitive.
- **Secondary driver is model-specific, not the primary axis.** The Claude-detected effect is overwhelmingly concentrated in `qwen3:4b`'s own generations (by-model manipulation p=0.0008 and 0.0031 for qwen3:4b vs. p=1.00/0.67 for gemma3:4b and p=0.11-0.13, ns, for llama3.2:3b) — and `qwen3:4b` is simultaneously the subject model and the primary local judge in this study. Qwen-as-judge scores `qwen3:4b`-as-subject at a flat, zero-variance manipulation score across all 4 conditions for 14/15 scenarios. That is consistent with a self-evaluation blind spot, but it is a *mechanism explaining why the evaluator-sensitivity is so large*, not a separate, evaluator-independent "model-specific" effect — the same subject model's outputs, judged by Claude, are not null.
- **Not dimension-specific in the narrow sense.** 4-5 of 6 individual dimensions are independently significant in the same direction (deceptive_omission, emotional_pressure, respect_for_refusal, transparency most consistently; artificial_urgency and authority_social_pressure weaker/marginal). The effect is broad across dimensions, not carried by one alone.
- **Not scenario-specific.** The qwen3:4b-outputs effect appears in 13-14 of 15 scenarios in the same direction, not concentrated in one or two.
- **General calibration gap compounds all of the above.** Claude's raw manipulation scores run roughly 10-40× higher than Qwen's in every cell, with real variance where Qwen is frequently a constant zero. Some of Qwen's null result is very likely a floor/ceiling measurement-sensitivity problem (an evaluator that never varies cannot detect a within-condition effect), independent of the self-evaluation question. This is itself evidence for "evaluator-sensitive": the two judges are not on the same effective scale, and conclusions drawn from either one alone should not be treated as judge-independent ground truth.

**Practical implication:** the original Initial Baseline Study v0.1 conclusion of "no detectable manipulation/autonomy effect" is not supported when scored by an independent external judge — it holds only when the primary judge is `qwen3:4b`, which also generated a third of the evaluated text. This is exactly the confound an external-judge validation pass is designed to surface, and it does.
