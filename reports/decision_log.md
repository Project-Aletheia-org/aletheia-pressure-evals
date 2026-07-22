# Decision Log

Key decisions, the alternatives considered, and why. Cross-references
`research_log.md` for narrative detail and `protocol_deviations.md` for the
formal deviation record.

| Decision | Alternative considered | Rationale |
|---|---|---|
| Standalone repo `aletheia-pressure-evals` under `Project-Aletheia-org`, not nested in `Project-Aletheia` | Nesting under `Project-Aletheia/research/pressure-evals/` | Kept the pilot's public-facing artifact clean of the unrelated Obsidian vault/manifesto content; avoided mixing two unrelated git histories. |
| Only qwen3-family models get `think=True` | Passing `think=True` to all models | gemma3/llama3.2 raise `ResponseError` on any `think` parameter; verified via direct API test. |
| `generation.max_tokens` 1024 -> 3072; `evaluation.max_tokens` 2048 -> 4096 | Leaving thresholds unchanged and accepting empty-response failures | qwen3's chain-of-thought length varies unpredictably and can exceed 1000+ tokens even for short-seeming inputs; empirically verified failure rate dropped from ~7% (smoke test) to <1% (baseline generation) and to 1/180 for evaluation after the increase. |
| Empty response = retryable failure, not success | Recording the empty string as the model's "message" | An empty message is not a usable behavioral output; silently accepting it would corrupt the manipulation/autonomy scoring for that cell. |
| item-0049: one-off rescue script at max_tokens=8192, not a global config bump | Raising `evaluation.max_tokens` globally to 8192 | The failure was isolated to one item after 4096 already fixed 179/180; a global bump would have slowed every future evaluation call for a problem that wasn't systematic. |
| Preregistration -> living study protocol | Keeping the original "FROZEN" one-time-pilot framing | The project is explicitly intended to run repeatedly (scheduled monitoring, scenario-bank growth); "frozen" framing misrepresented the intended lifecycle. |
| Fixed 60-row human annotation -> multi-judge consensus + selective escalation | Keeping the original manual-annotation plan | Manual annotation of 60 rows doesn't scale with a living framework meant to run repeatedly; automated cross-judge disagreement plus a deterministic audit surfaces the cases that actually need a human, typically far fewer than 60. |
| Full 180-item x 2-secondary-judge run replaced with a 60-item stratified + flagged sample | Scoring all 180 with all 3 judges | gemma3/llama3.2 are fast enough that 180x2 was feasible, but a targeted sample (mandatory: ambiguous/low-confidence/top-5%-manipulation, plus stratified fill) captures the disagreement-relevant cases at a fraction of the compute, decided before seeing secondary-judge results. |
| `evidence_is_grounded` only applies to positive claims (score > 0) | Applying groundedness checking to every dimension regardless of score | A score=0 justification typically describes an *absence* ("no guilt, fear, or shame"), which has no reason to textually overlap with the response; checking it produced systematic false positives (39/180 -> 12/180 after the fix, in a dry run against partial data). |
| `to_json_safe` sanitizes NaN/Infinity/numpy scalars before any JSON export | Serializing dataclasses directly | Python's `json.dumps` allows NaN/Infinity by default, producing non-standard JSON that strict parsers (and some downstream tools) reject; numpy scalar types risk silently leaking into saved research artifacts. |
