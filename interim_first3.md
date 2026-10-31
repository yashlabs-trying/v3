# DataForge V3.1 — Phase 1A Interim Results (First 3 Tasks)

Generated: 2026-10-30 (~17:00 UTC)
Status: nodebb + flipt complete; vuls in progress. Remaining 4 tasks queued.

## Upstream / environment (frozen)
- Repo: scaleapi/SWE-bench_Pro-os @ 66f92766bba642462d4bbe5479e83f91f9211862 (verified, unmodified)
- Backend: Harbor 0.25.0, local Docker (README's Modal backend unavailable — no Modal creds)
- Model: deepseek-ai/DeepSeek-V4.1-Flash via DeepInfra OpenAI-compatible endpoint (single model for all tasks)
- Harness: locked_mini_swe (mini-swe-agent), locked protocol, verifier never in agent sandbox
- Controls: oracle=1.0 / no-op=0.0 for ALL 7 selected tasks (validated)

## Interim results table (3 of 7)

| # | Task | Repo/Lang | Oracle | No-op | DS original | DS patch | Verifier | Class |
|---|------|-----------|--------|-------|-------------|----------|----------|-------|
| 1 | instance_NodeBB__NodeBB-00c70ce7 | NodeBB / JS (mocha) | 1.0 | 0.0 | 0.0 | 166,347 B (Redis dumps ONLY) | 0/2 required | ENVIRONMENT/HARNESS FAILURE + patch contamination (suspected defect) |
| 2 | instance_flipt-io__flipt-6fe76d02 | flipt / Go | 1.0 | 0.0 | 1.0 | 7,772 B (1 source file) | 13/13 required PASSED | AGENT SUCCESS (clean) |
| 3 | instance_future-architect__vuls-f0b3a8b1 | vuls / Go | 1.0 | 0.0 | pending | pending | pending | in progress |

## Task 2 (flipt) — clean success
- DeepSeek modified exactly `internal/server/auth/middleware.go` (7,772 B patch).
- Trajectory: 97 messages (real multi-step work).
- Verifier output.json: 13/13 required fail_to_pass tests PASSED; RESULT: PASSED.
- Agent time 9m27s; verifier 5.8s.
- No parser loss, no contradiction, runner/grader agree. => evaluator behaved correctly.

## Task 1 (NodeBB) — misleading verdict; harness did NOT run the agent
Evidence:
- `agent/mini-swe-agent.txt` = 8,681 bytes and contains ONLY the system+user prompt.
  No assistant turns, no tool calls. The agent never received a single DeepSeek response.
- NO `*trajectory*.json` produced.
- Harbor still ran the verifier and produced `reward.txt = 0`.
- `agent/model.patch` = 166,347 bytes, containing ONLY Redis AOF artefacts:
  - appendonlydir/appendonly.aof.1.base.rdb
  - appendonlydir/appendonly.aof.1.incr.aof
  - appendonlydir/appendonly.aof.manifest
  ZERO source-code diffs. (Patch capture is `git add -A; git diff --cached` in /app; the
  verifier's run_script.sh starts redis-server --appendonly yes, and/or the agent sandbox
  retained Redis state, so the captured "solution" is Redis binary state, not code.)
- Verifier: "Required tests: 2 / Passed tests: 0 / RESULT: FAILED".

Interpretation:
- The 0.0 reward is NOT evidence that DeepSeek failed to solve the task; the agent never
  ran far enough to attempt it. Classified ENVIRONMENT/HARNESS FAILURE.
- Independently, `model.patch` capture is proven to be polluted with non-source binary
  artefacts, which destroys the meaning of the fresh-sandbox patch_replay regrade for this
  task family (Redis-backed NodeBB tasks). This is a SUSPECTED/CONFIRMED harness defect
  (hypotheses H3 evidence-integrity, H8 output-vs-verdict, H10 regrade divergence).

## Root causes found and fixed during the run (harness compatibility, NOT benchmark)
mini-swe-agent 2.4.6 (unpinned, pulled by V2's `uv tool install`) breaks the V2 locked harness:
1. Requires a global config; otherwise with non-TTY stdin it prints an interactive setup
   wizard and ABORTS. Fix: MSWEA_CONFIGURED=true.
2. Fails hard computing cost for a model absent from litellm's cost map:
   "This model isn't mapped yet ... model=openai/deepseek-ai/DeepSeek-V4.1-Flash".
   Fix: MSWEA_COST_TRACKING=ignore_errors.
3. Environment/network on this host: PyPI requests take 12-23s; in-sandbox litellm cannot
   fetch the cost map (SSL UNEXPECTED_EOF); agent setup (wheel downloads) frequently times
   out. Mitigation: pre-baked agent images + raised UV/PIP timeouts.

## Outstanding mystery being investigated
NodeBB still produced zero model responses despite fixes 1-2 being applied (config building
logged, no wizard). flipt with identical config produced 97 messages. Likely a first-call
stall on the larger NodeBB prompt; being reproduced.

## What this means for V3.1 architecture
- The evaluator CAN be run reproducibly (controls prove it) and DOES grade correctly when the
  agent actually runs (flipt: clean pass).
- The dominant reliability risks observed so far are in the HARNESS boundary, not the tests:
  (a) agent-not-run silently yielding reward 0; (b) model.patch contaminated by environment
  side effects; (c) brittle unpinned agent dependency.
- A V3.1 reliability layer must: verify the agent actually executed (non-empty trajectory),
  sanitize/scope model.patch to source paths, pin the agent, and classify setup failure
  separately from agent failure.
