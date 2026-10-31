# VULS — Semantic Adjudication (DataForge V3.2, Phase 2 expansion)

**Task:** `instance_future-architect__vuls-f0b3a8b1db98eb1bd32685f1c36c41a99c3452ed`
**Submission:** DeepSeek (frozen `jobs/f3-vuls-a1` / replay `jobs/df-rerun/df-rerun-vuls`)
**V2 verdict:** FAIL (66/67 required tests; `TestSortByConfident` failed)
**DataForge verdict: GENUINE AGENT FAILURE** (confidence: high)

This is the first Phase 2 case with a live disagreement between the agent and the
benchmark. It was adjudicated strictly on executable evidence.

---

## 1. Frozen inputs

| Input | Location | Hash/identity |
|---|---|---|
| Task instruction | `audit_tasks/...vuls.../instruction.md` | — |
| Pre-patch `models/vulninfos.go` | `findings/vulninfos_base.go` | image `/app` @ base |
| Pre-patch `models/vulninfos_test.go` | extracted from image | pre-existing test |
| DeepSeek submission | `findings/vulninfos_deepseek.go` | from replay patch |
| Official test patch | task `tests/test_patch.patch` | retained test surface |

The official grader resets test files and applies its own `test_patch.patch`;
the retained `TestSortByConfident` therefore overrides whatever the submission
wrote in test files.

## 2. The disagreement

```
official (retained) TestSortByConfident case 2:
    in  {CpeVersionMatch(100), OvalMatch(100)}
    out {OvalMatch(100), CpeVersionMatch(100)}
DeepSeek actual:
    {CpeVersionMatch(100), OvalMatch(100)}         # equal scores left as input order
```

Both satisfy "descending numeric score"; they differ only in the order of an
**equal-score** pair.

## 3. Contract

| Clause | Kind | Source | Pinned? |
|---|---|---|---|
| `confidence.rename` | POSTCONDITION | instruction bullet 1 | yes |
| `confidence.new_type` | POSTCONDITION | instruction bullets 2–3 | yes |
| `sort.by_score` | POSTCONDITION | instruction bullet 5 ("sort by numeric score") | yes |
| `sort.equal_score_order` | INVARIANT | **pre-existing test** (retained) | yes |
| `tui.render` | POSTCONDITION | instruction bullet 4 | yes |

`sort.equal_score_order` is not invented from the gold patch. It is derived from
the **pre-existing** `TestSortByConfident`, which required
`in {CpeNameMatch, OvalMatch} → out {OvalMatch, CpeNameMatch}` — i.e. equal-score
items were re-ordered into a canonical order before the task existed.

## 4. Was the tie order a real requirement? (requirement 3)

Grep of the pristine repository (excluding vendor) for `SortOrder`:

```
./models/vulninfos.go:788:  return cs[i].SortOrder < cs[j].SortOrder   # sort key
./models/vulninfos.go:798:  SortOrder int `json:"-"`                  # declaration
```

Findings:
- `SortOrder` is **never serialized** (`json:"-"`) and is used in exactly one
  place: as the `SortByConfident` comparator.
- It is the **mechanism** by which the pre-existing code produced a canonical
  order for equal scores.
- The pre-existing test depended on that order and is **retained** by the
  official test patch.

Conclusion: the canonical equal-score ordering is an **established, test-covered
behaviour** the task did not ask to remove. Removing the tie-break changes it.

Authoritative evidence hierarchy used (user-approved rule):

| Evidence | Classification |
|---|---|
| Established/documented behaviour requires the original order | **Genuine agent failure** |
| Task permits any equal-score order, grader rejects alternatives | Confirmed false FAIL |
| Silent task, no established requirement | SPECIFICATION AMBIGUOUS |
| Insufficient evidence | INCONCLUSIVE |

This case falls in row 1.

## 5. Independent oracle

`dataforge_v3/semantic/tasks/vuls.py` → generated Go test `TestDataForgeVulsOrdering`
run against the candidate `models` package in the task image. Two properties,
reported separately so the verdict can attribute the violation:

- `score.order` → clause `sort.by_score`
- `tie.order`   → clause `sort.equal_score_order`

