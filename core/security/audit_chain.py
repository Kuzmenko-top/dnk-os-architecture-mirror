# --- DNK-MRH-HEADER ---
# mrh_id: "core/security/audit_chain.py"
# purpose: "Immutable Cryptographic Hash Chain Audit Engine (Sigstore / AWS CloudTrail SOTA)"
# author: "Maxim"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-09"
# --- END DNK-MRH-HEADER ---

import time
import json
import hashlib
from typing import List, Dict, Any, Tuple, Optional

GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

class ImmutableAuditChain:
    """
    Implements a tamper-evident append-only cryptographic hash chain.
    """
    def __init__(self, genesis_seed: str = GENESIS_HASH):
        self.genesis_seed = genesis_seed
        self.chain: List[Dict[str, Any]] = []

    def append_event(self, tenant_id: str, actor_id: str, action: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Appends a new event linked to the cryptographic hash of the previous event.
        """
        prev_hash = self.chain[-1]["current_hash"] if self.chain else self.genesis_seed
        timestamp = time.time()
        
        event_payload = {
            "index": len(self.chain),
            "prev_hash": prev_hash,
            "timestamp": timestamp,
            "tenant_id": tenant_id,
            "actor_id": actor_id,
            "action": action,
            "details": details
        }
        
        canonical_str = json.dumps(event_payload, sort_keys=True, separators=(',', ':'))
        current_hash = hashlib.sha256(canonical_str.encode('utf-8')).hexdigest()
        
        record = event_payload.copy()
        record["current_hash"] = current_hash
        self.chain.append(record)
        return record

    @staticmethod
    def verify_chain(chain: List[Dict[str, Any]], genesis_seed: str = GENESIS_HASH) -> Tuple[bool, Optional[int]]:
        """
        Verifies mathematical integrity of the entire audit chain.
        Returns (True, None) if 100% valid.
        Returns (False, corrupted_index) if tampering is detected.
        """
        if not chain:
            return True, None
            
        for i, record in enumerate(chain):
            expected_prev = chain[i-1]["current_hash"] if i > 0 else genesis_seed
            if record.get("prev_hash") != expected_prev:
                return False, i
                
            payload_copy = {k: v for k, v in record.items() if k != "current_hash"}
            canonical_str = json.dumps(payload_copy, sort_keys=True, separators=(',', ':'))
            computed_hash = hashlib.sha256(canonical_str.encode('utf-8')).hexdigest()
            
            if computed_hash != record.get("current_hash"):
                return False, i
                
        return True, None
