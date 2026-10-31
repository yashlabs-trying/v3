# Experiment Effectiveness — DataForge V3.3 (Phase F)

Machine-readable: `findings/intelligence/experiment_recommendations.json`.

---

## 1. Status

**The controlled experiment was NOT EXECUTED.** No new model execution was
authorized in this phase. No improvement is claimed. This section specifies the
experiment that would be run and the measurements it would produce.

## 2. Recommendation under test

`vuls:clause:sort.equal_score_order:rec`

- **Finding addressed:** removal of the established canonical tie-order
  (`sort.equal_score_order`).
- **Intervention:** mandatory pre-edit step — before changing behaviour covered by
  an existing test, inspect that test and the exercised code path and record the
  preserved invariant.
- **Hypothesis:** this reduces removal of established, test-covered behaviour.
- **Control:** the original workflow, same frozen task, same model and
  configuration, same budget, same independent semantic oracle.
- **Metric:** rate of satisfying **both** the new score-ordering clause
  (`sort.by_score`) **and** the pre-existing tie-order clause
  (`sort.equal_score_order`), as judged by the V3.2 oracle.
- **Secondary metrics:** additional time and tokens per run.
- **Confounders:** model stochasticity; small n; possible behaviour shift on
  other tasks.

## 3. Protocol that would be executed (for authorization)

1. Arm C (control): current workflow on the frozen vuls task.
2. Arm T (treatment): workflow + pre-edit comparator-test inspection step.
3. Repeat each arm `k` times (k ≥ 5 recommended) to separate signal from noise.
4. Score every run with the independent V3.2 oracle (both clauses reported
   separately so a partial fix is visible).
5. Record tokens, wall-clock and cost per run (Harbor metrics).
6. Report `control_metric`, `treatment_metric`, `delta`, `tokens_added`,
   `time_added_seconds` via `experiments.ExperimentOutcome`.

## 4. Outcome record

`experiments.not_executed(...)` was written for the recommendation:
`executed=false`, note "NOT_EXECUTED: no new model execution authorized".

## 5. Honesty statement

DataForge suggested an experiment. That is **not** evidence the experiment works,
nor evidence the model would improve with it. No such claim is made.
