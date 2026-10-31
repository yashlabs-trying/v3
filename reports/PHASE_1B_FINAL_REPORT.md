# DataForge V3.1 Phase 1B — Final Report

**Scope:** execution-reliability and false-validation-prevention layer around SWE-bench Pro V2 + Harbor, evaluated on the seven frozen DeepSeek-V4.1-Flash task patches.
**Branch:** `v3.1-phase1b` (based on `b7d78ad`).
**Result:** **GO** for Phase 2, subject to the conditions in §8.

---

## 1. Verdict summary

The original baseline contains one false validation and one infrastructure-invalid trial:

| Task | Original reward | Original interpretation | DataForge classification | Why |
|---|---:|---|---|---|
| NodeBB | 0.0 | failed model run | **INVALID** | agent produced **0 model responses**, timed out at exit 124, and the "patch" is three Redis AOF artifacts with **zero source hunks** |
| NodeBB recovery | 1.0 | pass | **PASS** | after provenance filtering: 7 source files applied atomically, 3 Redis artifacts excluded untouched, verifier still passes |
| flipt | 1.0 | pass | **PASS** | replay applies cleanly; evidence valid |
| vuls | 0.0 | fail | **FAIL** | replay applies cleanly; required test still fails; not invalidated |
| openlibrary | 1.0 | pass | **PASS** | replay applies cleanly; evidence valid |
| teleport | 1.0 | pass | **PASS** | replay applies cleanly; evidence valid |
| ansible | 1.0 | pass | **PASS** | replay applies cleanly; evidence valid |
| element-web | 1.0 | pass | **PASS** | replay applies cleanly; evidence valid |

Fleet metrics on the eight replay cases:

```json
{
  "tasks": 8,
  "valid_pass_preserved": 6,
  "valid_fail_preserved": 1,
  "legitimate_verdicts_incorrectly_invalidated": 0,
  "infrastructure_nonexecution_flagged_invalid": 1,
  "contamination_only_patches_flagged": 1
}
```

The seven original-verdict cases (baseline audit, no DataForge replay) produce the same verdicts: 5 PASS preserved, 1 FAIL preserved, NodeBB INVALID, 0 legitimate verdicts invalidated.

---

## 2. Baseline defects reproduced

### 2.1 NodeBB: non-execution reported as a model outcome

- `jobs/final-nodebb/.../agent/model.patch`: **166,347 bytes**, parsed as **3 entries**, all under `appendonlydir/`; **0 source hunks**.
- `agent/mini-swe-agent.txt`: **8,891 bytes**, prompt only; no assistant turn.
- `exception.txt`: `NonZeroAgentExitCodeError`, exit **124** from the agent timeout.
- Consequence: the run never called the model. The reward of 0 says nothing about model capability. DataForge classifies execution as `INFRASTRUCTURE_TIMEOUT`, model responses `0`, final **INVALID**.

### 2.2 NodeBB recovery: contamination and non-atomic upstream application

- Recovery `model.patch`: **172,965 bytes**, **10 entries**: 3 Redis AOF files plus 7 `src/` files.
- The old regrade recorded `apply_rc=1` yet still produced reward **1.0** because the fallback path (`--3way` / `patch --fuzz`) partially applied the patch.
- DataForge replays only the 7 source files with `git apply` (no 3-way, no fuzz), verifies the post-state, and requires excluded artifacts to keep identical hashes. Result: **PASS**, but for the right reason and with evidence.

### 2.3 vuls: a real failure must stay a failure

Replaying the vuls patch applies all four files cleanly (`apply_rc=0`), but the required test still fails. DataForge keeps **FAIL**; it does not convert a legitimate negative into INVALID.

### 2.4 Grading-script hazards confirmed

- Upstream `tests/test.sh` resets test-code files to HEAD and reapplies `test_patch.patch`, so agent edits to tests are reverted.
- `run_script.sh` masks exits with `|| true` / `|| echo`, which is why the layer validates the runner exit code and test evidence independently.

---

## 3. What was implemented

