# --- DNK-MRH-HEADER ---
# mrh_id: "core/plugins/plugin_models.py"
# purpose: "Plugin Lifecycle State Machine, Persistence Models, and Constraints Engine"
# author: "DNK-e.com Maksym"
# license: "MIT"
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-16"
# --- END DNK-MRH-HEADER ---

from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

class PluginLifecycleState(str, Enum):
    DISCOVERED = "discovered"
    DOWNLOADED = "downloaded"
    STAGED = "staged"
    MANIFEST_VALIDATED = "manifest_validated"
    HASH_VERIFIED = "hash_verified"
    SIGNATURE_VERIFIED = "signature_verified"
    TRUST_APPROVED = "trust_approved"
    INSTALLING = "installing"
    INSTALLED = "installed"
    ACTIVATING = "activating"
    ACTIVE = "active"
    FAILED = "failed"
    QUARANTINED = "quarantined"
    ROLLED_BACK = "rolled_back"
    UNINSTALLED = "uninstalled"

class PluginTrustState(str, Enum):
    TRUSTED = "trusted"
    UNTRUSTED = "untrusted"
    QUARANTINED = "quarantined"
    REVOKED = "revoked"
    PENDING_APPROVAL = "pending_approval"

class InvalidPluginInstallTransitionError(Exception):
    """Raised when an illegal state transition is attempted."""
    def __init__(self, current_state: str, target_state: str, reason: str = ""):
        message = f"Invalid plugin state transition from '{current_state}' to '{target_state}'."
        if reason:
            message += f" Reason: {reason}"
        super().__init__(message)
        self.error_code = "INVALID_PLUGIN_INSTALL_TRANSITION"
        self.current_state = current_state
        self.target_state = target_state

# State Machine Transition Table
# Maps current_state -> set of allowed next states
VALID_TRANSITIONS: Dict[PluginLifecycleState, set[PluginLifecycleState]] = {
    PluginLifecycleState.DISCOVERED: {
        PluginLifecycleState.DOWNLOADED,
        PluginLifecycleState.FAILED,
        PluginLifecycleState.QUARANTINED,
    },
    PluginLifecycleState.DOWNLOADED: {
        PluginLifecycleState.STAGED,
        PluginLifecycleState.FAILED,
        PluginLifecycleState.QUARANTINED,
    },
    PluginLifecycleState.STAGED: {
        PluginLifecycleState.MANIFEST_VALIDATED,
        PluginLifecycleState.FAILED,
        PluginLifecycleState.QUARANTINED,
    },
    PluginLifecycleState.MANIFEST_VALIDATED: {
        PluginLifecycleState.HASH_VERIFIED,
        PluginLifecycleState.FAILED,
        PluginLifecycleState.QUARANTINED,
    },
    PluginLifecycleState.HASH_VERIFIED: {
        PluginLifecycleState.SIGNATURE_VERIFIED,
        PluginLifecycleState.FAILED,
        PluginLifecycleState.QUARANTINED,
    },
    PluginLifecycleState.SIGNATURE_VERIFIED: {
        PluginLifecycleState.TRUST_APPROVED,
        PluginLifecycleState.FAILED,
        PluginLifecycleState.QUARANTINED,
    },
    PluginLifecycleState.TRUST_APPROVED: {
        PluginLifecycleState.INSTALLING,
        PluginLifecycleState.FAILED,
        PluginLifecycleState.QUARANTINED,
    },
    PluginLifecycleState.INSTALLING: {
        PluginLifecycleState.INSTALLED,
        PluginLifecycleState.FAILED,
        PluginLifecycleState.QUARANTINED,
        PluginLifecycleState.ROLLED_BACK,
    },
    PluginLifecycleState.INSTALLED: {
        PluginLifecycleState.ACTIVATING,
        PluginLifecycleState.UNINSTALLED,
        PluginLifecycleState.FAILED,
        PluginLifecycleState.QUARANTINED,
        PluginLifecycleState.ROLLED_BACK,
    },
    PluginLifecycleState.ACTIVATING: {
        PluginLifecycleState.ACTIVE,
        PluginLifecycleState.FAILED,
        PluginLifecycleState.QUARANTINED,
        PluginLifecycleState.ROLLED_BACK,
    },
    PluginLifecycleState.ACTIVE: {
        PluginLifecycleState.ACTIVATING,
        PluginLifecycleState.INSTALLED,
        PluginLifecycleState.UNINSTALLED,
        PluginLifecycleState.ROLLED_BACK,
        PluginLifecycleState.QUARANTINED,
        PluginLifecycleState.FAILED,
    },
    PluginLifecycleState.FAILED: {
        PluginLifecycleState.ROLLED_BACK,
        PluginLifecycleState.UNINSTALLED,
        PluginLifecycleState.STAGED,  # Retry from clean staging
    },
    PluginLifecycleState.QUARANTINED: {
        PluginLifecycleState.UNINSTALLED,
        PluginLifecycleState.ROLLED_BACK,
    },
    PluginLifecycleState.ROLLED_BACK: {
        PluginLifecycleState.ACTIVATING,
        PluginLifecycleState.UNINSTALLED,
        PluginLifecycleState.FAILED,
    },
    PluginLifecycleState.UNINSTALLED: set(),  # Terminal state
}

