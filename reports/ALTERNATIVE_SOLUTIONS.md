# ALTERNATIVE_SOLUTIONS — DataForge V3.2 (Phase 2)

Independently written, genuinely different but correct implementations. A sound
semantic verifier must **accept** all of them. This is the false-FAIL /
false-alarm guard.

## openlibrary

| Alternative | How it differs | Result |
|---|---|---|
| `reference` | Structurally similar to the contract, written from prose only; uses a recursive generator and sorted set difference | **accepted** |
| `unordered` | Same semantics; emits the removed set in arbitrary order (`list(set(...))`) | **accepted** |
| DeepSeek submission | Uses `old_docs[i]` indexing with a bounds guard and a different helper decomposition | **accepted** |

The `unordered` alternative exists specifically because an earlier oracle version
rejected it (and the real submission) by over-constraining the order of the
removal set. The contract defines the removal as a set difference, so order is
not required. See `FALSE_PASS_FINDINGS.md`.

## flipt

The submission must be a Go file implementing `UnaryInterceptor` with the new
options API. Two independent "shapes" were checked:

| Candidate | How it differs | Result |
|---|---|---|
| DeepSeek submission | Uses `strings.HasPrefix` + empty/space checks; per-value cookie parsing loop | **accepted** (14/14 probes) |
| Gold-style structure | Uses `strings.TrimPrefix` with an equality check; `http.Request.Cookie` via a fabricated request | not run in this pilot (the provided `gold_patch.diff` does not apply to the image's base — see note) |

Note: the task's `solution/gold_patch.diff` failed `git apply` and `git apply
--3way` against the image's `/app` checkout (context mismatch at
`middleware.go:2`). The gold patch was **not** used as authority anywhere in this
phase; it is recorded here only as a discrepancy worth flagging to the benchmark
maintainers.

## Why alternatives matter here

If the supplemental verifier had been written by reading the DeepSeek patch, it
would trivially accept that patch and could reject a different-but-correct
implementation. The reference and probes are written from the contract only, so
agreement between an independent alternative and the submission is real signal.
