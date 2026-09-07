# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-STD-0075"
# purpose: "Unit and integration test suite to verify the Pluggable ServiceRegistry framework."
# canonical_source: true
# alters_files: ["tests/verification/test_service_registry.py"]
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-09"
# --- END DNK-MRH-HEADER ---

import os
import sys
import pytest
from pydantic import ValidationError
from pathlib import Path

# Setup paths relative to test file
BASE_DIR = Path(__file__).resolve().parent.parent.parent # Resolve to DNK OS root
sys.path.insert(0, str(BASE_DIR))

# Safely import ServiceRegistry
from core.service_registry import ServiceRegistry, ServiceManifestModel

REGISTRY_DIR = str(BASE_DIR / "services")

def test_registry_initialization_and_scan():
    """Verify that ServiceRegistry successfully preloads registered services on init."""
    registry = ServiceRegistry()
    assert registry.services_dir.endswith("services")
    
    # We should have dnk_shopify_builder registered
    assert "dnk_shopify_builder" in registry.services
    manifest = registry.services["dnk_shopify_builder"]
    assert manifest.name == "Shopify Builder Microservice"
    assert manifest.port == 8081
    assert manifest.domain == "shopify"
    assert len(manifest.endpoints) == 2

def test_registry_validation_success_and_failure():
    """Verify manifest validation handles conformant and non-conformant schemas."""
    registry = ServiceRegistry()
    
    # Valid raw data
    valid_data = {
        "service_id": "test_service",
        "name": "Test Service",
        "port": 9999,
        "domain": "test",
        "status": "Active",
        "version": "1.0.0",
        "entrypoint": "test_module:app",
        "endpoints": [
            {"path": "/api/v1/test", "method": "GET", "handler": "test_handler"}
        ]
    }
    manifest = registry.validate_manifest(valid_data)
    assert manifest.service_id == "test_service"
    assert len(manifest.endpoints) == 1
    
    # Invalid raw data (missing required field 'entrypoint')
    invalid_data = {
        "service_id": "test_service",
        "name": "Test Service",
        "port": 9999,
        "domain": "test",
        "status": "Active",
        "version": "1.0.0",
        "endpoints": []
    }
    with pytest.raises(ValidationError):
        registry.validate_manifest(invalid_data)

def test_registry_dynamic_import(tmp_path, monkeypatch):
    """Verify that dynamic_import_entrypoint loads the python object correctly."""
    # Write a mock python file in temp path
    mock_module_dir = tmp_path / "mock_service"
    mock_module_dir.mkdir()
    
    mock_code = """
class MockApp:
    def __init__(self):
        self.state = "loaded"

app = MockApp()
"""
    (mock_module_dir / "main.py").write_text(mock_code, encoding="utf-8")
    
    # Mock sys.path to include temp path
    monkeypatch.syspath_prepend(str(mock_module_dir))
    
    # Initialize registry with temp service folder
    temp_services_dir = tmp_path / "services"
    temp_services_dir.mkdir()
    
    temp_service_path = temp_services_dir / "dnk_mock_service"
    temp_service_path.mkdir()
    
    manifest_yaml = """
service_id: "dnk_mock_service"
name: "Mock Service"
port: 9090
domain: "test"
status: "Active"
version: "1.0.0"
entrypoint: "main:app"
endpoints: []
"""
    (temp_service_path / "service_manifest.yaml").write_text(manifest_yaml, encoding="utf-8")
    
    registry = ServiceRegistry(services_dir=str(temp_services_dir))
    assert "dnk_mock_service" in registry.services
    
    # Import
    app_obj = registry.dynamic_import_entrypoint("dnk_mock_service")
    assert app_obj is not None
    assert app_obj.state == "loaded"

def test_no_port_collisions():
    """Verify that no two active services share the same port."""
    registry = ServiceRegistry()
    ports = {}
    for service_id, manifest in registry.services.items():
        port = manifest.port
        if port in ports:
            pytest.fail(f"🚨 PORT COLLISION: Service '{service_id}' and Service '{ports[port]}' both claim port {port}!")
        ports[port] = service_id
