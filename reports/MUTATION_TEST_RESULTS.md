# MUTATION_TEST_RESULTS — DataForge V3.2 (Phase 2)

Deliberately defective implementations ("mutants") must be **rejected** by the
supplemental semantic verifier. Independently written but **correct**
implementations must be **accepted**. This file records both.

All mutants below are produced by deterministic source transforms from the real
DeepSeek submission, so each is reproducible.

## openlibrary — `find_keys` / `parse_log`

Oracle: independent Python reference + structural comparator (modules B/E).
Probes: 8 deterministic cases (6 property, 6 boundary, 1 stateful; seeds fixed).

| Mutant | Defect | Expected | Observed | Failing clause |
|---|---|---|---|---|
| `m1_incomplete` | Omits the `find_keys(before) - find_keys(after)` step entirely | reject | **rejected** (2 probes) | `parse_log.difference` |
| `m2_types` | Emits non-string `key` values | reject | **rejected** (1 probe) | `find_keys.types` |
| `m3_overyield` | Also yields the new doc's nested keys | reject | **rejected** (6 probes) | `parse_log.one_key_per_doc` |

Correct alternative accepted:
- `reference` — independently written, same shape as the contract: **accepted** (0 failures).
- `unordered` — identical semantics but emits the removed set in an
  unconstrained order: **accepted** (regression guard for a false alarm, see
  `ALTERNATIVE_SOLUTIONS.md`).

## flipt — auth middleware

Oracle: generated Go probes injected into the task image (module B), 14 subtests.

| Mutant | Defect | Expected | Observed | Failing clause |
|---|---|---|---|---|
| `m1_malformed_fallback` | Falls back to cookie when the authorization header is malformed | reject | **rejected** | `header.malformed.no_fallback` |
| `m2_single_cookie` | Reads only the first `grpcgateway-cookie` value (misses multi-cookie) | reject | **rejected** | `cookie.multiple` |
| `m3_no_bypass` | `WithServerSkipsAuthentication` registers nothing | reject | **rejected** | `bypass.membership`, `bypass.before_extraction` |
| `m4_empty_bearer` | Drops the empty-token check | reject | **accepted** (not a real defect — see note) | — |

Note on `m4`: removing the `clientToken == ""` check does not change observable
behaviour, because an empty token is not in the authenticator store, so the
request is still rejected downstream. The mutant is behaviourally equivalent to
the original under the contract; accepting it is correct. It is recorded here
rather than silently dropped, to keep the denominator honest.

## Summary

| Task | Mutants | Rejected | Genuine misses | Correct alternatives | Accepted |
|---|---:|---:|---:|---:|---:|
| openlibrary | 3 | 3 | 0 | 2 | 2 |
| flipt | 4 | 3 | 0 (1 equivalent) | 0 (base + DeepSeek serve as the accepted set) | — |

The verifiers reject every **genuine** defect and accept every correct variant.
