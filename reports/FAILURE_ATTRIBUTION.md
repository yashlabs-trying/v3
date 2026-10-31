# Failure Attribution — DataForge V3.3 (System B)

## 1. What it does

Given a task attempt, produce `Finding`s that name a *specific verified defect*,
its category, the V3.2 contract clause (when relevant), supporting evidence, a
reproduction reference, confidence, competing explanations and limitations.

A finding separates the **verified defect** from a **hypothesis about why** the
agent produced it. Intentions are never inferred from tool traces.

## 2. Generic pipeline (no task special-casing)

1. **Execution validity first (V3.1).** If the run is not VALID, the engine emits
   a single infrastructure finding and **no coding-weakness finding**. An attempt
   that did not validly execute cannot evidence a coding defect.
2. **Semantic clause violations (V3.2).** For each *failed independent probe*, the
   engine attributes it to the clause(s) the probe reports, and maps the clause
   `kind` to a category:

   | Clause kind | Category |
   |---|---|
   | `INVARIANT` | `existing_behavior_removed` (now) / `regression` |
   | `POSTCONDITION` | `requirement_omitted` |
   | `EDGE_CASE` / `ERROR_BEHAVIOR` | `edge_case_failure` |
   | `PRECONDITION` | `requirement_omitted` |

3. **Patch-diff corroboration.** `existing_behavior_removed` is only claimed when
   the submitted patch actually **deletes identifiers that appear in the clause
   statement** (generic token overlap between deleted diff lines and clause text).
   Otherwise the category falls back to `requirement_omitted`. This prevents
   over-claiming removal from a probe failure alone.
4. **Process signals (observed only).** e.g. no test-execution command in the
   trajectory ⇒ `relevant_test_not_executed`, with a limitation noting absence in
   a possibly-incomplete trace is not proof.

Every finding carries an `EvidenceRef` list; the driver downgrades a finding
whose evidence does not resolve to `HYPOTHESIS`.

## 3. Finding schema

`finding_id, task_id, category, severity, symptom, violated_requirement,
source_changes, trace_event_ids, evidence[], confidence, competing_explanations[],
limitations[], kind`.

## 4. The vuls case, derived (not hardcoded)

Evidence flow, all generic:

- V3.1: `execution_validity = VALID`.
- V3.2: failed probe `vuls:tie.order` → clause `sort.equal_score_order`
  (`INVARIANT`), counterexample recorded → `REPRODUCED`, high confidence.
- Patch: deletes lines containing `OvalMatch` and `SortOrder`; the clause
  statement contains `OvalMatch` → corroborated → category `existing_behavior_removed`.

Resulting finding `vuls:clause:sort.equal_score_order`:

- **Category:** existing_behavior_removed | **Severity:** major | **Kind:** reproduced.
- **Symptom:** independent probe `vuls:tie.order` failed against clause
  `sort.equal_score_order`.
- **Evidence:** `findings/vuls_semantic_evidence.json` (probe result) + the
  submitted `model.patch` — both resolve and hash.
- **Competing explanations:** probe over-strict (checked by V3.2 correct-alternative
  acceptance); specification ambiguity.
- **Limitation:** the defect is verified; the model's reason is not observable.

A test (`test_vuls_diagnosis_is_not_hardcoded`) parses the engine's AST and
asserts the task tokens (`SortOrder`, `TestSortByConfident`, `CpeVersionMatch`) do
not occur in any *code string literal* of the attribution / capability /
recommendation / driver modules.

## 5. Categories supported

Requirement (omitted / existing-behaviour-removed / unsupported-assumption /
interface-compatibility), implementation (algorithm / edge-case / state-transition
/ concurrency-ordering / incomplete / regression), testing (test-not-executed /
failing-test-unresolved / insufficient-validation / test-misread), and
infrastructure (startup / invalid-patch / replay / invalid-verifier / budget).

## 6. Honest limits

- A finding is only as good as the V3.2 contract and probe coverage for that task.
- NodeBB has no oracle ⇒ no clause finding is possible (INCONCLUSIVE, by design).
- Causal "why" claims are never emitted as authoritative.
