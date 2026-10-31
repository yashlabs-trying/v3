# Phase 2 — Task Selection (frozen before observing candidate outcomes)

DataForge V3.2 / Phase 2. Selection was made from the seven frozen SWE-bench Pro V2
tasks already present in `audit_tasks/`. Criteria below were fixed **before** running
any semantic probe, so the selection cannot be tuned to a desired finding.

## Selection criteria (fixed)

A task is a strong Phase 2 candidate when it scores high on the following, judged
only from the task instruction, its test files, and its config:

1. **Contract richness** — the instruction states observable requirements
   (preconditions, precedence, invariants, error behavior) that a reference oracle
   can be built from without the gold patch.
2. **Oracle feasibility** — the required behavior can be re-expressed as an
   independent executable model (small surface, deterministic, no external service).
3. **Unexercised-requirement surface (false-FAIL risk)** — documented requirements
   that the selected tests plausibly do not pin down.
4. **Overfit surface (false-PASS risk)** — few required tests relative to the
   behavior space, so a solution could satisfy the tests while violating the contract.
5. **Parser risk** — the grader's pass rule (`success = all_required <= passed_tests`)
   could be fooled by name handling (dedup, parametrization, subtest naming).
6. **Cost** — can run in the existing image without new infrastructure.

Tasks scoring low on oracle feasibility (broad, integration-heavy) are deferred to
the expansion cohort, not dropped.

## Selected tasks (two, contrasting risk)

### Task 1 — `flipt` (`instance_flipt-io__flipt-6fe76d0…`)
- **Surface:** Go, `internal/server/auth/middleware.go`, gRPC unary interceptor.
- **Why:** richest textual contract in the set. The instruction enumerates exact
  requirements: `"Bearer <token>"` with capital B and a single space; cookie
  fallback via the `grpcgateway-cookie` metadata header under key
  `flipt_client_token`, handling multiple cookies; header preferred and **no
  fallback** when the header is present but malformed; `errUnauthenticated` plus a
  logged reason on every failure path; expiry check; a per-server bypass
  (`InterceptorOptions` / `WithServerSkipsAuthentication`) checked *before*
  extraction.
- **Oracle feasibility:** high. Pure function over `(ctx, md, info.Server)`; a
  reference interceptor can be written from the contract alone.
- **False-PASS risk:** high. Config is 13 subtests; a solution can pass them while
  mishandling multi-cookie headers, whitespace variants, or ordering.
- **False-FAIL risk:** moderate. "single space" is precise; a legitimate solution
  using a stricter split could be rejected by `require.Equal` on the error.
- Risk class: **logic / precedence / error-contract**.

### Task 2 — `openlibrary` (`instance_internetarchive__openlibrary-03095f…`)
- **Surface:** Python, `scripts/new-solr-updater.py` (`find_keys`, `parse_log`).
- **Why:** precise, set-based contract: `find_keys` yields every `'key'` value at
  any depth in dict/list traversal order; for `save`/`save_many` `parse_log` yields
  exactly one key per doc (its own top-level `key`), plus the set difference
  `find_keys(before) - find_keys(after)` when `before` is not `None`; skip the
  difference when `before` is `None`.
- **Oracle feasibility:** very high. Pure Python, deterministic, trivially
  re-implementable independently.
- **False-PASS risk:** high. Only 3 tests total (2 FAIL_TO_PASS + 1 PASS_TO_PASS);
  many wrong `parse_log` implementations satisfy those three.
- **False-FAIL risk:** moderate. Traversal order and "yield exactly one key per
  doc" are easy to over- or under-constrain.
- Risk class: **set semantics / traversal order / overfit**.

## Deferred (expansion cohort after methodology validation)
- `vuls` — broad Go surface; the one legitimate FAIL (66/67). Good for false-FAIL
  and semantic-breadth testing later.
- `nodebb`, `ansible`, `teleport`, `element-web` — larger surfaces; lower oracle
  tractability within the Phase 2 budget.

## What this selection does NOT claim
Selecting these tasks is a hypothesis about *where* semantic discrepancies are
findable. It is not evidence that either task is defective. Phase 2 explicitly
allows the result "no confirmed semantic defect found."
