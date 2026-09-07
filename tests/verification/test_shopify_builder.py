# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-STD-0075"
# purpose: "Unit test suite for validating the dnk_shopify_builder FastAPI endpoints."
# canonical_source: true
# alters_files: ["tests/verification/test_shopify_builder.py"]
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

# Import FastAPI app
from services.dnk_shopify_builder.main import app

client = TestClient(app)

def test_health_check():
    """Verify that both health endpoints return a healthy liveness status."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service_id": "dnk_shopify_builder"}

    response_v1 = client.get("/api/v1/health")
    assert response_v1.status_code == 200
    assert response_v1.json() == {"status": "healthy", "service_id": "dnk_shopify_builder"}

def test_get_canvas_node():
    """Verify that the visual canvas node representation is formatted and returned correctly."""
    response = client.get("/api/v1/canvas/node")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "dnk_shopify_builder"
    assert data["type"] == "AgentNode"
    assert data["state"] == "Done"
    assert "port" in data["metadata"]
    assert data["metadata"]["port"] == 8081

def test_build_theme_section_success():
    """Verify that the theme generation POST endpoint generates valid Shopify Liquid and JSON schema."""
    payload = {
        "section_name": "Featured Products",
        "settings": {"title": "Best Sellers"},
        "components": ["product-card", "buy-button"]
    }
    response = client.post("/api/v1/build", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "success"
    assert data["section_name"] == "Featured Products"
    assert "liquid" in data
    
    liquid = data["liquid"]
    assert "Featured Products" in liquid
    assert "{% schema %}" in liquid
    assert "product-card" in liquid
    assert "buy-button" in liquid

def test_build_theme_section_invalid_payload():
    """Verify that build endpoint returns validation error when payload schema is non-conformant."""
    # Missing required field 'section_name'
    payload = {
        "settings": {"title": "Best Sellers"}
    }
    response = client.post("/api/v1/build", json=payload)
    assert response.status_code == 422 # Pydantic validation error HTTP 422
