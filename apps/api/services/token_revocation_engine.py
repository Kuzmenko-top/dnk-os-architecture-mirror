# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_token_revocation_engine"
# purpose: "High-Performance Token Blacklisting, JTI Validation & Expired Token Pruning Engine (DNK-SECURITY-001 Phase 2)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class TokenRevocationEngine:
    """
    In-memory thread-safe blacklist engine for revoked JTIs with TTL tracking and automatic cleanup.
    """

    def __init__(self):
        self._lock = threading.Lock()
        # Key: token_jti -> Dict[str, Any]
        self._revocations: Dict[str, Dict[str, Any]] = {}

    def revoke_token(
        self,
        token_jti: str,
        subject_id: str,
        expires_at: datetime,
        token_type: str = "access",
        reason: str = "Explicit revocation",
    ) -> Dict[str, Any]:
        """
        Adds a token JTI to the revocation blacklist.
        """
        with self._lock:
            # Ensure expires_at has timezone
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)

            entry = {
                "token_jti": token_jti,
                "subject_id": subject_id,
                "token_type": token_type,
                "reason": reason,
                "is_revoked": True,
                "revoked_at": datetime.now(timezone.utc),
                "expires_at": expires_at,
            }
            self._revocations[token_jti] = entry
            return self._format_entry(entry)

    def is_token_revoked(self, token_jti: str) -> bool:
        """
        Checks whether the specified token JTI is revoked.
        """
        with self._lock:
            entry = self._revocations.get(token_jti)
            if not entry:
                return False

            # If the token has already naturally expired, it can be considered not actively revoked
            now = datetime.now(timezone.utc)
            if entry["expires_at"] < now:
                # Expired naturally
                return True
            return entry.get("is_revoked", True)

    def cleanup_expired_tokens(self, current_time: Optional[datetime] = None) -> int:
        """
        Prunes tokens from memory whose natural expiration time has passed.
        Returns the count of pruned tokens.
        """
        now = current_time or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        with self._lock:
            expired_jtis = [
                jti for jti, entry in self._revocations.items()
                if entry["expires_at"] < now
            ]
            for jti in expired_jtis:
                del self._revocations[jti]
            return len(expired_jtis)

    def list_revoked_tokens(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Lists actively revoked token entries.
        """
        with self._lock:
            entries = list(self._revocations.values())[:limit]
            return [self._format_entry(e) for e in entries]

    def get_revocation_stats(self) -> Dict[str, Any]:
        """
        Returns stats about the revocation store.
        """
        with self._lock:
            now = datetime.now(timezone.utc)
            active_count = sum(1 for e in self._revocations.values() if e["expires_at"] >= now)
            expired_count = len(self._revocations) - active_count
            return {
                "total_entries": len(self._revocations),
                "active_revocations": active_count,
                "stale_expired_entries": expired_count,
            }

    @staticmethod
    def _format_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "token_jti": entry["token_jti"],
            "subject_id": entry["subject_id"],
            "token_type": entry["token_type"],
            "reason": entry["reason"],
            "is_revoked": entry["is_revoked"],
            "revoked_at": entry["revoked_at"].isoformat() if hasattr(entry["revoked_at"], "isoformat") else str(entry["revoked_at"]),
            "expires_at": entry["expires_at"].isoformat() if hasattr(entry["expires_at"], "isoformat") else str(entry["expires_at"]),
        }
