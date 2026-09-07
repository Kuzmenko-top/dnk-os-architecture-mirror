# --- DNK-MRH-HEADER ---
# mrh_id: "core/plugins/plugin_audit.py"
# purpose: "Immutable Cryptographic Audit Logger for Plugin Lifecycle Events with Secret Scrubbing"
# author: "DNK-e.com Maksym"
# license: "MIT"
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-16"
# --- END DNK-MRH-HEADER ---

from typing import Dict, Any, List
from core.security.audit_chain import ImmutableAuditChain

SENSITIVE_KEY_PATTERNS = {
    "private_key",
    "secret",
    "token",
    "password",
    "credential",
    "private",
    "api_key",
    "auth",
}

def scrub_secrets(data: Any) -> Any:
    """Recursively redacts sensitive keys from audit log dictionaries/lists."""
    if isinstance(data, dict):
        cleaned = {}
        for k, v in data.items():
            if any(pat in k.lower() for pat in SENSITIVE_KEY_PATTERNS):
                cleaned[k] = "[REDACTED_SECRET]"
            else:
                cleaned[k] = scrub_secrets(v)
        return cleaned
    elif isinstance(data, list):
        return [scrub_secrets(item) for item in data]
    return data

class PluginAuditLogger:
    """Manages immutable audit logging for plugin lifecycle events."""
    def __init__(self, audit_chain: ImmutableAuditChain = None):
        self.chain = audit_chain or ImmutableAuditChain()
        self.logs: List[Dict[str, Any]] = []

    def log_event(
        self,
        workspace_id: str,
        actor_id: str,
        action: str,
        details: Dict[str, Any],
    ) -> Dict[str, Any]:
        sanitized_details = scrub_secrets(details)
        record = self.chain.append_event(
            tenant_id=workspace_id,
            actor_id=actor_id,
            action=action,
            details=sanitized_details,
        )
        self.logs.append(record)
        return record

    def get_logs_for_plugin(self, plugin_id: str) -> List[Dict[str, Any]]:
        return [
            log for log in self.logs
            if log.get("details", {}).get("plugin_id") == plugin_id
        ]
