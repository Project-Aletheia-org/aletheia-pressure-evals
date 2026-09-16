# MANUSCRIPT_CHANGELOG.md

Rewrite of `paper/` from a null-result pressure study to an **evaluator-sensitivity
/ measurement-instability** paper. Source of truth: `PAPER_SUBMISSION_AUDIT.md` +
`reports/claude_external_judge_analysis.md` + `reports/judge_sensitivity_summary.md`.
Date 2026-09-15. No experiment rerun; no new result generated. Every number below
was reconstructed from `reports/`, not copied from the prior manuscript.

---

## 1. Major scientific framing changes

- **Paper-level conclusion changed** from "preregistered null: goal pressure does
  not increase manipulation" to "the behavioral conclusion is **evaluator-dependent**;
  the same 180 outputs yield opposite substantive answers under an open-weight vs a
  frontier judge." The Qwen null is retained as *one judge's* result, not the thesis.
- **Central research question reframed** (Introduction) to: *"How stable are
  behavioral conclusions about pressure-induced manipulation across evaluators?"*
  The pressure/autonomy question is kept as the probe, not the contribution.
- **Frontier judge (`claude-sonnet-4-6`) promoted from a deferred "forthcoming
  revision / optional extension" to a core, co-primary evaluator** in Methods,
  Results, Ethics, and Reproducibility.
- **New Results subsection added: "Evaluator dependence of behavioral conclusions"**
  (`sec:res_evaldep`), plus dedicated subsections for the cross-judge disagreement
  (`sec:res_disagree`) and the same-family pattern (`sec:res_family`).
- **Self-family pattern stated as observational, not causal.** Framed throughout as
  "consistent with a self-evaluation measurement effect" with explicit statements
  that causal self-preference is *not* shown and evaluator motive cannot be inferred.
- **No ground-truth claim.** Neither judge is called correct; Claude is not treated
  as ground truth and Qwen is not called "biased."
- **Related Work** re-centered on LLM-as-judge reliability as the primary lineage
  (the study is positioned as a conclusion-flipping case, beyond prior score-shift
  bias findings).

## 2. Numerical changes (old manuscript → reconstructed from reports/)

- **Primary contrasts table (`tab:contrasts_qwen`, was `tab:contrasts`):** CIs
  updated to the recomputed values from `claude_external_judge_analysis.md` §2 (e.g.
  pressure−baseline manipulation CI **[−0.111,+0.111] → [−0.089,+0.089]**; p=1.000
  unchanged). Table expanded from **5 rows → 6** (the omitted autonomy−baseline
  *autonomy* contrast, +0.044, p=0.499, added). Reason for CI shift documented in
  Methods (`sec:stats`): original bootstrap script not preserved; recomputed at
  seed 42 from committed code.
- **New table `tab:contrasts_claude`** (frontier judge), from `analysis` §3:
  pressure−baseline manip +0.333 (d +0.24, p=0.138); **pressure_autonomy−pressure
  manip −0.800 (d −0.59, p=0.0003)**; **autonomy−baseline manip −0.689 (d −0.51,
  p=0.0017)**; autonomy-composite rows +0.578 (p=0.0003) and +0.489 (p=0.0013);
  pressure−baseline autonomy −0.222 (p=0.160).
- **Multiple-comparison correction added** (was absent): Holm–Bonferroni over the
  6-test confirmatory family for the frontier judge → 4 autonomy-instruction
  contrasts adjusted **p ≤ 0.0052**; 2 pressure−baseline contrasts adjusted **p =
  0.28**. (Computed analytically from the reported permutation p-values; flagged for
  re-derivation in-code — see §4.)
- **New cross-judge agreement table `tab:xjudge`** (qwen vs claude, 180 items), from
  `judge_sensitivity_summary.md` §C: all κ ≈ 0 (0.000–0.209); composite manipulation
  Pearson r=0.165; per-dimension means showing the 10–40× scale gap.
- **New by-model table `tab:claude_bymodel`** (frontier judge manipulation): qwen3:4b
  −1.800 (p=0.0008) / −1.333 (p=0.0031); gemma null; llama same-direction ns. Plus
  the qwen-self-scoring detail (manipulation=0, SD=0, 14/15 scenarios) vs Claude's
  pressure 2.87 → pressure_autonomy 1.07 → autonomy 0.73.
- **Consensus (two-judge) numbers added** in `sec:res_evaldep` from §D: autonomy−baseline
  manip −0.367 (p=0.0010); pressure_autonomy−pressure manip −0.389 (p=0.0021).
- **Descriptive frontier-judge means added** (baseline 1.87 / pressure 2.20 /
  autonomy 1.18 / pressure_autonomy 1.40 out of 8).
