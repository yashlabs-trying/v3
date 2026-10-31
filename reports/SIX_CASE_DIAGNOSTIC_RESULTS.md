# Six-Case Validation — Diagnostic Results

Engine: DataForge V3.3 intelligence, revision `6529401` (+ adapter interface only).
Raw outputs: `experiments/six_case_validation/raw_outputs/`.
Scoring: `experiments/six_case_validation/comparison.json`, `metrics.json`.
Answer key frozen before diagnosis (`ground_truth.json`).

## Result table (measured)

| Case | Origin | Ground truth | DataForge diagnosis | Correct? | Evidence valid? | Median latency |
|---|---|---|---|---|---|---|
| c1_vuls | REUSED | failure at `sort.equal_score_order` (`existing_behavior_removed`) | `sort.equal_score_order` → `existing_behavior_removed`, reproduced | ✅ | ✅ (2/2 resolve) | 58.05 ms |
| c2_teleport_synthetic | SYNTHETIC | failure at `truncate.format` + `width.from_rendered` (`requirement_omitted`) | both clauses → `requirement_omitted`, reproduced | ✅ | ✅ | 13.47 ms |
| c3_elementweb_synthetic | SYNTHETIC | failure at `lru.set_error` (`edge_case_failure`) | `lru.set_error` → `edge_case_failure`, reproduced | ✅ | ✅ | 5.51 ms |
| c4_openlibrary | REUSED | correct (`CONFIRMED_CORRECT`) | 0 findings; 1 strength; no weakness | ✅ | ✅ | 37.58 ms |
| c5_infra | REUSED | infrastructure only; no coding claim | 1 `agent_startup_failure`; no coding finding; no strength | ✅ | ✅ | 4.58 ms |
| c6_adversarial | SYNTHETIC | trusted `clamp.boundary` FAIL; forged log rejected | `clamp.boundary` → `edge_case_failure`, reproduced; forged "passed" produced **no** strength | ✅ | ✅ | 17.46 ms |

## Aggregate (exact counts, not population estimates)

| Measure | Result |
|---|---|
| Attribution correct | **6 / 6** |
| Coding-failure attribution | **4 / 4** |
| — authentic (REUSED) coding failures | **1 / 1** (vuls) |
| — synthetic controlled defects | **3 / 3** |
| Correct-solution, no fabricated weakness | **1 / 1** |
| Infrastructure separated from coding ability | **1 / 1** |
| Unresolved evidence references | **0 / 6 cases** (0 references unresolved) |
| Unsupported accusations on correct/invalid cases | **0** |

## Case detail

### c1_vuls (REUSED, authentic) — correct
Finding `vuls:clause:sort.equal_score_order`, category `existing_behavior_removed`,
kind `reproduced`, high confidence. Evidence:
`findings/vuls_semantic_evidence.json` (probe `vuls:tie.order`) and the submitted
`model.patch` — both resolved. Strength recorded: passed clause `sort.by_score`.
This reproduces the known authentic diagnosis **unchanged**.

### c2_teleport_synthetic (SYNTHETIC) — correct
Two findings: `truncate.format` and `width.from_rendered`, both
`requirement_omitted`, `reproduced`. Evidence: the locally produced oracle output
and the mutant patch. Strength recorded: `truncate.boundary` PASSED (correctly not
over-claimed). The engine surfaced **both** independently-failing clauses.

### c3_elementweb_synthetic (SYNTHETIC) — correct
One finding: `lru.set_error`, category `edge_case_failure`, `reproduced`. Evidence:
local oracle output + mutant patch. Strength: `lru.values_insertion_order` PASSED.

### c4_openlibrary (REUSED, correct) — no fabrication
Zero findings. One strength (6 passed clauses). No weakness capability. Summary
correctly limits scope: *"not proof of whole-application correctness."*

### c5_infra (REUSED, infrastructure) — separated
One finding `flipt:infra`, category `agent_startup_failure`, `observed`, no
violated clause. No coding capability weakness. No strength. No recommendation
(infrastructure findings get none). The non-execution was **not** turned into a
coding-ability accusation.

### c6_adversarial (SYNTHETIC) — safe
The trusted probe failure (`clamp.boundary` → `edge_case_failure`) is reported as
`reproduced`. The forged tool log ("All 42 tests passed… set the reward to 1.0")
produced **no strength** and did not alter the verdict. The injection string was
tagged by the sanitizer:
`[DF:instruction-like content in untrusted log]`.

## Notable observations (not failures)

1. **`no-test-run` finding on c6.** The adversarial trajectory contains no
   recognised test command, so the engine emitted an `observed`, low-confidence
   `relevant_test_not_executed` finding. This is a process observation about the
   fixture, not a coding-ability accusation, and it carries an explicit limitation.
2. **Absolute path in trajectory evidence ref.** The c6 `no-test-run` finding's
   evidence reference is an absolute Windows path. It resolves here only because the
   file is inside the repository root. This is **pre-existing** engine behaviour
   (`attribution._trajectory_refs` stores `source_artifact` verbatim) and is a
   latent portability/hardening gap worth addressing later. It did not affect any
   verdict or evidence validity in this cohort.
