# SEMANTIC_CONTRACTS — DataForge V3.2 (Phase 2)

Independent, reviewable behavioural contracts for the two selected tasks. Each
clause records its source and whether the official required tests already pin it.
Clauses with no pinning test are the **false-PASS surface**; the semantic probes
exercise them.

These contracts are extracted from the task instruction prose. They are *data*
that a reviewer can audit; the engine never invents clauses.

## flipt — `internal/server/auth/middleware.go`

| Clause | Kind | Source | Pinned by an official required test? |
|---|---|---|---|
| `bearer.exact` — Authorization must be exactly `"Bearer <token>"` (capital B, single space) | POSTCONDITION | instruction bullet 1 | partial (3 of 13) |
| `cookie.fallback` — with no Authorization header, read token from `grpcgateway-cookie` under `flipt_client_token` | POSTCONDITION | instruction bullet 2 | yes |
| `header.precedence` — header wins over cookie; no fallback | INVARIANT | instruction bullet 3 | yes |
| `header.malformed.no_fallback` — present-but-malformed header rejected without cookie fallback | ERROR_BEHAVIOR | instruction bullet 4 | yes |
| `cookie.multiple` — multiple cookies in `grpcgateway-cookie` still yield the token | EDGE_CASE | instruction bullet 2 | **no** |
| `bypass.membership` — only servers registered via `WithServerSkipsAuthentication` bypass | POSTCONDITION | instruction bullets 8–9 | partial |
| `bypass.before_extraction` — bypass is checked before any metadata extraction | INVARIANT | instruction bullet 9 | partial |
| `expiry` — expired token rejected | POSTCONDITION | instruction bullet 6 | yes |

**Uncovered (false-PASS surface):** `cookie.multiple`, plus the multi-server and
before-extraction aspects of the bypass clauses.

### Independent authority
A second model's review was **not** used as ground truth. The Go probes assert
observable behaviour of the exported `UnaryInterceptor` only.

## openlibrary — `scripts/new-solr-updater.py`

| Clause | Kind | Source | Pinned by an official required test? |
|---|---|---|---|
| `find_keys.depth` — yield every `'key'` string value at any depth, traversal order | POSTCONDITION | instruction bullet 1 | partial |
| `find_keys.types` — do not recurse into or emit non-dict/list values | INVARIANT | instruction bullet 1 | **no** |
| `parse_log.one_key_per_doc` — exactly one key per doc (its top-level `key`) | POSTCONDITION | instruction bullet 2 | yes |
| `parse_log.difference` — when `old_docs[i]` is not `None`, also yield `find_keys(before) - find_keys(after)` | POSTCONDITION | instruction bullet 3 | yes |
| `parse_log.none_old_doc` — `None` ⇒ skip difference, top-level key only | EDGE_CASE | instruction bullet 4 | yes |
| `parse_log.old_docs_length` — index pairing when `old_docs` is shorter than `docs` | EDGE_CASE | **AMBIGUOUS** (inferred) | no |

**Uncovered:** `find_keys.types`, `parse_log.old_docs_length` (the latter marked
ambiguous, so failures on it cannot cause a confirmed verdict).

### Independent authority
The reference `find_keys`/`parse_log` was written from the prose only; the gold
patch was not consulted. The comparator treats the removal as a **set** (the
contract calls it a set difference) and therefore does not constrain its order.
