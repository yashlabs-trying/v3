# Recommendation Engine — DataForge V3.3 (System D)

## 1. What a recommendation is

A **testable engineering experiment**, not advice. Templates are keyed by the
finding's category, so no task-specific prose is hardcoded. Every recommendation
carries all of:

`id, finding_id, task_id, evidence[], intervention, hypothesis, control,
expected_outcome, metric, cost_estimate, confounders[], executed, execution_note`.

## 2. Anti-promise rule

`executed` stays `False` unless a controlled run actually occurred. An unexecuted
recommendation is reported as `NOT_EXECUTED`. The system never claims an
improvement because it *suggested* an experiment.

Infrastructure findings receive **no** agent-workflow recommendation: a platform
failure is not an agent-capability finding.

## 3. Templates (generic)

| Category | Intervention sketch | Metric sketch |
|---|---|---|
| existing_behavior_removed / regression | mandatory pre-edit inspection of the pre-existing test/code path; record the invariant | rate of satisfying BOTH new behaviour AND the pre-existing invariant, under an independent oracle |
| requirement_omitted | explicit requirement→change checklist before submission | fraction of instruction bullets demonstrably satisfied |
| edge_case_failure | author + run boundary probes | edge-case probe pass rate |
| interface_compatibility_violation | enumerate all call sites before edit | number of inconsistent call sites |
| relevant_test_not_executed | execute the specific covering test | fraction that ran their covering test |
| failing_test_unresolved | no-red-submission gate | fraction with an unresolved failing test |

## 4. The vuls recommendation (generated, not handwritten)

`vuls:clause:sort.equal_score_order:rec`

- **Hypothesis:** requiring pre-edit inspection of pre-existing tests reduces
  removal of established, test-covered behaviour.
- **Intervention:** mandatory pre-edit step to inspect the covering test + code
  path and record the invariant being preserved.
- **Control:** same frozen task, model, configuration, budget and verifier; only
  the intervention differs.
- **Metric:** rate of satisfying both the newly requested behaviour and the
  pre-existing invariant, scored by an independent semantic oracle.
- **Status:** NOT_EXECUTED — no new model execution authorized.

## 5. Experiment execution tracking

`experiments.py` records `ExperimentOutcome` with
`control_metric, treatment_metric, delta, tokens_added, time_added_seconds`.
`write_outcomes` persists them. See `reports/EXPERIMENT_EFFECTIVENESS.md`.

## 6. Limits

- Sample size per class is one task; a run would need repetition to separate signal
  from model stochasticity.
- Confounders (listed per recommendation) include budget interaction and
  cross-task behaviour shift.
