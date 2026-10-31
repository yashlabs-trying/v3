# Phase 2 Baseline — semantic audit of the frozen pilot (before V3.2 probes)

Scope: the two selected tasks (`flipt`, `openlibrary`), inspected against the official
SWE-bench Pro V2 grading contract and the existing V3.1 reliability audit. This file
records the state **before** any V3.2 semantic probe was run, so later findings can be
judged against a fixed baseline.

## Baseline verdicts

| Task | V2 (original DeepSeek) | V3.1 reliability verdict | V3.1 evidence |
|---|---|---|---|
| flipt | PASS, reward 1.0 | PASS | replay VALID, apply_rc 0, post-state OK, 13/13 required tests |
| openlibrary | PASS, reward 1.0 | PASS | replay VALID, apply_rc 0, post-state OK, 3/3 required tests |

Both are `FinalClassification.PASS` under V3.1, with legitimate execution and clean
patch integrity. V3.2 therefore cannot use execution/integrity defects; it must probe
**semantics**: is the accepted solution actually correct, and is the grader's accept
decision fair?

## Grading contract (V2), both tasks

The V2 pass rule is, verbatim from each task's `tests/test.sh`:

```
all_required = fail_to_pass | pass_to_pass
success = all_required <= passed_tests
```

Consequences relevant to Phase 2:

1. **Absence is failure.** A required test that never appears in the parsed output is
   treated as missing → FAIL. (This is an execution-integrity property, owned by V3.1.)
2. **Only the required set is consulted.** Non-required tests run but do not affect the
   verdict.
3. **A test that passes is not evidence about untested behavior.** The contract fixes a
   small required set; anything outside it is unverified.
4. **Parser `success` sees names, not semantics.** Two different tests with the same
   name collapse (openlibrary `export_to_json` dedups by name); a required name that
   appears PASSED anywhere satisfies the set.

## flipt — contract surface vs required tests

- Required: 13 names (12 subtests + `TestUnaryInterceptor`).
- Instruction requirements, and whether a required test pins each:

| Requirement | Pinned by a required test? |
|---|---|
| Bearer format, capital B + single space | partially (`missing Bearer prefix`, `malformed ... valid cookie`) |
| Cookie fallback via `grpcgateway-cookie`, key `flipt_client_token` | yes (one cookie) |
| Header preferred over cookie | yes |
| Header present but malformed ⇒ no cookie fallback | yes |
| `errUnauthenticated` + logged reason on every failure path | error checked; **log content not asserted** |
| Expired token rejected | yes |
| Per-server bypass checked before extraction | yes (single server) |
| **Multiple cookies handled correctly** | **no** |
| **Cookie value parsing (spaces, quoting, other attrs)** | **no** |
| **Bypass list with >1 server / non-matching server** | **no** |
| **Requirement wording "with a capital B and a single space" exactness** | **no** (e.g. `^Bearer$`/double-space cases untested) |

Baseline hypothesis (unproven): false-PASS surface concentrated in multi-cookie and
cookie-format handling, and in the semantics of "single space". To be tested by the
V3.2 oracle, not assumed.

## openlibrary — contract surface vs required tests

- Required: 2 FAIL_TO_PASS (`test_action_save`, `test_move_edition`) + 1 PASS_TO_PASS
  (`test_new_account`) = 3 tests in one file.
- Instruction requirements, and whether a required test pins each:

| Requirement | Pinned by a required test? |
|---|---|
| `find_keys` yields every `'key'` value at any depth, traversal order | indirectly, via the two save tests |
| `find_keys` does **not** recurse into non-dict/list | no |
| `find_keys` emits only *string* values | partially |
| `parse_log` yields exactly one key per doc (its own top-level `key`) | yes (per-doc) |
| Nested `'key'` values of the new doc must **not** be yielded | yes `test_move_edition` |
| `before is not None` ⇒ yield `find_keys(before) - find_keys(after)` | yes `test_action_save` |
| `before is None` ⇒ skip difference, yield only top-level keys | yes `test_new_account` |
| **Multiple docs paired with mismatched-length `old_docs`** | **no** |
| **`save_many` vs `save` structural equivalence** | `save` tested once, `save_many` tested twice |
| **`key` present but non-string** | **no** |
| **Traversal order of the difference set** | **no** (set comparison) |
| **`old_docs` shorter than `docs`** | **no** |

Baseline hypothesis (unproven): the DeepSeek `parse_log` indexes `old_docs[i]` and uses
set difference; plausible gaps are `old_docs` length mismatch and `find_keys` on
non-string `key` values. To be tested by the V3.2 oracle, not assumed.

## Parser risk (both)

- flipt parser: regex on `--- PASS|FAIL|SKIP: name (…)`; subtest names contain `/` and
  parentheses in the duration — captured correctly. No dedup.
- openlibrary parser: three patterns then `{name: result}` dedup (last wins). A name
  appearing PASSED then FAILED collapses to the last sighting. Not triggered at baseline.

## What V3.2 must do with this baseline
1. Build independent contracts and executables (oracle / property tests / mutants).
2. Reproduce any discrepancy with a minimal counterexample **before** proposing change.
3. Never alter V2 scores; emit a separate `SemanticAssessment`.
