# Initial Baseline Study v0.1: Evaluation Audit

## Primary judge (qwen3:4b, all 180 outputs)

- 180/180 successful evaluations (one item, `item-0049`, required a
  documented one-off rescue; see `reports/protocol_deviations.md`)
- 4 historical failed attempts preserved (2 pre-fix for item-0001/
  item-0003, 2 for item-0049 before its rescue)
- 0 duplicate successful evaluations
- 0 invalid (out-of-range) scores
- Calibration check (`reports/tables/` calibration run against
  `data/calibration_examples.jsonl`): 60/72 (example, dimension) pairs
  landed within the pre-registered expected range; non-manipulative and
  strongly-autonomy-preserving calibration examples scored perfectly (100%
  in range), while strongly-manipulative examples showed more
  disagreement with the pre-registered expectation -- consistent with the
  broader finding that this judge/model combination is more reliable at
  the low end of the manipulation scale than at distinguishing degrees of
  strong manipulation.

## Deterministic audit (all 180 outputs, code-only, no model calls)

From `reports/tables/deterministic_audit_summary.json`:

| Signal | Rate |
|---|---|
| Discloses relevant tradeoff | 99.4% |
| Mentions known alternative | 91.7% |
| Mentions decline option | 39.4% |
| Urgency language detected | 1.1% |
| Emotional-pressure language detected | 0.0% |
| Authority/social-proof language detected | 1.7% |
| Possible scenario contradiction (coarse heuristic) | 1.1% |
| Mean response word count | 117.6 |
| Malformed evaluations | 0 |

This independently corroborates the primary judge's null finding via a
completely different (non-model, keyword/heuristic) measurement: urgency
and emotional-pressure language are essentially absent across the dataset,
regardless of condition, matching the judge's near-zero manipulation
scores.

## Secondary judges (60-item stratified sample)

- `gemma3:4b`: 60/60 successful, 0 failures, 2 empty-evidence cells
- `llama3.2:3b`: 60/60 successful, 0 failures, 89 empty-evidence cells (a
  genuine judge-quality finding for the smallest of the three models, not
  a pipeline defect -- see `reports/decision_log.md`)
- Exact sample-membership equality verified across all three judges
- No judge saw another judge's output, the subject model identity, the
  experimental condition, or the study hypotheses at any point (verified
  by direct inspection of the fixed judge system prompt and each
  evaluation call's arguments)

## Escalation

- 89/180 items flagged by the escalation logic
- Decomposed by cause (`reports/escalation_reason_summary.md`): 27
  genuine substantive score disagreement, 79 touch a judge output-quality
  issue (13 solely so), 35 in the top-5% consensus manipulation band, 31
  outside the 60-item multi-judge sample (single-judge-only signals)
- 20-case priority file for optional human review
  (`data/annotations/escalation_review_priority.csv`); 69 remaining
  flagged items carried via robustness/sensitivity analysis, not treated
  as resolved
