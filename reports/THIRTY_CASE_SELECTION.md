# Thirty-Case Validation — Selection

Frozen before any diagnostic run. Source: `experiments/thirty_case_validation/selection_manifest.json`.
Revision `6529401f362725acbb0be276ad9ec3e4d5b9ff05`.

## Composition (30 cases)

| Category | Target | Built | Origin mix |
|---|---:|---:|---|
| Authentic agent coding failures | 2 | 2 | 1 REUSED (vuls) + 1 labelled SYNTHETIC control (slot filler) |
| Controlled, executable coding defects | 12 | 12 | SYNTHETIC (real mechanisms + real pytest oracles) |
| Independently verified correct solutions | 6 | 6 | SYNTHETIC (correct implementations, real oracles) |
| Infrastructure-invalid executions | 4 | 4 | 3 REUSED + 1 SYNTHETIC |
| Ambiguous / incomplete evidence | 3 | 3 | SYNTHETIC |
| Forged / adversarial evidence | 3 | 3 | SYNTHETIC |

## Coverage gap (stated, not hidden)

A full sweep of every saved job (`jobs/**/instance_*/result.json`) found **exactly
one** authentic failure with real model tokens, a non-empty patch and reward 0:
`vuls`. Every other 0.0 is infrastructure (0 tokens), a timeout-constrained audit
run (empty patch), or a replay. The **second authentic-failure slot is therefore a
clearly-labelled synthetic control** (`auth_02_synthetic_control`, the teleport
no-ellipsis mutant reproduced locally in the six-case effort). No claim of
generalization to unseen authentic agent failures is made anywhere in this report.

## The 12 controlled defects (mechanism coverage)

| Case | Mechanism | Clause kind → engine category |
|---|---|---|
| def_01_boundary_offbyone | incorrect boundary condition | EDGE_CASE → edge_case_failure |
| def_02_error_handling | error handling | ERROR_BEHAVIOR → edge_case_failure |
| def_03_state_consistency | state consistency | INVARIANT → existing_behavior_removed |
| def_04_ordering_invariant | ordering invariant | INVARIANT → existing_behavior_removed |
| def_05_api_compat | API compatibility | EDGE_CASE → edge_case_failure |
| def_06_resource_cleanup | resource cleanup | ERROR_BEHAVIOR → edge_case_failure |
| def_07_data_transform | data transformation | INVARIANT → existing_behavior_removed |
| def_08_cache_invalidation | cache invalidation | INVARIANT → existing_behavior_removed |
| def_09_incorrect_fallback | incorrect fallback | POSTCONDITION → requirement_omitted |
| def_10_partial_update | partial update | POSTCONDITION → requirement_omitted |
| def_11_offbyone_rle | off-by-one (distinct function) | EDGE_CASE → edge_case_failure |
| def_12_regression | regression preservation | POSTCONDITION → requirement_omitted |

Each defect is a **multi-branch function** (not a one-line mutation), paired with a
real pytest oracle. The failing probe set was produced by running the real pytest
runner (`builder/run_oracles.py`), never asserted by hand.

## Correct solutions

Six correct implementations of the same real mechanisms (`paginate`, `kvstore`,
`resource`, `lookup`, `total`, `rle`), each verified to pass its oracle.

## Infrastructure / ambiguous / adversarial

- Infra: `deepseek2-flipt-a1` (0-token API failure), `final-nodebb` (contaminated
  patch, no responses), `deepseek2-nodebb-a1` (contaminated runtime-only patch),
  and a synthetic runner failure with a `replay.json`.
- Ambiguous: missing semantic oracle; contradictory probe records on one clause;
  truncated/incomplete evidence.
- Adversarial: forged success assertion, prompt injection, fabricated evidence
  reference.
