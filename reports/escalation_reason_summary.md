# Escalation Reason Decomposition

Refinement of the escalation review (2026-07-22), made **before** any
condition-level interpretation. All 89 originally-flagged items are
preserved in `data/annotations/escalation_review_full.csv`; nothing was
discarded. This document explains why 89 raw flags does not mean 89 items
genuinely need a human, and separates substantive disagreement from
judge-formatting artifacts.

## Categories

- **A -- Substantive score disagreement**: score range >= 2 on a primary
  dimension, no 2-of-3 majority on 2+ dimensions, manipulation composite
  disagreement >= 3, autonomy composite disagreement >= 2, or a judge
  marked the item ambiguous / reported confidence < 0.65.
- **B -- Judge output quality failure**: a positive score (>0) whose
  evidence could not be traced to the response text (includes empty
  evidence strings, which trivially fail groundedness).
- **C -- Deterministic audit contradiction**: the judge consensus
  materially conflicts with the code-based text audit (e.g. low
  manipulation score despite detected urgency/emotional/authority
  language, or the reverse).
- **D -- High severity / high impact**: top 5% of consensus manipulation
  scores.
- **E -- Primary-only items**: outside the 60-item three-judge overlap
  sample. Cross-judge disagreement (category A) is not meaningful for
  these -- only single-judge signals (ambiguity, confidence, deterministic
  contradiction, top-5%) can apply.

## Category membership (of 89 escalated items; an item can be in multiple)

| Category | Count |
|---|---|
| A (substantive disagreement) | 27 |
| B (judge output quality) | 79 |
| C (deterministic contradiction) | 0 |
| D (high severity/impact) | 35 |
| E (primary-only, outside sample) | 31 |

## Headline decomposition

- **Escalated *only* due to category B** (i.e. would not have escalated on
  any other ground): **13 of 89**.
- **Genuine substantive score disagreement (category A)**: **27 of 89**.
- **Outside the 60-item multi-judge sample (category E)**: **31 of 89** --
  these escalated on single-judge grounds only (overwhelmingly the top-5%
  manipulation criterion, since 0-confidence/0-ambiguity issues were found
  in the primary judge's data).
- **Remain flagged after removing evidence-only (B-only) flags**: **76 of
  89**. Category B is pervasive (79/89 touch it at all) but rarely the
  *sole* reason (13/89) -- most items also carry a substantive (A) or
  high-impact (D) signal independently.
- **Escalations attributable specifically to llama3.2:3b's empty evidence,
  and only that**: **11 of 89**. This confirms the earlier finding
  (llama3.2:3b: 89 empty-evidence cells across the 60-item sample vs.
  gemma3:4b's 2) is a real, but largely non-decisive, contributor -- most
  B-touched items also carry an independent substantive reason.

## Methodological rules applied

1. An empty evidence field is **not** treated as proof the underlying
   score is wrong -- it is marked evidence-deficient and reported
   separately (see the two-variant agreement tables below).
2. llama3.2:3b scores with missing evidence were **not** silently accepted
   as validated; they are flagged evidence-deficient at the dimension
   level.
3. Agreement statistics were computed twice:
   - `reports/judge_agreement.csv` -- all valid scores.
   - `reports/tables/judge_agreement_excluding_missing_evidence.json` --
     excluding dimension-level judgments with missing evidence.
   Excluding evidence-deficient judgments changes `artificial_urgency`'s
   sample size (60 -> 59, one item's evidence removed on that dimension for
   one judge) and shifts agreement rates modestly; no dimension had its
   data collapse entirely, so the primary agreement table remains usable
   with this caveat documented rather than silently ignored.
4. No item was discarded because only one judge's evidence was missing;
   the item and its other judges' scores remain in the record.
5. Escalation thresholds were not adjusted after seeing this breakdown --
   the underlying criteria (`consensus.py`) were frozen before any
   condition-level scores were inspected, and remain unchanged here; this
   analysis only *categorizes* the existing 89 flags, it does not
   re-threshold them.
6. The human-review target was **not** forced to 10-20. It is derived from
   substantive uncertainty: 20 cases were selected for the priority file
   because they carry a category A or D signal (not merely B), which is
   how many such cases existed -- not because 20 was a target to hit.

## Files produced

- `reports/escalation_reason_breakdown.csv` -- per-item category
  membership for all 89 escalated items.
- `data/annotations/escalation_review_full.csv` -- all 89 escalated items,
  full evidence/scores/categories, ranked by severity/disagreement/
  uncertainty (nothing discarded).
- `data/annotations/escalation_review_priority.csv` -- **20 cases**, all
  carrying a substantive (A) or high-impact (D) signal beyond mere
  judge-formatting issues (13 category ABD, 7 category BD). This is the
  recommended human-review set.
- `reports/judge_agreement.csv` and
  `reports/tables/judge_agreement_excluding_missing_evidence.json` --
  dimension-level agreement, both with and without evidence-deficient
  judgments included.

## What this does *not* resolve

The 69 non-priority escalated items (89 - 20) are not claimed to be
adjudicated or resolved. They remain flagged in
`escalation_review_full.csv` and will be carried through the primary
statistical analysis via bounded sensitivity analysis (lower/upper
plausible scores), not treated as settled.
