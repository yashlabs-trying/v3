# DataForge V3.3 — Local Performance & Correctness Smoke Test

**Scope:** run the existing V3.3 diagnostic pipeline on real frozen evidence and
report **actually measured** performance and correctness. No features added; no
architecture changes; no new phase. No model/API calls. No Docker/replay executed.

- **Repository:** `C:\Users\yashs\dataforge\v3`
- **Branch:** `v3.3-phase3`
- **Git revision:** `6529401f362725acbb0be276ad9ec3e4d5b9ff05`
- **Working tree:** clean before the test; only the smoke artifacts are new
  (no existing file modified, deleted or committed).

## 1. Machine and environment

| Item | Value |
|---|---|
| OS | Windows 11 (10.0.26200), single language |
| CPU | Intel Core i5-1155G7 @ 2.50 GHz (8 logical CPUs) |
| RAM | 15.7 GB |
| Python | 3.13.15 |
| Memory method | `psutil` process RSS (+ fresh-process delta) |
| Timing method | `time.perf_counter()` (wall), psutil `cpu_times()` (CPU) |

## 2. Exact commands used

```powershell
# baseline
python -m pytest dataforge_v3/tests -q

# pipeline invocation discovered from source:
#   python -m dataforge_v3.cli intelligence --root . --out-dir findings/intelligence
python -m dataforge_v3.cli intelligence --root . --out-dir findings/intelligence
```

Per-case and cohort timing harnesses call the same code paths
(`load_task_evidence` → `load_semantic_input` → `diagnose_task_with_observations`
→ `render_diagnosis_*`) so the CLI invocation is not a different code path.

## 3. Baseline tests

```
136 passed in 3.31s   (wall clock 4.50 s including interpreter startup)
```

Matches the prior report (136). **No failures, no skips.**

## 4. Results table (measured)

| Case | Verdict | Diagnosis correct? | Cold ms | Median ms (n=5) | Peak RSS MB | Evidence refs valid? |
|---|---|---|---:|---:|---:|---|
| vuls | VALID → GENUINE_AGENT_FAILURE | yes | 63.5 | 49.8 | 29.0 | yes (2/2) |
| NodeBB | INVALID → infra only | yes | 11.9 | 18.4 | 30.5 | yes (1/1) |
| flipt | VALID → CONFIRMED_CORRECT | yes | 24.3 | 18.1 | 30.2 | yes (0 refs) |
| Full cohort (8) | 8 records | yes | 218.7* | **242.9** | 31.3 | yes (all) |

*Cold ms for single cases is a fresh-interpreter run (true cold cache). Peak RSS is
whole-process RSS; see the incremental figures below. Cohort "cold" is the fastest
of 5 timed runs after warm-up.

## 5. Per-case detail

| Case | Findings | Unsupported | Unresolved refs | Events | Artifacts | Clause attributed |
|---|---:|---:|---:|---:|---:|---|
| vuls | 1 | 0 | 0 | 188 | 2 (+semantic json) | `sort.equal_score_order` |
| NodeBB | 1 (infra) | 0 | 0 | 0 (no trajectory) | 1 | — |
| flipt | 0 | 0 | 0 | 98 | 2 | — |

Stage breakdown (warm, vuls):
`ingest ≈ 83 ms` (cold file read of the 245 KB patch + 761 KB trajectory),
`attribution ≈ 7.4 ms`, `report ≈ 14.6 ms`; subsequent warm reads drop to
~2–4 ms each.

## 6. Fresh-process cold runs (separate interpreters)

| Case | Cold total ms | RSS delta MB | Process CPU s |
|---|---:|---:|---:|
| vuls | 63.5 | +1.02 | 0.063 |
| NodeBB | 11.9 | +0.57 | 0.016 |
| flipt | 24.3 | +0.80 | 0.016 |

Incremental memory for a full diagnosis is **under ~1 MB**; the ~23 MB process
floor is the Python interpreter plus module imports.

## 7. Full cohort (8 records, 1 warm-up + 5 timed runs)

| Metric | Value |
|---|---|
| Records | 8 (7 tasks + NodeBB recovery) |
| Median total runtime | **242.9 ms** |
| Min / Max | 218.7 ms / 268.9 ms |
| Observed p95 (n=5, = sample max) | 268.9 ms |
| Throughput | **32.9 records/s** |
| Peak RSS | 31.3 MB (process); ≈ +1 MB incremental |
| Evidence bytes processed | 7,037,112 B (7.04 MB) over 18 files |
| Unsupported accusations | **0** |
| Unresolved evidence references | **0** |
| Verdicts stable across 5 runs | **yes** |

