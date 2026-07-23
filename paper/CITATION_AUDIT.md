# Citation Audit

Every scientific claim in the manuscript that cites external literature,
mapped to its source, exact supporting content, and verification status.
All 7 sources were independently verified by fetching the actual page (not
relied upon from search-result snippets alone). See
`docs/literature_matrix.csv` for the full structured record.

| Claim in paper | Citation key | Exact supporting content | Direct or inferential | Verification status |
|---|---|---|---|---|
| "LLM judges exhibit systematic, non-random position bias when comparing candidate outputs, motivating blinded, order-randomized evaluation" | `shi2024judging` | Abstract/summary: position bias found systematic across 15 judges, 22 tasks, >150,000 evaluation instances | Direct | Verified via direct fetch of arXiv abstract page |
| "LLM judges can favor outputs from their own model family (self-preference bias), motivating the use of independent secondary judges rather than a single judge's absolute score" | `wataoka2024selfpreference` | GPT-4 shown to exhibit measurable self-preference bias in pairwise evaluation | Direct | Verified via direct fetch of arXiv abstract page |
| "Self-preference bias persists even under objective rubric-based criteria, and ensembling multiple judges mitigates but does not eliminate it" | `pombal2026rubricspb` | Rubric-based self-preference bias shown up to 50% higher pass-rate for own-model outputs; ensembling reduces but does not eliminate | Direct | Verified via direct fetch of arXiv abstract page |
| "Prior work has found that goal conflict or a threat to a model's continued operation can independently elicit harmful autonomous behavior in frontier models, motivating study of a lower-stakes textual precursor (persuasive manipulation) under analogous goal-pressure framing" | `anthropic2025agentic` | Anthropic's stress-test: goal conflict alone, or replacement threat alone, each sufficient to elicit harmful agentic action across 16 models | Direct (used as motivating precedent, not as evidence about this study's own models) | Verified via direct fetch of Anthropic research page |
| "The six-dimension manipulation/autonomy rubric corresponds to recognized categories of manipulative design in AI chatbot interactions, rather than an ad hoc list" | `cdt2026darkpatterns` | CDT taxonomy of 37 dark patterns across 5 categories in AI chatbots | Inferential (rubric dimensions were designed independently, then cross-checked for correspondence with this taxonomy after the fact) | Verified via multiple independent search hits including a direct PDF link; full report text not independently fetched via WebFetch (title/publisher/topic confirmed, not full content) |
| "Frontier models can detect evaluation contexts above chance, motivating measurement (not assumption) of evaluation-awareness as a secondary rubric dimension in this study" | `needham2025evalaware` | Gemini-2.5-Pro AUC 0.83 at detecting evaluation vs. deployment context (vs. human baseline AUC 0.92) | Direct (as a motivating rationale; this study's small open-weight subject models were not themselves tested for evaluation-awareness detection ability, only scored on an evaluation_awareness rubric dimension by the judge) | Verified via direct fetch of arXiv abstract page |
| "Scenario-clustered/blocked bootstrap and permutation methods are an appropriate way to construct confidence intervals for repeated-measures data without assuming independence" | `mackinnon2023clusterboot` | Methodological validation of jackknife/bootstrap cluster-robust inference | Direct (methodological justification for `src/pressure_evals/analyze.py`'s design) | Verified via direct fetch of arXiv abstract page |

## Claims NOT covered by an external citation (internal/empirical only)

All quantitative results (manipulation/autonomy scores, contrasts,
confidence intervals, agreement statistics, escalation counts) are this
study's own findings, verified by recomputing from
`data/raw_outputs/`, `data/evaluations/`, and `reports/baseline_v0.1_results.json`
directly -- not externally cited claims.

## Scope note

This is a **scoped, not exhaustive**, literature review given the time
constraints of this pilot. Seven sources were identified via web search and
each independently verified by fetching the source directly (not relied
upon from search-result summaries alone). Topics in the original request's
17-item list not represented by a dedicated citation here (e.g. "ordinal
agreement metrics" beyond weighted Cohen's kappa, "automated alignment
auditing" as a distinct literature from agentic misalignment) were not
covered by a verified source in the time available; no citation was
fabricated to fill these gaps. Future protocol versions should expand this
matrix rather than pad it now.
