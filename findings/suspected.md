# Suspected Findings — DataForge V3.1 Phase 1A

## SUSPECTED DEFECT — cost/token telemetry not captured for DeepInfra
`agent_result.n_input_tokens=0`, `cost_usd=0.0` on successful runs. DeepInfra returns per-call
`estimated_cost`, but Harbor's mini-swe-agent adapter did not aggregate it. Impact: cost accounting
only, not grading. Evidence: every `jobs/*/instance_*/result.json` `agent_result`.

## SUSPECTED (design, not defect) — agent edits to test files are reverted
On vuls the agent modified `models/vulninfos_test.go`; the verifier's `test.sh` resets test files and
re-applies `test_patch.patch`, so the edit had no effect. This is correct V2 design but means a model
that "fixes" tests instead of source is not rewarded. Informational.

## SUSPECTED — partial patch application in replay
For the nodebb-recovery patch (Redis + 7 source files), `apply_rc=1` but the `|| --3way/--fuzz`
fallback applied the 7 source files (diffstat non-empty) and regrade passed. This means replay can
*sometimes* partially apply a contaminated patch — the outcome depends on file ordering and fallback
behaviour. It worked here, but it is fragile and should not be relied upon.

## Unresolved
- Full scope of image-shipped untracked runtime state across other repos (only NodeBB proven).
- Whether the sidecar stall correlates with request size/streaming mode specifically.
