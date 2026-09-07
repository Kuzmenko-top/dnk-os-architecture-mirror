# Multi-Tenant OIDC, JWT Key Rotation (JWKS) & Replay Protection

## Multi-Tenant Isolation Invariant
In multi-tenant architectures, authorization tokens and policy evaluations MUST enforce tenant isolation at three distinct boundaries:
1. **Token Minting**: JWT claims must include immutable `tenant_id`, `sub`, `roles`, and `jti`.
2. **Context Validation**: The request principal's `tenant_id` must match target resource `tenant_id` unless the principal holds cross-tenant administrative override (`tenant:*`).
3. **Storage & Lookup Partitioning**: All user indexes, API keys, and sessions must be compound-indexed by `(tenant_id, identifier)`.

## Dynamic Key Rotation & JWKS Discovery
- **Key Rotation**: Cryptographic signing keys (RSA / EC / HMAC) should rotate on scheduled intervals or on-demand without invalidating active sessions during the grace period.
- **JWKS Endpoint**: Expose active public keys via standard JWKS format (`/.well-known/jwks.json` or `/api/v1/auth/jwks.json`):
  ```json
  {
    "keys": [
      {
        "kid": "key_2026_q3_01",
        "kty": "RSA",
        "use": "sig",
        "alg": "RS256",
        "n": "...",
        "e": "AQAB"
      }
    ]
  }
  ```
- **Validation Fallback**: Token verification searches the key store by `kid` in the token header, seamlessly validating tokens signed by previous keys within their validity window.

## Refresh Token Rotation & Replay Protection
1. **Single-Use Refresh Tokens**: Every refresh request burns the incoming refresh token and mints a new pair (access + refresh).
2. **Replay Detection**: If an already-rotated or revoked refresh token is presented:
   - Immediately invalidate the entire session family.
   - Denylist all issued child tokens for that subject.
   - Log an `AUDIT_SECURITY_BREACH` event to the tamper-evident audit log.

## Service & REST Router Interface Invariants
When wiring OIDC/JWT services to FastAPI routers:
1. **User Registration & Indexing**: Router `/register` endpoints must delegate directly to `OIDCAuthService.register_user(tenant_id, email, display_name, password, roles, provider)` to ensure compound index `(tenant_id, email.lower())` is maintained consistently across in-memory and database stores.
2. **Flexible Token Revocation**: `revoke_token(token: str, reason: Optional[str] = None)` must accept optional diagnostic reasons for security audit logging without breaking standard 1-arg callers.
3. **Configurable TTL Reflection**: Expose properties like `access_token_ttl_seconds` and `refresh_token_ttl_seconds` on the auth service so router response payloads (`expires_in`) accurately reflect the active token expiration policy.
