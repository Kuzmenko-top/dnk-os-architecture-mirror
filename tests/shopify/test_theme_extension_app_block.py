# --- DNK-MRH-HEADER ---
# mrh_id: "tests/shopify/test_theme_extension_app_block.py"
# purpose: "Unit and Integration Tests for Shopify App Block, Schema Generator & Theme Store V2 Compliance."
# canonical_source: true
# alters_files: []
# triggers_tasks: ["DNK-ECOM-003"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym / Gerych Prime"
# --- END DNK-MRH-HEADER ---

"""
Unit and Integration Tests for Shopify App Block & Theme Extension Integration (Phase 4).
Tests schema generation, section configuration, Theme Store V2 validation, and API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app
from apps.api.services.shopify_theme_extension import (
    AppBlockSchemaGenerator,
    SectionConfigManager,
    ThemeStoreV2Validator,
    AppBlockTarget,
    SettingType
)


@pytest.fixture
def api_client():
    return TestClient(app)


def test_app_block_schema_generation():
    settings = [
        {
            "type": "text",
            "id": "heading",
            "label": "Heading Text",
            "default": "DNK Star Rating"
        },
        {
            "type": "range",
            "id": "rating",
            "label": "Default Rating",
            "min": 1,
            "max": 5,
            "step": 0.5,
            "unit": "★",
            "default": 5
        },
        {
            "type": "select",
            "id": "color_scheme",
            "label": "Color Scheme",
            "options": [
                {"value": "gold", "label": "Gold"},
                {"value": "blue", "label": "Blue"}
            ],
            "default": "gold"
        }
    ]

    schema_liquid = AppBlockSchemaGenerator.generate_app_block_schema(
        name="DNK Star Rating",
        target="section",
        javascript="star-rating.js",
        stylesheet="star-rating.css",
        settings=settings
    )

    assert "{% schema %}" in schema_liquid
    assert "{% endschema %}" in schema_liquid

    parsed = AppBlockSchemaGenerator.extract_schema_from_liquid(schema_liquid)
    assert parsed is not None
    assert parsed["name"] == "DNK Star Rating"
    assert parsed["target"] == "section"
    assert parsed["javascript"] == "star-rating.js"
    assert parsed["stylesheet"] == "star-rating.css"
    assert len(parsed["settings"]) == 3
    assert parsed["settings"][1]["type"] == "range"
    assert parsed["settings"][1]["min"] == 1
    assert parsed["settings"][1]["unit"] == "★"


def test_section_schema_generation():
    settings = [
        {"type": "text", "id": "title", "label": "Section Title"}
    ]
    blocks = [
        {
            "type": "slide",
            "name": "Slide",
            "settings": [
                {"type": "image_picker", "id": "image", "label": "Slide Image"}
            ]
        }
    ]
    presets = [
        {
            "name": "Hero Slider",
            "category": "Hero",
            "settings": {"title": "Welcome to Store"}
        }
    ]

    schema_liquid = AppBlockSchemaGenerator.generate_section_schema(
        name="Hero Banner",
        tag="section",
        settings=settings,
        blocks=blocks,
        presets=presets,
        max_blocks=5
    )

    parsed = AppBlockSchemaGenerator.extract_schema_from_liquid(schema_liquid)
    assert parsed is not None
    assert parsed["name"] == "Hero Banner"
    assert parsed["tag"] == "section"
    assert parsed["max_blocks"] == 5
    assert len(parsed["blocks"]) == 1
    assert len(parsed["presets"]) == 1
    assert parsed["presets"][0]["category"] == "Hero"


def test_section_config_manager_template_and_groups():
    sections = {
        "hero": {
            "type": "hero-banner",
            "settings": {"title": "Big Sale"}
        },
        "featured": {
            "type": "featured-collection",
            "settings": {"collection": "all"}
        }
    }
    order = ["hero", "featured"]

    template = SectionConfigManager.build_template_json(sections, order, name="Home Page")
    assert template["name"] == "Home Page"
    assert template["order"] == ["hero", "featured"]
    assert "hero" in template["sections"]

    group = SectionConfigManager.build_section_group_json(
        name="Header Group",
        sections={"announcement": {"type": "announcement-bar"}, "header": {"type": "header"}},
        order=["announcement", "header"],
        group_type="header"
    )
    assert group["name"] == "Header Group"
    assert group["type"] == "header"
    assert group["order"] == ["announcement", "header"]

    app_block = SectionConfigManager.build_app_block_instance(
        app_block_type="shopify://apps/dnk-app/blocks/star-rating/123",
        settings={"color": "#ffaa00"}
    )
    assert app_block["type"] == "shopify://apps/dnk-app/blocks/star-rating/123"
    assert app_block["settings"]["color"] == "#ffaa00"


def test_theme_store_v2_validator_valid_app_block():
    content = """
    <div class="dnk-star-rating" data-rating="{{ block.settings.rating }}">
      {% render 'star-icon' %}
    </div>

    {% schema %}
    {
      "name": "Star Rating",
      "target": "section",
      "javascript": "rating.js",
      "stylesheet": "rating.css",
      "settings": [
        {
          "type": "range",
          "id": "rating",
          "label": "Rating",
          "min": 1,
          "max": 5,
          "default": 5
        }
      ]
    }
    {% endschema %}
    """
    report = ThemeStoreV2Validator.validate_app_block_liquid("blocks/rating.liquid", content)
    assert report.is_valid is True
    assert report.score == 100
    assert len(report.errors) == 0
    assert len(report.warnings) == 0


def test_theme_store_v2_validator_invalid_schema_and_deprecated_tags():
    content = """
    <div class="dnk-bad-block">
      {% include 'old-snippet' %}
      <script src="https://cdn.example.com/bad.js"></script>
    </div>

    {% schema %}
    {
      "target": "unknown_target",
      "settings": [
        {
          "type": "range",
          "id": "bad_range"
        },
        {
          "type": "invalid_type",
          "id": "bad_type"
        }
      ]
    }
    {% endschema %}
    """
    report = ThemeStoreV2Validator.validate_app_block_liquid("blocks/bad.liquid", content)
    assert report.is_valid is False
    assert report.score < 50
    error_codes = [e.code for e in report.errors]
    assert "SCHEMA_MISSING_NAME" in error_codes
    assert "INVALID_SCHEMA_TARGET" in error_codes
    assert "RANGE_MISSING_MIN_MAX" in error_codes
    assert "UNKNOWN_SETTING_TYPE" in error_codes

    warning_codes = [w.code for w in report.warnings]
    assert "DEPRECATED_INCLUDE_TAG" in warning_codes
    assert "BLOCKING_SCRIPT_TAG" in warning_codes


def test_theme_store_v2_validator_directory():
    files = {
        "blocks/badge.liquid": """
        <span>{{ block.settings.text }}</span>
        {% schema %}
        {
          "name": "Badge",
          "target": "body",
          "settings": [{"type": "text", "id": "text", "label": "Badge Text"}]
        }
        {% endschema %}
        """,
        "assets/badge.js": "console.log('Badge loaded');",
        "assets/badge.css": ".badge { color: red; }"
    }
    report = ThemeStoreV2Validator.validate_theme_extension_directory(files)
    assert report.is_valid is True
    assert report.score == 100

    # No blocks failure
    no_blocks = {"assets/badge.js": "console.log(1);"}
    bad_report = ThemeStoreV2Validator.validate_theme_extension_directory(no_blocks)
    assert bad_report.is_valid is False
    assert any(e.code == "NO_APP_BLOCKS_FOUND" for e in bad_report.errors)


def test_api_extension_validate_endpoint(api_client):
    files = {
        "blocks/counter.liquid": """
        <div id="counter">0</div>
        {% schema %}
        {
          "name": "Counter",
          "target": "section",
          "settings": []
        }
        {% endschema %}
        """
    }
    response = api_client.post("/api/shopify/extension/validate", json={"files": files})
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is True
    assert data["score"] == 100
    assert len(data["errors"]) == 0


def test_api_schema_generate_endpoint(api_client):
    req = {
        "name": "Live Viewers Counter",
        "target": "section",
        "javascript": "viewers.js",
        "settings": [
            {"type": "number", "id": "min_viewers", "label": "Min Viewers", "default": 5}
        ]
    }
    response = api_client.post("/api/shopify/schema/generate", json=req)
    assert response.status_code == 200
    data = response.json()
    assert "{% schema %}" in data["schema_liquid"]
    assert data["parsed_schema"]["name"] == "Live Viewers Counter"
    assert data["parsed_schema"]["target"] == "section"


def test_api_section_schema_endpoint(api_client):
    req = {
        "name": "Testimonials Grid",
        "tag": "section",
        "settings": [{"type": "text", "id": "heading", "label": "Heading"}],
        "blocks": [{"type": "review", "name": "Review", "settings": []}],
        "presets": [{"name": "Default Testimonials"}]
    }
    response = api_client.post("/api/shopify/section/schema", json=req)
    assert response.status_code == 200
    data = response.json()
    assert "{% schema %}" in data["schema_liquid"]
    assert data["parsed_schema"]["name"] == "Testimonials Grid"
    assert len(data["parsed_schema"]["blocks"]) == 1
