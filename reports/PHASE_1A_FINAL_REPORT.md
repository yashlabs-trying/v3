# DataForge V3.1 — Phase 1A Baseline Reliability Audit (FINAL)

Status: COMPLETE. 7 selected tasks executed, graded, regraded, and analysed.
Scope: INVESTIGATION ONLY. No classification of tasks after outcomes; no changes to upstream grading code.

---

## 0. One-paragraph summary

The SWE-bench Pro V2 evaluator, run under the locked protocol with DeepSeek
(`deepseek-ai/DeepSeek-V4.1-Flash`, DeepInfra), **grades correctly when the agent actually runs**:
5 of 6 valid tasks passed, 1 genuinely failed (66/67 tests), and every fresh-sandbox regrade
agreed with the original verdict. The reliability risks are concentrated in the **harness boundary**,
not in the hidden tests: (a) a NodeBB task produced a **reward 0.0 while the agent never ran at all**
(the captured `model.patch` was 166 KB of pre-existing Redis state, not code); (b) the
`patch_replay` regrade **silently applies nothing** in that case yet still reports a verdict;
(c) the unpinned `mini-swe-agent` dependency (resolved to 2.4.6) is **incompatible with the V2
harness** and had to be worked around; (d) Harbor's egress sidecar intermittently **stalls the first
model request** for some tasks. A separately-labelled recovery rerun shows DeepSeek passes NodeBB
once the agent runs, confirming the original 0.0 was an infrastructure artifact, not a model failure.

---

## 1. Which seven tasks were selected, and why

Frozen BEFORE outcomes (`selection_manifest.json`). Chosen for diversity of repo, language and
verifier failure mechanism; each maps to one or more of the ten investigation hypotheses.

| # | Task ID (short) | Repo | Lang | Primary mechanism targeted |
|---|---|---|---|---|
| 1 | instance_NodeBB__NodeBB-00c70ce7… | NodeBB/NodeBB | JS/mocha | masked hook failure; patch contamination; JSON-reporter parser |
| 2 | instance_flipt-io__flipt-6fe76d02… | flipt-io/flipt | Go | `\|\| true` masks nonzero exit; exact `-run` regex |
| 3 | instance_future-architect__vuls-f0b3a8b1… | future-architect/vuls | Go | parser `.split()[2]` fragility; ERROR semantics |
| 4 | instance_internetarchive__openlibrary-03095f26… | internetarchive/openlibrary | Python | regex + name-dedup parser; `\|\| echo` masking |
| 5 | instance_gravitational__teleport-46aa81b1… | gravitational/teleport | Go | Go `-json` parser; `-shuffle on`/`-race` nondeterminism |
| 6 | instance_ansible__ansible-d58e69c8… | ansible/ansible | Python | `\|\| true`; parametrized IDs; fail_to_pass subset |
| 7 | instance_element-hq__element-web-aec454dd… | element-hq/element-web | TS/jest | Unicode-checkmark parser; large p2p surface |

**Baseline:** scaleapi/SWE-bench_Pro-os @ `66f92766bba642462d4bbe5479e83f91f9211862` (verified,
unmodified; 642 tasks). No V1 used. Audit tools live in `dataforge/experiments/v3_1_baseline/`.

---

## 2. Did the reference and no-op controls behave as expected?

**Yes — 7/7 tasks, both directions.**

| Task | Oracle | No-op |
|---|---|---|
| nodebb | 1.0 | 0.0 |
| flipt | 1.0 | 0.0 |
| vuls | 1.0 | 0.0 |
| openlibrary | 1.0 | 0.0 |
| teleport | 1.0 | 0.0 |
| ansible | 1.0 | 0.0 |
| elementweb | 1.0 | 0.0 |

Repeat-control stability (flipt oracle, 3 independent runs): **1.0, 1.0, 1.0**. The environment and
verifier are stable and reproducible when the agent is not involved.

---

## 3. How did DeepSeek perform on each task? (full results table)

