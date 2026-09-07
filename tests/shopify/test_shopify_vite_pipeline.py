# --- DNK-MRH-HEADER ---
# mrh_id: "tests/shopify/test_shopify_vite_pipeline.py"
# purpose: "Unit tests verifying Shopify Vite pipeline asset bundling, Liquid section generation, and live preview harnesses."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import asyncio
import pytest
import sys
from pathlib import Path

HUB_ROOT = Path(__file__).resolve().parent.parent.parent
MVP_PATH = HUB_ROOT
if str(MVP_PATH) not in sys.path:
    sys.path.insert(0, str(MVP_PATH))

from services.dnk_shopify_builder.shopify_vite_pipeline import (
    shopify_vite_pipeline,
    ShopifyBundleManifest,
)
from services.dnk_shopify_builder.liquid_compiler import LiquidSectionModel


@pytest.mark.asyncio
async def test_shopify_vite_pipeline_bundle_build():
    sections = [
        LiquidSectionModel(
            name="Sticky ATC",
            liquid_body="<div class='sticky-atc'>{% if product.available %}<button>Buy</button>{% endif %}</div>",
            css_content=".sticky-atc { position: fixed; bottom: 0; }",
            settings_schema={"name": "Sticky ATC", "settings": []},
        ),
        LiquidSectionModel(
            name="Cart Drawer",
            liquid_body="<div class='cart-drawer'>{% for item in cart.items %}<div>{{ item.title }}</div>{% endfor %}</div>",
            css_content=".cart-drawer { width: 400px; }",
            settings_schema={"name": "Cart Drawer", "settings": []},
        ),
    ]

    manifest = await shopify_vite_pipeline.build_theme_bundle(sections, bundle_name="Alpha-Launch")

    assert isinstance(manifest, ShopifyBundleManifest)
    assert manifest.bundle_name == "Alpha-Launch"
    assert len(manifest.sections) == 2
    assert "Sticky ATC" in manifest.sections
    assert "Cart Drawer" in manifest.sections
    assert manifest.build_time_seconds >= 0.0
    assert manifest.preview_url is not None
    assert Path(manifest.preview_url).exists()

    # Verify preview content
    preview_content = Path(manifest.preview_url).read_text(encoding="utf-8")
    assert "Shopify Theme Preview" in preview_content
    assert "HMR Active (Vite)" in preview_content
