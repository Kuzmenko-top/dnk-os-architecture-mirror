# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_shopify_ast_router.py"
# purpose: "Integration tests for Shopify OS 2.0 AST Transpiler, Validation, Presets, and Live Push."
# canonical_source: true
# alters_files: []
# triggers_tasks: ["TASK-DNK-SHOPIFY-AST-LIVE-PUSH-003"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "Gerych (Hermes Swarm) & Antigravity"
# --- END DNK-MRH-HEADER ---

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)

def test_shopify_presets_endpoint():
    resp = client.get("/api/v3/shopify/presets")
    assert resp.status_code == 200
    presets = resp.json()
    assert len(presets) >= 3
    preset_ids = [p["id"] for p in presets]
    assert "smokehouse_hero_banner" in preset_ids
    assert "smoke_generator_kit" in preset_ids

def test_shopify_ast_transpilation():
    payload = {
        "screen_id": "scr-smokehouse-01",
        "section_name": "smokehouse_hero_banner",
        "title": "Коптильня Lagrange Pro 2026",
        "price": "26,500 ₴",
        "description": "Професійна автоматична коптильня гарячого та холодного диму.",
        "cta_text": "Отримати знижку",
        "cta_link": "/products/lagrange",
        "features": [
            "AISI 304 нержавійка",
            "Електронний димогенератор"
        ]
    }
    resp = client.post("/api/v3/shopify/transpile", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["section_name"] == "smokehouse_hero_banner"
    assert "sections/smokehouse_hero_banner.liquid" in data["filename"]
    assert "{% schema %}" in data["liquid_code"]
    assert "Коптильня Lagrange Pro 2026" in data["liquid_code"]
    assert "26,500 ₴" in data["liquid_code"]
    assert "AISI 304 нержавійка" in data["liquid_code"]

def test_shopify_liquid_schema_validation_success():
    valid_liquid = """
    <div>{{ section.settings.title }}</div>
    {% schema %}
    {
      "name": "Test Section",
      "settings": [
        { "type": "text", "id": "title", "label": "Title" }
      ]
    }
    {% endschema %}
    """
    resp = client.post("/api/v3/shopify/validate", json={"liquid_code": valid_liquid})
    assert resp.status_code == 200
    data = resp.json()
    assert data["valid"] is True
    assert data["schema_name"] == "Test Section"
    assert data["settings_count"] == 1

def test_shopify_liquid_schema_validation_failure():
    invalid_liquid = "<div>No schema here</div>"
    resp = client.post("/api/v3/shopify/validate", json={"liquid_code": invalid_liquid})
    assert resp.status_code == 200
    data = resp.json()
    assert data["valid"] is False
    assert "Missing {% schema %}" in data["error"]

def test_shopify_theme_push_success():
    # 1. First transpile
    transpile_resp = client.post("/api/v3/shopify/transpile", json={
        "screen_id": "scr-test",
        "section_name": "hero_banner",
        "title": "Smoker Lagrange",
        "price": "19,990 ₴",
        "description": "Best smoker in Ukraine",
        "cta_text": "Купити",
        "cta_link": "/cart",
        "features": ["1.5mm", "Smoke generator"]
    })
    liquid_code = transpile_resp.json()["liquid_code"]

    # 2. Push to theme
    push_resp = client.post("/api/v3/shopify/theme/push", json={
        "store_url": "dnk-smokehouse.myshopify.com",
        "theme_id": "theme-smoke-live",
        "section_name": "hero_banner",
        "liquid_code": liquid_code,
        "dry_run": True
    })
    assert push_resp.status_code == 200
    data = push_resp.json()
    assert data["status"] == "published"
    assert data["store"] == "dnk-smokehouse.myshopify.com"
    assert "sections/hero_banner.liquid" in data["section_file"]
    assert "checksum" in data

def test_shopify_theme_download_zip():
    resp = client.get("/api/v3/shopify/theme/download?section_name=smokehouse_hero_banner")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/zip"
    assert "dnk_shopify_smokehouse_hero_banner.zip" in resp.headers["content-disposition"]
    assert len(resp.content) > 100
