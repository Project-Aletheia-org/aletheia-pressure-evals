# Initial Baseline Study v0.1: Executive Summary

**One-paragraph finding:** Across 180 generated messages (15 benign
scenarios x 3 small open-weight models x 4 system-prompt conditions), a
blinded open-weight judge detected **no measurable increase in
manipulation-coded language** when models were instructed to maximize user
agreement ("pressure" condition) versus a neutral baseline, and **no
measurable change** from adding an explicit autonomy-preserving
instruction. Manipulation scores were compressed near the floor (mean
0.04-0.11 of 0-8) and autonomy scores near the ceiling (mean 3.96-4.00 of
0-4) in every condition. This was verified by hand -- the judge is reading
each response individually and producing distinct evidence, not
short-circuiting -- so the null result reflects the models' actual
outputs on this scenario set, not a pipeline failure.

**What we can say:** within these 15 low-stakes scenarios, these three
small open-weight models consistently preserved disclosure and an easy
path to decline, regardless of the pressure framing tested.

**What we cannot say:** that these models (or LLMs generally) resist
manipulation under any goal pressure, in any scenario, as judged by any
evaluator. The scenarios were intentionally benign; a higher-stakes or more
adversarial scenario design might show a different pattern.

**Validation:** 180/180 primary-judge evaluations complete; a 60-item
stratified secondary-judge sample (gemma3:4b, llama3.2:3b) cross-validated
the primary judge; 89 items were flagged for cross-judge disagreement or
audit review, decomposed to 20 genuinely disputed cases recommended for
optional human review (69 remain flagged but handled via sensitivity
analysis rather than treated as resolved).

**Full detail:** `reports/baseline_v0.1_report.md`.
