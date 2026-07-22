# Computational Costs

All runs executed locally via Ollama on a single Apple Silicon Mac. No paid
APIs, no cloud infrastructure. Figures below distinguish **wall-clock span**
(calendar time from first to last record, including any interruptions) from
**continuous compute time** (actual model-call time), since several runs in
this study were manually stopped and resumed.

## Generation (Initial Baseline Study v0.1, 180 outputs)

Ran continuously, no interruptions.

| Model | Calls | Total compute (s) | Avg latency (s) |
|---|---|---|---|
| qwen3:4b | 60 | 2756.7 | 45.9 |
| gemma3:4b | 60 | 592.0 | 9.9 |
| llama3.2:3b | 60 | 454.1 | 7.6 |
| **Total** | **180** | **3802.8 (63.4 min)** | -- |

Matches the generation manifest's wall-clock span exactly (no idle time).

## Primary judge evaluation (qwen3:4b, 180 items)

This run was manually interrupted and resumed multiple times (to fix the
`max_tokens` config, then again for the item-0049 rescue), so wall-clock
span substantially overstates actual compute time.

- Wall-clock span: 2026-07-22T11:47:06Z -> 2026-07-22T22:25:36Z (~10.6 hours)
- Approximate continuous compute time (sum of inter-record gaps under 5
  minutes, i.e. excluding manual stop/resume idle periods): ~424 minutes
  (~7.1 hours)
- 7 gaps of 5+ minutes (idle time between manual interventions), totaling
  ~3.6 hours
- `EvaluationRecord` does not currently store a per-call `latency_seconds`
  field (unlike `GenerationRecord`); the above is inferred from consecutive
  `evaluated_at` timestamps, not a direct per-call measurement -- noted as
  a real gap in the schema, not backfilled retroactively to avoid
  fabricating a number the pipeline didn't actually record.
- item-0049 rescue (separate one-off call, outside the main run):
  200.6 seconds, single attempt at `max_tokens=8192`.

## Secondary-judge sample (60 items each)

Ran continuously, no interruptions.

| Judge | Elapsed (min) | Avg per item (s) |
|---|---|---|
| gemma3:4b | 22.2 | 22.2 |
| llama3.2:3b | (recorded once the run completes; see the sample manifest) | -- |

## Total disk/model footprint

- `qwen3:4b`: ~2.5 GB (Q4_K_M quantization)
- `gemma3:4b`: ~3.3 GB (Q4_K_M)
- `llama3.2:3b`: ~2.0 GB (Q4_K_M)
- Total model weights: ~7.8 GB
- No GPU cluster, no paid inference API calls, no cloud storage costs.