Per-record latency (warm): NodeBB 4.4 ms, flipt 3.9 ms, vuls 2.7 ms, openlibrary
2.1 ms, teleport 1.3 ms, ansible 0.7 ms, element-web 0.7 ms, NodeBB-recovery 0.6 ms.

> Method note: in the single-interpreter harness, `os.times()`-based CPU
> (0.19–0.27 s) exceeds wall time because it aggregates threads; the fresh-process
> per-case CPU figures (0.016–0.063 s) are the reliable ones. `observed_p95` with
> n=5 is the sample maximum and is labelled observed, not a population estimate.

## 8. Diagnostic accuracy (verified independently of the output)

| Property | Required | Measured | Pass |
|---|---|---|---|
| vuls genuine failure + correct clause | `sort.equal_score_order`, `existing_behavior_removed`, V2 FAIL (0.0) preserved | exactly that; evidence resolves | ✅ |
| NodeBB original INVALID without accusations | infra-only, no coding weakness | 1 `agent_startup_failure` finding; forbidden phrases absent; 0 coding capability weakness | ✅ |
| flipt valid success, no invented weakness | 0 findings | 0 findings, CONFIRMED_CORRECT | ✅ |
| Other passing tasks | no unsupported weakness | 0 findings across all CONFIRMED_CORRECT tasks | ✅ |
| NodeBB recovery | separate from original | distinct VALID record; original stays INVALID | ✅ |

**Not task-hardcoded:** vuls attribution comes from the generic engine
(`attribute` maps the failed V3.2 probe `vuls:tie.order` → clause → category, with
diff-token corroboration). A test asserts the task tokens are absent from engine
code literals. Claims about source modification resolve to the submitted
`model.patch`; tool actions resolve to the trajectory artifact.

## 9. Cost of V3.3 (measured decomposition, vuls)

| Component | Median ms |
|---|---:|
| Evidence ingestion (trajectory + patch I/O) — shared with any approach | 31.5 |
| V3.2 semantic evidence load | 0.24 |
| **V3.3 attribution logic (added)** | **2.06** |
| V3.3 report render (added) | 3.80 |

- Existing V3.1/V3.2 evidence generation: **not re-run** (frozen artifacts reused);
  its historical oracle costs (~40–90 s Docker per Go/JS task) are unchanged and
  not part of offline diagnosis.
- V3.3-added logic: **~5.9 ms/record**.
- Full end-to-end replay / model execution: **not executed**.
- Model API cost: **$0** (zero API calls). Compute used: < 0.1 s CPU for the whole
  three-case run; ~0.22 s CPU for the full cohort.

## 10. Bottleneck

Evidence ingestion (cold file reads of the large submitted patch and trajectory)
dominates cold latency; warm-latency bottleneck is report rendering (~3.8 ms).
Attribution itself is ~2 ms. Nothing is super-linear.

## 11. Final decision — **GO**

- **Accurate and evidence-grounded locally?** Yes. vuls attributed to the correct
  clause and category; NodeBB isolated as infrastructure; flipt and the other
  passing tasks unaccused. 0 unresolved references, 0 unsupported claims.
- **Speed?** 12–64 ms cold per record; median 243 ms for the 8-record cohort.
- **Memory?** < 1 MB incremental per diagnosis; ~31 MB process peak.
- **Throughput?** ~33 records/s offline, single process.
- **Repeatable?** Yes — 5 cohort runs produced identical verdicts.
- **Ready for a larger controlled validation cohort?** **Yes, for the offline
  diagnostic layer.** The engine is deterministic, fast and evidence-faithful.
  Remaining gaps for a larger study: (a) additional semantic oracles (NodeBB and
  broader surfaces of teleport/ansible/element-web lack them), (b) the generic-LLM
  baseline is still unrun, (c) evidence is resolved but not pinned to a frozen
  manifest everywhere, (d) verdicts were verified on repeated runs but not on an
  expanded, randomized cohort.

*No new phase started. No model API called. Nothing committed or pushed.*

## Artifacts produced by this test

```
reports/V3_3_LOCAL_SMOKE.md                      (this file)
findings/intelligence/local_smoke_metrics.json   (machine metrics)
findings/intelligence/local_smoke_results.json   (accuracy + repeatability)
findings/intelligence/local_smoke_vuls.json      (raw)   - nb: per-case raw
findings/intelligence/local_smoke_NodeBB.json
findings/intelligence/local_smoke_flipt.json
```
