# --- DNK-MRH-HEADER ---
# mrh_id: "tests/shopify/test_template_state_engine.py"
# purpose: "Comprehensive Unit Tests for TemplateStateEngine RFC 6902 & Ordinal Mutation Algorithm"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-30"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import pytest
import sys
from pathlib import Path
from typing import Dict, Any

HUB_ROOT = Path(__file__).resolve().parent.parent.parent
MVP_PATH = HUB_ROOT
if str(MVP_PATH) not in sys.path:
    sys.path.insert(0, str(MVP_PATH))

from services.dnk_shopify_builder.template_state_engine import TemplateStateEngine, TemplateStateError


@pytest.fixture
def sample_template() -> Dict[str, Any]:
    return {
        "name": "Index Page",
        "layout": "theme",
        "wrapper": "div.main-content",
        "sections": {
            "hero_banner": {
                "type": "hero-image",
                "disabled": False,
                "settings": {
                    "heading": "Welcome to DNK Store",
                    "show_button": True
                },
                "blocks": {
                    "b1": {
                        "type": "button",
                        "settings": {"label": "Shop Now"}
                    }
                },
                "block_order": ["b1"]
            },
            "featured_collection": {
                "type": "collection-grid",
                "settings": {
                    "products_to_show": 4
                }
            },
            "footer_promo": {
                "type": "newsletter-signup",
                "settings": {
                    "title": "Subscribe"
                }
            }
        },
        "order": ["hero_banner", "featured_collection", "footer_promo"]
    }


def test_outline(sample_template):
    engine = TemplateStateEngine(sample_template)
    outline = engine.outline("index")
    assert outline["template_name"] == "index"
    assert outline["section_count"] == 3
    assert len(outline["sections"]) == 3
    assert outline["sections"][0]["id"] == "hero_banner"
    assert outline["sections"][0]["ordinal"] == 1
    assert outline["sections"][0]["type"] == "hero-image"
    assert outline["sections"][0]["block_count"] == 1


def test_add_section(sample_template):
    engine = TemplateStateEngine(sample_template)
    sec_id = engine.add_section(
        section_type="rich-text",
        after_ordinal=1,
        settings={"title": "Our Story"}
    )
    assert sec_id in engine.state["sections"]
    assert engine.state["order"] == ["hero_banner", sec_id, "featured_collection", "footer_promo"]
    assert engine.state["sections"][sec_id]["type"] == "rich-text"
    assert engine.state["sections"][sec_id]["settings"]["title"] == "Our Story"


def test_remove_section(sample_template):
    engine = TemplateStateEngine(sample_template)
    removed_id = engine.remove_section(ordinal_or_id=2)
    assert removed_id == "featured_collection"
    assert "featured_collection" not in engine.state["sections"]
    assert engine.state["order"] == ["hero_banner", "footer_promo"]


def test_reorder_sections(sample_template):
    engine = TemplateStateEngine(sample_template)
    engine.reorder(order_list=["footer_promo", "hero_banner", "featured_collection"])
    assert engine.state["order"] == ["footer_promo", "hero_banner", "featured_collection"]


def test_move_section(sample_template):
    engine = TemplateStateEngine(sample_template)
    engine.move_section(from_ordinal=3, to_ordinal=1)
    assert engine.state["order"] == ["footer_promo", "hero_banner", "featured_collection"]


def test_add_and_remove_block(sample_template):
    engine = TemplateStateEngine(sample_template)
    block_id = engine.add_block(
        section_ordinal_or_id=1,
        block_type="text_badge",
        settings={"badge_text": "New Arrival"}
    )
    assert block_id in engine.state["sections"]["hero_banner"]["blocks"]
    assert engine.state["sections"]["hero_banner"]["block_order"] == ["b1", block_id]

    removed_id = engine.remove_block(section_ordinal_or_id=1, block_id=block_id)
    assert removed_id == block_id
    assert block_id not in engine.state["sections"]["hero_banner"]["blocks"]
    assert engine.state["sections"]["hero_banner"]["block_order"] == ["b1"]


def test_patch_setting(sample_template):
    engine = TemplateStateEngine(sample_template)
    engine.patch_setting(
        section_ordinal_or_id=1,
        setting_id="heading",
        value="Super DNK Store!"
    )
    assert engine.state["sections"]["hero_banner"]["settings"]["heading"] == "Super DNK Store!"

    # Patch block setting
    engine.patch_setting(
        section_ordinal_or_id=1,
        setting_id="label",
        value="Explore Catalog",
        block_id="b1"
    )
    assert engine.state["sections"]["hero_banner"]["blocks"]["b1"]["settings"]["label"] == "Explore Catalog"


def test_rfc6902_json_patch(sample_template):
    engine = TemplateStateEngine(sample_template)
    ops = [
        {"op": "replace", "path": "/sections/hero_banner/settings/heading", "value": "Patched Title"},
        {"op": "add", "path": "/sections/custom_html", "value": {"type": "custom-html", "settings": {"html": "<p>Hi</p>"}}},
        {"op": "add", "path": "/order/-", "value": "custom_html"}
    ]
    res = engine.apply_json_patch(ops)
    assert res["applied_count"] == 3
    assert engine.state["sections"]["hero_banner"]["settings"]["heading"] == "Patched Title"
    assert "custom_html" in engine.state["sections"]
    assert "custom_html" in engine.state["order"]
