# PAPER_SUBMISSION_AUDIT.md

Scientific + submission-readiness audit of `paper/` against the final analysis
outputs in `reports/`. Generated 2026-09-15. **No experiment was rerun and no
scientific result was changed.** Repo was made safe/buildable and existing final
assets were wired in (see "Build/wiring changes already applied", bottom).

Anchor sources for every number below:
`reports/baseline_v0.1_executive_summary.md`,
`reports/claude_external_judge_analysis.md`,
`reports/judge_sensitivity_summary.md`,
`reports/tables/*.json`. Line refs into `paper/sections/*.tex` are 1-indexed.

---

## WHAT THE DATA ACTUALLY SUPPORT

Reconstructed independently from `reports/`, not from the current manuscript.

### 1. Strongest defensible one-sentence finding
With the generated text, rubric, blinding, and judge prompt held **identical**,
the study's headline conclusion — *does an autonomy-preserving instruction reduce
manipulation-coded language?* — **flips from a clean null under the small
open-weight judge `qwen3:4b` (all three contrasts p ≥ 0.63) to a significant,
moderate effect under the frontier judge `claude-sonnet-4-6`** (autonomy − baseline
manipulation −0.689, Cohen's d ≈ −0.51, p = 0.0017; pressure\_autonomy − pressure
−0.800, d ≈ −0.59, p = 0.0003), **and the null is largest exactly where the
open-weight judge scores its own family's outputs** (`qwen3:4b`-as-judge assigns
`qwen3:4b`-as-subject manipulation = 0, SD = 0 in 14/15 scenarios across all four
conditions). The primary empirical result is therefore **evaluator sensitivity / a
self-evaluation floor**, not a substantive null about model behavior.

### 2. What we cannot conclude
- **Not** that these models (or LLMs generally) resist manipulation under goal
  pressure — scenarios are benign, one generation per cell, scores floor/ceiling
  compressed.
- **Not** that the autonomy instruction robustly "works" as a behavioral fact: it
  is one frontier judge's scoring, with no human ground truth, and the effect is
  concentrated in a single subject model (`qwen3:4b`; `gemma3:4b` null,
  `llama3.2:3b` same direction but ns).
- **Not** that pressure increases manipulation: `pressure − baseline` is ns under
  every judge (Claude +0.333, p = 0.138 — trends toward *more*, but not
  significant).
- The **"exclude disagreement items → null"** analysis (E) is **not** an
  independent robustness check — its exclusion rule references the outcome being
  tested (see §E-circularity).
- The deterministic keyword audit does **not** independently corroborate "no
  manipulation" — it is blind by construction to what a frontier judge detects
  (emotional-pressure language 0.0% by keyword vs Claude mean 0.728/2 on that
  dimension).