- Deterministic-audit rates unchanged (1.1% urgency, 0.0% emotional, 1.7% authority,
  99.4% tradeoff disclosure) but **reinterpreted** (see §3).
- Secondary open-weight agreement numbers retained; `authority_social_pressure`
  now cited from the wired table as **17%** (was **13%** in old prose — see §4/A-4
  in audit; still to be reconciled against `judge_agreement.csv`).

## 3. Deleted or weakened claims

- **Deleted:** "We report a preregistered **null result**" as *the* contribution
  (Intro); "genuine, **verified null result**" (Conclusion); "**three independent
  judges** … no detectable effect" (Conclusion — was both a miscount and false, since
  the frontier judge found an effect).
- **Weakened:** "independent corroboration via deterministic audit" → the keyword
  audit now corroborates only that *overt lexical* manipulation is rare, consistent
  with **both** judges; it no longer props up the null.
- **Weakened:** "All three models overwhelmingly preserved disclosure … even under
  pressure" (behavioral claim) → now attributed to the open-weight judge's
  measurement and explicitly not asserted as judge-independent behavior.
- **Weakened:** "cross-validated against two additional independent judges" → now
  "cross-compared, with low agreement on the discriminating dimensions."
- **Replaced:** old robustness subsection (exclude 20 priority items, qwen-only:
  diff 0.029, CI [0.000,0.088], p=1.000) is **removed from Results** in favor of the
  **E-analysis** (exclude 48 high-disagreement items, consensus → null) *with an
  explicit circularity caveat* that it shows concentration, not disappearance.
- **Removed** the "forthcoming revision of this paper" hedge from the abstract; the
  frontier-judge result is now in this paper.

## 4. Unresolved issues remaining before arXiv

**Scientific / must-address:**
1. **No human ground truth.** The human-adjudication arm has **0 collected ratings**;
   it is excluded from the evidentiary basis and stated to validate nothing. Whether
   to collect ≥15–20 human labels before submission (to anchor which judge is closer)
   is a PI call — currently the paper honestly claims only disagreement.
2. **Holm correction is computed by hand** from reported p-values. Re-derive it inside
   the analysis code and confirm the adjusted values before submission.
3. **`authority_social_pressure` 17% vs 13%** discrepancy between the wired table and
   old prose is resolved in the manuscript toward the JSON (17%), but the underlying
   `reports/judge_agreement.csv` should be checked to confirm which sample/def is
   canonical (audit §A-4).
4. **`item-0049` token budget** (judge 4096 vs generation 3072) — confirm the judge
   ceiling and that the two budgets are deliberately different (audit §E-2).
5. **Figure caption metric** (`fig:judge_agreement` says "weighted Cohen's kappa")
   vs the wired agreement tables (Pearson/Spearman/MAE) — confirm the heatmap PNG
   actually plots kappa (audit "Minor structural nits").

**Content still stubbed (no results invented):**
6. `appendix/additional_results.tex` per-contrast zero-difference counts
   `[PLACEHOLDER PROSE]`; `appendix/qualitative_examples.tex` and
   `appendix/implementation_details.tex` are placeholder stubs to be filled from the
   frozen run before submission.
7. **No figure exists for the frontier-judge result or the cross-judge divergence**
   (presented as tables only). Adding those plots would need a plotting run
   (deliberately not done — no new results this pass).

**Citations:**
8. Verify all 7 `references.bib` entries against the live sources, especially
   `pombal2026rubricspb` (arXiv 2604.06996), `anthropic2025agentic` (companion id
   2510.05179, "16 models"), `cdt2026darkpatterns` ("37 patterns"),
   `needham2025evalaware` ("AUC 0.83 / 0.92").

**Title / build:**
9. **Title not chosen** — `paper/main.tex` carries a *provisional* title and a
   commented list of 5 candidates; the author must pick one.
10. **No PDF built** — no TeX engine in this environment. Source is verified
    structurally compile-ready (all `\input`/`\ref`/`\cite`/graphics resolve); build
    on Overleaf/tectonic (steps in the handoff message) and fix only real layout
    errors surfaced there.

## 5. Files touched this pass
Rewritten: `abstract, introduction, related_work, methods, results, discussion,
limitations, conclusion` (`sections/`), `ethics` + `reproducibility` (edits),
`main.tex` (title). Added earlier (readiness commit `9f70aaa`): `paper/figures/*`,
`paper/tables/*`, `paper/appendix/{additional_results,qualitative_examples,
implementation_details}.tex`, `PAPER_SUBMISSION_AUDIT.md`.
