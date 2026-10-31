# V2 Reliability Audit — DataForge V3.1 Phase 1A

Method: 7 frozen tasks, single DeepSeek model (`deepseek-ai/DeepSeek-V4.1-Flash`), locked protocol,
local Docker backend, oracle/no-op controls, fresh-sandbox regrade, repeat-control stability.

## Verdict
SWE-bench Pro V2's grader is reliable when the agent actually runs. Across the 7 tasks:
- oracle 7/7 pass, no-op 7/7 fail (no spurious passes, no spurious rejections of the reference),
- 6 valid DeepSeek runs: 5 pass, 1 honest fail (66/67),
- 7/7 regrades agreed with the original verdict,
- flipt oracle stable at 1.0 across 3 runs.

## The one task-level reliability failure
nodebb original: reward 0.0 with **the agent never having run** (0 model responses, no trajectory),
and a captured `model.patch` that was **166 KB of pre-existing Redis state, zero code**. The
subsequent fresh-sandbox regrade applied nothing (null replay) but still reported 0.0. A
separately-labelled recovery rerun scored 1.0.

## Why the grader itself looks sound
Where evidence was produced, parser output matched raw test output exactly (verified for Go text,
Go json, pytest, jest). No contradictory statuses, no dropped required identifiers, no
grader/runner disagreement.

## Where reliability breaks (harness boundary)
1. patch capture includes untracked image state → contaminated diffs;
2. replay silently no-ops on such diffs but still yields a reward;
3. no check that the agent ran → infrastructure failure indistinguishable from model failure;
4. unpinned agent dependency (mini-swe-agent 2.4.6) incompatible with the harness;
5. egress sidecar stalls the first model call intermittently.

## Severity ranking
See `reports/PHASE_1A_FINAL_REPORT.md` §10. The highest-value fixes are patch scoping, making
replay fail loudly, and asserting the agent ran — all low-complexity, high-impact.
