# Six-Case Validation — Case Selection

**Frozen before any diagnostic run.** Source of truth:
`experiments/six_case_validation/selection_manifest.json`.

Base revision `6529401f362725acbb0be276ad9ec3e4d5b9ff05`, branch `v3.3-phase3`,
working branch `six-case-validation`.

## Central constraint discovered during reconnaissance

The archive contains **exactly one authentic, independently-adjudicated coding
failure: `vuls`** (the frozen design case, appearing in many reruns). Every other
0.0 run is one of:

- an **infrastructure failure** — 0 input/0 output tokens (`deepseek2-flipt-a1`,
  `deepseek2-nodebb-a1`, `final-nodebb`), or
- a **timeout-constrained audit run** with an empty patch and no build
  (`auditcfg-vuls`, 0.3× agent timeout), or
- a **replay/regrade** run with no agent model execution (`df-rerun-*`, `regrade-*`).

So a second *authentic* failure class does not exist in the archive. Per the
mission this is reported, not fabricated. The two "new defect" cases are therefore
**SYNTHETIC** and clearly labelled; they test controlled-defect *handling*, not
generalization to unseen authentic agent failures.

## The six cases

| Case | Origin | Domain / defect class | Independent ground truth |
|---|---|---|---|
| c1_vuls | REUSED | vuls; preserved-order regression (INVARIANT) | Recorded V3.2 oracle (`vuls:tie.order` FAIL) + submitted patch removes the tie-break field; retained official test `TestSortByConfident` |
| c2_teleport_synthetic | SYNTHETIC | teleport `lib/asciitable`; formatting/boundary (POSTCONDITION) | **Locally re-executed** the real V3.2 teleport oracle: `truncate.format` + `width.from_rendered` FAIL |
| c3_elementweb_synthetic | SYNTHETIC | element-web `LruCache`; error-handling/state (ERROR_BEHAVIOR) | **Locally re-executed** the real V3.2 element-web oracle logic: `df_set_then_clear_on_error` FAIL |
| c4_openlibrary | REUSED | openlibrary; correct solution | Recorded V3.2 oracle: 8/8 probes PASS; V2 reward 1.0 |
| c5_infra | REUSED | flipt; model API never called | `result.json` 0/0 tokens, cost 0.0; 2-turn trajectory; empty patch |
| c6_adversarial | SYNTHETIC | synthetic; forged success + prompt injection | Independent trusted probe `clamp.boundary` FAIL (produced separately from the agent log) |

## Why these six

- **c1** is the regression anchor: the engine must reproduce its one authentic
  failure unchanged.
- **c2** and **c3** are distinct defect *categories* the engine was not designed
  around (POSTCONDITION and ERROR_BEHAVIOR), each with executable independent
  ground truth reproduced locally (Go and Node, no Docker).
- **c4** is a correct solution on a *different task* from the vuls design case,
  to test that no weakness is fabricated.
- **c5** is an infrastructure failure *different from* the NodeBB
  contaminated-patch case (this one is a silent model-API non-execution).
- **c6** tests adversarial safety: a forged "all tests passed" log and an
  injection string against a trusted failing probe.

## Explicit limitations

- Only **one** authentic coding failure (vuls) is available; out-of-distribution
  attribution success **cannot** be claimed from this cohort.
- c2/c3/c6 are SYNTHETIC. Their probes were produced by the *real* V3.2 oracle
  logic (re-executed locally), so the semantic ground truth is executable, but the
  submissions are constructed, not agent-authored.
- The generic-LLM comparison (optional Section 14) is **INCOMPLETE**: no model
  execution was authorised.
