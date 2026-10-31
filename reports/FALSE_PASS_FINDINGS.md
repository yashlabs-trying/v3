# FALSE_PASS_FINDINGS — DataForge V3.2 (Phase 2)

Question: did the benchmark accept a solution that is functionally incorrect —
passes the required tests but violates the documented contract?

Method: independent contracts + reference/structure oracle + boundary/property/
stateful probes (see `SEMANTIC_CONTRACTS.md`, `MUTATION_TEST_RESULTS.md`).

## Result: no confirmed false PASS in the selected submissions

| Task | Submission | V2 | V3.2 verdict | Confidence | Probes run | Supported clauses failed |
|---|---|---|---|---|---|---|
| flipt | DeepSeek | PASS | CONFIRMED_CORRECT | high | 14 | 0 |
| openlibrary | DeepSeek | PASS | CONFIRMED_CORRECT | high | 8 | 0 |

Both accepted submissions satisfy **every supported contract clause**, including
the clauses the official tests do not pin:

- flipt: multi-cookie headers (`cookie.multiple`); bypass membership and
  before-extraction ordering; exact Bearer-format variants (double space,
  lowercase, no space, empty token).
- openlibrary: non-string `key` values (`find_keys.types`); a before-doc
  containing non-string keys; `find_keys` depth beyond the tested shapes.

## One false alarm found and removed (methodology result)

An earlier version of the openlibrary oracle sorted the removed-key set and
compared lists exactly. That rejected the correct DeepSeek submission because
the contract defines the removal as a **set difference** with no order
requirement. The comparator was corrected to be order-agnostic on the removal
set, and a regression probe (`unordered`) was added. This is recorded because
Phase 2 requires the supplemental verifier not to reject correct solutions.

**Counterexample (before fix):**

```
expected (sorted, over-strict): [... /works/OL245227W, /works/OL660415W, /works/OL913787W ...]
observed (set order, correct) : [... /works/OL913787W, /works/OL660415W, /works/OL245227W ...]
```

After the fix the same submission is CONFIRMED_CORRECT and the `unordered`
alternative is accepted.

## Honest boundary

A CONFIRMED_CORRECT verdict means "no contract violation was found by the probes
run". It is not a proof of full functional correctness. The probes target the
declared contract; behaviour outside it is unverified. Both tasks also carry
clauses marked AMBIGUOUS, which can never produce a confirmed false-PASS finding.
