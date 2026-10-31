# Confirmed Findings — DataForge V3.1 Phase 1A

Classifications: CONFIRMED DEFECT / SUSPECTED DEFECT / AGENT FAILURE / INFRASTRUCTURE FAILURE /
NO ISSUE OBSERVED.

## CONFIRMED DEFECT 1 — NodeBB `model.patch` contaminated by pre-existing untracked image state
See `confirmed_redis_patch_contamination.md`. 166 KB patch composed solely of `appendonlydir/*` Redis
AOF/RDB files baked into the image since 2025-07-07, untracked and not gitignored. Captured by
`git add -A; git diff --cached` in `v2/tooling/locked_mini_swe.py`. Zero source hunks.

## CONFIRMED DEFECT 2 — `patch_replay` null replay
Replaying the NodeBB patch on a pristine image fails at `git apply` ("already exists"),
`git apply --3way` ("does not apply"), and the `patch --fuzz` fallback. The command's trailing `||`
returns success; Harbor emits a reward for an unchanged tree. `replay.json apply_rc=1`,
post-apply diffstat empty.

## CONFIRMED DEFECT 3 — mini-swe-agent unpinned (2.4.6) incompatible with V2 locked harness
Interactive setup wizard aborts on non-TTY; cost-calc raises `RuntimeError: This model isn't mapped
yet` for DeepSeek. Mitigated in audit overlay (`MSWEA_CONFIGURED`, `MSWEA_COST_TRACKING=ignore_errors`,
`--with mcp`); not an upstream fix.

## CONFIRMED DEFECT 4 — Harbor egress sidecar stalls first model call
Sidecar holds `api.deepinfra.com:443` open ~892 s while `curl` succeeds in 1.7 s. Mitigated by
`stream:false`, `timeout:120`, `num_retries:3`.

## INFRASTRUCTURE FAILURE — nodebb original attempt
Agent produced 0 model responses; transcript = prompt only; no trajectory. Verdict 0.0 is invalid.
Recovery rerun (separately labelled) scored 1.0.

## AGENT FAILURE — vuls
66/67 required tests passed; `TestSortByConfident` genuinely FAILED in raw `go test`. Correctly graded.

## NO ISSUE OBSERVED
flipt, openlibrary, teleport, ansible, elementweb — parser consistent with raw output; regrade agrees.

## SUSPECTED DEFECT — cost telemetry
Harbor reports 0 tokens/cost for DeepInfra. Not yet reproduced as a grader-affecting issue.
