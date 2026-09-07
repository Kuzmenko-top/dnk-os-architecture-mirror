# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_middleware_zero_trust_middleware"
# purpose: "FastAPI Zero-Trust Request Interception, Token Validation, Dynamic ABAC Enforcement & Audit Logging Middleware (DNK-SECURITY-001 Phase 3)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import time
import fnmatch
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from apps.api.services.audit_trail_engine import AuditTrailEngine
from apps.api.services.token_revocation_engine import TokenRevocationEngine
from apps.api.services.token_signature_verifier import TokenSignatureVerifier
from apps.api.services.zero_trust_policy_engine import RequestContext, ZeroTrustPolicyEngine


class ZeroTrustMiddleware(BaseHTTPMiddleware):
    """
    FastAPI Middleware providing continuous Zero-Trust evaluation on every request:
    1. Public route bypass.
    2. Bearer token extraction & cryptographic verification.
    3. Token revocation blacklist verification (JTI lookup).
    4. Multi-factor request context construction (IP, Geo, Velocity, Trust Score, MFA).
    5. Dynamic RBAC/ABAC policy evaluation.
    6. Tamper-evident cryptographic audit log recording.
    """

    DEFAULT_EXEMPT_PATHS = [
        "/docs",
        "/docs/*",
        "/redoc",
        "/redoc/*",
        "/openapi.json",
        "/health",
        "/api/health",
        "/api/v1/health",
        "/metrics",
        "/favicon.ico",
    ]

    def __init__(
        self,
        app,
        policy_engine: Optional[ZeroTrustPolicyEngine] = None,
        revocation_engine: Optional[TokenRevocationEngine] = None,
        audit_engine: Optional[AuditTrailEngine] = None,
        token_verifier: Optional[TokenSignatureVerifier] = None,
        policies_provider: Optional[Callable[[], List[Dict[str, Any]]]] = None,
        exempt_paths: Optional[List[str]] = None,
    ):
        super().__init__(app)
        self.policy_engine = policy_engine or ZeroTrustPolicyEngine()
        self.revocation_engine = revocation_engine or TokenRevocationEngine()
        self.audit_engine = audit_engine or AuditTrailEngine()
        self.token_verifier = token_verifier or TokenSignatureVerifier()
        self.policies_provider = policies_provider or (lambda: [])
        self.exempt_paths = exempt_paths or self.DEFAULT_EXEMPT_PATHS
        # Velocity tracker: ip -> list of timestamps
        self._velocity_tracker: Dict[str, List[float]] = defaultdict(list)

    def _is_path_exempt(self, path: str) -> bool:
        for pattern in self.exempt_paths:
            if fnmatch.fnmatch(path, pattern) or path == pattern:
                return True
        return False

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        client = request.client
        return client.host if client else "127.0.0.1"

    def _get_request_velocity(self, ip: str) -> int:
        now = time.time()
        window_start = now - 60.0
        # Clean timestamps older than 1 minute
        self._velocity_tracker[ip] = [ts for ts in self._velocity_tracker[ip] if ts >= window_start]
        self._velocity_tracker[ip].append(now)
        return len(self._velocity_tracker[ip])

    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
        path = request.url.path

        # 1. Check path exemption
        if self._is_path_exempt(path):
            return await call_next(request)

        client_ip = self._get_client_ip(request)
        geo_country = request.headers.get("X-Geo-Country") or request.headers.get("X-Country-Code")
        user_agent = request.headers.get("User-Agent")
        velocity_rpm = self._get_request_velocity(client_ip)

        # 2. Extract Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            self.audit_engine.record_event(
                workspace_id="anonymous",
                subject_id="unauthenticated",
                action=request.method.lower(),
                resource=path,
                decision="DENIED",
                reason="Missing or invalid Bearer Authorization header",
                ip_address=client_ip,
                geo_country=geo_country,
                user_agent=user_agent,
                trust_score=0.0,
            )
            return JSONResponse(
                status_code=401,
                content={"detail": "Unauthorized: Missing or invalid Bearer token."},
            )

        token_str = auth_header[7:].strip()

        # 3. Cryptographic Token Verification
        verification = self.token_verifier.verify_token(token_str)
        if not verification.valid or not verification.payload:
            self.audit_engine.record_event(
                workspace_id="anonymous",
                subject_id="unauthenticated",
                action=request.method.lower(),
                resource=path,
                decision="DENIED",
                reason=f"Token verification failed: {verification.error}",
                ip_address=client_ip,
                geo_country=geo_country,
                user_agent=user_agent,
                trust_score=0.0,
            )
            return JSONResponse(
                status_code=401,
                content={"detail": f"Unauthorized: {verification.error}", "error_code": verification.error_code},
            )

        payload = verification.payload

        # 4. Token Revocation Check (JTI Blacklist)
        if self.revocation_engine.is_token_revoked(payload.jti):
            self.audit_engine.record_event(
                workspace_id=payload.workspace_id,
                subject_id=payload.sub,
                action=request.method.lower(),
                resource=path,
                decision="DENIED",
                reason=f"Token JTI '{payload.jti}' is revoked in blacklist.",
                ip_address=client_ip,
                geo_country=geo_country,
                user_agent=user_agent,
                trust_score=payload.trust_score,
            )
            return JSONResponse(
                status_code=401,
                content={"detail": "Unauthorized: Token has been revoked.", "error_code": "REVOKED"},
            )

        # 5. Build Dynamic RequestContext
        ctx = RequestContext(
            subject_id=payload.sub,
            subject_type=payload.subject_type,
            roles=payload.roles,
            trust_score=payload.trust_score,
            mfa_authenticated=payload.mfa_authenticated,
            ip_address=client_ip,
            geo_country=geo_country,
            user_agent=user_agent,
            request_count_last_minute=velocity_rpm,
            attributes=payload.custom_claims,
        )

        # Resource formatting (e.g. "api:canvas:v3:nodes" or raw path)
        clean_path_parts = [p for p in path.strip("/").split("/") if p]
        resource_id = f"api:{':'.join(clean_path_parts)}" if clean_path_parts else "api:root"
        action = request.method.lower()

        # 6. Evaluate Policies
        active_policies = self.policies_provider()
        eval_result = self.policy_engine.evaluate(
            context=ctx,
            resource=resource_id,
            action=action,
            policies=active_policies,
        )

        # 7. Record Audit Event
        self.audit_engine.record_event(
            workspace_id=payload.workspace_id,
            subject_id=payload.sub,
            action=action,
            resource=resource_id,
            decision=eval_result.decision,
            reason=eval_result.reason,
            ip_address=client_ip,
            geo_country=geo_country,
            user_agent=user_agent,
            trust_score=payload.trust_score,
            policy_id=eval_result.matched_policy_id,
            extra_context=eval_result.context_evaluations,
        )

        if not eval_result.allowed:
            return JSONResponse(
                status_code=403,
                content={
                    "detail": f"Forbidden: {eval_result.reason}",
                    "decision": eval_result.decision,
                    "required_mfa": eval_result.required_mfa,
                    "policy_id": eval_result.matched_policy_id,
                },
            )

        # 8. Attach state to request and proceed
        request.state.security_subject = payload
        request.state.security_context = ctx
        request.state.policy_result = eval_result

        return await call_next(request)
