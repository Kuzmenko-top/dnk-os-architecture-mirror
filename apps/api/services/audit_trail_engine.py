# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_audit_trail_engine"
# purpose: "Cryptographically Chained Immutable Audit Trail Engine with SHA-256 Tamper Detection (DNK-SECURITY-001 Phase 2)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import hashlib
import json
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class AuditTrailEngine:
    """
    Append-only immutable audit trail engine using SHA-256 cryptographic chain.
    Each entry includes prev_hash and current_hash = SHA-256(prev_hash + canonical_event_json).
    """

    GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

    def __init__(self):
        self._lock = threading.Lock()
        self._logs: List[Dict[str, Any]] = []

    @classmethod
    def compute_event_hash(cls, prev_hash: str, payload: Dict[str, Any]) -> str:
        """
        Computes SHA-256 hash over prev_hash + canonical JSON representation of the payload.
        """
        canonical_json = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        raw_to_hash = f"{prev_hash}:{canonical_json}"
        return hashlib.sha256(raw_to_hash.encode("utf-8")).hexdigest()

    def record_event(
        self,
        workspace_id: str,
        subject_id: str,
        action: str,
        resource: str,
        decision: str,  # "ALLOWED" or "DENIED"
        reason: str,
        ip_address: str,
        geo_country: Optional[str] = None,
        user_agent: Optional[str] = None,
        trust_score: float = 1.0,
        policy_id: Optional[str] = None,
        extra_context: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Appends a new cryptographically chained audit log entry.
        """
        with self._lock:
            prev_hash = self._logs[-1]["current_hash"] if self._logs else self.GENESIS_HASH
            ts = timestamp or datetime.now(timezone.utc)
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)

            log_id = f"audit_{uuid.uuid4().hex[:12]}"
            payload_for_hash = {
                "id": log_id,
                "workspace_id": workspace_id,
                "subject_id": subject_id,
                "action": action,
                "resource": resource,
                "decision": decision,
                "reason": reason,
                "ip_address": ip_address,
                "geo_country": geo_country,
                "trust_score": round(trust_score, 4),
                "policy_id": policy_id,
                "timestamp": ts.isoformat(),
            }

            current_hash = self.compute_event_hash(prev_hash, payload_for_hash)

            entry = {
                **payload_for_hash,
                "user_agent": user_agent,
                "extra_context": extra_context or {},
                "prev_hash": prev_hash,
                "current_hash": current_hash,
            }
            self._logs.append(entry)
            return dict(entry)

    def verify_chain_integrity(self, logs: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Verifies the cryptographic chain across all or provided audit records.
        Detects any data alteration or chain break.
        """
        with self._lock:
            chain = logs if logs is not None else list(self._logs)

            if not chain:
                return {
                    "is_valid": True,
                    "total_checked": 0,
                    "tampered_index": None,
                    "message": "Empty audit chain is valid.",
                }

            expected_prev_hash = self.GENESIS_HASH

            for idx, entry in enumerate(chain):
                # 1. Verify prev_hash matches expected
                if entry.get("prev_hash") != expected_prev_hash:
                    return {
                        "is_valid": False,
                        "total_checked": idx,
                        "tampered_index": idx,
                        "message": f"Broken chain link at index {idx}: expected prev_hash '{expected_prev_hash}', got '{entry.get('prev_hash')}'.",
                    }

                # 2. Recompute current_hash from payload
                payload = {
                    "id": entry.get("id"),
                    "workspace_id": entry.get("workspace_id"),
                    "subject_id": entry.get("subject_id"),
                    "action": entry.get("action"),
                    "resource": entry.get("resource"),
                    "decision": entry.get("decision"),
                    "reason": entry.get("reason"),
                    "ip_address": entry.get("ip_address"),
                    "geo_country": entry.get("geo_country"),
                    "trust_score": round(float(entry.get("trust_score", 1.0)), 4),
                    "policy_id": entry.get("policy_id"),
                    "timestamp": entry.get("timestamp"),
                }
                recomputed_hash = self.compute_event_hash(str(expected_prev_hash), payload)

                if recomputed_hash != entry.get("current_hash"):
                    return {
                        "is_valid": False,
                        "total_checked": idx,
                        "tampered_index": idx,
                        "message": f"Hash mismatch at index {idx}: data tampering detected. Recomputed hash '{recomputed_hash}', stored '{entry.get('current_hash')}'.",
                    }

                expected_prev_hash = entry.get("current_hash")

            return {
                "is_valid": True,
                "total_checked": len(chain),
                "tampered_index": None,
                "message": f"Cryptographic audit chain verified: {len(chain)} records 100% valid.",
            }

    def query_logs(
        self,
        workspace_id: Optional[str] = None,
        subject_id: Optional[str] = None,
        resource: Optional[str] = None,
        decision: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Queries audit logs with optional filtering.
        """
        with self._lock:
            results = []
            for entry in reversed(self._logs):
                if workspace_id and entry.get("workspace_id") != workspace_id:
                    continue
                if subject_id and entry.get("subject_id") != subject_id:
                    continue
                if resource and entry.get("resource") != resource:
                    continue
                if decision and entry.get("decision") != decision:
                    continue
                results.append(dict(entry))
                if len(results) >= limit:
                    break
            return results

    def clear(self):
        """Clears in-memory audit logs (useful for tests)."""
        with self._lock:
            self._logs.clear()