FORBIDDEN_DIRECT_TRANSITIONS = {
    (PluginLifecycleState.DISCOVERED, PluginLifecycleState.INSTALLED),
    (PluginLifecycleState.DOWNLOADED, PluginLifecycleState.ACTIVE),
    (PluginLifecycleState.STAGED, PluginLifecycleState.ACTIVE),
}

def validate_state_transition(current_state: str, target_state: str) -> bool:
    try:
        curr_enum = PluginLifecycleState(current_state)
        target_enum = PluginLifecycleState(target_state)
    except ValueError as e:
        raise InvalidPluginInstallTransitionError(current_state, target_state, str(e))

    if (curr_enum, target_enum) in FORBIDDEN_DIRECT_TRANSITIONS:
        raise InvalidPluginInstallTransitionError(
            current_state, target_state, "Forbidden direct transition."
        )

    allowed = VALID_TRANSITIONS.get(curr_enum, set())
    if target_enum not in allowed:
        raise InvalidPluginInstallTransitionError(
            current_state, target_state, f"Allowed next states from '{current_state}': {[s.value for s in allowed]}"
        )

    return True


class PluginInstallationRecord:
    def __init__(
        self,
        workspace_id: str,
        plugin_id: str,
        version: str,
        publisher: str,
        content_hash: str,
        hash_algorithm: str = "sha256",
        signature_fingerprint: str = "",
        key_id: str = "",
        trust_state: str = PluginTrustState.UNTRUSTED.value,
        install_state: str = PluginLifecycleState.DISCOVERED.value,
        source: str = "local",
        staging_path: str = "",
        installed_path: str = "",
        created_by: str = "system",
        installation_id: Optional[str] = None,
    ):
        self.installation_id = installation_id or f"inst_{uuid.uuid4().hex[:16]}"
        self.workspace_id = workspace_id
        self.plugin_id = plugin_id
        self.version = version
        self.publisher = publisher
        self.content_hash = content_hash
        self.hash_algorithm = hash_algorithm
        self.signature_fingerprint = signature_fingerprint
        self.key_id = key_id
        self.trust_state = trust_state
        self.install_state = install_state
        self.source = source
        self.staging_path = staging_path
        self.installed_path = installed_path
        self.created_by = created_by
        self.installed_at: Optional[str] = None
        self.activated_at: Optional[str] = None
        self.deactivated_at: Optional[str] = None
        self.rollback_version: Optional[str] = None
        self.failure_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "installation_id": self.installation_id,
            "workspace_id": self.workspace_id,
            "plugin_id": self.plugin_id,
            "version": self.version,
            "publisher": self.publisher,
            "content_hash": self.content_hash,
            "hash_algorithm": self.hash_algorithm,
            "signature_fingerprint": self.signature_fingerprint,
            "key_id": self.key_id,
            "trust_state": self.trust_state,
            "install_state": self.install_state,
            "source": self.source,
            "staging_path": self.staging_path,
            "installed_path": self.installed_path,
            "installed_at": self.installed_at,
            "activated_at": self.activated_at,
            "deactivated_at": self.deactivated_at,
            "rollback_version": self.rollback_version,
            "failure_reason": self.failure_reason,
            "created_by": self.created_by,
        }