Package: `dataforge_v3/`.

| Module | Responsibility |
|---|---|
| `patch/validation.py` | unified-diff parser; path safety; symlink/gitlink/duplicate rejection; CRLF normalization; sha256 |
| `patch/provenance.py` | pristine-baseline comparison; provenance-based accept/exclude/review; filtered patch construction; no extension allow-list |
| `patch/capture.py` | two-phase capture replacing `git add -A`: stage only agent-created/modified content, restore index, exclude pre-existing untracked state |
| `replay/controller.py` | strict apply command; post-state assessment; fail-closed replay decisions |
| `lifecycle/state_machine.py` | 11 evidence-gated states; monotonic transitions; no state without required evidence |
| `lifecycle/failure_classifier.py` | distinguishes nonexecution, startup/auth/network errors, interruption, timeout, and completed runs |
| `evidence/parser.py` | required-test contract loading; output/reward parsing; masking detection |
| `evidence/validation.py` | absent vs not-passed; parser-drop detection; contradictions; reward cross-check; runner exit/timeout |
| `evidence/manifest.py` | artifact manifest build/verify |
| `runtime/compatibility.py` | pinned versions, Harbor/upstream commits, required agent env |
| `runtime/health.py` | endpoint reachability, startup-failure report, labeled infrastructure retries |
| `reporting/schema.py` | final classification; fleet report; comparison CSV; metrics |
| `integrations/harbor_adapter.py` | turns real Harbor jobs into verdicts; preserves original reward; maps WSL paths on Windows |
| `integrations/df_replay_agent.py` | Harbor agent `dataforge_v3.integrations.df_replay_agent:DataForgeReplayAgent`; lifecycle-tracked, fail-closed replay |
| `cli.py` | `audit`, `classify`, `verify-manifest`, `preflight` |

### Fail-closed rules

1. No authoritative verdict without execution evidence; 0 model responses is INVALID, never FAIL.
2. No replay without a structurally valid, provenance-approved patch.
3. `git apply --check` then `git apply`; no 3-way and no fuzz.
4. Every accepted path must appear in the post-apply state; every unexpected path is an error.
5. Excluded pre-existing artifacts must hash identically before and after replay.
6. Missing, unparsed, contradictory, or runner-broken evidence is INVALID, not PASS/FAIL.
7. The original V2 reward and verdict are preserved alongside the DataForge classification.
8. No fabricated values: absent artifacts are reported as absent.

---

## 4. Real replay evidence

Each replay was run with the actual task image through Harbor 0.25.0 in WSL, using the source job's frozen patch.

| Case | Execution (source job) | Patch | Replay | Verification | Final |
|---|---|---|---|---|---|
| nodebb | INFRASTRUCTURE_TIMEOUT, 0 responses | CONTAMINATED_ONLY, 0 accepted / 3 excluded | not applied | PATCH_INVALID | **INVALID** |
| recovery | COMPLETED, 93 responses | VALID, 7 accepted / 3 excluded | `apply_rc=0`, post-state OK, excluded hashes unchanged | VALID, reward 1.0 | **PASS** |
| flipt | COMPLETED, 47 responses | VALID, 1 accepted | `apply_rc=0`, post-state OK | VALID, reward 1.0 | **PASS** |
| vuls | COMPLETED, 65 responses | VALID, 4 accepted | `apply_rc=0`, post-state OK | VALID, reward 0.0 | **FAIL** |
| openlibrary | COMPLETED, 43 responses | VALID, 1 accepted | `apply_rc=0`, post-state OK | VALID, reward 1.0 | **PASS** |
| teleport | COMPLETED, 25 responses | VALID, 1 accepted | `apply_rc=0`, post-state OK | VALID, reward 1.0 | **PASS** |
| ansible | COMPLETED, 67 responses | VALID, 3 accepted | `apply_rc=0`, post-state OK | VALID, reward 1.0 | **PASS** |
| element-web | COMPLETED, 96 responses | VALID, 5 accepted | `apply_rc=0`, post-state OK | VALID, reward 1.0 | **PASS** |

