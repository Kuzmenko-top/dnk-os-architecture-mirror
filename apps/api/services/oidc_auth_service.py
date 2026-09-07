# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/services/oidc_auth_service.py"
# purpose: "OAuth2/OIDC, Multi-Tenant JWT Token Engine, Key Rotation & Revocation Service for DNK OS."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import time
import uuid
import secrets
import hashlib
import json
import base64
import hmac
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

from apps.api.db.models.auth_user import AuthUser, UserAccountStatus, UserAuthProvider
from apps.api.db.models.auth_session import AuthSession, SessionStatus
from apps.api.db.models.auth_audit_log import AuthAuditLog, AuditEventType, AuditSeverity


class TokenSigningKey:
    """Represents an active or retired cryptographic signing key in key ring."""
    def __init__(self, kid: str, secret: str, algorithm: str = "HS256", is_active: bool = True):
        self.kid = kid
        self.secret = secret
        self.algorithm = algorithm
        self.is_active = is_active
        self.created_at = datetime.now(timezone.utc)

    def to_jwk(self) -> Dict[str, Any]:
        """Expose public JWK format without leaking private secrets."""
        return {
            "kty": "oct",
            "use": "sig",
            "alg": self.algorithm,
            "kid": self.kid,
            "status": "active" if self.is_active else "retired",
        }


