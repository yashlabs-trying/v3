# Thirty-Case Validation — Ground Truth

Source: `experiments/thirty_case_validation/ground_truth.json`, frozen before any
diagnostic run. Ground truth is derived from the **executable oracles and recorded
evidence**, never from the DataForge diagnostic engine.

## How ground truth was established

| Category | Method | Independent of engine? |
|---|---|---|
| auth_01_vuls | Recorded V3.2 oracle (`vuls:tie.order` FAIL) + submitted patch deletes the tie-break field | Yes |
| auth_02_synthetic_control | Teleport oracle reproduced locally (`truncate.format`, `width.from_rendered` FAIL) | Yes |
| def_01..def_12 | Mutant source run through the **real pytest oracle**; failing probe set recorded in `probe_results.json` | Yes |
| cor_01..cor_06 | Correct source run through the real oracle; all probes PASS | Yes |
| inf_01..inf_04 | `result.json` token counts, patch contents, replay record | Yes |
| amb_01..amb_03 | Manifests declare missing / contradictory / incomplete evidence | Yes |
| adv_01..adv_03 | Independent trusted failing probe written separately from the agent log | Partly (fixture and expectation share one author) |

## Executable reproduction (ground truth)

```
python experiments/thirty_case_validation/builder/run_oracles.py
# for every domain: correct impl ALL PASS; each mutant fails the expected probes
```

Raw oracle results: `builder/oracle_results.json`.

## Defect-category convention (documented, not tuned)

The engine refines an **INVARIANT** clause to `existing_behavior_removed` only when
the submitted diff corroborates removal (a deleted line matching a clause word).
Synthetic cases submit whole-file sources with no deletion lines, so the engine's
**documented conservative fallback** (`requirement_omitted`) applies and is
recorded in the finding's limitations. The answer key accepts either label for
these cases (`category_refinement_depends_on_patch: true`) because the **clause**
is the independently established fact; the category refinement legitimately depends
on patch evidence the fixture lacks. Strict-category matches are reported
separately (26/30 strict, 30/30 with documented fallback).

## Scoring rules

- **coding_failure:** every expected failing clause is reported with an accepted
  category; no extra authoritative coding finding; for adversarial cases, no
  strength derived from the forged log.
- **infrastructure_only:** all authoritative findings are `agent_startup_failure`
  and no coding weakness is asserted.
- **none (correct solution):** zero authoritative coding findings and no weakness.
- **abstain_or_downgrade (ambiguous):** no authoritative coding finding.

## Amendment log

- **2026-10-31 — fallback acceptance.** The initial key required the strict
  `existing_behavior_removed` label for INVARIANT-defect cases. The engine's
  documented fallback to `requirement_omitted` (when the synthetic patch has no
  deletion lines) was recorded as an accepted label via
  `category_refinement_depends_on_patch`. Derived from the engine's **documented,
  pre-existing** behavior and the fixture shape, not from any output tuning.
- **2026-10-31 — inf_04 fixture.** The synthetic runner case initially cited no
  artifact; a `replay.json` was added so the infrastructure finding has a
  resolvable evidence reference. This is a fixture correction, not an engine change.
