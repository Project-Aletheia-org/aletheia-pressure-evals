# arXiv Submission Checklist

Status as of this writing: `paper/main.tex` compiles cleanly (pdflatex +
bibtex + pdflatex x2, no undefined references, no errors) to a 24-page
PDF, with the evaluator-sensitivity result as the paper's headline
finding, matching the README. This document is the remaining steps to get
it onto arXiv -- none of them can be done by an agent, all require the
account holder.

## 1. Category

**Recommended primary: `cs.AI`** (Artificial Intelligence). This is a
behavioral evaluation of language models under a controlled prompt
manipulation, with a methodological finding about LLM-as-judge validity
-- squarely cs.AI territory. "Neuroethics" is not an arXiv category (it's
a term from bioethics/neuroscience-ethics discourse, not computer
science); this paper has no neuroscience content, so it should not be
framed or tagged as such.

**Recommended cross-list: `cs.CY`** (Computers and Society), because a
manipulation/dark-patterns rubric and its ethics section are also
squarely a computers-and-society contribution. `cs.CL` (Computation and
Language) is a plausible second cross-list instead of/alongside `cs.CY`
given the LLM-judge and text-scoring methodology, if the category budget
allows only two.

## 2. Account and endorsement

- Create (or use an existing) arXiv account at arxiv.org with a real,
  identifiable email address -- arXiv requires this for the account of
  record; a privacy-relay address will not work for verification.
- First-time submitters to `cs.AI` typically need **endorsement** from an
  existing arXiv author in that category, unless the account already has
  a sufficient submission history. If no endorser is available, arXiv's
  own auto-endorsement process (based on institutional email domains) may
  apply; check arxiv.org/help/endorsement for current rules, since arXiv
  changes this policy periodically.

## 3. What to upload

- Prefer **source upload** (not PDF-only): a `.tar.gz` of `paper/main.tex`,
  `paper/references.bib`, `paper/sections/*.tex`, `paper/appendix/*.tex`,
  and `paper/figures/*.png` (the `.png` figures are already vendored into
  `paper/figures/`, mirroring `reports/figures/`, specifically so this
  bundle is self-contained). arXiv's TeX Live is usually current enough
  for this document's package set (`geometry`, `graphicx`, `booktabs`,
  `amsmath`, `hyperref`, `natbib`, `authblk`, `microtype`); if arXiv's
  compiler errors on a package version, the fallback is compiling locally
  and uploading the resulting PDF directly.
- Do not upload `.aux`/`.bbl`/`.log`/`.out` build artifacts -- arXiv
  recompiles from source. If bundling a pre-generated `.bbl` instead of
  `references.bib` + letting arXiv run bibtex, regenerate it fresh
  immediately before packaging (`bibtex main` in `paper/`) so it matches
  the current `.bib`.

## 4. License

arXiv requires selecting a distribution license at submission time,
separate from the repository's MIT license (which covers the code, not
the manuscript text). Common choices: **CC BY 4.0** (arXiv's suggested
default, permits reuse with attribution) or **arXiv's own
non-exclusive license to distribute**. Pick one before submitting; no
default was assumed in this repo.

## 5. Abstract and metadata

- arXiv's abstract field has a length limit (currently 1,920 characters);
  the current `paper/sections/abstract.tex` should be checked against
  this at submission time and trimmed if needed for the web-form field
  specifically (the in-PDF abstract can stay as written).
- Author field: matches `paper/main.tex`'s `\author{Sumeet Musfirah}`.
  arXiv's author-identity conventions (ORCID linking, etc.) are optional
  but worth setting up if not already done.

## 6. Before hitting submit

- Recompile locally one more time from a clean checkout to confirm
  nothing broke between this checklist being written and submission time.
- Read the PDF front-to-back once as a stranger would -- this checklist
  cannot verify prose quality or catch a misreported number, only that
  the document builds and the cross-references resolve.
- Decide, and say so explicitly if asked by a reviewer or reader, whether
  this is going up as a **preprint with an openly stated open item**
  (human adjudication 0/15 complete, third non-Anthropic judge not yet
  run -- both already stated in `paper/sections/limitations.tex` and
  `paper/sections/ethics.tex`) rather than a fully closed study. That is
  the current state of the evidence and this document does not recommend
  waiting on either to post a v1 preprint; arXiv supports posting a v2
  later when the human-adjudication layer completes.
