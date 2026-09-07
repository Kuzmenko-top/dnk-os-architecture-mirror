# --- DNK-MRH-HEADER ---
# mrh_id: "core/plugins/plugin_security_gate.py"
# purpose: "Ed25519 Cryptographic Verification, Hash Integrity, and Security Gate Policy Engine"
# author: "DNK-e.com Maksym"
# license: "MIT"
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-16"
# --- END DNK-MRH-HEADER ---

import os
import hashlib
import json
import base64
from typing import Dict, Any, Optional
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.exceptions import InvalidSignature

# Custom Security Gate Exceptions mapped to standard error codes
class ProductionUnsignedPluginError(Exception):
    def __init__(self, message: str = "Unsigned plugin is strictly blocked in production mode."):
        super().__init__(message)
        self.error_code = "PRODUCTION_UNSIGNED_PLUGIN"
        self.status_code = 403

class HashMismatchError(Exception):
    def __init__(self, expected: str, actual: str):
        message = f"Package hash mismatch. Expected '{expected}', got '{actual}'."
        super().__init__(message)
        self.error_code = "HASH_MISMATCH"
        self.status_code = 422

class InvalidSignatureError(Exception):
    def __init__(self, message: str = "Plugin Ed25519 signature verification failed."):
        super().__init__(message)
        self.error_code = "INVALID_SIGNATURE"
        self.status_code = 422

class UntrustedSigningKeyError(Exception):
    def __init__(self, key_id: str, reason: str = "Signing key is unknown or untrusted."):
        message = f"Untrusted signing key '{key_id}': {reason}"
        super().__init__(message)
        self.error_code = "UNTRUSTED_SIGNING_KEY"
        self.status_code = 403

class PluginQuarantinedError(Exception):
    def __init__(self, plugin_id: str, reason: str = "Package or signing key is revoked/quarantined."):
        message = f"Plugin '{plugin_id}' is quarantined: {reason}"
        super().__init__(message)
        self.error_code = "PLUGIN_QUARANTINED"
        self.status_code = 423

class DependencyNotSatisfiedError(Exception):
    def __init__(self, dependency_name: str, required_version: str):
        message = f"Dependency '{dependency_name}' ({required_version}) is not satisfied."
        super().__init__(message)
        self.error_code = "DEPENDENCY_NOT_SATISFIED"
        self.status_code = 424

class InstallationRollbackFailedError(Exception):
    def __init__(self, plugin_id: str, reason: str):
        message = f"Rollback failed for plugin '{plugin_id}': {reason}"
        super().__init__(message)
        self.error_code = "INSTALLATION_ROLLBACK_FAILED"
        self.status_code = 500


class TrustKeyRegistry:
    """Registry of trusted Ed25519 public keys and publisher policies."""
    def __init__(self):
        # key_id -> {"public_key_b64": str, "publisher": str, "status": "active"|"revoked"|"expired"}
        self._keys: Dict[str, Dict[str, Any]] = {}

    def register_key(self, key_id: str, public_key_bytes: bytes, publisher: str, status: str = "active") -> None:
        self._keys[key_id] = {
            "public_key_b64": base64.b64encode(public_key_bytes).decode('utf-8'),
            "publisher": publisher,
            "status": status,
        }

    def revoke_key(self, key_id: str) -> None:
        if key_id in self._keys:
            self._keys[key_id]["status"] = "revoked"

    def get_key_info(self, key_id: str) -> Optional[Dict[str, Any]]:
        return self._keys.get(key_id)