class OIDCAuthService:
    """
    Zero-Trust Multi-Tenant OIDC / JWT Authentication & Token Lifecycle Service.
    Handles JWT minting, verification with active key rings, refresh rotation, and denylisting.
    """

    def __init__(
        self,
        issuer: str = "https://auth.dnk-e.com",
        access_token_ttl_seconds: int = 900,  # 15 minutes
        refresh_token_ttl_seconds: int = 604800,  # 7 days
    ):
        self.issuer = issuer
        self.access_token_ttl = access_token_ttl_seconds
        self.refresh_token_ttl = refresh_token_ttl_seconds

        # In-memory stores (designed for pluggable persistence / Redis cache)
        self._key_ring: Dict[str, TokenSigningKey] = {}
        self._active_kid: Optional[str] = None
        self._revoked_tokens: Dict[str, float] = {}  # token_jti -> expiry_timestamp
        self._users_db: Dict[str, AuthUser] = {}  # user_id -> AuthUser
        self._user_email_index: Dict[Tuple[str, str], str] = {}  # (tenant_id, email) -> user_id
        self._sessions: Dict[str, AuthSession] = {}  # session_id -> AuthSession
        self._audit_logs: List[AuthAuditLog] = []

        # Initialize primary master signing key
        self.rotate_signing_key()

    @property
    def access_token_ttl_seconds(self) -> int:
        return self.access_token_ttl

    def rotate_signing_key(self, algorithm: str = "HS256") -> str:
        """Generates a new active signing key and marks older keys as retired."""
        new_kid = f"key_{uuid.uuid4().hex[:10]}"
        new_secret = secrets.token_urlsafe(48)
        
        # Retire old active keys
        for k in self._key_ring.values():
            k.is_active = False

        key_obj = TokenSigningKey(kid=new_kid, secret=new_secret, algorithm=algorithm, is_active=True)
        self._key_ring[new_kid] = key_obj
        self._active_kid = new_kid
        return new_kid

    def get_jwks(self) -> Dict[str, List[Dict[str, Any]]]:
        """Public JWKS endpoint payload."""
        return {"keys": [k.to_jwk() for k in self._key_ring.values()]}

    # --- Pure Python JWT (HS256) implementation with standard base64url ---

    def _b64url_encode(self, data: bytes) -> str:
        return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")

    def _b64url_decode(self, s: str) -> bytes:
        padding = "=" * (4 - (len(s) % 4)) if (len(s) % 4) != 0 else ""
        return base64.urlsafe_b64decode((s + padding).encode("utf-8"))

    def _sign_jwt(self, header: Dict[str, Any], payload: Dict[str, Any], secret: str) -> str:
        h_bytes = json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8")
        p_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        
        h_b64 = self._b64url_encode(h_bytes)
        p_b64 = self._b64url_encode(p_bytes)
        signing_input = f"{h_b64}.{p_b64}".encode("utf-8")
        
        sig = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
        sig_b64 = self._b64url_encode(sig)
        return f"{h_b64}.{p_b64}.{sig_b64}"

    def _verify_jwt(self, token: str) -> Dict[str, Any]:
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Malformed JWT structure")

        h_b64, p_b64, sig_b64 = parts
        
        try:
            header = json.loads(self._b64url_decode(h_b64).decode("utf-8"))
            payload = json.loads(self._b64url_decode(p_b64).decode("utf-8"))
        except Exception as e:
            raise ValueError(f"Invalid JSON in token headers/payload: {e}")

        kid = header.get("kid")
        if not kid or kid not in self._key_ring:
            raise ValueError(f"Unknown signing key ID: {kid}")

        key_obj = self._key_ring[kid]
        signing_input = f"{h_b64}.{p_b64}".encode("utf-8")
        expected_sig = hmac.new(key_obj.secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
        actual_sig = self._b64url_decode(sig_b64)

        if not hmac.compare_digest(expected_sig, actual_sig):
            raise ValueError("Invalid cryptographic signature")

        # Expiration and Issuer Check
        now = time.time()
        if payload.get("exp", 0) < now:
            raise ValueError("Token has expired")
        if payload.get("iss") != self.issuer:
            raise ValueError(f"Invalid token issuer: {payload.get('iss')}")

        # Revocation / Denylist Check
        jti = payload.get("jti")
        if jti and jti in self._revoked_tokens:
            raise ValueError("Token has been revoked")

        return payload

    # --- User Management & Registration ---

    def register_user(
        self,
        tenant_id: str,
        email: str,
        display_name: str,
        password: Optional[str] = None,
        roles: Optional[List[str]] = None,
        provider: UserAuthProvider = UserAuthProvider.LOCAL,
    ) -> AuthUser:
        key = (tenant_id, email.lower())
        if key in self._user_email_index:
            raise ValueError(f"User with email '{email}' already exists in tenant '{tenant_id}'")

        pwd_hash, salt = None, None
        if password:
            pwd_hash, salt = AuthUser.hash_password(password)

        user = AuthUser(
            tenant_id=tenant_id,
            email=email.lower(),
            display_name=display_name,
            password_hash=pwd_hash,
            salt=salt,
            roles=roles or ["viewer"],
            provider=provider,
            status=UserAccountStatus.ACTIVE,
        )

        self._users_db[user.id] = user
        self._user_email_index[key] = user.id
        return user

    def get_user_by_id(self, user_id: str) -> Optional[AuthUser]:
        return self._users_db.get(user_id)

    def get_user_by_email(self, tenant_id: str, email: str) -> Optional[AuthUser]:
        user_id = self._user_email_index.get((tenant_id, email.lower()))
        if not user_id:
            return None
        return self._users_db.get(user_id)

    # --- Token Minting & Authentication ---

    def authenticate_local_user(
        self,
        tenant_id: str,
        email: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Tuple[str, str, AuthSession]:
        """Authenticate user with credentials, create session, and issue access + refresh tokens."""
        user = self.get_user_by_email(tenant_id, email)
        
        if not user or not user.verify_password(password):
            self._record_audit_log(
                tenant_id=tenant_id,
                actor_id=user.id if user else "anonymous",
                event_type=AuditEventType.USER_LOGIN_FAILED,
                severity=AuditSeverity.WARNING,
                details={"email": email, "ip": ip_address},
            )
            raise ValueError("Invalid email or password")

        if not user.is_active():
            raise ValueError("User account is inactive, suspended or pending verification")

        user.record_login()

        # Create session
        now = datetime.now(timezone.utc)
        session = AuthSession(
            tenant_id=tenant_id,
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=now + timedelta(seconds=self.refresh_token_ttl),
        )
        self._sessions[session.id] = session

        # Issue token pair
        access_token = self.mint_access_token(user, session_id=session.id)
        refresh_token = self.mint_refresh_token(user, session_id=session.id)

        session.refresh_token_hash = hashlib.sha256(refresh_token.encode("utf-8")).hexdigest()

        self._record_audit_log(
            tenant_id=tenant_id,
            actor_id=user.id,
            event_type=AuditEventType.USER_LOGIN_SUCCESS,
            severity=AuditSeverity.INFO,
            details={"session_id": session.id, "ip": ip_address},
        )

        return access_token, refresh_token, session

    def mint_access_token(
        self,
        user: AuthUser,
        session_id: Optional[str] = None,
        custom_claims: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Mint a short-lived, cryptographically signed Access Token."""
        if not self._active_kid or self._active_kid not in self._key_ring:
            self.rotate_signing_key()

        active_key = self._key_ring[str(self._active_kid)]
        now = time.time()
        jti = f"tok_{uuid.uuid4().hex[:14]}"

        header = {"alg": "HS256", "typ": "JWT", "kid": active_key.kid}
        payload = {
            "iss": self.issuer,
            "sub": user.id,
            "tenant_id": user.tenant_id,
            "email": user.email,
            "roles": user.roles,
            "custom_permissions": user.custom_permissions,
            "session_id": session_id,
            "token_type": "access_token",
            "jti": jti,
            "iat": int(now),
            "exp": int(now + self.access_token_ttl),
        }

        if custom_claims:
            payload.update(custom_claims)

        return self._sign_jwt(header, payload, active_key.secret)

    def mint_refresh_token(self, user: AuthUser, session_id: str) -> str:
        """Mint a longer-lived Refresh Token."""
        if not self._active_kid or self._active_kid not in self._key_ring:
            self.rotate_signing_key()

        active_key = self._key_ring[str(self._active_kid)]
        now = time.time()
        jti = f"ref_{uuid.uuid4().hex[:14]}"

        header = {"alg": "HS256", "typ": "JWT", "kid": active_key.kid}
        payload = {
            "iss": self.issuer,
            "sub": user.id,
            "tenant_id": user.tenant_id,
            "session_id": session_id,
            "token_type": "refresh_token",
            "jti": jti,
            "iat": int(now),
            "exp": int(now + self.refresh_token_ttl),
        }
        return self._sign_jwt(header, payload, active_key.secret)

    def refresh_access_token(self, refresh_token: str) -> Tuple[str, str]:
        """Validate refresh token, rotate it, and issue a fresh token pair."""
        payload = self._verify_jwt(refresh_token)
        
        if payload.get("token_type") != "refresh_token":
            raise ValueError("Provided token is not a refresh token")

        session_id = payload.get("session_id")
        user_id = payload.get("sub")
        old_jti = payload.get("jti")

        if not session_id or not user_id:
            raise ValueError("Invalid refresh token claims")

        session = self._sessions.get(str(session_id))
        if not session or not session.is_valid():
            raise ValueError("Session is expired or revoked")

        # Verify refresh token hash to prevent token replay
        current_token_hash = hashlib.sha256(refresh_token.encode("utf-8")).hexdigest()
        if session.refresh_token_hash and session.refresh_token_hash != current_token_hash:
            # Possible token theft! Revoke session immediately
            session.revoke()
            raise ValueError("Security violation: Refresh token reused or mismatched")

        user = self.get_user_by_id(str(user_id))
        if not user or not user.is_active():
            raise ValueError("User account is no longer active")

        # Revoke old refresh token JTI
        if old_jti:
            self._revoked_tokens[old_jti] = payload.get("exp", time.time() + 3600)

        # Issue new token pair
        new_access_token = self.mint_access_token(user, session_id=session.id)
        new_refresh_token = self.mint_refresh_token(user, session_id=session.id)

        session.refresh_token_hash = hashlib.sha256(new_refresh_token.encode("utf-8")).hexdigest()
        session.touch()

        return new_access_token, new_refresh_token

    def verify_token(self, token: str) -> Dict[str, Any]:
        """Cryptographically verify token signature, expiry, and revocation."""
        return self._verify_jwt(token)

    def revoke_token(self, token: str, reason: Optional[str] = None) -> None:
        """Revoke a token by adding its JTI to the denylist."""
        try:
            payload = self._verify_jwt(token)
            jti = payload.get("jti")
            exp = payload.get("exp", time.time() + self.access_token_ttl)
            if jti:
                self._revoked_tokens[jti] = exp
        except Exception:
            # If token is invalid or already expired, still proceed
            pass

    def revoke_session(self, session_id: str) -> None:
        """Revoke user session."""
        session = self._sessions.get(session_id)
        if session:
            session.revoke()

    def _record_audit_log(
        self,
        tenant_id: str,
        actor_id: str,
        event_type: AuditEventType,
        severity: AuditSeverity = AuditSeverity.INFO,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        log = AuthAuditLog(
            tenant_id=tenant_id,
            actor_id=actor_id,
            actor_type="user",
            event_type=event_type,
            severity=severity,
            details=details or {},
        )
        log.seal()
        self._audit_logs.append(log)

    def get_audit_logs(self, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        logs = self._audit_logs
        if tenant_id:
            logs = [l for l in logs if l.tenant_id == tenant_id]
        return [l.to_dict() for l in logs]
