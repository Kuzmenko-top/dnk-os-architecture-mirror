# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_token_signature_verifier"
# purpose: "Cryptographic JWT/Token Signature Verification & Claims Validation Engine (DNK-SECURITY-001 Phase 3)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import base64
import hashlib
import hmac
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TokenPayload(BaseModel):
    jti: str
    sub: str
    workspace_id: str = "ws_default"
    roles: List[str] = Field(default_factory=list)
    subject_type: str = "user"  # user, service, agent
    trust_score: float = 1.0
    mfa_authenticated: bool = False
    iss: str = "dnk-security-auth"
    aud: str = "dnk-os-api"
    iat: int
    exp: int
    custom_claims: Dict[str, Any] = Field(default_factory=dict)


class TokenVerificationResult(BaseModel):
    valid: bool
    payload: Optional[TokenPayload] = None
    error: Optional[str] = None
    error_code: Optional[str] = None  # "EXPIRED", "INVALID_SIGNATURE", "MALFORMED", "REVOKED", etc.


class TokenSignatureVerifier:
    """
    HMAC-SHA256 JWT Token Signer and Verifier for Zero-Trust authentication.
    """

    def __init__(self, secret_key: str = "dnk-zero-trust-secret-key-production-change-me"):
        self.secret_key = secret_key.encode("utf-8")

    @staticmethod
    def _b64url_encode(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")

    @staticmethod
    def _b64url_decode(s: str) -> bytes:
        padding = 4 - (len(s) % 4)
        if padding != 4:
            s += "=" * padding
        return base64.urlsafe_b64decode(s.encode("utf-8"))

    def create_token(
        self,
        subject_id: str,
        workspace_id: str = "ws_default",
        roles: Optional[List[str]] = None,
        subject_type: str = "user",
        trust_score: float = 1.0,
        mfa_authenticated: bool = False,
        expires_in_seconds: int = 3600,
        jti: Optional[str] = None,
        custom_claims: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Creates a signed HMAC-SHA256 JWT token.
        """
        now = datetime.now(timezone.utc)
        iat = int(now.timestamp())
        exp = int((now + timedelta(seconds=expires_in_seconds)).timestamp())
        token_jti = jti or f"jti_{uuid.uuid4().hex}"

        header = {"alg": "HS256", "typ": "JWT"}
        payload = {
            "jti": token_jti,
            "sub": subject_id,
            "workspace_id": workspace_id,
            "roles": roles or ["user"],
            "subject_type": subject_type,
            "trust_score": float(trust_score),
            "mfa_authenticated": mfa_authenticated,
            "iss": "dnk-security-auth",
            "aud": "dnk-os-api",
            "iat": iat,
            "exp": exp,
            "custom_claims": custom_claims or {},
        }

        header_b64 = self._b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
        payload_b64 = self._b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))

        signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
        signature = hmac.new(self.secret_key, signing_input, hashlib.sha256).digest()
        signature_b64 = self._b64url_encode(signature)

        return f"{header_b64}.{payload_b64}.{signature_b64}"

    def verify_token(self, token_str: str) -> TokenVerificationResult:
        """
        Verifies the signature and standard claims of a JWT string.
        """
        if not token_str or not isinstance(token_str, str):
            return TokenVerificationResult(valid=False, error="Empty token provided", error_code="MALFORMED")

        parts = token_str.strip().split(".")
        if len(parts) != 3:
            return TokenVerificationResult(valid=False, error="Malformed JWT structure", error_code="MALFORMED")

        header_b64, payload_b64, signature_b64 = parts

        # Verify signature
        signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
        expected_sig = hmac.new(self.secret_key, signing_input, hashlib.sha256).digest()

        try:
            actual_sig = self._b64url_decode(signature_b64)
        except Exception:
            return TokenVerificationResult(valid=False, error="Invalid base64 signature", error_code="MALFORMED")

        if not hmac.compare_digest(expected_sig, actual_sig):
            return TokenVerificationResult(valid=False, error="Invalid token signature", error_code="INVALID_SIGNATURE")

        # Parse payload
        try:
            payload_raw = json.loads(self._b64url_decode(payload_b64).decode("utf-8"))
        except Exception:
            return TokenVerificationResult(valid=False, error="Invalid payload encoding", error_code="MALFORMED")

        # Validate expiration
        now_ts = int(datetime.now(timezone.utc).timestamp())
        exp_ts = payload_raw.get("exp", 0)
        if exp_ts < now_ts:
            return TokenVerificationResult(valid=False, error="Token has expired", error_code="EXPIRED")

        try:
            parsed_payload = TokenPayload(**payload_raw)
            return TokenVerificationResult(valid=True, payload=parsed_payload)
        except Exception as e:
            return TokenVerificationResult(valid=False, error=f"Invalid payload claims: {str(e)}", error_code="MALFORMED")
