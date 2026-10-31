# DataForge V3.1 — Phase 1A Baseline

Investigation-only audit of SWE-bench Pro V2 (scaleapi/SWE-bench_Pro-os @
`66f92766bba642462d4bbe5479e83f91f9211862`) using DeepSeek `deepseek-ai/DeepSeek-V4.1-Flash`.

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
v3_1_baseline/
  environment_manifest.json  harness_revision.json  selection_manifest.json
  results.json  results.csv  metrics.json  evidence_checksums.txt
  interim_first3.md
  findings/   reports/   jobs/   logs/
  audit_tasks/        # task overlays pointing at pre-baked agent images (tests unchanged)
  tooling_overlay/    # locked_mini_swe.py (+mcp) and mini_toolcall_audit.yaml (stream=false)
  upstream_lf/        # LF mirror of the upstream commit (unmodified content)
```

## Rules honoured
Upstream repo unmodified; grading code (test.sh/parser.py/config.json/test_patch.patch) byte-identical
to upstream in every executed task; tasks frozen before outcomes; original results preserved and
checksummed; recovery rerun separately labelled and not counted as the original attempt; no V3.1 fixes
implemented.
