# --- DNK-MRH-HEADER ---
# mrh_id: "core/tests/test_service_registry.py"
# purpose: "Unit tests for ServiceRegistry scanning, Pydantic manifest validation, and dnk_shopify_builder discovery."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-09"
# --- END DNK-MRH-HEADER ---

import pytest
from pydantic import ValidationError
from core.service_registry import ServiceRegistry, ServiceManifestModel

def test_service_registry_scanning_and_discovery():
    """Verify that ServiceRegistry discovers and registers dnk_shopify_builder."""
    registry = ServiceRegistry()
    
    assert "dnk_shopify_builder" in registry.services, "dnk_shopify_builder should be registered."
    
    manifest = registry.services["dnk_shopify_builder"]
    assert manifest.service_id == "dnk_shopify_builder"
    assert manifest.name == "Shopify Builder Microservice"
    assert manifest.port == 8081
    assert manifest.domain == "shopify"
    assert manifest.status == "Active"
    assert manifest.version == "1.0.0"
    assert manifest.entrypoint == "services.dnk_shopify_builder.main:app"

def test_service_registry_endpoints():
    """Verify registered endpoints for dnk_shopify_builder microservice."""
    registry = ServiceRegistry()
    manifest = registry.services["dnk_shopify_builder"]
    
    assert len(manifest.endpoints) == 2, "Expected exactly 2 endpoints for dnk_shopify_builder."
    
    ep1 = manifest.endpoints[0]
    assert ep1.path == "/api/v1/build"
    assert ep1.method == "POST"
    assert ep1.handler == "build_theme_section"

    ep2 = manifest.endpoints[1]
    assert ep2.path == "/api/v1/canvas/node"
    assert ep2.method == "GET"
    assert ep2.handler == "get_canvas_node"

def test_service_registry_invalid_manifest():
    """Verify that invalid manifests fail Pydantic schema validation."""
    registry = ServiceRegistry()
    
    # Missing required 'service_id' and 'port'
    bad_manifest = {
        "name": "Broken Microservice",
        "domain": "utils",
        "status": "Draft",
        "version": "0.1.0",
        "entrypoint": "services.broken.main:app"
    }
    
    with pytest.raises(ValidationError):
        registry.validate_manifest(bad_manifest)