Model: `deepseek-ai/DeepSeek-V4.1-Flash` via DeepInfra (single model throughout).
Original = first official attempt. Regrade = fresh-sandbox `patch_replay` on the saved patch.

| Task | Lang | Oracle | No-op | DS original | Regrade | Patch | Src files | Traj msgs | Agent s | Verify s | Classification |
|---|---|---|---|---|---|---|---|---|---|---|---|
| nodebb | JS | 1.0 | 0.0 | **0.0** | 0.0 | 166,347 B (Redis only) | **0** | **0** | 2952 | 44 | **INFRASTRUCTURE FAILURE** (suspected false-negative) |
| flipt | Go | 1.0 | 0.0 | **1.0** | 1.0 | 7,772 B | 1 | 97 | 567 | 6 | NO ISSUE OBSERVED (clean pass) |
| vuls | Go | 1.0 | 0.0 | **0.0** | 0.0 | 6,733 B | 4 | 160 | 1048 | 11 | AGENT FAILURE (66/67) |
| openlibrary | Py | 1.0 | 0.0 | **1.0** | 1.0 | 2,573 B | 1 | 89 | 419 | 5 | NO ISSUE OBSERVED |
| teleport | Go | 1.0 | 0.0 | **1.0** | 1.0 | 5,688 B | 1 | 53 | 360 | 90 | NO ISSUE OBSERVED |
| ansible | Py | 1.0 | 0.0 | **1.0** | 1.0 | 16,513 B | 3 | 158 | 771 | 68 | NO ISSUE OBSERVED |
| elementweb | TS | 1.0 | 0.0 | **1.0** | 1.0 | 17,194 B | 5 | 206 | 1728 | 30 | NO ISSUE OBSERVED |
| _nodebb-recovery (rerun, NOT counted)_ | JS | 1.0 | 0.0 | **1.0** | 1.0 | 172,965 B | 7 | 190 | 651 | 108 | _recovery evidence only_ |

Valid DeepSeek score: **5/6 = 83%** (excluding the invalid nodebb original).

Details:
- **flipt (pass):** DeepSeek edited exactly `internal/server/auth/middleware.go`; verifier recorded 13/13 required PASSED.
- **vuls (fail, honest):** DeepSeek edited `detector/detector.go`, `models/vulninfos.go`, `tui/tui.go` (and a test file). Raw `go test` shows `--- FAIL: TestSortByConfident`; parser correctly recorded FAILED; 66/67 required passed. Legitimate near-miss agent failure.
- **openlibrary/teleport/ansible/elementweb (pass):** each modified the expected source files; required tests fully passed (3/3, 3/3, 48/48, 163/163).

---

## 4. Which reliability problems were actually observed?

### CONFIRMED DEFECT 1 — NodeBB `model.patch` contamination by pre-existing untracked image state
- The upstream image ships `/app/appendonlydir/{*.rdb,*.aof,*.manifest}` (dated 2025-07-07), untracked and NOT in `.gitignore`.
- `locked_mini_swe.py` captures the patch with `git add -A; git diff --cached`; this necessarily stages those files.
- Observed patch: **166,347 B, three `diff --git` entries, all `appendonlydir/*`, zero source hunks.**
- Evidence: `findings/confirmed_redis_patch_contamination.md`; raw patch in `jobs/final-nodebb/.../agent/model.patch`.

### CONFIRMED DEFECT 2 — `patch_replay` silently applies nothing ("null replay")
- Replaying the NodeBB 166 KB patch on a pristine image: `git apply` → "already exists in working directory"; `--3way` → "does not apply"; the `|| patch --fuzz` fallback cannot create existing files.
- The replay command's trailing `||` still returns success, so Harbor produces a reward from a tree **identical to pristine**. `replay.json apply_rc=1`.
- Consequence: the authoritative regrade for NodeBB is meaningless (reward 0.0 by absence of changes, not by evaluation of the model).

