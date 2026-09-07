# FastAPI Zero-Trust Middleware & Token Signature Verification Pipeline

## 1. Zero-Trust Continuous Request Interception Lifecycle

In a Zero-Trust architecture, every HTTP request must undergo continuous verification before reaching route handlers.

```
Incoming Request
      │
      ▼
[1. Path Exemption Check] ──(Exempt)──► Allow route handler
      │ (Protected)
      ▼
[2. Authorization Header Extraction] ──(Missing/Malformed)──► 401 Unauthorized
      │ (Bearer <JWT>)
      ▼
[3. Cryptographic Signature & Claims Verification] ──(Invalid/Expired)──► 401 Unauthorized
      │ (Valid Token Payload)
      ▼
[4. JTI Blacklist Revocation Check] ──(Revoked)──► 401 Unauthorized
      │ (Not Revoked)
      ▼
[5. RequestContext Construction (IP, Geo, Velocity, Trust, MFA)]
      │
      ▼
[6. Dynamic Policy Evaluation (RBAC + ABAC + Deny-Overrides)] ──(Denied)──► 403 Forbidden
      │ (Allowed)
      ▼
[7. SHA-256 Audit Trail Event Logging (Immutable Chaining)]
      │
      ▼
[8. Inject Security State into `request.state`] ──► Route Handler
```

---

## 2. Token Signature Verifier Pattern

A robust JWT verifier handles signing, verification, and standard claims validation:

```python
import jwt
from datetime import datetime, timezone

class TokenSignatureVerifier:
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm

    def verify_token(self, token: str) -> tuple[bool, dict | None, str | None]:
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": True, "require": ["sub", "jti", "exp", "iat"]}
            )
            return True, payload, None
        except jwt.ExpiredSignatureError:
            return False, None, "EXPIRED"
        except jwt.InvalidSignatureError:
            return False, None, "INVALID_SIGNATURE"
        except jwt.InvalidTokenError:
            return False, None, "MALFORMED"
```

---

## 3. BaseHTTPMiddleware Implementation Best Practices

```python
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

class ZeroTrustMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Check exemptions
        if any(request.url.path.startswith(p) for p in self.exempt_paths):
            return await call_next(request)

        # 2. Extract bearer token
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse({"detail": "Missing Authorization header"}, status_code=401)
        token = auth_header[7:].strip()

        # 3. Verify signature
        valid, payload, err = self.token_verifier.verify_token(token)
        if not valid:
            return JSONResponse({"detail": f"Unauthorized: {err}"}, status_code=401)

        # 4. Check revocation
        if self.revocation_engine.is_token_revoked(payload["jti"]):
            return JSONResponse({"detail": "Token has been revoked"}, status_code=401)

        # 5. Build context & evaluate policies
        ctx = self.build_context(request, payload)
        res = self.policy_engine.evaluate(ctx, resource=request.url.path, action=request.method.lower())
        
        # 6. Record audit log
        self.audit_engine.log_event(
            action=request.method.lower(),
            resource=request.url.path,
            subject_id=payload["sub"],
            status="ALLOWED" if res.allowed else "DENIED"
        )

        if not res.allowed:
            return JSONResponse({"detail": f"Forbidden: {res.reason}"}, status_code=403)

        request.state.security_subject = payload
        request.state.security_context = ctx
        return await call_next(request)
```
