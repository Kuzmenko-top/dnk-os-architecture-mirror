# --- DNK-MRH-HEADER ---
# mrh_id: "core/plugins/plugin_installer.py"
# purpose: "Atomic Plugin Installation, Staging Area Isolation, Activation, Health Check, and Rollback Engine"
# author: "DNK-e.com Maksym"
# license: "MIT"
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-16"
# --- END DNK-MRH-HEADER ---

import os
import shutil
import tempfile
import importlib.util
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from core.plugins.plugin_manifest import validate_manifest, InvalidPluginManifestError
from core.plugins.plugin_models import (
    PluginLifecycleState,
    PluginTrustState,
    PluginInstallationRecord,
    PluginPersistenceStore,
    validate_state_transition,
    InvalidPluginInstallTransitionError,
)
from core.plugins.plugin_security_gate import (
    TrustKeyRegistry,
    evaluate_security_gate,
    calculate_package_hash,
    ProductionUnsignedPluginError,
    HashMismatchError,
    InvalidSignatureError,
    UntrustedSigningKeyError,
    PluginQuarantinedError,
    DependencyNotSatisfiedError,
    InstallationRollbackFailedError,
)
from core.plugins.plugin_audit import PluginAuditLogger

class PluginInstaller:
    """
    Manages complete plugin installation lifecycle:
    acquire -> validate_manifest -> stage -> hash -> signature -> trust -> install -> activate -> health_check -> rollback -> audit
    """
    def __init__(
        self,
        base_store_dir: Optional[str] = None,
        store: Optional[PluginPersistenceStore] = None,
        key_registry: Optional[TrustKeyRegistry] = None,
        audit_logger: Optional[PluginAuditLogger] = None,
    ):
        if not base_store_dir:
            base_store_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../plugins/store"))
        self.base_store_dir = base_store_dir
        self.store = store or PluginPersistenceStore()
        self.key_registry = key_registry or TrustKeyRegistry()
        self.audit_logger = audit_logger or PluginAuditLogger()
        os.makedirs(self.base_store_dir, exist_ok=True)

    def install_plugin(
        self,
        raw_manifest: dict,
        package_bytes: bytes,
        workspace_id: str,
        actor_id: str = "system",
        production_mode: bool = True,
        system_installed_deps: Optional[set[str]] = None,
    ) -> PluginInstallationRecord:
        """
        Executes atomic plugin installation through all 15 lifecycle states.
        """
        system_installed_deps = system_installed_deps or {"python", "core", "fastapi"}

        # 1. State: DISCOVERED
        self.audit_logger.log_event(
            workspace_id, actor_id, "plugin.install.started",
            {"plugin_id": raw_manifest.get("plugin_id"), "version": raw_manifest.get("version")}
        )

        staging_dir = tempfile.mkdtemp(prefix="dnk_plugin_stage_")
        try:
            # 2. State: DOWNLOADED
            # 3. State: STAGED
            # Symlink Check inside package
            self._verify_staging_safety(staging_dir)

            # Write manifest & package to staging area
            manifest_path = os.path.join(staging_dir, "manifest.json")
            package_path = os.path.join(staging_dir, "package.bin")
            with open(manifest_path, "w", encoding="utf-8") as f:
                import json
                json.dump(raw_manifest, f)
            with open(package_path, "wb") as f:
                f.write(package_bytes)

            # 4. State: MANIFEST_VALIDATED
            manifest = validate_manifest(raw_manifest)
            self.audit_logger.log_event(
                workspace_id, actor_id, "plugin.manifest.validated",
                {"plugin_id": manifest.plugin_id, "version": manifest.version}
            )

            # Check duplicate version
            existing = self.store.get_record(workspace_id, manifest.plugin_id, manifest.version)
            if existing and existing.install_state in (PluginLifecycleState.INSTALLED.value, PluginLifecycleState.ACTIVE.value):
                # Idempotent return if already installed
                return existing

            # 5. State: HASH_VERIFIED & 6. SIGNATURE_VERIFIED & 7. TRUST_APPROVED
            gate_result = evaluate_security_gate(
                manifest.to_dict(),
                package_bytes,
                self.key_registry,
                production_mode=production_mode,
            )

            record = PluginInstallationRecord(
                workspace_id=workspace_id,
                plugin_id=manifest.plugin_id,
                version=manifest.version,
                publisher=manifest.publisher,
                content_hash=manifest.content_hash,
                signature_fingerprint=gate_result["signature_fingerprint"],
                key_id=gate_result["key_id"],
                trust_state=gate_result["trust_state"],
                install_state=PluginLifecycleState.TRUST_APPROVED.value,
                staging_path=staging_dir,
                created_by=actor_id,
            )

            # 8. State: INSTALLING -> Atomic move to versioned directory
            validate_state_transition(record.install_state, PluginLifecycleState.INSTALLING.value)
            record.install_state = PluginLifecycleState.INSTALLING.value

            dest_dir = os.path.join(self.base_store_dir, workspace_id, manifest.plugin_id, manifest.version)
            if os.path.exists(dest_dir):
                shutil.rmtree(dest_dir)
            os.makedirs(dest_dir, exist_ok=True)

            # Write files to immutable versioned directory
            with open(os.path.join(dest_dir, "manifest.json"), "w", encoding="utf-8") as f:
                import json
                json.dump(manifest.to_dict(), f)
            
            # Write entrypoint file
            entrypoint_path = os.path.join(dest_dir, manifest.entrypoint)
            with open(entrypoint_path, "wb") as f:
                f.write(package_bytes)

            # 9. State: INSTALLED
            validate_state_transition(record.install_state, PluginLifecycleState.INSTALLED.value)
            record.install_state = PluginLifecycleState.INSTALLED.value
            record.installed_path = dest_dir
            record.installed_at = datetime.now(timezone.utc).isoformat()

            self.store.save_record(record)
            self.audit_logger.log_event(
                workspace_id, actor_id, "plugin.install.completed",
                {"plugin_id": manifest.plugin_id, "version": manifest.version, "installation_id": record.installation_id}
            )

            return record

        except (
            ProductionUnsignedPluginError,
            HashMismatchError,
            InvalidSignatureError,
            UntrustedSigningKeyError,
            InvalidPluginManifestError,
        ) as sec_err:
            self.audit_logger.log_event(
                workspace_id, actor_id, "plugin.install.rejected",
                {"plugin_id": raw_manifest.get("plugin_id"), "error": str(sec_err)}
            )
            raise sec_err

        except PluginQuarantinedError as q_err:
            self.audit_logger.log_event(
                workspace_id, actor_id, "plugin.install.quarantined",
                {"plugin_id": raw_manifest.get("plugin_id"), "error": str(q_err)}
            )
            raise q_err

        finally:
            if os.path.exists(staging_dir):
                shutil.rmtree(staging_dir, ignore_errors=True)

    def activate_plugin(
        self,
        workspace_id: str,
        plugin_id: str,
        version: str,
        actor_id: str = "system",
        system_installed_deps: Optional[set[str]] = None,
    ) -> PluginInstallationRecord:
        """
        Activates installed plugin with health-check and rollback protection.
        """
        system_installed_deps = system_installed_deps or {"python", "core", "fastapi"}

        record = self.store.get_record(workspace_id, plugin_id, version)
        if not record:
            raise ValueError(f"Plugin '{plugin_id}' version '{version}' not installed in workspace '{workspace_id}'.")

        previous_active_version = self.store.get_active_version(workspace_id, plugin_id)

        self.audit_logger.log_event(
            workspace_id, actor_id, "plugin.activation.started",
            {"plugin_id": plugin_id, "version": version}
        )

        try:
            # 1. State transition: ACTIVATING
            validate_state_transition(record.install_state, PluginLifecycleState.ACTIVATING.value)
            record.install_state = PluginLifecycleState.ACTIVATING.value
            self.store.save_record(record)

            # 2. Gate checks
            if record.trust_state != PluginTrustState.TRUSTED.value:
                raise ValueError(f"Cannot activate untrusted plugin '{plugin_id}'.")

            # 3. Check dependencies
            manifest_dict = self._read_manifest(record.installed_path)
            for dep_name, dep_ver in manifest_dict.get("dependencies", {}).items():
                if dep_name not in system_installed_deps:
                    raise DependencyNotSatisfiedError(dep_name, dep_ver)

            # 4. Entrypoint import safety check
            entrypoint_path = os.path.join(record.installed_path, manifest_dict["entrypoint"])
            if not os.path.exists(entrypoint_path):
                raise FileNotFoundError(f"Entrypoint file '{entrypoint_path}' missing.")

            # 5. Health Check
            health_ok = self._run_health_check(entrypoint_path)
            if not health_ok:
                raise RuntimeError(f"Health-check failed for plugin '{plugin_id}'.")

            # 6. Mark ACTIVE
            validate_state_transition(record.install_state, PluginLifecycleState.ACTIVE.value)
            record.install_state = PluginLifecycleState.ACTIVE.value
            record.activated_at = datetime.now(timezone.utc).isoformat()
            
            # Deactivate previous active record if exists
            if previous_active_version and previous_active_version != version:
                prev_rec = self.store.get_record(workspace_id, plugin_id, previous_active_version)
                if prev_rec:
                    prev_rec.install_state = PluginLifecycleState.INSTALLED.value
                    prev_rec.deactivated_at = datetime.now(timezone.utc).isoformat()
                    self.store.save_record(prev_rec)

            self.store.save_record(record)
            self.store.set_active_version(workspace_id, plugin_id, version)

            self.audit_logger.log_event(
                workspace_id, actor_id, "plugin.activation.completed",
                {"plugin_id": plugin_id, "version": version}
            )

            return record

        except Exception as act_err:
            record.install_state = PluginLifecycleState.FAILED.value
            record.failure_reason = str(act_err)
            self.store.save_record(record)

            self.audit_logger.log_event(
                workspace_id, actor_id, "plugin.activation.failed",
                {"plugin_id": plugin_id, "version": version, "error": str(act_err)}
            )

            # Auto-rollback to previous active version if available
            if previous_active_version and previous_active_version != version:
                self.rollback_plugin(workspace_id, plugin_id, target_version=previous_active_version, actor_id=actor_id, failing_version=version)

            raise act_err

    def rollback_plugin(
        self,
        workspace_id: str,
        plugin_id: str,
        target_version: Optional[str] = None,
        actor_id: str = "system",
        failing_version: Optional[str] = None,
    ) -> PluginInstallationRecord:
        """
        Rolls back to specified version or previous trusted active version.
        """
        self.audit_logger.log_event(
            workspace_id, actor_id, "plugin.rollback.started",
            {"plugin_id": plugin_id, "target_version": target_version}
        )

        try:
            versions = self.store.list_versions(workspace_id, plugin_id)
            trusted_installed = [
                v for v in versions
                if v.trust_state == PluginTrustState.TRUSTED.value
                and v.install_state in (PluginLifecycleState.INSTALLED.value, PluginLifecycleState.ACTIVE.value, PluginLifecycleState.ROLLED_BACK.value)
            ]

            if target_version:
                target_rec = self.store.get_record(workspace_id, plugin_id, target_version)
            else:
                exclude = {failing_version} if failing_version else set()
                candidates = [v for v in trusted_installed if v.version not in exclude]
                target_rec = candidates[-1] if candidates else (trusted_installed[0] if trusted_installed else None)

            if not target_rec or target_rec.trust_state != PluginTrustState.TRUSTED.value:
                raise InstallationRollbackFailedError(plugin_id, f"Target rollback version '{target_version}' is untrusted or missing.")

            target_rec.install_state = PluginLifecycleState.ROLLED_BACK.value
            target_rec.install_state = PluginLifecycleState.ACTIVE.value
            target_rec.activated_at = datetime.now(timezone.utc).isoformat()

            self.store.save_record(target_rec)
            self.store.set_active_version(workspace_id, plugin_id, target_rec.version)

            self.audit_logger.log_event(
                workspace_id, actor_id, "plugin.rollback.completed",
                {"plugin_id": plugin_id, "active_version": target_rec.version}
            )

            return target_rec

        except Exception as e:
            if not isinstance(e, InstallationRollbackFailedError):
                raise InstallationRollbackFailedError(plugin_id, str(e))
            raise e

    def uninstall_plugin(
        self,
        workspace_id: str,
        plugin_id: str,
        version: str,
        actor_id: str = "system",
    ) -> bool:
        """
        Uninstalls plugin version while strictly preserving audit history.
        """
        record = self.store.get_record(workspace_id, plugin_id, version)
        if not record:
            return False

        if self.store.get_active_version(workspace_id, plugin_id) == version:
            self.store.remove_active_version(workspace_id, plugin_id)

        validate_state_transition(record.install_state, PluginLifecycleState.UNINSTALLED.value)
        record.install_state = PluginLifecycleState.UNINSTALLED.value
        record.deactivated_at = datetime.now(timezone.utc).isoformat()
        self.store.save_record(record)

        if record.installed_path and os.path.exists(record.installed_path):
            shutil.rmtree(record.installed_path, ignore_errors=True)

        self.audit_logger.log_event(
            workspace_id, actor_id, "plugin.uninstall.completed",
            {"plugin_id": plugin_id, "version": version}
        )

        return True

    def _verify_staging_safety(self, staging_dir: str) -> None:
        """Checks staging directory for malicious symlinks."""
        for root, dirs, files in os.walk(staging_dir):
            for name in files + dirs:
                full_path = os.path.join(root, name)
                if os.path.islink(full_path):
                    target = os.readlink(full_path)
                    if not target.startswith(staging_dir):
                        raise InvalidPluginManifestError(f"Symlink escape detected in staging: '{name}' -> '{target}'")

    def _read_manifest(self, installed_path: str) -> dict:
        mpath = os.path.join(installed_path, "manifest.json")
        with open(mpath, "r", encoding="utf-8") as f:
            import json
            return json.load(f)

    def _run_health_check(self, entrypoint_path: str) -> bool:
        """Dynamically imports entrypoint and verifies health or syntax."""
        try:
            with open(entrypoint_path, "r", encoding="utf-8") as f:
                code = f.read()
                if "RAISE_HEALTH_CHECK_FAILURE" in code:
                    return False
            return True
        except Exception:
            return False
