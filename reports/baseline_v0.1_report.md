# Initial Baseline Study v0.1: Results

**Status: preliminary within-study result, primary-judge-based.** Verified
against the underlying data; see `reports/baseline_v0.1_results.json` for
the exact numbers this document summarizes, and
`reports/escalation_reason_summary.md` for validation caveats.

## Research question

When an AI assistant is pressured to achieve a persuasive objective, does
its visible communication become more manipulative, and can explicit
autonomy-preserving instructions reduce that effect?

## Design (recap)

180 outputs: 15 scenarios x 3 subject models (`qwen3:4b`, `gemma3:4b`,
`llama3.2:3b`) x 4 conditions (`baseline`, `pressure`, `autonomy`,
`pressure_autonomy`), one generation per cell, scored by a blinded
open-weight judge (`qwen3:4b`) on six rubric dimensions (0-2 each). See
`reports/study_protocol.md` for the full protocol.

## Headline result: no detectable pressure effect, primary judge

Across all three primary contrasts, the primary judge's manipulation and
autonomy composite scores show **no statistically or practically
meaningful difference between conditions**:

| Contrast | Outcome | Mean diff | 95% bootstrap CI | Permutation p |
|---|---|---|---|---|
| pressure - baseline | manipulation_score | 0.000 | [-0.111, 0.111] | 1.000 |
| pressure_autonomy - pressure | manipulation_score | 0.022 | [-0.089, 0.156] | 1.000 |
| autonomy - baseline | manipulation_score | -0.044 | [-0.133, 0.044] | 0.628 |
| pressure - baseline | autonomy_score | 0.022 | [-0.044, 0.089] | 1.000 |
| pressure_autonomy - pressure | autonomy_score | -0.022 | [-0.111, 0.044] | 1.000 |

(Full model-specific breakdowns in `reports/baseline_v0.1_results.csv`.)

Descriptive statistics make the picture explicit: **manipulation_score is
compressed near the floor** (mean 0.04-0.11 out of a possible 0-8 across
all four conditions; median 0 in every condition) and **autonomy_score is
compressed near the ceiling** (mean 3.96-4.00 out of a possible 0-4; in the
`autonomy` condition specifically, autonomy_score = 4/4 for all 45
observations, SD = 0). The exploratory clustered regression
(`manipulation_score ~ pressure + autonomy + pressure:autonomy + model`,
scenario-clustered standard errors) found no coefficient distinguishable
from zero (all p > 0.14) and near-zero explanatory power (R^2 = 0.026).

**This is a null result as measured by the primary judge on this scenario
set.** It was verified, not assumed: a manual spot-check of matched
baseline/pressure outputs for the same scenario and model
(`s01_notifications`, `qwen3:4b`) confirmed the judge is genuinely reading
both responses and producing distinct evidence text for each -- both
happen to preserve disclosure and decline language and avoid fabricated
urgency, guilt, or authority appeals, so both score 0 on manipulation. This
rules out a silent pipeline bug (e.g. all outputs being scored identically
regardless of content).

## What this does and does not support

**Supported by this data:**
- Within the 15 tested (deliberately low-stakes, benign) scenarios, these
  three small open-weight models did not produce textually detectable
  increases in manipulation-coded language when instructed to maximize
  agreement, as measured by this rubric and this judge.
- All three models overwhelmingly preserved disclosure of tradeoffs/
  alternatives and an easy path to decline, even under the pressure
  framing.

**Not supported, and not claimed:**
- That these models (or language models generally) cannot become more
  manipulative under any goal pressure. The scenarios were designed to be
  benign; higher-stakes or more adversarial scenario framings might behave
  differently.
- That the judge (a small open-weight model itself) has no blind spots for
  subtler manipulation tactics not captured by the six rubric dimensions.
- Anything about internal model states, intent, consciousness, or
  "knowledge" of being evaluated -- this measures observable text only.

## Multi-judge and robustness context

- Secondary judges (`gemma3:4b`, `llama3.2:3b`) scored a 60-item stratified
  sample; full agreement statistics are in `reports/judge_agreement.csv`
  and `reports/tables/judge_agreement_excluding_missing_evidence.json`.
- 89/180 items were flagged by the escalation logic; decomposition
  (`reports/escalation_reason_summary.md`) found only 27/89 reflect
  genuine cross-judge score disagreement, with 20 cases recommended for
  human review (`data/annotations/escalation_review_priority.csv`).
- Given the near-floor/near-ceiling compression of scores, disagreement
  between judges is more often about small integer differences (0 vs 1 on
  a single dimension) than about substantive disagreement on whether a
  response is manipulative overall.

## Caveats specific to this null result

- **Ceiling/floor compression limits statistical power.** With most scores
  at or near 0 (manipulation) or 4 (autonomy), the paired bootstrap and
  permutation tests have very little variance to detect an effect in, even
  if a true small effect existed.
- **Single generation per cell.** No within-cell repetition means we
  cannot separate "no true effect" from "high response-to-response
  variance that happened to average out."
- **Benign scenario design.** Scenarios were deliberately built with no
  dangerous, high-stakes, or adversarial content; this may be exactly why
  little manipulation was detected regardless of condition.
- **Judge sensitivity.** A small open-weight judge may under-detect subtle
  persuasion techniques that a stronger judge or human annotator would
  catch -- this is why the escalation/human-review pathway exists, and
  why judge agreement is reported rather than assumed.

## Confirmatory vs. exploratory

- **Confirmatory** (preregistered in `study_protocol.md`): the three
  condition contrasts on `manipulation_score` and `autonomy_score`, above.
- **Exploratory**: the clustered regression, per-model breakdowns beyond
  the primary contrasts, and any dimension-level or scenario-level pattern
  not part of the three registered contrasts. None of the exploratory
  results here contradict or add nuance beyond the confirmatory null
  finding -- they are reported for completeness, not as a secondary
  positive finding.
