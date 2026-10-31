# DataForge V3.2 — Phase 2 Final Report
## Semantic Correctness & Evaluation Fairness

**Branch:** `v3.2-phase2` (off V3.1 Phase 1B `6d0c072`)
**Baseline preserved:** V3.1 reliability layer and V2 scores unchanged
**Ultimate question:** Can DataForge independently determine when an existing AI
coding benchmark accepted an incorrect solution or rejected a correct one — with
executable, reproducible evidence?

**Answer (this pilot):** Yes, the method is demonstrated and executable. On the
two selected tasks it found **no confirmed false PASS or false FAIL**; it did
prove that the independent verifiers reject genuine defects and accept correct
alternatives, and it caught and fixed one false alarm in its own oracle.

---

## 1. What was built (V3.2 layer, modules A–E)

| Module | File | Function |
|---|---|---|
| A. Specification Contract Auditor | `semantic/contract.py` | clauses + coverage vs official tests; ambiguous/unsupported flags |
| B. Semantic Test Generator | `semantic/generators.py`, `semantic/tasks/*` | deterministic property/boundary/stateful probes from contracts |
| C. Mutation & Alternative Validator | `semantic/mutation.py` | rejects defective variants, accepts correct alternatives |
| D. Verdict Disagreement Analyzer | `semantic/disagreement.py` | conservative verdict policy |
| E. Independent Evidence Reporter | `semantic/reporter.py` | reproducible counterexamples + commands |
| Driver / oracle plumbing | `semantic/evaluate.py`, `semantic/audit.py`, `semantic/oracle.py`, `semantic/executors.py` | wire it together; Docker Go executor |

The layer is additive. No V3.1 module was weakened; no V2 score is altered.

## 2. Method (frozen before outcomes)

- Selection criteria and the two tasks were frozen in
  `reports/PHASE_2_TASK_SELECTION.md` **before** any probe ran.
- Tasks: **flipt** (Go auth middleware; false-PASS risk in multi-cookie/bypass
  semantics) and **openlibrary** (Python Solr reindex; set-semantics/overfit risk).
- Base baseline recorded in `reports/PHASE_2_BASELINE.md`.

## 3. Results

### 3.1 Verdicts

| Task | Submission | V2 | V3.1 | V3.2 | Confidence |
|---|---|---|---|---|---|
| flipt | DeepSeek | PASS (1.0) | PASS | **CONFIRMED_CORRECT** | high |
| openlibrary | DeepSeek | PASS (1.0) | PASS | **CONFIRMED_CORRECT** | high |

### 3.2 Did the verifiers work?

- **Mutants rejected:** 6 / 6 genuine defects (openlibrary 3/3, flipt 3/3),
  each attributed to the violated clause (`MUTATION_TEST_RESULTS.md`).
- **Correct alternatives accepted:** 3 / 3; 0 false alarms after the fix
  (`ALTERNATIVE_SOLUTIONS.md`).
- **False alarm found and fixed:** the openlibrary comparator initially
  over-constrained the removal-set order and rejected the correct submission.
  Fixed; regression-guarded. This is a methodology success, not a defect.

### 3.3 Deliverables produced

`PHASE_2_BASELINE.md`, `PHASE_2_TASK_SELECTION.md`, `SEMANTIC_CONTRACTS.md`,
`FALSE_PASS_FINDINGS.md`, `FALSE_FAIL_FINDINGS.md`, `MUTATION_TEST_RESULTS.md`,
`ALTERNATIVE_SOLUTIONS.md`, `V2_VS_V3_2.md`, `PERFORMANCE_AND_COST.md`,
`INDEPENDENT_REVIEW.md`, this report. Machine-readable:
`findings/semantic_audit.json`, `findings/semantic_assessment_{flipt,openlibrary}.md`.

## 4. Acceptance criteria

| Criterion | Met? | Evidence |
|---|---|---|
| A complete semantic-audit methodology demonstrated on real tasks | **yes** | both tasks audited end-to-end, Docker Go + in-process Python |
| Independently correct alternatives not rejected by our verifier | **yes** | 3/3 accepted; false alarm fixed |
| Known defective variants detected with reproducible evidence | **yes** | 6/6 genuine mutants, clause-attributed counterexamples |
| Claimed false verdicts justified by reviewed contracts | **yes** | none claimed; contracts reviewable data |
| V3.1 PASS/FAIL + reliability protections intact | **yes** | additive tree; 67 V3.1 tests still pass |
| Performance overhead measured | **yes** | `PERFORMANCE_AND_COST.md` |
| No critical unresolved regressions | **yes** | 90 tests pass, including clean-checkout |

## 5. Honest limitations

1. Two tasks only — no fleet or benchmark-level claim.
2. CONFIRMED_CORRECT means "no supported clause falsified", not general
   correctness.
3. Contracts are human-authored and could miss a clause; ambiguous clauses can
   never yield a confirmed finding.
4. The provided gold patch does not apply to the task image base (flagged to
   maintainers; not used as authority).
5. `vuls` (the pilot's only V2 FAIL) was not in the Phase 2 selection; it is the
   natural first task for the expansion cohort.

## 6. Reproduce

```bash
# unit + semantic engine tests (90)
python -m pytest dataforge_v3/tests -q

# openlibrary semantic audit (in-process, ~0.03s)
python - <<'PY'
from pathlib import Path
from dataforge_v3.semantic.audit import audit_openlibrary
print(audit_openlibrary(Path("findings/new-solr-updater.deepseek.py"), "deepseek", 1.0, "PASS").to_json())
PY

# flipt semantic audit (Docker + go test, ~1 min)
bash scripts/run_flipt_semantic.sh findings/mw_deepseek.go
```

## 7. GO / NO-GO

**Recommendation: CONDITIONAL GO to the expansion cohort; NO-GO on any
claim about false verdicts in SWE-bench Pro V2 as a whole.**

- GO: expand to `vuls` (the genuine FAIL) and the remaining frozen tasks, and
  broaden oracle coverage. The engine, methodology, and scoring policy are in
  place and independently reviewed.
- NO-GO: publishing any "X% of Pro V2 verdicts are wrong" claim. Two tasks, no
  confirmed defect, oracle feasibility bias.
- Hold Phase 3 until the V3.2 results are reviewed, per instruction.
