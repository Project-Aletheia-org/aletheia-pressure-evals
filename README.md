# aletheia-pressure-evals

> Behavioral evaluation framework for goal-pressure and manipulative
> persuasion in open-weight language models. Initial Baseline Study v0.1 is
> complete and **frozen**. Findings are preliminary and specific to the
> models, prompts, and 15 scenarios tested. Do not generalize beyond them.

## What this is

An evaluation pipeline that asks a simple question: when a language model is
pushed to achieve a persuasive goal, does its visible communication get more
manipulative, and does a short autonomy-preserving instruction change that?

Three small open-weight models (`qwen3:4b`, `gemma3:4b`, `llama3.2:3b`)
generate a message under four system-prompt conditions (`baseline`,
`pressure`, `autonomy`, `pressure_autonomy`) across 15 benign persuasion
scenarios: 180 outputs total. Each output is scored 0-2 on six behavioral
dimensions (deceptive omission, emotional pressure, artificial urgency,
authority/social pressure, respect for refusal, transparency) by blinded
judge models. All model inference for the core study runs locally through
[Ollama](https://ollama.com); no paid API is required to reproduce it.

## The finding so far: the result depends on who scores it

Scored by the open-weight primary judge (`qwen3:4b`), the study is a clean
null: no detectable manipulation shift under any condition (all three
primary paired-contrast permutation tests p >= 0.63).

Scored by an independent frontier judge (`claude-sonnet-4-6`) on the
identical blinded items, with the same rubric, prompt, and temperature, the
null does not hold: the autonomy-preserving instruction significantly
reduces manipulation-coded language, both versus pressure (p = 0.0003) and
versus baseline (p = 0.0017). The two judges agree at barely above chance,
and the disagreement concentrates in the outputs of `qwen3:4b`, which is
also the primary judge, consistent with a self-evaluation blind spot.

We classify v0.1 as **evaluator-sensitive** and report both the null and
the disagreement as findings. Full analysis:

- `reports/judge_sensitivity_summary.md` (the two-judge comparison + classification)
- `reports/claude_external_judge_analysis.md` (per-dimension, per-model detail)
- `reports/v1_closure_report.md` (what is settled, what is not)

**Important honesty note:** this finding currently rests on two LLM judges
disagreeing. Human adjudication is designed but **not yet complete**, so no
result here is human-validated. The corroborating judge is an Anthropic
model and Anthropic tooling assisted the analysis; a non-Anthropic third
judge and human scoring are the required next steps.

## How to run it

Requires [Ollama](https://ollama.com) (macOS 14+) and [uv](https://docs.astral.sh/uv/).

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
SHA-256 hash; raw records are never overwritten. Provenance for the frozen
run is in `data/*/baseline-v0.1-20260722.manifest.json`.

The external-judge (Claude) extension and the cross-judge statistical
analysis were run as one-off scripts and are being consolidated into a
provider-neutral successor pipeline (see below); they are not yet
single-command reproducible from this repo.

## Layout

```
src/pressure_evals/   pipeline: generation, blinded judging, audit, consensus, analysis
data/                 scenarios, raw outputs, evaluations, manifests (append-only)
reports/              analysis outputs, the frozen study reports, limitations
paper/                LaTeX write-up (in revision to match the evaluator-sensitive finding)
tests/                109 tests
```

## What's next (V2)

A separate, in-progress successor (`aletheia-pressure-evals-v2`) generalizes
this into a config-driven, provider-neutral pipeline: model discovery,
pre-run compatibility checks, full provenance, a rule that forbids a model
from grading its own outputs in the primary analysis, and disagreement
escalation built in. No full V2 experiment has run yet. Design notes:
`reports/v2_pipeline_design.md`.

## Limitations (short)

Small quantized models, not frontier systems. One generation per cell.
Fifteen benign scenarios in a single "organization requests compliance"
frame. n = 45 scenario-model pairs per contrast; underpowered for small
effects, and the floor/ceiling compression limits detection power. Every
label is a model judgment, not human ground truth. Full list:
`reports/v1_closure_report.md` and `paper/sections/limitations.tex`.

## Citation

```
Musfirah, S. (2026). aletheia-pressure-evals: A Behavioral Evaluation
Framework for Goal Pressure and Manipulative Persuasion in Open-Weight
Language Models. Initial Baseline Study v0.1 (evaluator-sensitive).
```
