# Zero-Trust Policy Engine & Tamper-Evident Audit Reference

## 1. Context Evaluation Schema (ABAC)

The context evaluator receives a dictionary representing request metadata:
```python
context = {
    "ip_address": "192.168.1.50",
    "country_code": "UA",
    "timestamp_utc": "2026-08-29T14:30:00Z",
    "device_trust_score": 0.95,
    "request_velocity_rpm": 25,
    "mfa_authenticated": True
}
```

### Policy Rules Matching Logic
1. **IP Range (CIDR)**: Use `ipaddress.ip_network` to check if request IP falls within allowed CIDR blocks.
2. **Time Window**: Parse `time_window_utc` (e.g. `{"start": "06:00", "end": "20:00"}`) and compare against current UTC time.
3. **Geo-Location**: Check if `context["country_code"]` is in `policy.allowed_geo_countries`.
4. **Trust Score**: Verify `context["device_trust_score"] >= policy.min_trust_score`.
5. **Velocity**: Ensure `context["request_velocity_rpm"] <= policy.max_velocity_rpm`.
6. **MFA Enforcement**: If `policy.mfa_required` is True, verify `context["mfa_authenticated"]` is True.

---

## 2. Cryptographic Hash Chaining for Immutable Audit Logs

### Formula & Canonical JSON Serialization
To guarantee deterministic hashing regardless of dictionary key ordering:
```python
import hashlib
import json

def compute_event_hash(prev_hash: str, payload: dict) -> str:
    canonical_json = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    raw_to_hash = f"{prev_hash}:{canonical_json}"
    return hashlib.sha256(raw_to_hash.encode("utf-8")).hexdigest()
```

### Overnight Time Window Handling (UTC)
When a policy time window crosses midnight (e.g., `22:00:00` to `06:00:00`):
```python
if t_start <= t_end:
    is_valid = t_start <= cur_t <= t_end
else:
    is_valid = cur_t >= t_start or cur_t <= t_end
```

### Fast-Lookup In-Memory Token Blacklist with TTL
```python
class TokenRevocationEngine:
    def __init__(self):
        self._lock = threading.Lock()
        self._revocations: dict[str, dict] = {}
        
    def is_token_revoked(self, jti: str) -> bool:
        with self._lock:
            entry = self._revocations.get(jti)
            if not entry:
                return False
            if entry["expires_at"] < datetime.now(timezone.utc):
                return True
            return entry.get("is_revoked", True)
```

---

## 3. Token Refresh Rotation & Replay Attack Mitigation

When issuing refresh tokens in OAuth2/OIDC flows:
1. **Refresh Token Rotation**: Every call to `/refresh` invalidates the old refresh token (`is_revoked = True`) and issues a brand-new refresh token paired with a updated access token.
2. **Replay Detection & Session Invalidation**: If an already-revoked refresh token is submitted again (indicating a potential token theft/replay attack), the authentication service immediately revokes the **entire user session** and blacklists all associated active access tokens.
3. **Password Hashing Standard**: Use PBKDF2-HMAC-SHA256 (or Argon2id) with cryptographically secure random 16-byte salt per user.

---

## 4. Method Signature Alignment Pitfall in Auth Routers

- **Avoid Monolithic vs Specific Naming Discrepancies**: When delegating route authentication from FastAPI routers to an underlying OIDC/Auth service:
  - Distinguish local password authentication (`authenticate_local_user(...)`) from third-party OAuth2/OIDC code exchange (`authenticate_oidc_code(...)`).
  - Distinguish token rotation (`refresh_access_token(refresh_token)`) from full credential re-authentication.
  - Ensure `UserLoginRequest` schemas correctly map `tenant_id`, `email`, and `password` to service parameters.

### Tamper Verification Algorithm
```python
def verify_audit_trail_integrity(records: list[SecurityAuditLogModel]) -> tuple[bool, str | None]:
    expected_prev_hash = "0" * 64
    for record in records:
        if record.prev_hash != expected_prev_hash:
            return False, f"Broken chain at ID {record.id}: expected prev_hash {expected_prev_hash}, got {record.prev_hash}"
        
        computed_hash = compute_record_hash(record.prev_hash, record)
        if record.current_hash != computed_hash:
            return False, f"Tampered record at ID {record.id}: payload mismatch"
            
        expected_prev_hash = record.current_hash
    return True, None
```
