# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-STD-0075"
# purpose: "End-to-End integration pipeline test combining OmniRouter intent routing, ServiceRegistry lookup, and dnk_shopify_builder APIs."
# canonical_source: true
# alters_files: ["tests/verification/test_e2e_omni_pipeline.py"]
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-09"
# --- END DNK-MRH-HEADER ---

import os
import sys
import pytest
from fastapi.testclient import TestClient
from pathlib import Path

# Setup paths relative to test file
BASE_DIR = Path(__file__).resolve().parent.parent.parent # Resolve to DNK OS root
sys.path.insert(0, str(BASE_DIR))

from core.omni_router import OmniRouter
from core.service_registry import ServiceRegistry

def test_e2e_omni_routing_pipeline():
    """
    End-to-End Test: 
    OmniRouter -> Intent Classifier -> ServiceRegistry -> dnk_shopify_builder FastAPI -> Liquid compilation
    """
    router = OmniRouter()
    assert router.service_registry is not None
    assert "dnk_shopify_builder" in router.service_registry.services
    
    # 1. Dispatch a shopify-related goal
    task_goal = "I need to build a modular Frequently Bought Together pdp section for our shopify theme"
    dispatch_result = router.dispatch(task_goal)
    
    assert dispatch_result["status"] == "dispatched"
    assert dispatch_result["classification"]["intent"] == "shopify"
    assert dispatch_result["classification"]["assigned_agent"] == "shopify_pro"
    
    # 2. Verify Pluggable Routing Mesh successfully identified target microservice
    target_service = dispatch_result["target_service"]
    assert target_service is not None
    assert target_service["service_id"] == "dnk_shopify_builder"
    assert target_service["port"] == 8081
    assert target_service["entrypoint"] == "services.dnk_shopify_builder.main:app"
    
    # 3. Dynamic Import of the service app through ServiceRegistry
    app_obj = router.service_registry.dynamic_import_entrypoint("dnk_shopify_builder")
    assert app_obj is not None
    
    # 4. Invoke API endpoints via FastAPI TestClient on the imported app object
    client = TestClient(app_obj)
    
    # Test Liveness / Health check
    res_health = client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "healthy"
    
    # Test PDP Bundles Generator Endpoint
    bundles_payload = {
        "product_id": "998877",
        "buy_together_products": ["4455", "5566"],
        "discount_percentage": 20.0
    }
    res_bundles = client.post("/api/v1/bundles/generate", json=bundles_payload)
    assert res_bundles.status_code == 200
    bundles_data = res_bundles.json()
    
    assert bundles_data["status"] == "success"
    assert "liquid" in bundles_data
    assert "javascript" in bundles_data
    
    liquid = bundles_data["liquid"]
    assert 'data-product-id="998877"' in liquid
    assert "Знижка 20.0%" in liquid
    assert "Volume Discounts" in liquid
    
    js = bundles_data["javascript"]
    assert "class DNKPDPBundles" in js
    assert "this.discount = 20.0" in js
