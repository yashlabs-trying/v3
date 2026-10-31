# V2 vs V3.1 vs V3.2 — comparative experiment (Phase 2)

Same submissions, same tasks. V2 = official SWE-bench Pro V2 grading. V3.1 =
reliability layer (execution/patch integrity). V3.2 = semantic layer (this
phase). V3.2 never changes the V2 score.

## Per-task comparison (two selected tasks)

| Task | Submission | V2 reward | V3.1 | V3.2 verdict | V3.2 confidence | Agreement? |
|---|---|---|---|---|---|---|
| flipt | DeepSeek | 1.0 (PASS) | PASS | CONFIRMED_CORRECT | high | agrees |
| openlibrary | DeepSeek | 1.0 (PASS) | PASS | CONFIRMED_CORRECT | high | agrees |

## Required measurements (counts and denominators)

| Metric | Value | Denominator |
|---|---:|---:|
| Independently confirmed false PASS detected | 0 | 2 accepted submissions |
| Independently confirmed false FAIL detected | 0 | 2 accepted submissions (0 rejected in selection) |
| Known incorrect mutations rejected | 6 | 6 genuine mutants (openlibrary 3, flipt 3) |
| Mutants missed (genuine) | 0 | 6 |
| Behaviourally-equivalent mutant accepted (correctly) | 1 | 7 (flipt `m4`) |
| Independently verified correct alternatives accepted | 3 | 3 (openlibrary ref, openlibrary unordered, flipt submission) |
| Correct alternatives incorrectly rejected by V3.2 | 0 | 3 |
| False alarms introduced by V3.2 (after fix) | 0 | 3 alternatives + 2 submissions |
| False alarms found and fixed during development | 1 | — (removal-set ordering) |
| Specification mismatches discovered | 1 | — (gold patch does not apply to image base) |

## What each layer contributes

| Question | Owned by | Evidence used |
|---|---|---|
| Did the agent run? Was evidence valid? | V3.1 | lifecycle, patch provenance, execution classification |
| Did the decision match the contract? | V3.2 | independent contracts, oracles, mutants, alternatives |

## Pilot-level context (for reference only)

The V2/V3.1 fleet of seven frozen tasks: 6 PASS, 1 FAIL (`vuls`, 66/67), 0
false validation after V3.1. V3.2's two-task selection is a *risk-targeted*
subset, not the whole fleet; no fleet-wide semantic conclusions are drawn.

## Interpretation

On the two selected tasks, V2's accept decisions are **independently
corroborated**. V3.2 found no false PASS and no false FAIL. The valuable results
are (a) the verifiers provably reject genuine defects, (b) they accept correct
alternatives, and (c) the exercise surfaced a real disagreement between the
provided gold patch and the task image. "No finding" is reported as such, per
the phase rule against fabricating one.
