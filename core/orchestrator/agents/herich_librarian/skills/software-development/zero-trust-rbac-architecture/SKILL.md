---
name: zero-trust-rbac-architecture
description: "Use for Zero-Trust RBAC/ABAC and tamper-evident audit logs."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [zero-trust, rbac, abac, security, audit-trail, token-revocation, fastapi]
    related_skills: [adversarial-code-verification, requesting-code-review, test-driven-development]
---

# Zero-Trust Dynamic RBAC & ABAC Architecture

Design and implementation patterns for Zero-Trust access control, continuous context evaluation (IP, geolocation, time, device trust, velocity), token revocation blacklists, and cryptographically chained immutable audit logs.

## When to Use

- When designing or refactoring authentication & authorization layers from perimeter security to Zero-Trust ("never trust, always verify").
- When implementing attribute-based access control (ABAC) alongside role-based access control (RBAC).
- When tracking security-critical events with tamper-evident audit trails (cryptographic hash chaining).
- When handling immediate token invalidation (JTI blacklists, session revocation, token rotation).

## Core Architecture Pillars

1. **Continuous Context Evaluation (ABAC + RBAC)**:
   - Evaluates subject roles and dynamic contextual attributes on every request:
     - **Network Context**: IP address matches against allowed/blocked CIDR ranges (`ip_cidr_rules`).
     - **Geolocation**: Allowed country codes (`allowed_geo_countries`).
     - **Time Windows**: Allowed execution windows in UTC (`time_window_utc`).
     - **Device & Subject Trust**: Dynamic trust score threshold (`min_trust_score: 0.0..1.0`).
     - **Request Velocity**: Rate limiting per subject/IP (`max_velocity_rpm`).
     - **MFA Enforcement**: Enforces `mfa_required` flag on high-privilege operations.

2. **Hierarchical Subjects & Roles**:
   - Subjects encompass Users, Service Accounts, and Autonomous AI Agents.
   - Roles inherit permissions transitively (`system:admin` -> `canvas:write` -> `canvas:read`).
   - Permissions are atomic key tuples formatted as `<domain>:<action>` (e.g. `security:revoke_token`, `canvas:modify_node`).

3. **Cryptographically Chained Immutable Audit Trail**:
   - Each audit entry contains a cryptographic hash of its payload and links to the previous entry's hash:
     $$\text{current\_hash} = \text{SHA-256}(\text{prev\_hash} + \text{action} + \text{subject\_id} + \text{resource} + \text{status} + \text{timestamp})$$
   - Genesis block uses `"0" * 64` as `prev_hash`.
   - Verification scans the chain linearly to detect unauthorized row tampering or deletion.

4. **Fast-Lookup Token Revocation (Redis / DB Blacklist)**:
   - Fast check by unique JWT identifier (`jti`).
   - Entries store expiration timestamps (`expires_at`) allowing automatic TTL cleanup once tokens expire naturally.

5. **FastAPI Zero-Trust Request Interception Middleware**:
   - Continuous 8-stage interception lifecycle: path exemptions -> bearer token extraction -> JWT signature verification -> JTI blacklist revocation check -> `RequestContext` assembly -> dynamic ABAC/RBAC policy evaluation -> SHA-256 audit trail event logging -> state injection.
   - See `references/fastapi_zero_trust_middleware.md` for full implementation details.

6. **Multi-Tenant OIDC, Dynamic JWKS Key Rotation & Replay Protection**:
   - Strict tenant boundary isolation, automatic signing key rotation with standard JWKS endpoint exposure (`/api/v1/auth/jwks.json`), and single-use refresh token rotation with immediate session family invalidation on replay detection.
   - See `references/multi_tenant_oidc_jwt_jwks.md` for complete patterns.

## Verification & Testing Patterns

```python
# Verifying Cryptographic Hash Chaining in Tests
prev_hash = "0" * 64
for entry in audit_logs:
    expected_hash = compute_audit_hash(prev_hash, entry)
    assert entry.current_hash == expected_hash, f"Tamper detected at log id {entry.id}"
    prev_hash = entry.current_hash
```

## Pitfalls & Best Practices

- **Never Trust Cached Permissions**: Permissions and subject trust scores must be re-evaluated when risk signals change (e.g., suspicious IP shift, velocity spike).
- **Fast Revocation Lookups**: Place token blacklist checks in fast in-memory stores (e.g. Redis) with persistent DB fallback to avoid latency spikes on protected routes.
- **Fail-Closed Policy Engine**: If policy evaluation encounters an unrecognized condition or malformed context, default to `DENY`.
- **Absolute Path & Secret Hygiene**: Ensure audit payloads sanitize credentials and mask tokens as `[REDACTED]`.