### CONFIRMED DEFECT 3 — unpinned `mini-swe-agent` is incompatible with the V2 locked harness
- `uv tool install mini-swe-agent` (no pin) resolved to **2.4.6**. Two hard failures observed:
  1. Interactive global-config setup wizard aborts on non-TTY stdin (`MSWEA_CONFIGURED` unset).
  2. `RuntimeError: This model isn't mapped yet` in cost calculation for DeepSeek (`MSWEA_COST_TRACKING`).
- Harbor 0.25.0 does set both env vars, but earlier code paths / manual runs hit the aborts. Mitigated in the audit overlay (env + `--with mcp`); not an upstream fix.

### CONFIRMED DEFECT 4 — Harbor egress sidecar stalls the first model call (some tasks)
- Sidecar log shows a connection to `api.deepinfra.com:443` held open **~892 s** (`duration:891823869964`) while a plain `curl` through the same sidecar succeeds in 1.7 s.
- Effect: several tasks printed the prompt then produced **zero model responses** for the whole budget (nodebb original, vuls first attempts).
- Mitigation that worked: agent config with `stream:false`, `timeout:120`, `num_retries:3` → agent then ran normally (53–206 messages).

### SUSPECTED DEFECT — token/cost telemetry lost
- `agent_result` reports `n_input_tokens=0, cost_usd=0.0` for DeepInfra despite real runs. Cost not captured by Harbor for this provider.

### NO ISSUE OBSERVED
- flipt, vuls, openlibrary, teleport, ansible, elementweb: parser output matched raw test output; runner and grader agreed; regrades reproduced.

---

## 5. Did any test parser produce incomplete or contradictory evidence?

No parser defect was **proven** in the 7 tasks. Specific checks:
- **vuls:** raw `--- FAIL: TestSortByConfident` ⇒ `output.json` FAILED ⇒ reward 0.0. Consistent (parser handled the failure correctly).
- **openlibrary:** triple-regex parser + name-dedup produced 3/3 required PASSED; raw pytest agreed.
- **elementweb:** Unicode-checkmark parser produced 163/163 required PASSED; jest output had checkmarks; no loss.
- **nodebb:** parser captured a "before all" hook failure (suite init) under `failures`; required tests absent. Consistent with a broken run, but see INFRA finding — the run was broken before grading.
- **No contradictory statuses, no missing required identifiers** were observed for tasks where the agent ran.

Parser risk remains theoretical for the unexercised branches (e.g. spaces in vuls-style names, glyph absence in jest).

---

## 6. Did the original and fresh-sandbox verdicts disagree?

**No — 0/7 disagreements.** All regrades matched the original reward.
Important caveat: nodebb's *agreement is spurious* — both are 0.0, but the regrade applied **nothing**
(null replay). Agreement of two algorithms on the same wrong input is not corroboration.

---

## 7. Were any false PASS or false FAIL outcomes independently confirmed?

- **False PASS:** none. The 5 passes were checked against raw test output (required tests genuinely present and PASSED).
- **False FAIL:** one **suspected** — nodebb original 0.0 was presented as a model failure, but the agent produced **0 model responses**; the separately-labelled recovery rerun scored **1.0**. This is a **suspected false-negative caused by infrastructure**, not an evaluator defect in the grader itself. It is not counted as a confirmed false-FAIL of the model because we cannot prove what the original attempt would have scored.

---

## 8. What environmental failures occurred?

1. **Host network degradation:** PyPI latency 12–23 s/request; in-sandbox litellm cost-map fetch fails (SSL UNEXPECTED_EOF). Mitigated with pre-baked agent images + raised timeouts.
2. **CRLF checkout artifact:** the Windows-side clone had CRLF working-tree files; `#!/bin/bash\r` broke script execution. Not a benchmark defect; fixed by an LF mirror of the same commit.
3. **Agent-setup timeouts:** default 360 s insufficient; raised (worked around with multiplier + pre-baked images).
4. **Egress-sidecar stalls** (DEFECT 4).
5. **`dataforge-agent` build for ansible** needed explicit `curl` install (image ships without curl).

---

## 9. How much time and money did evaluations consume?