class PluginPersistenceStore:
    """In-memory thread-safe state store enforcing workspace and version constraints."""
    def __init__(self):
        # (workspace_id, plugin_id, version) -> PluginInstallationRecord
        self._records: Dict[tuple[str, str, str], PluginInstallationRecord] = {}
        # (workspace_id, plugin_id) -> active_version
        self._active_versions: Dict[tuple[str, str], str] = {}
        # installation_id -> PluginInstallationRecord
        self._by_id: Dict[str, PluginInstallationRecord] = {}
        # installation_id -> list of audit records
        self._audit_logs: Dict[str, List[Dict[str, Any]]] = {}

    def save_record(self, record: PluginInstallationRecord) -> None:
        key = (record.workspace_id, record.plugin_id, record.version)
        existing = self._records.get(key)
        
        if existing and existing.installation_id != record.installation_id:
            raise ValueError(f"DUPLICATE_PLUGIN_VERSION: Version {record.version} already exists for plugin {record.plugin_id} in workspace {record.workspace_id}")
            
        if existing and existing.content_hash != record.content_hash and existing.install_state in (PluginLifecycleState.INSTALLED.value, PluginLifecycleState.ACTIVE.value):
            raise ValueError("IMMUTABLE_CONTENT_HASH: Content hash cannot be mutated after installation.")

        # Constraint: No active record without trusted provenance
        if record.install_state == PluginLifecycleState.ACTIVE.value and record.trust_state != PluginTrustState.TRUSTED.value:
            raise ValueError("UNTRUSTED_ACTIVE_RECORD: No plugin can be set to active state without trusted trust_state.")

        self._records[key] = record
        self._by_id[record.installation_id] = record

    def get_record(self, workspace_id: str, plugin_id: str, version: str) -> Optional[PluginInstallationRecord]:
        return self._records.get((workspace_id, plugin_id, version))

    def get_record_by_id(self, installation_id: str) -> Optional[PluginInstallationRecord]:
        return self._by_id.get(installation_id)

    def set_active_version(self, workspace_id: str, plugin_id: str, version: str) -> None:
        rec = self.get_record(workspace_id, plugin_id, version)
        if not rec:
            raise ValueError(f"Plugin version {version} not found.")
        if rec.trust_state != PluginTrustState.TRUSTED.value:
            raise ValueError("UNTRUSTED_ACTIVE_RECORD: Active plugin must have trusted provenance.")
        self._active_versions[(workspace_id, plugin_id)] = version

    def get_active_version(self, workspace_id: str, plugin_id: str) -> Optional[str]:
        return self._active_versions.get((workspace_id, plugin_id))

    def remove_active_version(self, workspace_id: str, plugin_id: str) -> None:
        self._active_versions.pop((workspace_id, plugin_id), None)

    def list_versions(self, workspace_id: str, plugin_id: str) -> List[PluginInstallationRecord]:
        return [
            rec for ((w, p, _), rec) in self._records.items()
            if w == workspace_id and p == plugin_id
        ]

    def add_audit_event(self, installation_id: str, event: Dict[str, Any]) -> None:
        if installation_id not in self._audit_logs:
            self._audit_logs[installation_id] = []
        self._audit_logs[installation_id].append(event)

    def get_audit_trail(self, installation_id: str) -> List[Dict[str, Any]]:
        return self._audit_logs.get(installation_id, [])
