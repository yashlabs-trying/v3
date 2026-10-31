"""Independent contract + oracle harness for the flipt auth-middleware task (V3.2).

Unlike openlibrary, flipt is Go and must be executed inside its task image. This
module therefore provides:

  * CONTRACT            - clauses from the task instruction with the official
                          tests that pin each (if any).
  * generate_go_probes  - emits a self-contained `_df_semantic_test.go` file in
                          package auth that exercises the clauses *observably*
                          through the exported `UnaryInterceptor`, using only
                          the public API. Probe inputs are derived from the
                          contract, never from the gold patch.
  * FliptOracle         - a runner abstraction; it shells out to a provided
                          executor (Docker in production, a fake in unit tests)
                          to compile and run the generated tests against a
                          candidate `middleware.go`.

The generated tests assert only what the contract states. They are intentionally
stronger than the official 13 subtests: multi-cookie headers, whitespace
variants, bypass-list membership, and precedence under malformation.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from dataforge_v3.semantic.model import ClauseKind, ContractClause, ProbeResult

TASK = "flipt"

CONTRACT: list[ContractClause] = [
    ContractClause(
        id="bearer.exact",
        kind=ClauseKind.POSTCONDITION,
        statement=(
            'Authorization metadata must be exactly "Bearer <token>" with a '
            "capital B and a single space; any other format is unauthenticated."
        ),
        source="instruction.md Requirements bullet 1",
        tested_by_original=[
            "TestUnaryInterceptor/client_token_missing_Bearer_prefix",
            "TestUnaryInterceptor/malformed_authorization_header_with_valid_cookie",
            "TestUnaryInterceptor/authorization_header_empty",
        ],
    ),
    ContractClause(
        id="cookie.fallback",
        kind=ClauseKind.POSTCONDITION,
        statement=(
            "When no authorization header is present, extract the token from "
            "cookies in grpcgateway-cookie under key flipt_client_token, "
            "handling multiple cookies."
        ),
        source="instruction.md Requirements bullet 2",
        tested_by_original=["TestUnaryInterceptor/successful_authentication_(cookie_header)"],
    ),
    ContractClause(
        id="header.precedence",
        kind=ClauseKind.INVARIANT,
        statement=(
            "When both authorization header and cookie are present, prefer the "
            "header and do not fall back to the cookie."
        ),
        source="instruction.md Requirements bullet 3",
        tested_by_original=["TestUnaryInterceptor/authorization_header_preferred_over_cookie"],
    ),
    ContractClause(
        id="header.malformed.no_fallback",
        kind=ClauseKind.ERROR_BEHAVIOR,
        statement=(
            "A present-but-malformed authorization header must be rejected as "
            "unauthenticated without falling back to the cookie."
        ),
        source="instruction.md Requirements bullet 4",
        tested_by_original=["TestUnaryInterceptor/malformed_authorization_header_with_valid_cookie"],
    ),
    ContractClause(
        id="cookie.multiple",
        kind=ClauseKind.EDGE_CASE,
        statement=(
            "A grpcgateway-cookie header carrying multiple cookies must still "
            "yield the flipt_client_token value; unrelated cookies are ignored."
        ),
        source="instruction.md Requirements bullet 2",
        tested_by_original=[],
    ),
    ContractClause(
        id="bypass.membership",
        kind=ClauseKind.POSTCONDITION,
        statement=(
            "Only servers registered via WithServerSkipsAuthentication bypass "
            "auth; a non-matching server does not bypass and is still validated."
        ),
        source="instruction.md Requirements bullet 8/9",
        tested_by_original=["TestUnaryInterceptor/successful_authentication_(skipped)"],
    ),
    ContractClause(
        id="bypass.before_extraction",
        kind=ClauseKind.INVARIANT,
        statement=(
            "The bypass check runs before any metadata extraction, so a skipped "
            "server succeeds even with no metadata at all."
        ),
        source="instruction.md Requirements bullet 9",
        tested_by_original=["TestUnaryInterceptor/successful_authentication_(skipped)"],
    ),
    ContractClause(
        id="expiry",
        kind=ClauseKind.POSTCONDITION,
        statement="An expired token must be rejected with errUnauthenticated.",
        source="instruction.md Requirements bullet 6",
        tested_by_original=["TestUnaryInterceptor/token_has_expired"],
    ),
]

REQUIRED_TESTS = {
    "TestUnaryInterceptor",
    "TestUnaryInterceptor/successful_authentication_(authorization_header)",
    "TestUnaryInterceptor/successful_authentication_(cookie_header)",
    "TestUnaryInterceptor/authorization_header_preferred_over_cookie",
    "TestUnaryInterceptor/successful_authentication_(skipped)",
    "TestUnaryInterceptor/token_has_expired",
    "TestUnaryInterceptor/client_token_not_found_in_store",
    "TestUnaryInterceptor/client_token_missing_Bearer_prefix",
    "TestUnaryInterceptor/malformed_authorization_header_with_valid_cookie",
    "TestUnaryInterceptor/authorization_header_empty",
    "TestUnaryInterceptor/cookie_header_with_no_flipt_client_token",
    "TestUnaryInterceptor/authorization_header_not_set",
    "TestUnaryInterceptor/no_metadata_on_context",
}


GO_PROBE = r'''
// Code generated by DataForge V3.2 semantic generator. DO NOT EDIT.
// Probes are derived from the task contract, not from the gold patch.
package auth

import (
	"context"
	"testing"

	"go.flipt.io/flipt/internal/containers"
	"go.flipt.io/flipt/internal/storage/auth"
	"go.flipt.io/flipt/internal/storage/auth/memory"
	authrpc "go.flipt.io/flipt/rpc/flipt/auth"
	"go.uber.org/zap/zaptest"
	"google.golang.org/grpc"
	"google.golang.org/grpc/metadata"
)

type dfSkipServer struct{}

func dfHandlerOK(_ context.Context, _ interface{}) (interface{}, error) { return "ok", nil }

func dfNewToken(t *testing.T, store *memory.Store) string {
	t.Helper()
	token, _, err := store.CreateAuthentication(context.TODO(),
		&auth.CreateAuthenticationRequest{Method: authrpc.Method_METHOD_TOKEN})
	if err != nil {
		t.Fatalf("create authentication: %v", err)
	}
	return token
}

func dfCall(t *testing.T, store *memory.Store, md metadata.MD, server any, opts ...containers.Option[InterceptorOptions]) error {
	t.Helper()
	ctx := context.Background()
	if md != nil {
		ctx = metadata.NewIncomingContext(ctx, md)
	}
	_, err := UnaryInterceptor(zaptest.NewLogger(t), store, opts...)(
		ctx, nil, &grpc.UnaryServerInfo{Server: server}, dfHandlerOK,
	)
	return err
}

func TestDataForgeSemanticProbes(t *testing.T) {
	store := memory.NewStore()
	token := dfNewToken(t, store)

	cases := []struct {
		name    string
		md      metadata.MD
		server  any
		wantErr bool
	}{
		{name: "bearer.exact/valid", md: metadata.MD{"authorization": []string{"Bearer " + token}}},
		{name: "bearer.exact/double_space_rejected", md: metadata.MD{"authorization": []string{"Bearer  " + token}}, wantErr: true},
		{name: "bearer.exact/lowercase_rejected", md: metadata.MD{"authorization": []string{"bearer " + token}}, wantErr: true},
		{name: "bearer.exact/no_space_rejected", md: metadata.MD{"authorization": []string{"Bearer" + token}}, wantErr: true},
		{name: "bearer.exact/empty_token_rejected", md: metadata.MD{"authorization": []string{"Bearer "}}, wantErr: true},
		{name: "cookie.fallback/single", md: metadata.MD{"grpcgateway-cookie": []string{"flipt_client_token=" + token}}},
		{name: "cookie.multiple/first_unrelated", md: metadata.MD{"grpcgateway-cookie": []string{"other=1; flipt_client_token=" + token}}},
		{name: "cookie.multiple/second_value", md: metadata.MD{"grpcgateway-cookie": []string{"other=1", "flipt_client_token=" + token}}},
		{name: "cookie.multiple/missing_token_rejected", md: metadata.MD{"grpcgateway-cookie": []string{"other=1; another=2"}}, wantErr: true},
		{name: "header.precedence/valid_header_beats_bad_cookie", md: metadata.MD{"authorization": []string{"Bearer " + token}, "grpcgateway-cookie": []string{"flipt_client_token=notreal"}}},
		{name: "header.malformed.no_fallback/malformed_header_with_valid_cookie", md: metadata.MD{"authorization": []string{"Malformed"}, "grpcgateway-cookie": []string{"flipt_client_token=" + token}}, wantErr: true},
		{name: "bypass.membership/non_matching_server_does_not_bypass", md: metadata.MD{}, server: &dfSkipServer{}, wantErr: true},
	}

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			err := dfCall(t, store, tc.md, tc.server)
			gotErr := err != nil
			if gotErr != tc.wantErr {
				t.Fatalf("%s: wantErr=%v got err=%v", tc.name, tc.wantErr, err)
			}
		})
	}

	t.Run("bypass.membership/matching_server_bypasses", func(t *testing.T) {
		srv := &dfSkipServer{}
		err := dfCall(t, store, metadata.MD{}, srv, WithServerSkipsAuthentication(srv))
		if err != nil {
			t.Fatalf("matching server should bypass auth, got err=%v", err)
		}
	})

	t.Run("bypass.before_extraction/no_metadata_skipped_server_ok", func(t *testing.T) {
		srv := &dfSkipServer{}
		// No incoming metadata at all: a skipped server must still succeed.
		_, err := UnaryInterceptor(zaptest.NewLogger(t), store, WithServerSkipsAuthentication(srv))(
			context.Background(), nil, &grpc.UnaryServerInfo{Server: srv}, dfHandlerOK,
		)
		if err != nil {
			t.Fatalf("skipped server must bypass without metadata, got err=%v", err)
		}
	})
}
'''


def generate_go_probes() -> str:
    """Return a self-contained Go test file exercising the contract clauses."""
    return GO_PROBE



# --- Oracle / runner abstraction -------------------------------------------


Executor = Callable[[dict], ProbeResult]


@dataclass
class FliptOracle:
    """Runs the generated Go probes via an injected executor.

    `executor` receives a payload describing (candidate source, probe source) and
    returns a `ProbeResult`. In production it is backed by Docker; in unit tests
    it is a fake. This keeps the oracle task-agnostic and testable off-Docker.
    """

    task: str = TASK
    executor: Executor | None = None

    def run(self, cases, candidates=None) -> list[ProbeResult]:  # type: ignore[override]
        if self.executor is None:
            return [
                ProbeResult(
                    name="flipt:no-executor",
                    kind="differential",
                    passed=False,
                    detail="no executor configured",
                )
            ]
        probe_src = generate_go_probes()
        results: list[ProbeResult] = []
        for name, source in candidates or []:
            if hasattr(source, "read_text"):
                middleware_source = source.read_text(encoding="utf-8")
            else:
                middleware_source = Path(source).read_text(encoding="utf-8")
            results.append(
                self.executor(
                    {
                        "candidate": name,
                        "middleware_source": middleware_source,
                        "probe_source": probe_src,
                    }
                )
            )
        return results