### Provenance facts

- The pristine NodeBB image already contains exactly three untracked files at start:
  - `appendonlydir/appendonly.aof.1.base.rdb`
  - `appendonlydir/appendonly.aof.1.incr.aof`
  - `appendonlydir/appendonly.aof.manifest`
- The original NodeBB patch is exactly those three paths; DataForge excludes all three and accepts nothing.
- The recovery patch contains those three plus seven `src/` files. The filtered patch accepts exactly the seven source files; the filtered sha differs from the source sha (`66c8046c…` → `701b501a…`), proving the filter ran.
- For every other task the filtered sha equals the source sha, i.e. filtering changed nothing:
  - flipt `84d420e0…`, vuls `6ffc2645…`, openlibrary `82daa6dd…`, teleport `bfc10356…`, ansible `cd3172f6…`, element-web `5ae7b2ae…`.
- Canonical patch identity is EOL-aware: a file whose newlines are all CRLF is a checkout-encoded LF patch, so its LF hash is authoritative; mixed content (Redis AOF lines genuinely end in CRLF) keeps its raw hash. All eight canonical source hashes match the WSL artifacts, including NodeBB `f2d6bc2e…` and recovery `66c8046c…`.

### Lifecycle evidence

Every successful replay records:
`SETUP_COMPLETE → PATCH_CAPTURED → PATCH_VALIDATED → PATCH_APPLIED → FINALIZED`.
The rejected NodeBB replay records:
`SETUP_COMPLETE → PATCH_CAPTURED → PATCH_VALIDATED → FINALIZED`.
No transition is recorded without its required evidence.

---

## 5. Tests

`python -m pytest dataforge_v3/tests -q` → **67 passed** (66 core tests plus a relocation guard proving replay source evidence resolves inside a cloned checkout).

Coverage includes:

- non-execution vs confirmed model failure; API failure before first response; startup/cost-accounting failure; NodeBB-style zero-response timeout;
- legitimate PASS and FAIL preservation;
- Redis contamination only; legitimate new file; modify/delete/rename; malformed, path-escape, symlink, duplicate patches; binary pre-existing vs binary new;
- filtered-patch content; test-file touch;
- apply failure; partial application; unexpected path; empty submission;
- missing verifier output; contradictory statuses; parser drop; runner nonzero; runner timeout; reward disagreement;
- endpoint unreachable; unsupported cost accounting; missing env; version mismatch; labeled retries;
- safe capture vs legacy `git add -A` contamination (real temporary git repositories);
- frozen baseline end-to-end verdicts;
- real replay end-to-end verdicts, including NodeBB INVALID and recovery PASS;
- replay source-evidence relocation: an absolute `source_trial` that no longer exists resolves relative to the checkout's own `jobs/` directory.

---

## 6. Evidence integrity findings

`evidence_checksums.txt` contains **42 entries** covering `final-nodebb`, `final-flipt`, and `final-vuls`. Verification in the WSL baseline copy:

- **40 / 42 match.**
- **2 mismatches**, both in the incomplete `final-vuls` job:
  - `jobs/final-vuls/job.log` — expected `a846370a…`, actual `779a9468…`
  - `jobs/final-vuls/instance_future-architect__vuls__8Cyvgz3/trial.log` — expected `c066a856…`, actual `fc1723f2…`
- Both files have mtime `17:40:18`; the checksum file has mtime `17:31:39`. The job is incomplete (`n_running_trials=1`, empty patch); it is **not** the authoritative vuls run, which is `f3-vuls-a1` with full verifier evidence.
- The mismatches affect only mutable run logs. They are disclosed here, not hidden or “fixed” by rewriting the manifest. Byte-identical copies and both hashes are preserved in `evidence_preserved/final-vuls/` and `evidence_preserved/PRESERVATION_MANIFEST.md`; the originals were not overwritten.

The Windows checkout stores text with CRLF; its file hashes differ from the WSL baseline even when content is equivalent. All checksum and patch-hash verification in this report was therefore performed in WSL. DataForge normalizes CRLF to LF before parsing and applying patches; the normalized flipt patch sha256 matches the frozen value `84d420e0…` exactly.

