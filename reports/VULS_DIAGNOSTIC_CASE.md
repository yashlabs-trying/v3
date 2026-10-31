# VULS Diagnostic Case — DataForge V3.3

**Task:** `instance_future-architect__vuls-f0b3a8b1db98eb1bd32685f1c36c41a99c3452ed`
**Attempt:** `f3-vuls-a1` / `instance_future-architect__vuls__sNqH5s4` (original DeepSeek).
**V2:** FAIL (score 0.0). **V3.1:** VALID. **V3.2:** GENUINE_AGENT_FAILURE.

Generated artifact: `findings/intelligence/per_task/vuls.md` (+ `.json`).

---

## 1. Transformation

Ordinary result:

> DeepSeek — vuls — FAIL

DataForge V3.3 output:

- **Evaluation integrity:** VALID (V3.1).
- **Semantic verdict:** GENUINE_AGENT FAILURE (V3.2).
- **Verified defect:** the implementation removed the established canonical
  tie-breaking behaviour while changing confidence-score sorting.
- **Demonstrated success:** descending numeric-score ordering is correct on the
  audited cases (clause `sort.by_score` probe PASSED).
- **Demonstrated failure:** equal-score canonical ordering is not preserved
  (clause `sort.equal_score_order` probe FAILED).
- **Evidence:** the executable independent oracle counterexample and the submitted
  source diff, both resolvable and hashed.
- **Observed process:** tests were run during the attempt (observed command
  events); the defect is a behavioral regression, not an untested submission.
- **Engineering recommendation:** test whether mandatory pre-edit inspection of
  the pre-existing comparator test reduces this class of regression.
- **Uncertainty:** the defect is verified; the model's internal reason is not
  observable.

## 2. How each claim was derived (no hardcoding)

| Output element | Source | Mechanism |
|---|---|---|
| Execution VALID | V3.1 replay / Phase-1B label | label read from `TaskEvidence` |
| Failed clause `sort.equal_score_order` | V3.2 probe `vuls:tie.order` | probe→clause id from `vuls_semantic_evidence.json` |
| Category `existing_behavior_removed` | clause kind `INVARIANT` **and** patch deletes clause-mechanism tokens | generic token overlap between deleted diff lines and clause text (`OvalMatch` deleted) |
| Confidence high, kind reproduced | probe carries a counterexample | `_clause_finding` rule |
| Strength `sort.by_score` | passing probe `vuls:score.order` | passed-probe → strength |
| Recommendation | category template | `recommendations._TEMPLATES[existing_behavior_removed]` |

The engine contains no `vuls`, `SortOrder`, `CpeVersionMatch` or
`TestSortByConfident` token in its code string literals (enforced by
`test_vuls_diagnosis_is_not_hardcoded`).

## 3. The disagreement, precisely

The official retained test requires, for equal scores (100, 100):

```
in  {CpeVersionMatch, OvalMatch} -> out {OvalMatch, CpeVersionMatch}
```

DeepSeek's comparator `cs[i].Score > cs[j].Score` is a *non-stable* sort by score;
equal-score items retain input order, so the output is a function of input order,
not of the confidence set. The pre-existing implementation ordered equal scores
via a `SortOrder` field. Removing it changes established, test-covered behaviour.

## 4. Reproduce

```bash
# offline (no Docker)
python -m pytest dataforge_v3/tests/test_vuls_oracle.py dataforge_v3/tests/test_intelligence_integration.py -q
# regenerate this diagnosis
python -m dataforge_v3.cli intelligence --root . --out-dir findings/intelligence
```

## 5. Limits

- One disputed test (`TestSortByConfident`); the broader vuls surface was not
  re-audited in this step.
- The engine confirms the V2 FAIL; it does **not** overturn it.
- The verified defect does not establish a general model deficiency.