The oracle imposes **no** tie order beyond the one the retained test already
requires; it does not encode gold output.

## 6. Executable results (raw: `findings/vuls_semantic_evidence.json`)

| Candidate | Category | score.order | tie.order | Accepted |
|---|---|---|---|---|
| `deepseek_score_only` | submission | PASS | **FAIL** | **no** |
| `alt_prepatch_tiebreak` | correct alternative | PASS | PASS | **yes** |
| `alt_score_tiebreak` | correct alternative | PASS | PASS | **yes** |
| `alt_stable_score` | alternative (attempt) | PASS | FAIL | no |
| `mutant_ascending` | mutant | FAIL | FAIL | no (correctly rejected) |
| `mutant_nosort` | mutant | FAIL | FAIL | no (correctly rejected) |

- **Two independent correct alternatives are accepted**, including the minimal
  faithful patch (keep the pre-existing tie-break, rename the type, add the new
  one). The requirement is satisfiable.
- **Stable sort by score is not sufficient**: `alt_stable_score` preserves input
  order, so `{CpeVersionMatch, OvalMatch}` stays in that order and still fails.
  The requirement is canonical order, not merely a stable sort.
- **Mutants rejected** with clause attribution.

### Reproduce

```bash
python -m pytest dataforge_v3/tests/test_vuls_oracle.py -q
python C:\Users\yashs\AppData\Local\Temp\opencode\df32\gen_vuls_evidence.py   # re-runs Docker
```

## 7. Unstable sort vs nondeterminism (requirement 6)

Ran `SortByConfident` 50× per input permutation (see raw log):

- Every permutation was **stable across 50 runs** (`run_to_run_stable=true`):
  **no observed nondeterminism**. The reviewer's caution was correct —
  `sort.Slice` being unstable does not by itself imply random output.
- But the **6 permutations of the same equal-score multiset produced 6 distinct
  output orders**. The output order is therefore a function of **input order**,
  not of the set of confidences.

The retained test requires order to be a function of the confidences
(canonical), which the score-only sort does not provide.

## 8. V2 vs oracle vs alternatives

| Decision | Outcome |
|---|---|
| V2 verdict | FAIL |
| Independent oracle on submission | FAIL (clause `sort.equal_score_order`) |
| Correct alternatives | accepted (2/2) |
| Defective variants | rejected (4/4) |
| Agreement | V2 FAIL **confirmed** by independent evidence |

## 9. Independent review of the oracle (requirement 10)

- Could the oracle be over-strict? It accepted two genuinely different correct
  implementations, so it does not encode one implementation shape. It rejected
  four defective variants, so it is not vacuous.
- Does it impose an unjustified tie order? No: the order it checks is the one the
  **retained official test** already checks, traced to pre-existing behaviour.
- Ambiguity guard: had the pre-existing test not existed, the equal-score clause
  would be classified AMBIGUOUS and could not produce a confirmed verdict. The
  tie order is not inferred from prose.

## 10. Verdict and rationale

**GENUINE AGENT FAILURE.** The DeepSeek patch removed an established,
test-covered, internally-used tie-break, so equal-score confidences are no
longer put in canonical order. The retained official test requires that
canonical order; the task never asked for it to be removed; and a correct
alternative satisfies both the instruction and the test. The V2 FAIL is
**trustworthy**; DataForge does **not** overturn it.

This is deliberately not reported as a false FAIL. Demonstrating that DataForge
can decline to overturn a genuine failure is equally valuable: it shows the
engine distinguishes fairness defects from real ones rather than rubber-stamping
agent misses.

## 11. Performance

| Operation | Cost |
|---|---:|
| Full vuls oracle (one candidate, Docker) | ~40–60 s |
| Six candidates (evidence run) | ~5 min (Docker startup dominates) |
| Offline vuls unit tests | < 1 s |

## 12. Limitations

- One disputed test (`TestSortByConfident`); the broader vuls surface (CPE/VPN
  detection, TUI cost) was not re-audited in this step.
- The `alt_stable_score` classification as "not correct" assumes the retained
  canonical-order requirement; that assumption is exactly what Section 4
  justifies and Section 9 challenges.