See `reports/EVIDENCE_INTEGRITY_NOTE.md` for the detailed table and recommendations.

---

## 7. Residual risks and honest limitations

1. **Harbor may run the verifier even when the agent fails.** The original NodeBB run did, producing reward 0 despite nonexecution. The DataForge replay record, not the raw Harbor reward, is authoritative whenever a replay is invalid.
2. **One run per task.** These results establish defect reproduction and verdict preservation, not model variance or benchmark-level rates.
3. **Seven tasks only.** No statistical claim beyond this frozen set.
4. **Legacy baseline jobs have no DataForge replay.** They are classified `UNVERIFIED_ORIGINAL`; the reruns in §4 are the authoritative evidence.
5. **Provenance depends on service state being present at replay start.** For NodeBB this was verified directly: the three Redis files exist in the pristine image. A service that creates state only after setup could still evade provenance; that needs a per-image baseline capture step before general rollout.
6. **Binary additions require human review.** This path is implemented and tested but not exercised by the seven tasks.
7. **Mutable logs can change after a freeze.** See §6.
8. **Windows/WSL split.** Harbor and Docker run only in WSL; the Windows checkout is for development and audit. Path localization handles `/mnt/<drive>` but the WSL baseline remains the source of truth for historical hashes.

---

## 8. Conditions for Phase 2 (GO)

1. Re-freeze `evidence_checksums.txt` over immutable, final job directories, excluding mutable `job.log` / `trial.log`, or mark those as non-authoritative.
2. Make the DataForge audit the only source of PASS/FAIL/INVALID; never consume a raw Harbor reward when a replay record exists.
3. Keep `source_job`, `dataforge_replay.json`, and the filtered patch with every result.
4. Capture a pristine `git status` + artifact hash baseline per task image before scaling to new tasks.
5. Expand to more tasks and repeated seeds before publishing capability or reliability rates.
6. Keep the fail-closed policy: no 3-way/fuzz application, no extension allow-list, and evidence-free transitions rejected.

With those conditions, the Phase 1B objective is met: the false validation is caught, the legitimate verdicts are preserved, and every conclusion is backed by replayable evidence.

---

## 9. Artifacts and reproduction

Key outputs:

- `jobs/df-rerun/audit.json` — eight replay verdicts with lifecycle and replay evidence.
- `jobs/df-rerun/comparison.csv` — per-task comparison table.
- `jobs/df-rerun/metrics.json` — fleet metrics.
- `jobs/df-baseline-audit.json`, `jobs/df-baseline-comparison.csv`, `jobs/df-baseline-metrics.json` — original-seven audit.
- `jobs/df-rerun/df-rerun-*/instance_*/agent/dataforge_replay.json` — per-trial patch, provenance, apply, post-state, artifact hashes, lifecycle.
- `reports/EVIDENCE_INTEGRITY_NOTE.md` — checksum mismatch disclosure.

Reproduce (WSL for Harbor/Docker; Windows for unit tests):

```bash
# unit + integration tests
python -m pytest dataforge_v3/tests -q

# rebuild the fleet audit
bash /mnt/c/Users/yashs/dataforge/audit_all.sh

# rebuild the original-seven audit
bash /mnt/c/Users/yashs/dataforge/audit_baseline.sh
```

Harbor replay invocation used:

```bash
PYTHONPATH=/mnt/c/Users/yashs/dataforge/v3 \
harbor run \
  --agent dataforge_v3.integrations.df_replay_agent:DataForgeReplayAgent \
  --ak source_job=/mnt/c/Users/yashs/dataforge/v3/jobs/<source-job> \
  --path /home/yashs/dataforge/experiments/v3_1_baseline/audit_tasks/<task-id> \
  --jobs-dir /home/yashs/dataforge/experiments/v3_1_baseline/rerun \
  --job-name df-rerun-<name> \
  --n-concurrent 1
```

