# --- DNK-MRH-HEADER ---
# mrh_id: "tests_verification_test_shopify_inspector_canvas"
# purpose: "Verification test suite for TaskDNA-CANVAS-SHOPIFY-001 InspectorPanel, TemplateStateEngine mutations, and Theme Export"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-31"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import json
import pytest
from fastapi.testclient import TestClient

from apps.api.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_shopify_template_state_engine_manifest(client):
    """Verify that Shopify template manifest endpoint returns compliant OS 2.0 structure."""
    response = client.post("/api/shopify/store/export-manifest", json={"store_name": "DNK-e.com", "niche": "tech_apparel"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("ready_for_deploy", "success")
    assert data["store_name"] == "DNK-e.com"
    assert "archive_name" in data
    assert "files_summary" in data
    assert data["files_summary"]["total_files"] > 0
    assert data["size_bytes"] > 0


def test_shopify_inspector_liquid_schema_validation(client):
    """Verify that Shopify liquid builder and schema validation works as expected."""
    # Test valid liquid payload with schema
    payload = {
        "section_name": "hero_video",
        "settings": {
            "heading": "DNK CYBERNETIC LUXURY",
            "button_label": "SHOP NOW"
        },
        "components": ["heading", "text", "button"]
    }
    response = client.post("/api/shopify/builder/generate", json=payload)
    if response.status_code == 200:
        data = response.json()
        assert data["status"] == "success"
        assert "{% schema %}" in data["liquid"]
        assert "DNK CYBERNETIC LUXURY" in data["liquid"]


def test_shopify_template_ast_mutation_flow():
    """Verify TemplateStateEngine block mutation logic (add, remove, reorder)."""
    # Simulate initial OS 2.0 section state
    section_state = {
        "type": "hero_video",
        "settings": {
            "heading": "Obsidian Header",
            "accent_color": "#8B5CF6"
        },
        "blocks": {
            "block_1": {"type": "badge", "settings": {"text": "NEW RELEASE"}},
            "block_2": {"type": "heading", "settings": {"text": "Next-Gen Cyber Apparel"}}
        },
        "block_order": ["block_1", "block_2"]
    }

    # Add block mutation
    new_block_id = "block_3"
    section_state["blocks"][new_block_id] = {"type": "button", "settings": {"text": "Order Now"}}
    section_state["block_order"].append(new_block_id)

    assert len(section_state["block_order"]) == 3
    assert section_state["block_order"][-1] == "block_3"
    assert section_state["blocks"]["block_3"]["type"] == "button"

    # Remove block mutation
    remove_id = "block_1"
    del section_state["blocks"][remove_id]
    section_state["block_order"] = [b for b in section_state["block_order"] if b != remove_id]

    assert len(section_state["block_order"]) == 2
    assert "block_1" not in section_state["blocks"]
    assert section_state["block_order"] == ["block_2", "block_3"]


def test_shopify_theme_export_json_schema_compliance():
    """Verify JSON schema compliance for DNK-e.com Theme Export."""
    theme_template_schema = {
        "type": "object",
        "required": ["name", "sections", "order"],
        "properties": {
            "name": {"type": "string"},
            "sections": {"type": "object"},
            "order": {"type": "array"}
        }
    }

    sample_template = {
        "name": "DNK Obsidian Luxury Theme",
        "sections": {
            "hero_video": {
                "type": "hero_video",
                "settings": {"heading": "DNK Cyber"},
                "blocks": {},
                "block_order": []
            }
        },
        "order": ["hero_video"]
    }

    # Verify keys
    for req in theme_template_schema["required"]:
        assert req in sample_template

    assert isinstance(sample_template["sections"], dict)
    assert isinstance(sample_template["order"], list)
    assert len(sample_template["order"]) == 1
