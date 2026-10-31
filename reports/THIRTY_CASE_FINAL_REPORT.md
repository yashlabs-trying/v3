# Thirty-Case Validation — Final Report

**Scope:** a controlled 30-case diagnostic benchmark of the existing DataForge V3.3
engine, preceded by evidence-path hardening. Offline; no model calls; no Docker.

**Verdict: CONDITIONAL GO — controlled behaviour demonstrated; authentic held-out
failure coverage remains insufficient.**

---

## 1. What was done

- Reconnaissance of `C:\Users\yashs\dataforge\v3` (branch `v3.3-phase3`, rev `6529401`);
  the uncommitted six-case work was preserved.
- **Section 2 — evidence-path hardening.** Reproduced the absolute-path / broad-trust
  weakness (pre-fix **8/11** expectations met) and fixed it with approved-evidence-root
  containment plus absolute/UNC/traversal rejection (post-fix **11/11**). `.git/config`
  and answer keys can no longer be cited as verification evidence.
- Searched the entire archive: **exactly one authentic failure (vuls)** exists.
- Built a **frozen 30-case cohort** with executable, independently-produced ground
  truth (real pytest oracles; local Go/Node re-execution).
- Ran the real engine, adjudicated mismatches, applied **one general fix** for a
  genuine defect, and reran — preserving all raw results.

## 2. Results

### Headline (post-fix)

| Measure | Value |
|---|---:|
| Correct case classifications | **30 / 30** |
| Evidence-valid cases | **30 / 30** |
| Unresolved evidence references | **0** |
| False accusations on correct solutions | **0 / 6** |
| Infrastructure attributed to model | **0 / 4** |
| Authentic failures correct | 1 / 1 |
| Controlled defects correct | 12 / 12 |
| Ambiguous correctly abstained/downgraded | 3 / 3 |
| Adversarial forged-log rejected | 3 / 3 |

### Before / after

| Run | Correct | Evidence | Unresolved |
|---|---:|---:|---:|
| First pass (naive key) | 24/30 | 29/30 | 1 |
| Pre-fix (adjudicated key) | 29/30 | 29/30 | 1 |
| **Post-fix** | **30/30** | **30/30** | **0** |

### Defects found and fixed (general, regression-tested)

1. **Contradictory probe evidence** on one clause produced an **authoritative**
   finding (`amb_02`). Fixed by `attribution._contradictory_clauses`: such clauses
   downgrade to hypothesis. 2 regression tests.
2. **Absolute-path evidence ref** emitted for trajectories (pre-existing) — now
   normalised to repo-relative. 2 regression tests.
3. **Broad evidence trust** — any repo file (including `.git/config`, answer keys)
   resolved as authoritative. Fixed by approved-root containment. 7 regression tests.

The other first-pass mismatches were **answer-key corrections** (the documented
INVARIANT→requirement_omitted fallback), explicitly logged, not engine changes.

## 3. Acceptance criteria

| Criterion | Met? |
|---|---|
| Engine behaves correctly across the independently verified cohort | ✅ 30/30 |
| Evidence security protections pass | ✅ 11/11 (was 8/11) |
| No critical false accusations remain | ✅ 0/6 correct solutions accused |
| Results reproducible | ✅ `reproduce.md`; deterministic |
| Authentic held-out failure coverage | ❌ only 1 real failure exists |

## 4. Decision

**CONDITIONAL GO — Controlled behaviour demonstrated.**

- All controlled, correct, infrastructure, ambiguous and adversarial cases behave
  correctly; the evidence-security protections pass; one genuine robustness defect
  was found and fixed generally with regression tests; no critical false accusation
  or fabricated authoritative claim remains.
- **Genuine held-out failure coverage is insufficient** (one authentic failure), so
  a GO is not justified and generalization to unseen authentic agent failures is
  **not claimed**.
- No NO-GO condition was observed.

## 5. Limitations

- One authentic coding failure (vuls); its "authentic-failure" partner is a
  labelled synthetic control.
- Controlled defects and correct solutions are synthetic (real mechanisms + real
  oracles, but not agent submissions).
- Adversarial fixtures are single-author.
- The generic-LLM baseline is **INCOMPLETE** (no model authorised); no superiority
  claim.
- Strict defect-category match is 26/30; 4 use the engine's documented fallback.
- Performance figures are observed samples (per-case n=5), not population estimates.

## 6. Deliverables

```
experiments/thirty_case_validation/
  selection_manifest.json  ground_truth.json  evidence_manifest.json
  original_scores.json  post_fix_scores.json  metrics.json  performance.json  reproduce.md
  cases/ (30)  raw_outputs/{original,postfix}/  builder/  security/
reports/
  THIRTY_CASE_SELECTION.md  THIRTY_CASE_GROUND_TRUTH.md  THIRTY_CASE_DIAGNOSTIC_RESULTS.md
  THIRTY_CASE_ADVERSARIAL_AUDIT.md  THIRTY_CASE_PERFORMANCE.md
  THIRTY_CASE_INDEPENDENT_REVIEW.md  THIRTY_CASE_FINAL_REPORT.md
engine changes:
  dataforge_v3/intelligence/evidence.py (security), attribution.py (contradiction + path),
  cli.py (diagnose-case), case_adapter.py, tests/* (+18 tests)
```

Regression suite: **154 passed** (143 baseline → 152 → 154 with the new tests).
Frozen V3.1/V3.2/V3.3 evidence restored unchanged. Nothing committed or pushed.
