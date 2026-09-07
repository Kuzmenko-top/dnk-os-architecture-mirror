# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_a2a_message_codec_service"
# purpose: "Wire Codec, Cryptographic Signature Verification & Trace Context Propagation (DNK-A2A-004 Phase 2)"
# author: "DNK-e.com Maksym & Gerych Prime"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import base64
import hashlib
import hmac
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger("dnk.a2a.codec")


class A2AMessageCodecService:
    """Handles serialization, HMAC-SHA256 signing, verification, and trace context propagation for A2A wire messages."""

    @staticmethod
    def compute_signature(payload_bytes: bytes, secret_key: str) -> str:
        """Computes HMAC-SHA256 signature for the given payload bytes."""
        return hmac.new(secret_key.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()

    @staticmethod
    def verify_signature(payload_bytes: bytes, signature: str, secret_key: str) -> bool:
        """Constant-time verification of HMAC-SHA256 signature."""
        expected = A2AMessageCodecService.compute_signature(payload_bytes, secret_key)
        return hmac.compare_digest(expected, signature)

    def create_envelope(
        self,
        workspace_id: str,
        sender_agent_id: str,
        recipient_agent_id: str,
        method: str,
        payload: Dict[str, Any],
        trace_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
        protocol_pattern: str = "peer-to-peer",
        headers: Optional[Dict[str, str]] = None,
        secret_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Creates a standardized wire envelope with tracing headers and optional cryptographic signature."""
        envelope_id = f"env_{uuid.uuid4().hex[:12]}"
        effective_trace_id = trace_id or f"trc_{uuid.uuid4().hex[:12]}"
        span_id = f"spn_{uuid.uuid4().hex[:8]}"

        envelope_dict = {
            "id": envelope_id,
            "workspace_id": workspace_id,
            "trace_id": effective_trace_id,
            "span_id": span_id,
            "parent_span_id": parent_span_id,
            "sender_agent_id": sender_agent_id,
            "recipient_agent_id": recipient_agent_id,
            "protocol_pattern": protocol_pattern,
            "method": method,
            "payload": payload,
            "headers": headers or {},
            "delivery_attempts": 1,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        if secret_key:
            canonical_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
            signature = self.compute_signature(canonical_bytes, secret_key)
            envelope_dict["signature_hash"] = signature
        else:
            envelope_dict["signature_hash"] = None

        return envelope_dict

    def encode_wire_format(self, envelope: Dict[str, Any], format_type: str = "json") -> str:
        """Serializes envelope to wire representation (JSON or Base64 binary)."""
        json_str = json.dumps(envelope, ensure_ascii=False)
        if format_type == "base64":
            return base64.b64encode(json_str.encode("utf-8")).decode("ascii")
        return json_str

    def decode_wire_format(
        self, raw_wire: str, format_type: str = "json", secret_key: Optional[str] = None
    ) -> Tuple[Dict[str, Any], bool]:
        """Deserializes wire representation into an envelope dictionary and verifies signature if key provided.
        Returns (envelope_dict, is_valid_signature).
        """
        if format_type == "base64":
            raw_json = base64.b64decode(raw_wire.encode("ascii")).decode("utf-8")
        else:
            raw_json = raw_wire

        envelope = json.loads(raw_json)
        sig = envelope.get("signature_hash")

        if secret_key and sig:
            payload = envelope.get("payload", {})
            canonical_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
            valid = self.verify_signature(canonical_bytes, sig, secret_key)
            return envelope, valid
        elif secret_key and not sig:
            return envelope, False

        return envelope, True

    def inject_trace_context(
        self, headers: Dict[str, str], trace_id: str, span_id: str, parent_span_id: Optional[str] = None
    ) -> Dict[str, str]:
        """Injects W3C / A2A distributed trace context into outbound headers."""
        out = dict(headers)
        out["x-dnk-trace-id"] = trace_id
        out["x-dnk-span-id"] = span_id
        if parent_span_id:
            out["x-dnk-parent-span-id"] = parent_span_id
        return out

    def extract_trace_context(self, headers: Dict[str, str]) -> Dict[str, Optional[str]]:
        """Extracts trace identifiers from inbound request headers."""
        return {
            "trace_id": headers.get("x-dnk-trace-id") or headers.get("traceparent"),
            "span_id": headers.get("x-dnk-span-id"),
            "parent_span_id": headers.get("x-dnk-parent-span-id"),
        }
