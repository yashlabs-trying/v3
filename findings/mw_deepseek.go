package auth

import (
	"context"
	"errors"
	"net/http"
	"strings"
	"time"

	"go.flipt.io/flipt/internal/containers"
	authrpc "go.flipt.io/flipt/rpc/flipt/auth"
	"go.uber.org/zap"
	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/metadata"
	"google.golang.org/grpc/status"
)

const (
	// authenticationHeaderKey is the metadata key which carries the
	// HTTP Authorization header through grpc-gateway.
	authenticationHeaderKey = "authorization"
	// cookieHeaderKey is the metadata key which carries the HTTP Cookie
	// header through grpc-gateway.
	cookieHeaderKey = "grpcgateway-cookie"
	// clientTokenCookieKey is the name of the cookie which may carry a
	// client token for browser based sessions.
	clientTokenCookieKey = "flipt_client_token"
	// bearerPrefix is the exact prefix expected on a well formed
	// Authorization header.
	bearerPrefix = "Bearer "
)

var (
	errUnauthenticated = status.Error(codes.Unauthenticated, "request was not authenticated")

	errMetadataNotFound       = errors.New("metadata not found on context")
	errNoAuthorization        = errors.New("no authorization provided")
	errAuthorizationMalformed = errors.New("authorization malformed")
	errNoClientTokenCookie    = errors.New("no client token cookie provided")
)

type authenticationContextKey struct{}

// Authenticator is the minimum subset of an authentication provider
// required by the middleware to perform lookups for Authentication instances
// using a obtained clientToken.
type Authenticator interface {
	GetAuthenticationByClientToken(ctx context.Context, clientToken string) (*authrpc.Authentication, error)
}

// GetAuthenticationFrom is a utility for extracting an Authentication stored
// on a context.Context instance
func GetAuthenticationFrom(ctx context.Context) *authrpc.Authentication {
	auth := ctx.Value(authenticationContextKey{})
	if auth == nil {
		return nil
	}

	return auth.(*authrpc.Authentication)
}

// InterceptorOptions holds the configuration for the authentication
// unary interceptor. It tracks the set of server instances which are
// permitted to bypass authentication entirely.
type InterceptorOptions struct {
	serverSkipsAuthentication map[any]struct{}
}

// WithServerSkipsAuthentication registers the provided server instance so
// that requests handled by it bypass the authentication middleware. This is
// useful for servers which delegate authentication to an external system,
// such as an internal OIDC server.
func WithServerSkipsAuthentication(server any) containers.Option[InterceptorOptions] {
	return func(o *InterceptorOptions) {
		if o.serverSkipsAuthentication == nil {
			o.serverSkipsAuthentication = map[any]struct{}{}
		}

		o.serverSkipsAuthentication[server] = struct{}{}
	}
}

// UnaryInterceptor is a grpc.UnaryServerInterceptor which extracts a clientToken
// from the incoming request metadata.
//
// The client token is looked up from the authorization metadata header when it
// is present, where the value is expected to be in the form "Bearer <clientToken>".
// If (and only if) the authorization header is not present, the client token is
// instead looked up from the cookies carried in the grpcgateway-cookie metadata
// header, under the "flipt_client_token" key.
//
// Servers registered via WithServerSkipsAuthentication bypass the authentication
// flow entirely.
func UnaryInterceptor(logger *zap.Logger, authenticator Authenticator, opts ...containers.Option[InterceptorOptions]) grpc.UnaryServerInterceptor {
	options := &InterceptorOptions{}
	containers.ApplyAll(options, opts...)

	return func(ctx context.Context, req interface{}, info *grpc.UnaryServerInfo, handler grpc.UnaryHandler) (interface{}, error) {
		if info != nil {
			if _, ok := options.serverSkipsAuthentication[info.Server]; ok {
				logger.Debug("skipping authentication", zap.Any("server", info.Server))

				return handler(ctx, req)
			}
		}

		clientToken, err := getClientToken(ctx)
		if err != nil {
			logger.Error("unauthenticated", zap.String("reason", err.Error()))

			return ctx, errUnauthenticated
		}

		auth, err := authenticator.GetAuthenticationByClientToken(ctx, clientToken)
		if err != nil {
			logger.Error("unauthenticated",
				zap.String("reason", "error retrieving authentication for client token"),
				zap.Error(err))

			return ctx, errUnauthenticated
		}

		if auth.ExpiresAt != nil && auth.ExpiresAt.AsTime().Before(time.Now()) {
			logger.Error("unauthenticated",
				zap.String("reason", "authorization expired"),
				zap.String("authentication_id", auth.Id),
			)

			return ctx, errUnauthenticated
		}

		return handler(context.WithValue(ctx, authenticationContextKey{}, auth), req)
	}
}

// getClientToken extracts the client token from the incoming request metadata.
//
// The authorization header takes precedence over any cookies. If the
// authorization header is present then it must contain a valid Bearer token,
// otherwise the request is rejected without falling back to the cookies.
func getClientToken(ctx context.Context) (string, error) {
	md, ok := metadata.FromIncomingContext(ctx)
	if !ok {
		return "", errMetadataNotFound
	}

	if authorization := md.Get(authenticationHeaderKey); len(authorization) > 0 {
		return clientTokenFromAuthorization(authorization[0])
	}

	if cookies := md.Get(cookieHeaderKey); len(cookies) > 0 {
		if clientToken, ok := clientTokenFromCookies(cookies); ok {
			return clientToken, nil
		}

		return "", errNoClientTokenCookie
	}

	return "", errNoAuthorization
}

// clientTokenFromAuthorization parses a client token from an authorization
// header value. Only the exact "Bearer <clientToken>" format is accepted.
func clientTokenFromAuthorization(authorization string) (string, error) {
	if !strings.HasPrefix(authorization, bearerPrefix) {
		return "", errAuthorizationMalformed
	}

	clientToken := strings.TrimPrefix(authorization, bearerPrefix)
	if clientToken == "" || clientToken != strings.TrimSpace(clientToken) {
		return "", errAuthorizationMalformed
	}

	return clientToken, nil
}

// clientTokenFromCookies searches a set of raw Cookie header values for a
// cookie named flipt_client_token. Each value may itself contain multiple
// cookies.
func clientTokenFromCookies(cookies []string) (string, bool) {
	for _, raw := range cookies {
		// Reconstruct a minimal request so that the standard library can
		// correctly parse the (potentially multiple) cookies in the header.
		request := &http.Request{
			Header: http.Header{"Cookie": []string{raw}},
		}

		cookie, err := request.Cookie(clientTokenCookieKey)
		if err == nil {
			return cookie.Value, true
		}
	}

	return "", false
}
