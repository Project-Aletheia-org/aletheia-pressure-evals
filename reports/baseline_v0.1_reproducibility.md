# Initial Baseline Study v0.1: Reproducibility

## Repository and commit

- Repository: https://github.com/Project-Aletheia-org/aletheia-pressure-evals
- Commits containing the full analysis: see `git log` on `main`; the
  generation run's exact commit is recorded in
  `data/raw_outputs/baseline-v0.1-20260722.manifest.json`'s `git_commit`
  field, and each evaluation manifest records its own `git_commit`.

## Environment

- Hardware: Apple Silicon Mac (local, no cloud infrastructure)
- Inference: Ollama (version recorded in each run manifest's
  `ollama_version` field)
- Models (with digests recorded in manifests): `qwen3:4b`, `gemma3:4b`,
  `llama3.2:3b`, all Q4_K_M quantization
- Python: managed via `uv`; see `pyproject.toml` / `uv.lock` for exact
  dependency versions

## Exact commands

```bash
uv sync
uv run pressure-evals check
uv run pressure-evals generate --run-id baseline-v0.1-20260722
uv run pressure-evals evaluate --run-id baseline-v0.1-20260722
uv run pressure-evals evaluate-sample --run-id baseline-v0.1-20260722 --judge-model gemma3:4b
uv run pressure-evals evaluate-sample --run-id baseline-v0.1-20260722 --judge-model llama3.2:3b
uv run pressure-evals escalate --run-id baseline-v0.1-20260722
```

All four generation/evaluation commands are resumable: rerunning with the
same `--run-id` skips already-successful cells and retries only failures.

## item-0049 rescue (not reproducible via the standard CLI)

One evaluation item (`item-0049`: scenario `s11_course_continuation`,
model `qwen3:4b`, condition `pressure_autonomy` -- see
`data/evaluations/baseline-v0.1-20260722.blinding_key.json` for the exact
mapping) permanently failed at the standard `max_tokens=4096` ceiling
(empty response, token exhaustion) and was rescued with a one-off script
using `max_tokens=8192`, identical judge/rubric/prompt/temperature
otherwise. This is not part of the standard CLI path; the rescue logic is
recorded in `reports/research_log.md` and `reports/protocol_deviations.md`
for exact reproduction if needed.

## Random seeds

- Generation: `random_seed: 42` (temperature 0.7, top_p 0.9 -- generation
  itself is stochastic; exact text will differ on rerun, but the pipeline,
  scenario order, and analysis methodology are fully deterministic given
  the same generated data)
- Evaluation blinding order: seed 42 (deterministic given the same
  generation file)
- Secondary-judge sample selection: seed 42 (deterministic)
- Judge temperature: 0 (evaluation scoring is deterministic given
  identical model weights, though Ollama/hardware nondeterminism at the
  numerical level is possible and not separately verified)
- Bootstrap/permutation analysis: seed 42, 5,000/10,000 resamples

## What is and isn't bitwise-reproducible

- **Bitwise reproducible**: the analysis pipeline given the saved raw
  data (all `data/raw_outputs/*.jsonl`, `data/evaluations/*.jsonl` files
  are committed).
- **Not bitwise reproducible**: re-running generation or evaluation from
  scratch will produce different response text (temperature > 0 for
  generation) and possibly different judge scores (a re-run at temperature
  0 for the judge should be close but Ollama does not guarantee bit-exact
  determinism across runs/hardware).
