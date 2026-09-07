# Zero-Trust REST API Router & Endpoint Reference

## 1. REST API Architecture for Zero-Trust Systems

A complete Zero-Trust Security layer exposes REST endpoints for policy administration, live access evaluation, token revocation management, and tamper-evident audit log verification.

### Key Endpoints Overview

| Method | Path | Description | Access Level |
|---|---|---|---|
| `POST` | `/api/v1/security/evaluate` | Dynamic RBAC/ABAC access simulation & evaluation | High / System |
| `POST` | `/api/v1/security/tokens/revoke` | Revoke a JWT token by `token_jti` | Admin / Security |
| `GET` | `/api/v1/security/tokens/is-revoked/{token_jti}` | Check if token is in blacklist | Public / Middleware |
| `GET` | `/api/v1/security/tokens/stats` | Active and total revocation statistics | Security Monitor |
| `POST` | `/api/v1/security/tokens/cleanup` | Trigger TTL cleanup of expired blacklist entries | Maintenance Cron |
| `GET` | `/api/v1/security/audit/logs` | Query audit log entries with filters | Compliance Auditor |
| `GET` | `/api/v1/security/audit/verify-chain` | Verify cryptographic hash chain integrity | Compliance Auditor |
| `POST` | `/api/v1/security/policies` | Create a dynamic RBAC/ABAC policy | Security Admin |
| `GET` | `/api/v1/security/policies` | List all active policies for workspace | Security Admin |
| `GET` | `/api/v1/security/policies/{policy_id}` | Retrieve policy details | Security Admin |
| `DELETE` | `/api/v1/security/policies/{policy_id}` | Delete / deactivate policy | Security Admin |

---

## 2. Request & Response Patterns

### Dynamic Policy Evaluation Request (`/evaluate`)
```json
{
  "subject_id": "usr_alpha_999",
  "subject_type": "user",
  "roles": ["developer"],
  "trust_score": 0.85,
  "mfa_authenticated": true,
  "ip_address": "192.168.1.100",
  "geo_country": "UA",
  "user_agent": "Mozilla/5.0",
  "velocity_rpm": 5,
  "action": "canvas:write",
  "resource": "canvas:node_123",
  "workspace_id": "ws-alpha-001"
}
```

### Policy Evaluation Response
```json
{
  "allowed": true,
  "decision": "ALLOW",
  "reason": "Allowed by dynamic policy pol_dev_001",
  "matching_policy_id": "pol_dev_001",
  "evaluation_time_ms": 0.42,
  "audit_logged": true
}
```

### Tamper-Evident Audit Chain Verification Response (`/audit/verify-chain`)
```json
{
  "is_valid": true,
  "total_checked": 142,
  "tampered_index": null,
  "message": "Audit trail is 100% verified and tamper-free."
}
```
