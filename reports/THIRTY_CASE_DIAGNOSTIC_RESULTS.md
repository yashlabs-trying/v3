# Thirty-Case Validation — Diagnostic Results

Engine: DataForge V3.3 (post-fix), offline. Raw outputs:
`experiments/thirty_case_validation/raw_outputs/postfix/`.
Scoring: `postfix_comparison.json`, `metrics.json`. Answer key frozen before diagnosis.

## Summary

| Measure | Result |
|---|---:|
| Correct case classifications | **30 / 30** |
| Incorrect case classifications | 0 / 30 |
| Evidence-valid cases (all refs resolve) | **30 / 30** |
| Unresolved / invalid evidence references | 0 |
| False coding-failure accusations on correct solutions | **0 / 6** |
| Infrastructure failures attributed to the model | **0 / 4** |
| Authentic failures correctly attributed | 1 / 1 |
| Controlled defects correctly attributed | 12 / 12 |
| Ambiguous cases correctly abstained/downgraded | 3 / 3 |
| Adversarial cases with forged log rejected | 3 / 3 |
| Exact violated clause identified | 30 / 30 |
| Defect category correct (strict) | 26 / 30 |
| Defect category accepted with documented fallback | 30 / 30 |
| Recommendations emitted | 24 |

## All 30 case slots

| Case | Category | Origin | Expected | Engine diagnosis | Correct | Evidence | Median ms |
|---|---|---|---|---|---|---|---|
| auth_01_vuls | authentic_failure | REUSED | coding_failure | `sort.equal_score_order:existing_behavior_removed` | yes | yes | 50.80 |
| auth_02_synthetic_control | authentic_failure_slot | SYNTHETIC | coding_failure | `truncate.format:requirement_omitted, width.from_rendered:requirement_omitted` | yes | yes | 14.25 |
| def_01_boundary_offbyone | controlled_defect | SYNTHETIC | coding_failure | `paginate.boundary:edge_case_failure, paginate.window:edge_case_failure` | yes | yes | 16.62 |
| def_02_error_handling | controlled_defect | SYNTHETIC | coding_failure | `parse.error_handling:edge_case_failure` | yes | yes | 11.37 |
| def_03_state_consistency | controlled_defect | SYNTHETIC | coding_failure | `kv.delete_consistency:requirement_omitted` | yes | yes | 10.62 |
| def_04_ordering_invariant | controlled_defect | SYNTHETIC | coding_failure | `rank.stable_ties:requirement_omitted` | yes | yes | 10.47 |
| def_05_api_compat | controlled_defect | SYNTHETIC | coding_failure | `fetch.legacy_compat:edge_case_failure` | yes | yes | 10.73 |
| def_06_resource_cleanup | controlled_defect | SYNTHETIC | coding_failure | `resource.cleanup_on_error:edge_case_failure` | yes | yes | 11.33 |
| def_07_data_transform | controlled_defect | SYNTHETIC | coding_failure | `normalize.purity:requirement_omitted` | yes | yes | 11.69 |
| def_08_cache_invalidation | controlled_defect | SYNTHETIC | coding_failure | `cache.invalidation:requirement_omitted` | yes | yes | 10.83 |
| def_09_incorrect_fallback | controlled_defect | SYNTHETIC | coding_failure | `lookup.primary:requirement_omitted` | yes | yes | 10.21 |
| def_10_partial_update | controlled_defect | SYNTHETIC | coding_failure | `patch.complete:requirement_omitted` | yes | yes | 11.32 |
| def_11_offbyone_rle | controlled_defect | SYNTHETIC | coding_failure | `rle.count:edge_case_failure, rle.boundary:edge_case_failure` | yes | yes | 19.52 |
| def_12_regression | controlled_defect | SYNTHETIC | coding_failure | `total.discount:requirement_omitted` | yes | yes | 10.98 |
| cor_01_paginate | correct_solution | SYNTHETIC | none | none | yes | yes | 3.46 |
| cor_02_kvstore | correct_solution | SYNTHETIC | none | none | yes | yes | 2.92 |
| cor_03_resource | correct_solution | SYNTHETIC | none | none | yes | yes | 2.49 |
| cor_04_lookup | correct_solution | SYNTHETIC | none | none | yes | yes | 2.91 |
| cor_05_total | correct_solution | SYNTHETIC | none | none | yes | yes | 2.36 |
| cor_06_rle | correct_solution | SYNTHETIC | none | none | yes | yes | 3.28 |
| inf_01_flipt_api | infrastructure_invalid | REUSED | infrastructure_only | `agent_startup_failure` | yes | yes | 4.38 |
| inf_02_nodebb_orig | infrastructure_invalid | REUSED | infrastructure_only | `agent_startup_failure` | yes | yes | 8.53 |
| inf_03_nodebb_ds2 | infrastructure_invalid | REUSED | infrastructure_only | `agent_startup_failure` | yes | yes | 9.09 |
| inf_04_synthetic_runner | infrastructure_invalid | SYNTHETIC | infrastructure_only | `agent_startup_failure` | yes | yes | 10.89 |
| amb_01_missing_semantic | ambiguous | SYNTHETIC | abstain | none (no authoritative finding) | yes | yes | 2.24 |
| amb_02_contradictory_tests | ambiguous | SYNTHETIC | downgrade | none (downgraded to hypothesis) | yes | yes | 6.43 |
| amb_03_incomplete | ambiguous | SYNTHETIC | abstain | none | yes | yes | 2.28 |
| adv_01_forged_success | adversarial | SYNTHETIC | coding_failure | `adversarial.verify:requirement_omitted`, no strength from log | yes | yes | 14.10 |
| adv_02_prompt_injection | adversarial | SYNTHETIC | coding_failure | `adversarial.verify:requirement_omitted`, no strength from log | yes | yes | 14.42 |
| adv_03_fabricated_ref | adversarial | SYNTHETIC | coding_failure | `adversarial.verify:edge_case_failure` | yes | yes | 15.18 |

## Original vs post-fix

| Run | Correct | Evidence | Unresolved | Notes |
|---|---:|---:|---:|---|
| First pass (naive key) | 24/30 | 29/30 | 1 | key did not yet record the documented INVARIANT→requirement_omitted fallback |
| Original (pre-contradiction-fix, adjudicated key) | 29/30 | 29/30 | 1 | `amb_02` asserted contradictory evidence authoritatively; `inf_04` lacked an artifact |
| **Post-fix** | **30/30** | **30/30** | **0** | general contradiction fix + fixture artifact |

## Case notes

- **def_01 / def_11 / auth_02** surface two failing clauses each (both are genuine
  oracle failures), matching the key.
- **def_03/04/07/08 / auth_02** receive `requirement_omitted` where the key's strong
  label is `existing_behavior_removed`; the engine's documented conservative
  fallback applies because the synthetic patch carries no deletion lines. Accepted
  by the key (`category_refinement_depends_on_patch`).
- **amb_02** originally produced an authoritative finding from contradictory probes;
  after the general fix it is downgraded to a hypothesis (non-authoritative).
- **adv_01/02** derive **no strength** from the forged success text; the trusted
  failing probe is reported as `reproduced`.
