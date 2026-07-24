# V1 Closure Report

**Scope of "V1":** the Initial Baseline Study v0.1 generation/evaluation run (`baseline-v0.1-20260722`), the Qwen primary judge, the Claude Sonnet 4.6 external-judge validation pass, and the resulting sensitivity/agreement/escalation analysis. Frozen artifact list and hashes: `reports/v1_freeze_manifest.json`.

## 1-3. Human ratings validation / comparison / closer-judge determination — **BLOCKED, not completed**

A 15-item blinded human-adjudication packet (`reports/human_adjudication_blinded_15.md` / `.csv`) was generated and opened for review. As of freeze time, **no scoring fields were saved back to either file** — every field (`deceptive_omission` through `reviewer_notes`) is still blank, confirmed by re-reading both files immediately before this freeze. No human ratings exist to validate or compare. I have not fabricated, estimated, or guessed at this data.

**This is an open item, not a resolved one.** See `reports/v1_completion_checklist.md`. When the ratings are actually saved, re-run this step: validate all 15 rows have every field filled, then compare against the corresponding Qwen/Claude scores already in `reports/qwen_claude_high_disagreement_review.csv` via the `reports/human_adjudication_unblinding_key.csv` mapping.

## 4. Final V1 classification

This rests entirely on the completed Qwen-vs-Claude automated comparison (`reports/judge_sensitivity_summary.md`), unchanged by the missing human layer:

**Classification: evaluator-sensitive.**

- Qwen-only: robust null on all three condition contrasts (all permutation p≥0.49, all effects <0.05 on an 8-point scale).
- Claude-only: two of three contrasts significant (`pressure_autonomy − pressure` p=0.0003, `autonomy − baseline` p=0.0017), moderate effect sizes (|d|≈0.5-0.6).
- Consensus (mean of both): the two contrasts remain significant (p=0.0021, p=0.0010), attenuated.
- Driving mechanism: the Claude-detected effect concentrates in `qwen3:4b`'s own generations (the same model that is also the primary judge) — a self-evaluation blind spot, not a scenario- or single-dimension-specific artifact (broad across 13-14/15 scenarios and 4-5/6 dimensions).
- Excluding the 48 high-disagreement items nulls the effect (E), but that exclusion criterion is partly defined by the same manipulation scores being tested, so it demonstrates concentration, not independent refutation.

This classification does not change based on the pending human layer — it was reached from the two-LLM-judge comparison alone. The human packet was commissioned as a *further* check on which of Qwen/Claude is better calibrated on the specific 48 disputed items, not as a precondition for the classification itself.

## 5. V1 limitations (concise)

- **No human ground truth yet.** Every score in this study, including the "external validation," comes from LLM judges. The 15-item human-adjudication packet exists to start closing this gap but is not yet completed.
- **Judge/subject conflation.** `qwen3:4b` is simultaneously a subject model and the primary judge; this is very likely the dominant driver of the evaluator-sensitivity finding and was not designed out of the original study.
- **Evidence-groundedness heuristic gap.** `audit.evidence_is_grounded`'s quote regex misses ASCII straight single quotes, producing ~149/180 false-positive "unverifiable evidence" flags against Claude's quoting style (traced and excluded from the disagreement rule; not fixed in the shared code, since that would touch the Qwen-facing pipeline out of scope for this work).
- **Small per-model N.** By-model contrasts rest on 15 scenario-pairs per model; individually-significant qwen3:4b effects are robust but the null results for gemma3:4b/llama3.2:3b by-model breakdowns are underpowered to rule out smaller effects.
- **Bootstrap CI non-reproducibility.** The recomputed Qwen-only (A) analysis matches the original `baseline_v0.1_results.json` exactly on mean/median/permutation-p, but bootstrap CI bounds differ slightly — the original analysis script isn't preserved in the repo, so the exact RNG sequence can't be recovered. Substantive conclusions are unaffected (both CIs are tiny and straddle zero).
- **E's exclusion criterion is partly circular.** Several of the "high-disagreement" escalation reasons are defined using the same manipulation/autonomy scores whose condition-effect is being tested, so E's null result should be read as "effect concentrated in the disagreement subset," not as an independent robustness check.
- **15-scenario, 3-model, benign-scenario design.** Inherited from the original study: results don't generalize to higher-stakes, more adversarial, or larger-model settings.

## 6. Freeze

All V1 inputs, outputs, hashes, manifests, and test results are recorded in `reports/v1_freeze_manifest.json` (32 files, sha256 each, git commit `7a639bd96352fd15685b1486a3f91219aeb3babf`, full test suite 109/109 passing at freeze time). Nothing in this freeze has been pushed, committed, or published.

## 7. Checklist

See `reports/v1_completion_checklist.md`.
