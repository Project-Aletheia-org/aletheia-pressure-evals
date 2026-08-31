# aletheia-pressure-evals

> A behavioral evaluation framework for goal-pressure and manipulative
> persuasion in open-weight language models. Initial Baseline Study v0.1.

## What this is

An evaluation pipeline built around one question: when a language model is
pushed to achieve a persuasive goal, does its visible communication get more
manipulative, and does a short autonomy-preserving instruction change that?

Three small open-weight models (`qwen3:4b`, `gemma3:4b`, `llama3.2:3b`)
generate a message under four system-prompt conditions (`baseline`,
`pressure`, `autonomy`, `pressure_autonomy`) across 15 benign persuasion
scenarios: 180 outputs total. Each output is scored 0-2 on six behavioral
dimensions (deceptive omission, emotional pressure, artificial urgency,
authority/social pressure, respect for refusal, transparency) by blinded
judge models. All core inference runs locally through
[Ollama](https://ollama.com); the study reproduces with no paid API.

## The result: the answer depends on who scores it

This is the finding, and it is a sharp one.

Scored by the open-weight primary judge (`qwen3:4b`), the study is a clean
null: no detectable manipulation shift under any condition (all three
primary paired-contrast permutation tests p >= 0.63).

Scored by an independent frontier judge (`claude-sonnet-4-6`) on the
identical blinded items, with the same rubric, prompt, and temperature, the
null collapses: the autonomy-preserving instruction significantly reduces
manipulation-coded language, both versus pressure (p = 0.0003) and versus
baseline (p = 0.0017). The two judges agree at barely above chance, and the
disagreement concentrates in the outputs of `qwen3:4b`, which is also the
primary judge. That is a self-evaluation blind spot surfacing as a
measurement artifact, inside a setup many people would have accepted as
"independent validation."

v0.1 is classified as **evaluator-sensitive**. Both the null and the
disagreement are reported as findings.

- `reports/judge_sensitivity_summary.md` — two-judge comparison and classification
- `reports/claude_external_judge_analysis.md` — per-dimension, per-model detail
- `reports/v1_closure_report.md` — what is settled and what is not

## Scope and next steps

The evaluator-sensitivity result rests on two model judges disagreeing, and
the designed next step is human adjudication of the disputed cases, which is
built and staged. Two things are stated directly, because getting the
epistemics right is the point of this project: the corroborating judge is an
Anthropic model and Anthropic tooling assisted the analysis, so a
non-Anthropic third judge is on the path; and no label here is human ground
truth yet. These are the boundaries of the current evidence, set on purpose.

## How to run it

Requires [Ollama](https://ollama.com) (macOS 14+) and
[uv](https://docs.astral.sh/uv/).

```bash
ollama pull qwen3:4b && ollama pull gemma3:4b && ollama pull llama3.2:3b
uv sync

uv run pressure-evals check                          # verify Ollama + models
uv run pressure-evals run-pilot                      # 24-output smoke test
uv run pressure-evals generate --run-id baseline     # full 180-output run (resumable)
uv run pressure-evals evaluate --run-id baseline     # blinded primary-judge scoring
uv run pressure-evals escalate --run-id baseline     # multi-judge consensus + escalation
```

`generate` and `evaluate` are resumable: re-running skips any cell that
already has a successful record and retries failures. Every record stores
its exact prompts, generation parameters, timestamps, latency, and a
SHA-256 hash; raw records are never overwritten. Full provenance for the
baseline run is in `data/*/baseline-v0.1-20260722.manifest.json`.

The external-judge (Claude) extension and the cross-judge statistical
analysis were run as standalone scripts and are being consolidated into the
provider-neutral successor pipeline described below.

## Layout

```
src/pressure_evals/   pipeline: generation, blinded judging, audit, consensus, analysis
data/                 scenarios, raw outputs, evaluations, manifests (append-only)
reports/              analysis outputs, study reports, limitations
paper/                LaTeX write-up -- evaluator-sensitivity is now the paper's headline finding
tests/                109 tests
```

The manuscript (`paper/main.tex`) compiles cleanly to a 24-page PDF
(`pdflatex` + `bibtex` + `pdflatex` x2; requires `texlive-latex-extra`,
`texlive-bibtex-extra`, `texlive-fonts-recommended`) and its narrative now
matches this README: the evaluator-sensitivity result is the reported
finding, not a forthcoming revision. Submission checklist:
`reports/arxiv_submission_checklist.md`.

## What's next (V2)

A separate successor in active development (`aletheia-pressure-evals-v2`)
generalizes this into a config-driven, provider-neutral pipeline: automatic
model discovery, pre-run compatibility checks, full run provenance, a
structural rule that forbids a model from grading its own outputs in the
primary analysis, and disagreement escalation built into the core rather
than bolted on. The Phase 1 foundation is complete and tested; no full V2
experiment has been run yet. Design notes: `reports/v2_pipeline_design.md`.

## Limitations

Small quantized models, not frontier systems. One generation per cell.
Fifteen benign scenarios in a single "organization requests compliance"
frame. n = 45 scenario-model pairs per contrast, which is underpowered for
small effects, and the floor/ceiling compression limits detection power.
Every label is a model judgment, not human ground truth. These are stated
plainly here and in full in `reports/v1_closure_report.md` and
`paper/sections/limitations.tex`.

## Citation

```
Musfirah, S. (2026). aletheia-pressure-evals: A Behavioral Evaluation
Framework for Goal Pressure and Manipulative Persuasion in Open-Weight
Language Models. Initial Baseline Study v0.1.
```