### 3. Why the evaluator disagreement is itself scientifically interesting
It is a concrete, quantified instance of a **self-evaluation blind spot** surfacing
*inside a design that many would accept as independent validation* (a blinded
multi-judge ensemble). The same model family, used as both subject and primary
judge, produces zero-variance floor scores for its own generations that an
independent judge does not share; cross-judge agreement is at or near chance on
every dimension (all Cohen's κ ≈ 0; composite manipulation Pearson r = 0.165), and
the two judges' raw scales differ 10–40×. That is a **measurement-validity result
about the now-common practice of using small open-weight LLMs as judges** — more
transferable, and more publishable, than the original null.

### 4. What would materially strengthen the paper vs. what can be deferred
**Materially strengthens (do before making strong claims):**
1. **Human adjudication** on the blinded 15/20-item packet — currently **empty
   (0 filled ratings)** — to anchor *which* judge is closer to ground truth.
   Without it the paper can show judges disagree but cannot say who is right.
2. **≥1 more independent judge** (the DeepSeek-V3.1 OpenRouter judge is already
   coded but **unrun** — see §Dirty-files) to show the effect is not a
   Claude-specific idiosyncrasy.
3. **Replicates > 1 per cell** to separate a true null from cancelled variance
   (schema already supports `replicate_id`).
4. A **disagreement definition that does not reference the outcome**, to make the
   exclusion (E) analysis a genuine robustness check.

**Reasonably deferred to follow-up work:** higher-stakes / adversarial scenarios;
larger or additional model families; multilingual; multi-turn; longitudinal
re-measurement. These are scope extensions, not gaps in the current claim.

---

## THE CENTRAL PROBLEM: the manuscript still tells the wrong story

The final analysis (`reports/judge_sensitivity_summary.md`) classifies the study
**"evaluator-sensitive."** The manuscript still leads with the **null** and
demotes the evaluator-sensitivity to a deferred parenthetical. Every place this
happens:

| Loc | Current text | Problem |
|---|---|---|
| `abstract.tex:20-25` | "A subsequent extension … being integrated into a **forthcoming revision of this paper**" | The paper's actual finding is treated as *not in this paper*. The headline (null) is contradicted by the repo's own final analysis. |
| `introduction.tex:74-77` | "We report a preregistered **null result**" as the contribution | Overclaims the null as *the* finding; buries the evaluator-sensitivity. |
| `results.tex` (whole) | Only the qwen-judge null is in Results; Claude analysis absent | The significant frontier-judge contrasts (p = 0.0003–0.0017) never appear in Results. |
| `discussion.tex:406-410` | Judge sensitivity listed as one of four *speculative* "why might the effect be absent" bullets | It is no longer speculative — it is measured. Should be promoted from hypothesis to result. |
| `conclusion.tex:515-517` | "three models, and **three independent judges**, we find **no detectable effect**" | Factually contradicted: the third truly-independent judge (Claude) **did** find an effect. See §Overclaims C-1. |

**Required (do not silently resolve — this is a scientific-framing decision for
the PI):** decide whether v1 is (a) the honest null *plus* the evaluator-sensitivity
as co-headline, or (b) reframed so evaluator-sensitivity is the primary
contribution. Everything below assumes the paper must at minimum stop asserting a
clean null as the finding.

---

## A. Contradictions between sections and the final analysis

- **A-1 (severe).** Abstract/Intro/Conclusion assert a verified null; `reports/
  claude_external_judge_analysis.md` §3 and `reports/judge_sensitivity_summary.md`
  §B/D show two of three contrasts significant under Claude and still significant
  (attenuated, p < 0.01) under the two-judge consensus. The manuscript's own
  repository refutes its headline.
- **A-2.** `conclusion.tex:515` "three independent judges … no detectable effect."
  The three judges that produced the null are qwen3:4b + gemma3:4b + llama3.2:3b
  (all small open-weight; the latter two only on a 60-item subset). Claude is a
  *fourth* judge and the only frontier one, and it is non-null. Sentence is both a
  miscount and a false implication.
- **A-3.** `results.tex:316-323` frames the deterministic audit as "independent
  corroboration" of the null. It corroborates the *keyword floor* only; the
  frontier judge, on identical text, is far from floored (manipulation means
  1.18–2.20/8 vs qwen 0.04–0.11). Recharacterize as "corroborates that overt
  keyword-level manipulation is rare," not "corroborates absence of manipulation."
- **A-4 (verify).** `results.tex:352` states `authority_social_pressure` exact
  agreement **13%** on the 60-item sample; `reports/tables/judge_agreement_
  excluding_missing_evidence.json` gives **16.7%** (now Table `tab:dim_agreement`).
  Likely a full-sample vs excluding-missing-evidence difference — reconcile against
  `reports/judge_agreement.csv` and make the text and the wired table cite the same
  computation. (`artificial_urgency`: text 87% vs JSON 86.4% — rounding, fine.)

## B. Places still implying a simple pressure-effect / null story
- `abstract.tex:14-20`; `introduction.tex:74`; `results.tex:257` ("no detectable
  effect"); `conclusion.tex:511-519`; `discussion.tex:376-381`. All predate the
  Claude analysis and must be reconciled with §A-1.
- `ethics.tex:504-507` and the reproducibility framing call the Claude judge an
  "optional extension … reported separately from the core findings." If
  evaluator-sensitivity becomes the finding, the frontier judge is **core**, not
  optional — and the "no paid API required" claim needs the caveat in §COI/repro.

## C. Claims stronger than the evidence
- **C-1.** "verified null result" (`conclusion.tex:517`, `introduction.tex:74`).
  Verified only under one judge family that includes the subject model. Downgrade
  to "judge-conditional null."
- **C-2.** `discussion.tex:379-381` "All three models overwhelmingly preserved
  disclosure … even under explicit pressure." This is a **behavioral** claim
  resting on a judge that scores its own family at a flat zero. Attribute to the
  measurement, or support with the deterministic audit only (which is keyword-level
  and cannot see subtle omission).
- **C-3.** Abstract "cross-validated against two additional independent judges" —
  the 60-item secondary judges *agree poorly* with the primary on the discriminating
  dimensions (`deceptive_omission` exact agreement 8.3%, `authority_social_pressure`
  16.7%; Table `tab:dim_agreement`). "Cross-validated" overstates; "cross-compared,
  with low agreement on the discriminating dimensions" is accurate.

## D. Missing numerical results needed to support statements
- **D-1.** Results claims "39–43 of 45 pairs show zero difference"
  (`results.tex:288-291`) and points to `Appendix~\ref{app:additional}`, which did
  not exist. I created the appendix stub; the **per-contrast zero-difference counts
  must be filled** from `reports/baseline_v0.1_results.{csv,json}` (marked
  `[PLACEHOLDER PROSE]` in `appendix/additional_results.tex`).
- **D-2.** The entire **Claude-judge result table** (contrasts, d, CI, p; by-model
  breakdown) has no home in the manuscript. It exists in
  `reports/claude_external_judge_analysis.md` §3–3.2 and must become a Results
  table if the finding is promoted.
- **D-3.** Cross-judge agreement (qwen vs claude κ per dimension;
  `reports/judge_sensitivity_summary.md` §C) is central to the evaluator-sensitivity
  claim and is not tabulated in the paper.
- **D-4.** `qualitative_examples.tex` and `implementation_details.tex` are
  placeholder stubs; exact digests/seeds/token budgets and verbatim example outputs
  must be transcribed from `data/raw_outputs/*.manifest.json`,
  `reports/computational_costs.md`, and the frozen run before submission.

## E. Consistency of sizes / names / p-values / procedures
- Sample sizes **consistent**: 180 total; n = 45 scenario-model pairs per pooled
  contrast (15×3); 60-item tri-judge overlap; 89 flagged → 20 priority. Matches
  across methods/results/exec summary.
- Model names **consistent** (`qwen3:4b`, `gemma3:4b`, `llama3.2:3b`); condition
  names consistent (baseline/pressure/autonomy/pressure\_autonomy).
- Procedures **consistent**: 5,000-resample scenario-blocked bootstrap; 10,000
  sign-flip permutations; seed 42; scenario-clustered OLS as exploratory.
- **E-1 (multiple comparisons).** `limitations.tex:462-465` acknowledges 3
  contrasts × 2 outcomes × pooled/per-model but the paper applies **no correction**
  (no Bonferroni/Holm/FDR). Fine for the qwen null (nothing significant to inflate),
  but if the Claude contrasts are promoted (p = 0.0003–0.0017, several below any
  reasonable corrected threshold anyway), state the correction explicitly.
- **E-2 (verify).** `methods.tex:195-198` cites a "standard **4096**-token ceiling"
  for the failed item rescue, while generation uses `max_tokens=**3072**`
  (`methods.tex:169`). Confirm the *judge* ceiling is 4096 and that the two budgets
  are deliberately different (generation vs evaluation), then say so.
- **E-3 (CI reproducibility).** `reports/claude_external_judge_analysis.md` §1
  notes the **original bootstrap-CI script is not preserved**, so CIs recompute to
  slightly different bounds (e.g. [−0.089,+0.089] vs published [−0.111,+0.111]) at
  the same seed. Disclose this, or re-run all CIs with the committed
  `analyze.scenario_blocked_bootstrap_ci` and update Table `tab:contrasts` so the
  paper's numbers match a script that exists in the repo.

## F. Separation of observed behavior vs evaluator disagreement
- Currently **conflated.** Abstract/Discussion move between "models did not become
  manipulative" (behavior) and "the judge detected no manipulation" (measurement)
  as if identical. The paper's own finding is that these come apart. Add an explicit
  framing sentence early (Intro) that every score is a *measurement by a specific
  judge*, and reserve behavioral claims for where judges agree or human/deterministic
  evidence backs them.

## G. Human-adjudication arm — exact status and dependence
- **Status: unstarted.** `reports/human_adjudication_blinded_15.*` contains the
  blinded packet but **0 filled ratings**; the unblinding key exists (private,
  gitignored).
- **Dependence: none for the current results.** `methods.tex:207-210` states the
  planned human sample was *replaced* by the secondary-judge sample before any human
  annotation began; results depend on model judges only. So the paper does **not**
  currently rest on human data — but that also means **no human ground truth exists
  to adjudicate the qwen-vs-Claude disagreement**, which is the single biggest
  evidential gap (see §WHAT-THE-DATA/4-1). The manuscript must not imply human
  validation occurred (it did not).

## H. E-analysis circularity — exact disclosure required
- `reports/judge_sensitivity_summary.md` §E: excluding the 48/180 "high-disagreement"
  items yields an all-null result, **but the exclusion reasons
  (`score_range≥2`, `primary_secondary_manipulation_diff≥3`,
  `top_5pct_consensus_manipulation`, …) are partly defined by the very
  qwen-vs-Claude divergence being tested.** Excluding them mechanically removes the
  items that carry the signal.
- **Required limitation text (verbatim intent):** "Excluding high-disagreement
  items is not an outcome-independent robustness check; because the exclusion
  criteria reference cross-judge divergence and consensus manipulation level, the
  resulting null shows the effect is *concentrated in the disagreement-flagged
  subset*, not that it disappears under a neutral filter. Distinguishing a true
  concentrated effect from an exclusion artifact requires a disagreement definition
  that does not reference the tested outcome." The current manuscript's robustness
  section (`results.tex:334-344`) reports a *different* exclusion (20 priority items,
  qwen-only) and **must not** be conflated with the E analysis.

## I. COI / disclosure / reproducibility / data-release before arXiv
- **I-1 (COI, must add).** `qwen3:4b` is simultaneously a **subject model and the
  primary judge** — the central confound and the mechanism of the finding. State it
  as a conflict/limitation in its own right, not only as multi-judge motivation.
- **I-2 (paid-API caveat).** `reproducibility.tex` and `ethics.tex` say the core
  study needs no paid API. True for the null; **false for the central finding**,
  which requires the `claude-sonnet-4-6` judge ($3.36, per
  `reports/claude_external_judge_analysis.md`). If evaluator-sensitivity is
  promoted, add: "reproducing the central finding requires a paid frontier judge."
- **I-3 (AI-assist disclosure).** Present and adequate (`reproducibility.tex:561-565`).
  Keep.
- **I-4 (data release).** Reproducibility command block omits the external-judge
  path; add the `evaluate`/judge commands that regenerate
  `data/evaluations/*.claude-sonnet-4-6.jsonl` and the sensitivity analysis, or the
  central result is not reproducible from the paper alone.
- **I-5 (repo public-state).** Remote is
  `github.com/Project-Aletheia-org/aletheia-pressure-evals`. Before pushing,
  confirm the private files remain gitignored (verified below) and that the repo is
  actually public as the paper claims.

## J. Citations / related-work claims
- All 7 `\cite` keys resolve to `references.bib` (verified). **Each must still be
  checked against the live source before submission**, especially:
  - `pombal2026rubricspb` — arXiv id **2604.06996** (April 2026); confirm it exists
    and the self-preference-in-rubric claim is stated as cited.
  - `anthropic2025agentic` — cited as a web report with "arXiv companion paper
    2510.05179"; confirm the companion id and that the "goal conflict / threat to
    operation → harmful autonomous action across all models tested" summary
    (`intro`, `related_work`) matches the source's actual claims and model count
    (manuscript says "16").
  - `cdt2026darkpatterns` — confirm "37 patterns across five categories" is exact.
  - `needham2025evalaware` — confirm "Gemini-2.5-Pro AUC 0.83, human 0.92."
- No `\cite` placeholders or undefined keys remain. No "TODO/CITE" markers found in
  the section files.

## K. Anonymity / private-information / security
- **Verified clean for git:** every sensitive file is gitignored and none is tracked
  — `reports/*unblinding_key.csv`, `reports/human_adjudication_blinded_15.*`,
  `reports/qwen_claude_high_disagreement_review.*`, `.env` (holds a live
  `ANTHROPIC_API_KEY`), and backstage docs. `git add -A --dry-run` stages nothing
  private; `git ls-files` shows none tracked.
- **Action before publishing:** the untracked, **not-gitignored** files
  `src/pressure_evals/openrouter_judge.py` and `tests/test_openrouter_judge.py`
  would be staged by `git add -A`. They contain **no secret** (key is env-only) but
  are unrun WIP for a *paid* third judge — keep them out of the paper commit
  (see §Dirty-files).
- arXiv is not double-blind, so the named author + repo URL are fine. No third-party
  PII in the manuscript or appendices.

---

## Dirty / untracked files (unrelated to the paper — do not commit with it)
`git status` shows an in-progress, **never-run** third-judge extension:
`src/pressure_evals/openrouter_judge.py`, `tests/test_openrouter_judge.py`, a
`judge-openrouter` CLI command in `src/pressure_evals/cli.py`, and an `openai`
dependency in `pyproject.toml`. It adds a **paid** DeepSeek-V3.1-via-OpenRouter
judge. It produced **no result in `reports/`** and touches **no** number in the
paper. It is a legitimate follow-up (the "add a 3rd judge" evidence from
§WHAT-THE-DATA/4-2) but belongs to a future measurement-sensitivity study, not this
commit. **Recommendation:** leave it uncommitted/unstaged; do not `git add -A`.

## Build / wiring changes already applied (safe, non-scientific)
1. Verified `.gitignore` already covers all unblinding keys, the blinded packet,
   `.env`, and backstage docs; confirmed none are tracked and none would be staged.
2. Copied the 5 final rendered figures `reports/figures/*.png → paper/figures/`
   (no regeneration).
3. Transcribed `reports/tables/*.json → paper/tables/{deterministic_audit,
   composite_agreement,dimension_agreement}.tex` (faithful; rounding only).
4. Created the 3 missing appendix files
   (`additional_results.tex` [label `app:additional`, hosts the wired tables +
   the 2 extra figures], `qualitative_examples.tex`, `implementation_details.tex`)
   as **clearly-marked structural stubs** so `main.tex` compiles; narrative left as
   explicit `[PLACEHOLDER]` — **no results invented**.
5. Verified structurally compilable: all 19 `\input` targets exist, all 7 citation
   keys resolve, every `\ref` has a `\label`, all 5 `\includegraphics` files
   present. No TeX toolchain is installed, so **no PDF was built** — the source is
   Overleaf/tectonic-ready.

## Minor structural nits (non-blocking)
- `results.tex:364-369`: the judge-agreement **figure** carries a **table** label
  (`\label{tab:judge_agreement}`) and is referenced as "Table~\ref{...}". It renders
  as a figure. Either relabel to `fig:` or make it an actual table.
- Same figure's caption says "**weighted Cohen's kappa** by rubric dimension," but
  the wired agreement tables (`tab:dim_agreement`, `tab:composite_agreement`) report
  Pearson/Spearman/MAE/agreement-rates, not kappa. Confirm the heatmap PNG actually
  plots kappa and that the metric is consistent between figure and tables.
- Hardcoded section numbers in prose ("Section~4", "Section~3.5", "Section~2.6",
  `limitations.tex`) will silently go stale if sections move; convert to
  `\ref{}`/`\label{}`.