- **Agent execution (valid runs):** 360–1728 s each (nodebb original 2952 s but invalid; elementweb 1728 s longest valid).
- **Verifier:** 5–108 s.
- **Estimated DeepSeek cost:** **~$1.48** (rough proxy from trajectories; DeepInfra per-call `estimated_cost` not aggregated by Harbor). Actual API spend is small; no Modal/cloud spend (local Docker only).
- Wall-clock: most of the elapsed time was image pulls (3.6–4.9 GB each) and infrastructure retries, not model inference.

---

## 10. Ranked reliability improvements for DataForge V3.1 to consider (do NOT implement yet)

| Rank | Improvement | Severity | Reproducibility | Impact | Scope | Fix complexity |
|---|---|---|---|---|---|---|
| 1 | Scope/sanitise `model.patch` to source paths (exclude untracked runtime state; use `git diff` of tracked files or an allow-list) | Critical | Always | Restores regrade meaning | All repos shipping untracked state | Low |
| 2 | Make `patch_replay` fail loudly when nothing applies (treat apply_rc!=0 and empty diffstat as INVALID, not a reward) | Critical | Always | Stops null-replay false verdicts | All tasks | Low |
| 3 | Verify the agent actually ran (non-empty trajectory / ≥1 model response) before accepting a reward; else classify ENVIRONMENT_FAILURE | Critical | Intermittent | Stops infra failures disguised as model failures | All tasks | Low |
| 4 | Pin the coding-agent + litellm versions; assert import/tool availability at setup | High | Always | Removes version-drift aborts | All tasks | Low |
| 5 | Fix or bypass the egress sidecar for model endpoints (or force non-streaming + short timeout + retries) | High | Intermittent | Removes 50-min stalls | All tasks | Medium |
| 6 | Capture token/cost telemetry for OpenAI-compatible providers | Medium | Always | Enables cost accounting | All tasks | Medium |
| 7 | Add a "patch touched a test file" flag (informational) | Low | Sometimes | Transparency on measured scope | Some tasks | Low |

---

## 11. What evidence is missing

- Original nodebb attempt has **no trajectory** (agent never ran) — cannot know what it would have scored.
- DeepSeek token/cost telemetry (Harbor reports 0 for DeepInfra).
- Only 1 task family (NodeBB) demonstrated the contamination/null-replay defect; whether other
  repos ship similar untracked runtime state was not fully enumerated (38 NodeBB tasks affected by
  construction; other repos not systematically scanned).
- H8/H9 (grader accepts incomplete/contradictory evidence) were not exercised — no contradictory
  evidence was produced by these 7 tasks; the null-replay (DEFECT 2) is the closest analogue.

---

## 12. Which exact tests should be rerun after implementing V3.1

1. **nodebb (this instance)** — recovery rerun already gives the "after-fix" reference (1.0); rerun the FULL NodeBB set (38 tasks) to quantify contamination/null-replay scope.
2. **vuls (this instance)** — confirm the 66/67 remains stable and the parser still records the genuine FAIL under any new patch-scoping.
3. **All 7 selected tasks** — rerun oracle + no-op + a fixed agent under the new patch-scoping to confirm no regression.
4. A **contradictory-evidence** synthetic test (same test PASSED and FAILED in output) across each parser family (mocha/pytest/jest/go-json/go-text) to exercise H3/H9 deliberately.
5. A **repeat-run trio** per task (like the flipt stability check) to measure verdict determinism at scale.

---

## Appendix — artifact locations

- `environment_manifest.json`, `harness_revision.json`, `selection_manifest.json`
- `results.json`, `results.csv`, `metrics.json`
- `evidence_checksums.txt` (frozen sha256 of all original results)
- `findings/confirmed_redis_patch_contamination.md`, `findings/confirmed.md` (to be mirrored)
- `interim_first3.md`
- Raw jobs under `jobs/<job>/instance_*/{agent,verifier}/`
- Reproduce: scripts `run_controls.sh`, `run_ds.sh`/`run_f3.sh`, `run_regrade.sh`, `run_nodebb_recovery.sh`, `build_agent_image.sh`, `make_audit_tasks.sh`.
