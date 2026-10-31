# Semantic assessment — flipt

- **Submission:** `deepseek`
- **V2 reward:** 1.0
- **V3.1 classification:** PASS
- **Semantic verdict:** **CONFIRMED_CORRECT**
- **Confidence:** high

## Contract coverage

| Clause | Kind | Covered by official tests | Statement |
|---|---|---|---|
| bearer.exact | POSTCONDITION | TestUnaryInterceptor/client_token_missing_Bearer_prefix, TestUnaryInterceptor/malformed_authorization_header_with_valid_cookie, TestUnaryInterceptor/authorization_header_empty | Authorization metadata must be exactly "Bearer <token>" with a capital B and a single space; any other format is unauthenticated. |
| cookie.fallback | POSTCONDITION | TestUnaryInterceptor/successful_authentication_(cookie_header) | When no authorization header is present, extract the token from cookies in grpcgateway-cookie under key flipt_client_token, handling multiple cookies. |
| header.precedence | INVARIANT | TestUnaryInterceptor/authorization_header_preferred_over_cookie | When both authorization header and cookie are present, prefer the header and do not fall back to the cookie. |
| header.malformed.no_fallback | ERROR_BEHAVIOR | TestUnaryInterceptor/malformed_authorization_header_with_valid_cookie | A present-but-malformed authorization header must be rejected as unauthenticated without falling back to the cookie. |
| cookie.multiple | EDGE_CASE | — | A grpcgateway-cookie header carrying multiple cookies must still yield the flipt_client_token value; unrelated cookies are ignored. |
| bypass.membership | POSTCONDITION | TestUnaryInterceptor/successful_authentication_(skipped) | Only servers registered via WithServerSkipsAuthentication bypass auth; a non-matching server does not bypass and is still validated. |
| bypass.before_extraction | INVARIANT | TestUnaryInterceptor/successful_authentication_(skipped) | The bypass check runs before any metadata extraction, so a skipped server succeeds even with no metadata at all. |
| expiry | POSTCONDITION | TestUnaryInterceptor/token_has_expired | An expired token must be rejected with errUnauthenticated. |

## Probe evidence

| Probe | Kind | Clauses | Result | Detail |
|---|---|---|---|---|
| flipt:deepseek | differential |  | PASS |  |

## Reproduce

```bash
wsl -d Ubuntu -- bash /mnt/c/Users/yashs/dataforge/run_flipt_semantic.sh
```

## Notes

- accepted submission satisfies every supported clause
