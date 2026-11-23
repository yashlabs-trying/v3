# SWE-bench Pro harness reliability audit

Can you trust an agentic coding benchmark's score? This audit ran
[SWE-bench Pro](https://github.com/scaleapi/SWE-bench_Pro-os) (public set, commit
`66f92766`) with DeepSeek-V4.1-Flash as the agent and checked the *harness*
before trusting the *model score*: oracle and no-op controls on every task,
independent regrading, frozen task selection, and checksummed evidence.

**What it found:** four confirmed harness defects that can silently change a
benchmark result:

1. **Patch contamination.** The NodeBB "model patch" was 166 KB of Redis
   AOF/RDB files that were baked into the image, untracked and not gitignored,
   and swept up by `git add -A`. It contained zero source changes.
2. **Null replay.** Replaying that patch on a clean image fails at every
   `git apply`/`patch` fallback, but a trailing `||` returns success, so the
   harness rewarded an unchanged tree.
3. **Unpinned agent.** mini-swe-agent 2.4.6, which was not pinned, aborts its
   setup wizard without a TTY, and its cost calculator crashes for DeepSeek.
4. **Egress-sidecar stall.** The network sidecar held the model API connection
   open for ~892 s, while a direct `curl` took 1.7 s.

One more defect is suspected: lost cost telemetry. Details and reproduction steps are in
[`findings/`](findings/).

Later phases (execution-reliability layer, semantic verification, agent
diagnostic engine, six- and thirty-case validation) are on the branches
`v3.1-phase1b`, `v3.2-phase2`, `v3.3-phase3` and `six-case-validation`.

## Read in this order
1. `reports/PHASE_1A_FINAL_REPORT.md` — the final audit.
2. `reports/V2_RELIABILITY_AUDIT.md` — reliability verdict.
3. `results.csv` / `results.json` — per-task results.
4. `metrics.json` — aggregate metrics.
5. `findings/confirmed.md`, `findings/suspected.md`, `findings/confirmed_redis_patch_contamination.md`.
6. `reports/PARSER_INTEGRITY.md`, `reports/ENVIRONMENT_RELIABILITY.md`, `reports/FALSE_VALIDATION_FINDINGS.md`.
7. `findings/reproduction_steps.md`.

## Headline
- Controls: oracle 1.0 / no-op 0.0 on all 7 tasks. Repeat oracle (flipt) 1.0 ×3.
- DeepSeek valid score: 5/6 = 83% (nodebb original excluded as infrastructure failure).
- Regrade agreement: 7/7 (nodebb's agreement is a spurious null replay).
- Confirmed defects: patch contamination (Redis state), null replay, unpinned-agent incompatibility,
  egress-sidecar stall. Suspected: cost telemetry loss.
- nodebb original = INFRASTRUCTURE FAILURE (agent never ran). Separately-labelled rerun = 1.0.

## Layout
```
./
  environment_manifest.json  harness_revision.json  selection_manifest.json
  results.json  results.csv  metrics.json  evidence_checksums.txt
  interim_first3.md
  findings/   reports/   jobs/   logs/
  audit_tasks/        # task overlays pointing at pre-baked agent images (tests unchanged)
  tooling_overlay/    # locked_mini_swe.py (+mcp) and mini_toolcall_audit.yaml (stream=false)
  upstream_lf/        # LF mirror of the upstream commit (unmodified content)
  *.sh, *.py          # pipeline scripts: build images, run controls/agent, regrade, metrics
  scratch/            # one-off inspection and debugging probes used during the audit
```

## Rules honoured
Upstream repo unmodified; grading code (test.sh/parser.py/config.json/test_patch.patch) byte-identical
to upstream in every executed task; tasks frozen before outcomes; original results preserved and
checksummed; recovery rerun separately labelled and not counted as the original attempt; no V3.1 fixes
implemented.
