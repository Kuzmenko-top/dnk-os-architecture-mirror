# --- DNK-MRH-HEADER ---
# mrh_id: "tests/plugins/test_plugin_manifest_validation.py"
# purpose: "Unit tests for plugin manifest schema validation, path safety, and semver compliance"
# author: "DNK-e.com Maksym"
# license: "MIT"
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-16"
# --- END DNK-MRH-HEADER ---

import pytest
from core.plugins.plugin_manifest import validate_manifest, InvalidPluginManifestError

def get_valid_manifest_dict():
    return {
        "plugin_id": "test_plugin_01",
        "name": "Test Plugin",
        "version": "1.0.0",
        "publisher": "DNK-e.com",
        "entrypoint": "main.py",
        "runtime_compatibility": ">=0.1.0",
        "permissions": ["read_memory", "write_memory"],
        "dependencies": {"python": ">=3.12"},
        "content_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "signature_metadata": {"key_id": "key_01", "signature": "test_sig"},
    }

def test_valid_manifest_passes():
    m_dict = get_valid_manifest_dict()
    m = validate_manifest(m_dict)
    assert m.plugin_id == "test_plugin_01"
    assert m.version == "1.0.0"

def test_missing_required_field_rejected():
    m_dict = get_valid_manifest_dict()
    del m_dict["entrypoint"]
    with pytest.raises(InvalidPluginManifestError) as exc_info:
        validate_manifest(m_dict)
    assert "Missing required manifest fields" in str(exc_info.value)

def test_invalid_semver_rejected():
    m_dict = get_valid_manifest_dict()
    m_dict["version"] = "1.0"
    with pytest.raises(InvalidPluginManifestError) as exc_info:
        validate_manifest(m_dict)
    assert "Invalid SemVer" in str(exc_info.value)

def test_path_traversal_entrypoint_rejected():
    m_dict = get_valid_manifest_dict()
    m_dict["entrypoint"] = "../../../etc/passwd"
    with pytest.raises(InvalidPluginManifestError) as exc_info:
        validate_manifest(m_dict)
    assert "Path traversal detected" in str(exc_info.value)

def test_absolute_path_entrypoint_rejected():
    m_dict = get_valid_manifest_dict()
    m_dict["entrypoint"] = "/usr/local/bin/malicious.py"
    with pytest.raises(InvalidPluginManifestError) as exc_info:
        validate_manifest(m_dict)
    assert "Absolute path entrypoint forbidden" in str(exc_info.value)
