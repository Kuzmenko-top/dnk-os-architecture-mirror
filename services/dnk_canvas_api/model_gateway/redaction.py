# --- DNK-MRH-HEADER ---
# mrh_id: "model_gateway/redaction.py"
# purpose: "Implement secret redaction, credential filtering, and prompt injection detection."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

import re
from typing import Dict, Any, List

class SecurityRedactor:
    @staticmethod
    def redact_secrets(text: str) -> str:
        # Redact generic authorization token signatures and api keys
        text = re.sub(r"(bearer|api[_-]?key|password|secret|passwd)(?:\s+is)?[\s:=]+['\"]?[a-zA-Z0-9_\-]{12,}['\"]?", r"\1: [REDACTED]", text, flags=re.IGNORECASE)
        return text

    @staticmethod
    def detect_prompt_injection(text: str) -> bool:
        # Detect standard prompt injection patterns
        injection_patterns = [
            r"ignore\s+(previous|prior)\s+instructions",
            r"system\s*prompt\s*bypass",
            r"you\s+are\s+now\s+an\s+unrestricted",
            r"forget\s+all\s+(prior|previous)\s+rules"
        ]
        for pattern in injection_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    @classmethod
    def sanitize_messages(cls, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        sanitized = []
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                # Redact
                content = cls.redact_secrets(content)
                # Check injection
                if cls.detect_prompt_injection(content):
                    content = f"[SECURITY WARNING: untrusted_source_text - possible prompt injection blocked] {content}"
            sanitized.append({**msg, "content": content})
        return sanitized
