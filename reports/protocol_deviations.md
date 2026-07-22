# Protocol Deviations

Formal record of every deviation from an originally-stated plan. See
`reports/study_protocol.md`'s own changelog for the versioned protocol
history; this table is the audit-oriented cross-reference. None of these
deviations altered the original 15 scenarios, the four condition prompts,
the six primary rubric dimensions, or the three primary hypotheses'
wording.

| # | Original plan | Deviation | When | Why | Affects primary comparisons? |
|---|---|---|---|---|---|
| 1 | `generation.max_tokens: 1024` | Raised to 3072 | Before main generation began (during smoke testing) | qwen3 reasoning length exceeded 1024 tokens, causing empty responses | No -- config parameter only, not scenario/prompt/hypothesis content |
| 2 | Preregistration frozen, one-time pilot framing | Replaced with versioned living study protocol | Before main generation began | Project explicitly intended for repeated/longitudinal runs | No |
| 3 | Fixed 60-row human annotation sample | Multi-judge (3-judge) consensus + deterministic audit + selective escalation, targeting 10-20 human-reviewed cases | Before any human annotation began | Scales better with a living framework meant to run repeatedly; escalation criteria frozen before condition-level results were inspected | No -- validation methodology only |
| 4 | 30-item secondary-judge audit (gemma3:4b only) | 60-item stratified + flagged sample, scored by both gemma3:4b and llama3.2:3b | Before secondary judging began | Broader, better-targeted coverage than a fixed small audit; sample composition (mandatory + stratified) fixed before scoring | No |
| 5 | `evaluation.max_tokens: 2048` | Raised to 4096 | After 2 permanent failures in the first 4 items of primary evaluation | Same token-exhaustion pattern as generation | No |
| 6 | (implicit) evaluation should not require per-item exceptions | item-0049 rescued with a one-off `max_tokens=8192` call, outside the global config | After item-0049 failed twice at 4096 | Isolated failure, not systematic; avoided slowing every other evaluation call | No -- one item's evaluation call parameters only; same blinded content/judge/rubric/prompt |
| 7 | `evidence_is_grounded` checks all dimensions | Restricted to positive claims (score > 0) | During dry-run testing of the escalation pipeline, before secondary judges ran | Score=0 justifications describe absence, not a verifiable positive claim; original check produced high false-positive escalation rates | No -- diagnostic heuristic only |

No deviation has yet required altering H1-H5, the four experimental
conditions, the 15 scenarios' prompts, or the six primary rubric
dimensions. Any future deviation of that kind would be recorded here before
being applied, per `study_protocol.md` Section 11's change policy.

## Data-integrity correction: primary evaluation manifest timestamp

- **Original (stale) value:** `started_at_utc: 2026-07-22T08:37:04Z` in
  `data/evaluations/baseline-v0.1-20260722.manifest.json`. This value was
  set incorrectly during a manual manifest finalization: a placeholder
  timestamp was reused instead of the actual first evaluation record's
  time.
- **Corrected value:** `started_at_utc: 2026-07-22T11:47:05.930205Z`.
- **Source used for correction:** the earliest `evaluated_at` timestamp
  actually present across all rows in
  `data/evaluations/baseline-v0.1-20260722.jsonl` (the raw, immutable
  evaluation records themselves), not a re-derived or estimated value.
- **Scope of the correction:** provenance metadata only. It changes
  nothing about any evaluation score, any judge output, any generation
  record, or any analysis result -- only the manifest's record of *when
  the run started*. No evaluation record, score, or hash was modified.
- Verified: `data/evaluations/baseline-v0.1-20260722.manifest.json`
  reconciles with the JSONL (180/180 successful_evaluations,
  `completed_at_utc` unchanged, all other fields identical to the prior
  manifest write).
