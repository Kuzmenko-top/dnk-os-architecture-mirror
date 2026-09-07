# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-STD-0075"
# purpose: "Unit test suite for validating the Cart Drawer & PDP Bundles Commerce Suite FastAPI endpoints."
# canonical_source: true
# alters_files: ["tests/verification/test_commerce_suite.py"]
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

def test_generate_cart_drawer_success():
    """Verify that Cart Drawer generator endpoint produces expected Liquid and AJAX JS."""
    payload = {
        "free_shipping_threshold": 1200.0,
        "current_cart_total": 850.0
    }
    response = client.post("/api/v1/cart-drawer/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "success"
    assert "liquid" in data
    assert "javascript" in data
    assert "metadata" in data
    
    # Progress math verification
    meta = data["metadata"]
    assert meta["free_shipping_threshold"] == 1200.0
    assert meta["current_cart_total"] == 850.0
    assert meta["is_free_shipping_achieved"] is False
    
    liquid = data["liquid"]
    assert "dnk-shipping-goal" in liquid
    assert "Нова Пошта" in liquid
    assert 'data-threshold="1200.0"' in liquid

    js = data["javascript"]
    assert "class DNKCartDrawer" in js
    assert "this.threshold = 1200.0" in js

def test_generate_cart_drawer_free_shipping_achieved():
    """Verify that metadata correctly updates when free shipping goal is met."""
    payload = {
        "free_shipping_threshold": 1000.0,
        "current_cart_total": 1500.0
    }
    response = client.post("/api/v1/cart-drawer/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    meta = data["metadata"]
    assert meta["is_free_shipping_achieved"] is True
    
    liquid = data["liquid"]
    assert "безкоштовна доставка" in liquid

def test_generate_cart_drawer_invalid_input():
    """Verify input validation raises HTTP 400 for negative numbers."""
    payload = {
        "free_shipping_threshold": -500.0,
        "current_cart_total": 100.0
    }
    response = client.post("/api/v1/cart-drawer/generate", json=payload)
    assert response.status_code == 400
    assert "must be positive" in response.json()["detail"]

def test_generate_pdp_bundles_success():
    """Verify Frequently Bought Together (FBT) generator endpoint works correctly."""
    payload = {
        "product_id": "887766",
        "buy_together_products": ["1122", "3344"],
        "discount_percentage": 15.0
    }
    response = client.post("/api/v1/bundles/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "success"
    assert "liquid" in data
    assert "javascript" in data
    
    meta = data["metadata"]
    assert meta["product_id"] == "887766"
    assert meta["discount_percentage"] == 15.0
    
    liquid = data["liquid"]
    assert 'data-product-id="887766"' in liquid
    assert "buy_together_products" not in liquid
    assert "Знижка 15.0% на весь комплект" in liquid
    assert "Volume Discounts" in liquid

    js = data["javascript"]
    assert "class DNKPDPBundles" in js
    assert "this.discount = 15.0" in js

def test_generate_pdp_bundles_invalid_input():
    """Verify that bundles endpoint rejects bad discount percentage inputs."""
    payload = {
        "product_id": "887766",
        "buy_together_products": ["1122"],
        "discount_percentage": 150.0
    }
    response = client.post("/api/v1/bundles/generate", json=payload)
    assert response.status_code == 400
    assert "must be between 0 and 100" in response.json()["detail"]