def calculate_package_hash(package_path_or_bytes: Any) -> str:
    """
    Calculates deterministic SHA-256 hash of a package file, directory, or raw bytes.
    """
    hasher = hashlib.sha256()
    
    if isinstance(package_path_or_bytes, bytes):
        hasher.update(package_path_or_bytes)
        return hasher.hexdigest()

    if isinstance(package_path_or_bytes, str):
        if os.path.isfile(package_path_or_bytes):
            with open(package_path_or_bytes, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
            return hasher.hexdigest()
        elif os.path.isdir(package_path_or_bytes):
            # Sort files deterministically
            for root, _, files in sorted(os.walk(package_path_or_bytes)):
                for fname in sorted(files):
                    fpath = os.path.join(root, fname)
                    relpath = os.path.relpath(fpath, package_path_or_bytes)
                    hasher.update(relpath.encode('utf-8'))
                    with open(fpath, "rb") as f:
                        while chunk := f.read(65536):
                            hasher.update(chunk)
            return hasher.hexdigest()

    raise ValueError("Invalid package input type for hash calculation.")


def verify_ed25519_signature(data_bytes: bytes, signature_b64: str, public_key_bytes: bytes) -> bool:
    """Verifies Ed25519 signature over raw data bytes."""
    try:
        sig_bytes = base64.b64decode(signature_b64)
        public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
        public_key.verify(sig_bytes, data_bytes)
        return True
    except (InvalidSignature, Exception):
        return False


def generate_ed25519_keypair():
    """Generates a new Ed25519 keypair for signing test packages."""
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    return private_key, public_key


def sign_data_ed25519(data_bytes: bytes, private_key) -> str:
    """Signs data bytes using Ed25519 private key and returns base64 signature."""
    sig_bytes = private_key.sign(data_bytes)
    return base64.b64encode(sig_bytes).decode('utf-8')


def evaluate_security_gate(
    manifest_dict: dict,
    package_data: bytes,
    key_registry: TrustKeyRegistry,
    production_mode: bool = True,
) -> Dict[str, Any]:
    """
    Evaluates complete Security Gate rules per DNK-TRUST-016:
    manifest valid AND package hash valid AND signature valid AND signing key active and trusted
    """
    sig_meta = manifest_dict.get("signature_metadata", {})
    key_id = sig_meta.get("key_id", "")
    signature_b64 = sig_meta.get("signature", "")
    is_signed = bool(key_id and signature_b64)

    # 1. Production Mode: Unsigned plugin is strictly blocked
    if production_mode and not is_signed:
        raise ProductionUnsignedPluginError("Unsigned plugin is strictly blocked in production policy.")

    # If unsigned and not in production, set state as untrusted/dev
    if not is_signed:
        return {
            "trust_state": "untrusted",
            "key_id": "",
            "signature_fingerprint": "",
        }

    # 2. Key Resolution
    key_info = key_registry.get_key_info(key_id)
    if not key_info:
        raise UntrustedSigningKeyError(key_id, "Signing key is unknown in key registry.")

    key_status = key_info.get("status", "unknown")
    if key_status == "revoked":
        raise PluginQuarantinedError(
            manifest_dict.get("plugin_id", "unknown"),
            f"Signing key '{key_id}' has been REVOKED."
        )
    elif key_status == "expired":
        raise UntrustedSigningKeyError(key_id, "Signing key is expired.")
    elif key_status != "active":
        raise UntrustedSigningKeyError(key_id, f"Signing key has non-active status '{key_status}'.")

    # 3. Canonical Hash Verification
    expected_hash = manifest_dict.get("content_hash", "")
    actual_hash = calculate_package_hash(package_data)
    if expected_hash.lower() != actual_hash.lower():
        raise HashMismatchError(expected=expected_hash, actual=actual_hash)

    # 4. Ed25519 Signature Verification
    public_key_bytes = base64.b64decode(key_info["public_key_b64"])
    canonical_payload = f"{manifest_dict['plugin_id']}:{manifest_dict['version']}:{actual_hash}".encode('utf-8')
    
    if not verify_ed25519_signature(canonical_payload, signature_b64, public_key_bytes):
        raise InvalidSignatureError("Ed25519 signature is invalid or tampered.")

    # Fingerprint of signature
    sig_fingerprint = hashlib.sha256(base64.b64decode(signature_b64)).hexdigest()[:16]

    return {
        "trust_state": "trusted",
        "key_id": key_id,
        "signature_fingerprint": sig_fingerprint,
    }
