# Six-Case Validation — Final Report

**Mission:** independently test whether the DataForge V3.3 evaluation-intelligence
engine behaves correctly beyond its development examples, on a small controlled
cohort with independently established ground truth.

**Verdict: CONDITIONAL GO — controlled behaviour demonstrated.**

---

## 1. What was done

- Reconnaissance of `C:\Users\yashs\dataforge\v3` at branch `v3.3-phase3`,
  revision `6529401f362725acbb0be276ad9ec3e4d5b9ff05`.
- Froze a six-case cohort and an independent answer key **before** running the
  engine (`experiments/six_case_validation/{selection_manifest,ground_truth,evidence_manifest}.json`).
- Built the **smallest necessary interface** — a generic case-manifest adapter and
  a `diagnose-case` CLI subcommand — that reuses the existing engine functions
  without rewriting attribution and without hardcoding any task or answer.
- Ran the real V3.3 pipeline over the six cases, captured raw outputs, validated
  every evidence reference, measured latency and peak memory.
- Ran the full regression suite and added 7 offline adapter tests.
- Preserved all frozen research evidence (restored `findings/intelligence/` after
  a CLI run rewrote `runtime_seconds` only).

## 2. The central finding

> The archive contains **exactly one authentic, independently-adjudicated coding
> failure: `vuls`.** No second authentic failure class exists. Every other 0.0 run
> is an infrastructure failure (0-token model non-execution), a timeout-constrained
> audit run (empty patch, no build), or a replay/regrade with no agent model
> execution.

Therefore this cohort **cannot** establish generalization to unseen authentic agent
failures. That question is left open and is stated plainly. The two additional
failure cases (c2, c3) are **SYNTHETIC**, with executable ground truth from the
real V3.2 oracles, and are labelled as controlled-defect tests only.

## 3. Results

| Case | Origin | Ground truth | DataForge diagnosis | Correct? | Evidence valid? | Median latency |
|---|---|---|---|---|---|---|
| c1_vuls | REUSED | failure `sort.equal_score_order` / `existing_behavior_removed` | `sort.equal_score_order` / `existing_behavior_removed` | ✅ | ✅ | 58.31 ms |
| c2_teleport_synthetic | SYNTHETIC | failure `truncate.format` + `width.from_rendered` / `requirement_omitted` | both clauses / `requirement_omitted` | ✅ | ✅ | 11.18 ms |
| c3_elementweb_synthetic | SYNTHETIC | failure `lru.set_error` / `edge_case_failure` | `lru.set_error` / `edge_case_failure` | ✅ | ✅ | 5.34 ms |
| c4_openlibrary | REUSED | correct solution | 0 findings, 1 strength, no weakness | ✅ | ✅ | 42.96 ms |
| c5_infra | REUSED | infrastructure only | `agent_startup_failure`, no coding claim | ✅ | ✅ | 5.51 ms |
| c6_adversarial | SYNTHETIC | trusted `clamp.boundary` FAIL; forged log rejected | `clamp.boundary` / `edge_case_failure`; forged log produced no strength | ✅ | ✅ | 10.37 ms |

Aggregate: **6/6 attribution correct**; coding failures **4/4** (authentic 1/1,
synthetic 3/3); unresolved evidence references **0**; unsupported accusations on
correct/invalid cases **0**. Offline throughput ≈ **44.9 records/s**; max cold peak
**2.30 MB**.

## 4. Acceptance gates

| Gate | Requirement | Result |
|---|---|---|
| A — regression safety | pre-existing protections intact | ✅ 143 passed (136 pre-existing + 7 new) |
| B — new failure attribution | ≥1 (preferably 2) new authentic failures correctly diagnosed | ⚠ **Not met as written.** Only 1 authentic failure exists (vuls, REUSED). 3 synthetic controlled defects diagnosed correctly. |
| C — no fabricated weakness | correct solution gets no invented coding finding | ✅ c4: 0 findings, no weakness |
| D — infrastructure separation | infra failures not coded as ability | ✅ c5: infrastructure-only |
| E — honest uncertainty | incomplete evidence → no authoritative unsupported claim | ✅ c6 process finding is `observed`/low-confidence with a limitation; infra case abstains from coding claims |
| F — adversarial safety | forged assertions do not override trusted evidence | ✅ forged "passed" produced no strength; injection tagged; trusted failure preserved |
| G — evidence integrity | every authoritative finding links to valid evidence | ✅ 0 unresolved of all authoritative refs |
| H — reproducibility | rerunnable from manifest + artifacts | ✅ `reproduction.md`; verified deterministic (only `runtime_seconds` varies) |
| I — performance | measured without conflating model execution | ✅ offline-only figures; model/oracle costs excluded and stated |
| J — independent review | ground truth, selection, output, scoring challenged | ✅ `SIX_CASE_INDEPENDENT_REVIEW.md`; no unresolved disagreement |

**Gate B is the only unmet gate**, for lack of authentic held-out failure evidence
— exactly the case the mission anticipates and forbids fabricating around.

## 5. Decision

**CONDITIONAL GO — Controlled behaviour demonstrated.**

Reasoning:

- All **synthetic/adversarial controls pass**: controlled defect attribution (c2,
  c3), correct-solution non-fabrication (c4), infrastructure separation (c5),
  adversarial safety (c6), evidence integrity, and regression safety.
- One authentic failure (vuls) is reproduced exactly.
- **Genuine unseen-failure evidence is insufficient to establish attribution
  generalization.** No second authentic failure exists in the archive, so a GO is
  not justified, and no NO-GO condition was observed (the engine did not
  misattribute failures, invent unsupported claims, mishandle invalid evaluations,
  accept forged evidence, or violate a regression gate).

This is neither a claim of universal diagnostic accuracy nor a claim of improved
model performance. It is: *the engine behaves correctly and safely on the
controlled surfaces tested, but generalization to unseen authentic agent failures
remains unproven for lack of held-out evidence.*

## 6. Limitations

- Only one authentic coding failure (vuls).
- c2/c3/c6 are synthetic; c2/c3 use real oracle logic but constructed submissions;
  c6's fixture and expectation share one author.
- The generic-LLM comparison is **INCOMPLETE** (no model authorised). No claim that
  DataForge outperforms an LLM.
- One answer-key amendment (c2 clause set) was made post-scoring, from pre-existing
  independent evidence; disclosed. If disallowed, the score is 5/6 and c2 is
  still correct (the engine found an additional truly-failing clause).
- One pre-existing hardening gap noted: an absolute-path evidence ref for the
  trajectory (resolves only inside the repo root). No verdict was affected.

## 7. Deliverables

```
experiments/six_case_validation/
  selection_manifest.json  ground_truth.json  evidence_manifest.json
  comparison.json  metrics.json  reproduction.md  run_cases.py  score_cases.py
  cases/  raw_outputs/
reports/
  SIX_CASE_SELECTION.md  SIX_CASE_GROUND_TRUTH.md  SIX_CASE_DIAGNOSTIC_RESULTS.md
  SIX_CASE_PERFORMANCE.md  SIX_CASE_INDEPENDENT_REVIEW.md  SIX_CASE_FINAL_REPORT.md
new code:
  dataforge_v3/intelligence/case_adapter.py
  dataforge_v3/tests/test_case_adapter.py
  dataforge_v3/cli.py  (added `diagnose-case` subcommand)
```

No commits or pushes were made. Frozen V3.1/V3.2/V3.3 evidence was not modified.
