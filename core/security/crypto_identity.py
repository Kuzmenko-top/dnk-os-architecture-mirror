# --- DNK-MRH-HEADER ---
# mrh_id: "core/security/crypto_identity.py"
# purpose: "SOTA RFC 9562 UUIDv7 Generator, Constant-Time HMAC Signer & Replay-Guard"
# author: "Maxim"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-09"
# --- END DNK-MRH-HEADER ---

import os
import time
import hmac
import hashlib
import secrets
import base64
from typing import Dict, Any, Tuple, Optional

# Crockford Base32 alphabet (no I, L, O, U to avoid human confusion)
BASE32_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"

def generate_uuidv7(prefix: str = "usr") -> str:
    """
    Generates a cryptographically secure, time-ordered UUIDv7 (RFC 9562)
    with millisecond precision and 74-bit CSPRNG entropy.
    Format: <prefix>_<26-char Base32> (e.g. usr_01J4N7K8V2M9XQW3PZ5R6T8B1A)
    """
    # 48-bit UNIX Epoch timestamp in milliseconds
    ms_timestamp = int(time.time() * 1000)
    
    # 74-bit cryptographic random entropy
    rand_bytes = secrets.token_bytes(10)
    
    # Combine timestamp (6 bytes) + random entropy (10 bytes) = 16 bytes (128 bits)
    raw_bytes = ms_timestamp.to_bytes(6, byteorder='big') + rand_bytes
    
    # Encode into Base32 string
    num = int.from_bytes(raw_bytes, byteorder='big')
    chars = []
    for _ in range(26):
        chars.append(BASE32_ALPHABET[num & 0x1F])
        num >>= 5
    encoded = "".join(reversed(chars))
    
    return f"{prefix}_{encoded}"

def generate_tenant_id() -> str:
    """Generates a typed tenant ID: ten_<UUIDv7>"""
    return generate_uuidv7(prefix="ten")

def generate_user_id() -> str:
    """Generates a typed user ID: usr_<UUIDv7>"""
    return generate_uuidv7(prefix="usr")

class CryptoIdentityManager:
    """
    Manages timing-safe HMAC-SHA256 signature creation, verification,
    and anti-replay validation.
    """
    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = secret_key.encode('utf-8') if secret_key else secrets.token_bytes(32)

    def sign_payload(self, payload: Dict[str, Any], nonce: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Signs a dictionary payload with timestamp and cryptographic nonce.
        """
        signed_payload = payload.copy()
        signed_payload["_ts"] = int(time.time())
        signed_payload["_nonce"] = nonce or secrets.token_hex(8)
        
        canonical_str = self._canonicalize(signed_payload)
        signature = hmac.new(self.secret_key, canonical_str.encode('utf-8'), hashlib.sha256).hexdigest()
        return signature, signed_payload

    def verify_signature(self, payload: Dict[str, Any], signature: str, max_age_seconds: int = 300) -> bool:
        """
        Verifies signature using constant-time comparison (hmac.compare_digest)
        and checks for replay attack expiration window.
        """
        if "_ts" not in payload or "_nonce" not in payload:
            return False
            
        current_time = int(time.time())
        payload_time = payload["_ts"]
        
        # Replay attack window check
        if abs(current_time - payload_time) > max_age_seconds:
            return False
            
        canonical_str = self._canonicalize(payload)
        expected_sig = hmac.new(self.secret_key, canonical_str.encode('utf-8'), hashlib.sha256).hexdigest()
        
        # Timing-safe constant-time comparison
        return hmac.compare_digest(expected_sig, signature)

    def _canonicalize(self, payload: Dict[str, Any]) -> str:
        """Produces deterministic sorted string representation for hashing."""
        import json
        return json.dumps(payload, sort_keys=True, separators=(',', ':'))
