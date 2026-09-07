# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_gcp_stitch_routers.py"
# purpose: "Integration tests for GCP Account Rotation & Google Stitch Canvas FastAPI routers."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)

def test_gcp_status_endpoint():
    response = client.get("/api/v3/gcp/status")
    assert response.status_code == 200
    data = response.json()
    assert "active_account" in data
    assert "active_project" in data
    assert "quota_status" in data
    assert len(data["available_projects"]) >= 1

def test_gcp_projects_pool_endpoint():
    response = client.get("/api/v3/gcp/projects")
    assert response.status_code == 200
    data = response.json()
    assert "pool" in data
    assert len(data["pool"]) >= 2

def test_stitch_projects_list_endpoint():
    response = client.get("/api/v3/stitch/projects")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

def test_stitch_screen_generation_and_linking():
    # 1. Generate Screen 1
    resp1 = client.post("/api/v3/stitch/screens/generate", json={
        "project_id": "proj-main-001",
        "prompt": "Hero Landing Section with Video and CTA",
        "device_type": "desktop"
    })
    assert resp1.status_code == 200
    s1 = resp1.json()
    assert s1["id"].startswith("scr-")
    assert "Hero Landing Section" in s1["html_content"]

    # 2. Generate Screen 2
    resp2 = client.post("/api/v3/stitch/screens/generate", json={
        "project_id": "proj-main-001",
        "prompt": "Pricing & Checkout Modal",
        "parent_screen_id": s1["id"],
        "device_type": "desktop"
    })
    assert resp2.status_code == 200
    s2 = resp2.json()

    # 3. Link Screens
    link_resp = client.post("/api/v3/stitch/screens/link", json={
        "project_id": "proj-main-001",
        "source_screen_id": s1["id"],
        "target_screen_id": s2["id"],
        "trigger_selector": "#btn-pricing",
        "label": "openPricingModal"
    })
    assert link_resp.status_code == 200
    edge = link_resp.json()
    assert edge["source_screen_id"] == s1["id"]
    assert edge["target_screen_id"] == s2["id"]

def test_stitch_design_system_parsing_and_linter():
    design_md_content = """---
name: CapCut Dark Pro
colors:
  primary: "#0F172A"
  secondary: "#38BDF8"
  neutral: "#F8FAFC"
  background: "#020617"
---
# CapCut AI Design Rationale
High contrast kinetic interface with spring physics.
"""
    resp = client.post("/api/v3/stitch/design_system/parse", json={"content": design_md_content})
    assert resp.status_code == 200
    data = resp.json()
    assert data["tokens"]["name"] == "CapCut Dark Pro"
    assert "tailwind_v4_css" in data
    assert "@theme" in data["tailwind_v4_css"]
    assert "dtcg_json" in data

def test_stitch_export_shopify_liquid():
    # First get or generate screen
    gen_resp = client.post("/api/v3/stitch/screens/generate", json={
        "project_id": "proj-main-001",
        "prompt": "Featured Product Showcase",
        "device_type": "desktop"
    })
    screen = gen_resp.json()

    export_resp = client.post("/api/v3/stitch/export/shopify", json={
        "project_id": "proj-main-001",
        "screen_id": screen["id"],
        "section_name": "featured_stitch_promo"
    })
    assert export_resp.status_code == 200
    data = export_resp.json()
    assert "{% schema %}" in data["liquid_code"]
    assert "featured_stitch_promo" in data["liquid_code"]
