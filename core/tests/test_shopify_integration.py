# --- DNK-MRH-HEADER ---
# mrh_id: "core/tests/test_shopify_integration.py"
# purpose: "Unit tests for Shopify 3.0 Integration in DNK OS."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "0.1.0"
# updated_at: "2026-08-06"
# --- END DNK-MRH-HEADER ---

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from services.dnk_shopify.main import shopify_engine


def test_shopify_theme_version():
    assert shopify_engine.theme_version == "Tinker 4.3.1"
    assert shopify_engine.architecture == "Shopify 3.0"


def test_build_section():
    res = shopify_engine.build_section("hero_banner", {"title": "DNK OS Store"})
    assert res["status"] == "success"
    assert res["section"] == "hero_banner"
    assert res["theme"] == "Tinker 4.3.1"


def test_update_css_tokens():
    res = shopify_engine.update_css_tokens({"primary": "#0052FF", "secondary": "#111827"})
    assert res["status"] == "success"
    assert res["tokens_updated"] == 2


def test_metaobject_schema():
    res = shopify_engine.generate_metaobject_schema("designer_product", ["name", "specs", "variant_id"])
    assert res["status"] == "success"
    assert res["fields_count"] == 3


def test_service_bridge_deploy():
    import asyncio
    from services.dnk_shopify.main import bridge, StoreRequest
    req = StoreRequest(brand_name="ReBurn", niche="smokers", colors={"primary": "#ff0000"})
    res = asyncio.run(bridge.generate_and_deploy_store(req))
    assert res.status == "success"
    assert res.shop_url == "dev-store.myshopify.com"
    assert "EVENT: TOKENS_TRANSPILED" in res.events_streamed
    assert "EVENT: STORE_PUBLISHED" in res.events_streamed

