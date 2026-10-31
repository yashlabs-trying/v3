# Seven-Task Diagnostics — DataForge V3.3

Cohort: the seven frozen tasks plus the NodeBB recovery attempt. Reports in
`findings/intelligence/per_task/`; machine aggregate in
`findings/intelligence/fleet_diagnosis.json`.

---

## 1. Per-task results

| Task | V2 | V3.1 | V3.2 | V3.3 findings | Verified strength | Verified failure |
|---|---|---|---|---|---|---|
| flipt | PASS | VALID | CONFIRMED_CORRECT | 0 | tests run (observed) | — |
| openlibrary | PASS | VALID | CONFIRMED_CORRECT | 0 | 12 clause(s) probed passing | — |
| teleport | PASS | VALID | CONFIRMED_CORRECT | 0 | probed surface passing | — |
| ansible | PASS | VALID | CONFIRMED_CORRECT | 0 | probed surface passing | — |
| element-web | PASS | VALID | CONFIRMED_CORRECT (LruCache) | 0 | LruCache surface passing | — |
| vuls | FAIL | VALID | GENUINE_AGENT_FAILURE | 1 | score ordering correct | tie order removed |
| NodeBB original | INVALID | INVALID | INCONCLUSIVE | 1 (infra) | — | infrastructural only |
| NodeBB recovery | PASS | VALID | CONFIRMED_CORRECT | 0 | probed surface passing | — |

No passing task received a weakness finding. No failure was fabricated.

## 2. Coverage limitations (respected, not hidden)

- **element-web:** correctness is established only for the audited `LruCache`
  surface; `UserProfilesStore`/SDK-context was not oracle-tested. Verdict
  confidence is medium.
- **NodeBB original:** no independent oracle ⇒ no semantic verdict; engine emits
  infrastructure only.
- **vuls:** the oracle covers only the disputed `SortByConfident`; the wider vuls
  surface was not re-audited.
- **teleport / ansible:** conclusions are limited to the audited surfaces
  (`lib/asciitable`, `module_utils/urls` gzip handling).

## 3. Preliminary aggregate capability profile

| Dimension | observations | n_tasks | strengths | weaknesses |
|---|---:|---:|---|---|
| correct_implementation | 2 | 2 | openlibrary, vuls | — |
| regression_avoidance | 1 | 1 | — | vuls |
| testing_discipline | 7 | 7 | all valid tasks | — |

Sample note for every single-task row: "single-task observation; not a general
ability claim". This is a preliminary profile, not a calibrated ranking.

## 4. What a reader may and may not conclude

- **May:** on vuls, one established ordering invariant was removed; tests were
  observed running across the cohort; the audited surfaces of five PASS tasks
  satisfy their independent probes.
- **May not:** that the model is globally weak/strong at Go, JavaScript,
  distributed systems or caching; the cohort is small, non-random, and unevenly
  audited.

## 5. Reproduce

```bash
python -m dataforge_v3.cli intelligence --root . --out-dir findings/intelligence
python -m pytest dataforge_v3/tests -q          # 136 passing
```
