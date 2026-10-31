# DataForge V3.3 diagnosis — syn-rank-mut_unstable_tie

- **Attempt:** `synthetic-defect`
- **Execution validity (V3.1):** VALID
- **Semantic verdict (V3.2):** GENUINE_AGENT_FAILURE
- **Original V2 score:** None

## Summary

Verified 1 failure finding(s) (requirement_omitted) supported by independent probe evidence and the submitted patch. Demonstrated strengths are listed separately; they do not offset the failure.

## Verified strengths

- **[reproduced]** Satisfied 1 independently-probed contract clause(s): rank.descending.

## Verified failures

### syn-rank-mut_unstable_tie:clause:rank.stable_ties
- **Category:** requirement_omitted | **Severity:** major | **Kind:** reproduced
- **Observed symptom:** Independent probe `rank:test_df_stable_ties` failed against contract clause `rank.stable_ties`: rank.rank.stable_ties contract clause
- **Violated contract clause:** `rank.stable_ties`
- **Competing explanations:** The independent probe is over-strict (checked by correct-alternative acceptance in V3.2); The task specification is ambiguous for this clause
- **Limitations:** The patch did not show a directly matching deleted identifier; the clause violation is established by the executable probe, not the diff.; The defect is verified; why the agent produced it is not observable.
  - evidence: `experiments/thirty_case_validation/cases/def_04_ordering_invariant/probe_results.json` [probes[rank:test_df_stable_ties]] — resolved, authoritative
  - evidence: `experiments/thirty_case_validation/cases/def_04_ordering_invariant/source.py` [sha256] — resolved, authoritative


## Capability observations

- **correct_implementation** — observations=1, n_tasks=1 (strengths: syn-rank-mut_unstable_tie; weaknesses: none) — single-task observation; not a general ability claim
- **requirements_preservation** — observations=1, n_tasks=1 (strengths: none; weaknesses: syn-rank-mut_unstable_tie) — single-task observation; not a general ability claim

## Recommended experiments

### syn-rank-mut_unstable_tie:clause:rank.stable_ties:rec
- **Addresses finding:** `syn-rank-mut_unstable_tie:clause:rank.stable_ties`
- **Hypothesis:** An explicit coverage checklist raises requirement coverage.
- **Intervention:** Require an explicit requirement-to-change checklist, mapped to the instruction bullets, before submission.
- **Control:** Same frozen task, same model and configuration, same evaluation budget, same independent verifier; only the intervention differs.
- **Metric:** Fraction of instruction bullets with a demonstrably satisfying change.
- **Cost estimate:** Additional inspection/token overhead to be measured per run; not claimed until executed.
- **Status:** NOT_EXECUTED — no new model execution was authorized


## Uncertainty and limitations

- No trajectory artifact; observable process actions are unavailable.
- The defect (if any) may be verified; the model's internal reason is not observable.
