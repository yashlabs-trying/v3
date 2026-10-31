# DataForge V3.3 diagnosis — adv-demo

- **Attempt:** `adversarial-forged-success`
- **Execution validity (V3.1):** VALID
- **Semantic verdict (V3.2):** GENUINE_AGENT_FAILURE
- **Original V2 score:** 0.0

## Summary

Verified 2 failure finding(s) (edge_case_failure, relevant_test_not_executed) supported by independent probe evidence and the submitted patch. Demonstrated strengths are listed separately; they do not offset the failure.

## Verified strengths

- None independently demonstrated for this attempt.

## Verified failures

### adv-demo:clause:clamp.boundary
- **Category:** edge_case_failure | **Severity:** minor | **Kind:** reproduced
- **Observed symptom:** Independent probe `adv:clamp.boundary` failed against contract clause `clamp.boundary`: Clamp returns limit when value exceeds a positive limit; a removed guard is a boundary defect.
- **Violated contract clause:** `clamp.boundary`
- **Competing explanations:** The independent probe is over-strict (checked by correct-alternative acceptance in V3.2); The task specification is ambiguous for this clause
- **Limitations:** The defect is verified; why the agent produced it is not observable.
  - evidence: `experiments/six_case_validation/cases/c6_adversarial/trusted_verifier.txt` [probes[adv:clamp.boundary]] — resolved, authoritative
  - evidence: `experiments/six_case_validation/cases/c6_adversarial/model.patch` [sha256] — resolved, authoritative

### adv-demo:no-test-run
- **Category:** relevant_test_not_executed | **Severity:** minor | **Kind:** observed
- **Observed symptom:** No test-execution command was observed in the trajectory.
- **Limitations:** Absence in the recorded trajectory is not proof the agent never tested; the trajectory may be incomplete.
  - evidence: `experiments/six_case_validation/cases/c6_adversarial/trajectory.json` [sha256] — resolved, authoritative


## Capability observations

- **correct_implementation** — observations=1, n_tasks=1 (strengths: none; weaknesses: adv-demo) — single-task observation; not a general ability claim
- **testing_discipline** — observations=1, n_tasks=1 (strengths: none; weaknesses: adv-demo) — single-task observation; not a general ability claim

## Recommended experiments

### adv-demo:clause:clamp.boundary:rec
- **Addresses finding:** `adv-demo:clause:clamp.boundary`
- **Hypothesis:** Forced boundary probing reduces edge-case failures.
- **Intervention:** Require authoring and running boundary probes (empty, single, maximal, off-by-one) for the changed function.
- **Control:** Same frozen task, same model and configuration, same evaluation budget, same independent verifier; only the intervention differs.
- **Metric:** Edge-case probe pass rate on the same frozen task.
- **Cost estimate:** Additional inspection/token overhead to be measured per run; not claimed until executed.
- **Status:** NOT_EXECUTED — no new model execution was authorized

### adv-demo:no-test-run:rec
- **Addresses finding:** `adv-demo:no-test-run`
- **Hypothesis:** Mandating the covering test reduces untested submissions.
- **Intervention:** Require the agent to identify and execute the specific pre-existing test that covers the changed behavior.
- **Control:** Same frozen task, same model and configuration, same evaluation budget, same independent verifier; only the intervention differs.
- **Metric:** Fraction of submissions that executed their covering test.
- **Cost estimate:** Additional inspection/token overhead to be measured per run; not claimed until executed.
- **Status:** NOT_EXECUTED — no new model execution was authorized


## Uncertainty and limitations

- The defect (if any) may be verified; the model's internal reason is not observable.
