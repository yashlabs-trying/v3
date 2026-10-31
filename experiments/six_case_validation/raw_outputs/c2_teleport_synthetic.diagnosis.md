# DataForge V3.3 diagnosis — teleport

- **Attempt:** `synthetic-mutant-no-ellipsis`
- **Execution validity (V3.1):** VALID
- **Semantic verdict (V3.2):** GENUINE_AGENT_FAILURE
- **Original V2 score:** None

## Summary

Verified 2 failure finding(s) (requirement_omitted) supported by independent probe evidence and the submitted patch. Demonstrated strengths are listed separately; they do not offset the failure.

## Verified strengths

- **[reproduced]** Satisfied 1 independently-probed contract clause(s): truncate.boundary.

## Verified failures

### teleport:clause:truncate.format
- **Category:** requirement_omitted | **Severity:** major | **Kind:** reproduced
- **Observed symptom:** Independent probe `teleport:truncate.format` failed against contract clause `truncate.format`: A cell longer than positive MaxCellLength renders as the first MaxCellLength characters, then '...', then ' <label>' iff the column's FootnoteLabel is non-empty.
- **Violated contract clause:** `truncate.format`
- **Competing explanations:** The independent probe is over-strict (checked by correct-alternative acceptance in V3.2); The task specification is ambiguous for this clause
- **Limitations:** The defect is verified; why the agent produced it is not observable.
  - evidence: `experiments/six_case_validation/raw_outputs/c2_teleport_oracle_local.txt` [probes[teleport:truncate.format]] — resolved, authoritative
  - evidence: `experiments/six_case_validation/cases/c2_teleport_synthetic/model.patch` [sha256] — resolved, authoritative

### teleport:clause:width.from_rendered
- **Category:** requirement_omitted | **Severity:** major | **Kind:** reproduced
- **Observed symptom:** Independent probe `teleport:width.from_rendered` failed against contract clause `width.from_rendered`: Column width equals the width of the rendered text (incl. ellipsis/label).
- **Violated contract clause:** `width.from_rendered`
- **Competing explanations:** The independent probe is over-strict (checked by correct-alternative acceptance in V3.2); The task specification is ambiguous for this clause
- **Limitations:** The patch did not show a directly matching deleted identifier; the clause violation is established by the executable probe, not the diff.; The defect is verified; why the agent produced it is not observable.
  - evidence: `experiments/six_case_validation/raw_outputs/c2_teleport_oracle_local.txt` [probes[teleport:width.from_rendered]] — resolved, authoritative
  - evidence: `experiments/six_case_validation/cases/c2_teleport_synthetic/model.patch` [sha256] — resolved, authoritative


## Capability observations

- **correct_implementation** — observations=1, n_tasks=1 (strengths: teleport; weaknesses: none) — single-task observation; not a general ability claim
- **requirements_preservation** — observations=2, n_tasks=1 (strengths: none; weaknesses: teleport) — single-task observation; not a general ability claim

## Recommended experiments

### teleport:clause:truncate.format:rec
- **Addresses finding:** `teleport:clause:truncate.format`
- **Hypothesis:** An explicit coverage checklist raises requirement coverage.
- **Intervention:** Require an explicit requirement-to-change checklist, mapped to the instruction bullets, before submission.
- **Control:** Same frozen task, same model and configuration, same evaluation budget, same independent verifier; only the intervention differs.
- **Metric:** Fraction of instruction bullets with a demonstrably satisfying change.
- **Cost estimate:** Additional inspection/token overhead to be measured per run; not claimed until executed.
- **Status:** NOT_EXECUTED — no new model execution was authorized

### teleport:clause:width.from_rendered:rec
- **Addresses finding:** `teleport:clause:width.from_rendered`
- **Hypothesis:** An explicit coverage checklist raises requirement coverage.
- **Intervention:** Require an explicit requirement-to-change checklist, mapped to the instruction bullets, before submission.
- **Control:** Same frozen task, same model and configuration, same evaluation budget, same independent verifier; only the intervention differs.
- **Metric:** Fraction of instruction bullets with a demonstrably satisfying change.
- **Cost estimate:** Additional inspection/token overhead to be measured per run; not claimed until executed.
- **Status:** NOT_EXECUTED — no new model execution was authorized


## Uncertainty and limitations

- No trajectory artifact; observable process actions are unavailable.
- The defect (if any) may be verified; the model's internal reason is not observable.
