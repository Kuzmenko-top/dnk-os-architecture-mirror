# --- DNK-MRH-HEADER ---
# mrh_id: "core/plugins/plugin_manifest.py"
# purpose: "Plugin Manifest Specification, Validation, and Path Safety Verification Engine"
# author: "DNK-e.com Maksym"
# license: "MIT"
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-16"
# --- END DNK-MRH-HEADER ---

import os
import re

REQUIRED_MANIFEST_FIELDS = {
    "plugin_id",
    "name",
    "version",
    "publisher",
    "entrypoint",
    "runtime_compatibility",
    "permissions",
    "dependencies",
    "content_hash",
    "signature_metadata",
}

SEMVER_REGEX = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)

class InvalidPluginManifestError(Exception):
    """Raised when a plugin manifest fails validation or path safety checks."""
    def __init__(self, message: str, detail: str = ""):
        super().__init__(message)
        self.error_code = "INVALID_PLUGIN_MANIFEST"
        self.message = message
        self.detail = detail

class PluginManifest:
    """Validated representation of a plugin manifest."""
    def __init__(
        self,
        plugin_id: str,
        name: str,
        version: str,
        publisher: str,
        entrypoint: str,
        runtime_compatibility: str,
        permissions: list[str],
        dependencies: dict[str, str],
        content_hash: str,
        signature_metadata: dict,
    ):
        self.plugin_id = plugin_id
        self.name = name
        self.version = version
        self.publisher = publisher
        self.entrypoint = entrypoint
        self.runtime_compatibility = runtime_compatibility
        self.permissions = permissions
        self.dependencies = dependencies
        self.content_hash = content_hash
        self.signature_metadata = signature_metadata

    def to_dict(self) -> dict:
        return {
            "plugin_id": self.plugin_id,
            "name": self.name,
            "version": self.version,
            "publisher": self.publisher,
            "entrypoint": self.entrypoint,
            "runtime_compatibility": self.runtime_compatibility,
            "permissions": self.permissions,
            "dependencies": self.dependencies,
            "content_hash": self.content_hash,
            "signature_metadata": self.signature_metadata,
        }

def validate_manifest(raw_manifest: dict) -> PluginManifest:
    """
    Strictly validates raw manifest dictionary.
    Rejects missing fields, invalid semver, path traversal, absolute paths, and bad formats.
    """
    if not isinstance(raw_manifest, dict):
        raise InvalidPluginManifestError("Manifest must be a valid JSON object/dictionary.")

    # 1. Missing required fields
    missing = REQUIRED_MANIFEST_FIELDS - set(raw_manifest.keys())
    if missing:
        raise InvalidPluginManifestError(f"Missing required manifest fields: {sorted(list(missing))}")

    plugin_id = raw_manifest["plugin_id"]
    name = raw_manifest["name"]
    version = str(raw_manifest["version"])
    publisher = raw_manifest["publisher"]
    entrypoint = raw_manifest["entrypoint"]
    runtime_compatibility = raw_manifest["runtime_compatibility"]
    permissions = raw_manifest["permissions"]
    dependencies = raw_manifest["dependencies"]
    content_hash = raw_manifest["content_hash"]
    signature_metadata = raw_manifest["signature_metadata"]

    # 2. Field types
    if not isinstance(plugin_id, str) or not plugin_id.strip():
        raise InvalidPluginManifestError("plugin_id must be a non-empty string.")
    
    if not re.match(r"^[a-zA-Z0-9_\-]+$", plugin_id):
        raise InvalidPluginManifestError("plugin_id contains invalid characters. Use alphanumeric, hyphen, underscore.")

    if not isinstance(name, str) or not name.strip():
        raise InvalidPluginManifestError("name must be a non-empty string.")

    if not isinstance(publisher, str) or not publisher.strip():
        raise InvalidPluginManifestError("publisher must be a non-empty string.")

    # 3. SemVer validation
    if not SEMVER_REGEX.match(version):
        raise InvalidPluginManifestError(f"Invalid SemVer version string: '{version}'. Must follow X.Y.Z format.")

    # 4. Path traversal / absolute path checks on entrypoint
    if not isinstance(entrypoint, str) or not entrypoint.strip():
        raise InvalidPluginManifestError("entrypoint must be a non-empty string.")

    if os.path.isabs(entrypoint) or entrypoint.startswith("/"):
        raise InvalidPluginManifestError(f"Absolute path entrypoint forbidden: '{entrypoint}'")

    if ".." in entrypoint or "./" in entrypoint or "\\" in entrypoint:
        raise InvalidPluginManifestError(f"Path traversal detected in entrypoint: '{entrypoint}'")

    if not (entrypoint.endswith(".py") or re.match(r"^[a-zA-Z0-9_\.]+$", entrypoint)):
        raise InvalidPluginManifestError(f"Unknown or unsupported entrypoint format: '{entrypoint}'")

    # 5. Runtime compatibility check
    if not isinstance(runtime_compatibility, str) or not runtime_compatibility.strip():
        raise InvalidPluginManifestError("runtime_compatibility must be a non-empty string.")

    # 6. Permissions and dependencies structure
    if not isinstance(permissions, list):
        raise InvalidPluginManifestError("permissions must be a list of string permissions.")

    if not isinstance(dependencies, dict):
        raise InvalidPluginManifestError("dependencies must be a dictionary of package: version_spec.")

    # 7. Content hash format
    if not isinstance(content_hash, str) or not content_hash.strip():
        raise InvalidPluginManifestError("content_hash must be a non-empty string.")

    # 8. Signature metadata format
    if not isinstance(signature_metadata, dict):
        raise InvalidPluginManifestError("signature_metadata must be a dictionary.")

    return PluginManifest(
        plugin_id=plugin_id,
        name=name,
        version=version,
        publisher=publisher,
        entrypoint=entrypoint,
        runtime_compatibility=runtime_compatibility,
        permissions=permissions,
        dependencies=dependencies,
        content_hash=content_hash,
        signature_metadata=signature_metadata,
    )
