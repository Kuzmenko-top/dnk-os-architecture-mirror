# --- DNK-MRH-HEADER ---
# mrh_id: "tests/shopify/test_theme_adapter_and_store_synthesizer.py"
# purpose: "Unit tests for ThemeAdapter, Mega-Registry indexing, and Autonomous StoreSynthesizer"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-30"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import pytest
from services.dnk_shopify_builder.theme_adapter import theme_adapter, ThemeComponentCategory
from services.dnk_shopify_builder.store_synthesizer import store_synthesizer
from services.dnk_shopify_builder.template_state_engine import TemplateStateEngine


def test_theme_adapter_build_mega_registry():
    """Verify mega registry contains components from both Tinker and Legacy sources."""
    reg = theme_adapter.build_mega_registry()

    assert "stats" in reg
    assert reg["stats"]["total_components"] > 400
    assert reg["stats"]["total_blocks"] > 50
    assert reg["stats"]["total_sections"] > 50
    assert reg["stats"]["total_snippets"] > 100

    # Verify categories present
    categories = reg["stats"]["categories"]
    assert ThemeComponentCategory.PDP_CONVERSION in categories
    assert ThemeComponentCategory.CART_AND_CHECKOUT in categories
    assert ThemeComponentCategory.SOCIAL_PROOF in categories
    assert ThemeComponentCategory.HERO_AND_BANNERS in categories


def test_theme_adapter_classification():
    """Verify keyword classification logic for various component names."""
    assert theme_adapter.classify_component("hero-split-banner") == ThemeComponentCategory.HERO_AND_BANNERS
    assert theme_adapter.classify_component("bundle-offer-tiered") == ThemeComponentCategory.PDP_CONVERSION
    assert theme_adapter.classify_component("tiktok-video-reviews") == ThemeComponentCategory.SOCIAL_PROOF
    assert theme_adapter.classify_component("cart-drawer-upsell") == ThemeComponentCategory.CART_AND_CHECKOUT
    assert theme_adapter.classify_component("predictive-search-modal") == ThemeComponentCategory.DISCOVERY_AND_NAV
    assert theme_adapter.classify_component("exit-intent-popup") == ThemeComponentCategory.MARKETING_AND_PROMO


def test_store_synthesizer_index_generation():
    """Verify synthesis of high-converting home page template."""
    index_tpl = store_synthesizer.synthesize_index_template(
        store_name="Apex Cyber",
        niche="tech_apparel"
    )

    assert "sections" in index_tpl
    assert "order" in index_tpl
    assert len(index_tpl["order"]) >= 5

    # Check key sections presence
    assert "hero_banner" in index_tpl["sections"]
    assert "social_proof" in index_tpl["sections"]
    assert "faq_section" in index_tpl["sections"]

    # Verify order matches sections dict keys
    for sec_id in index_tpl["order"]:
        assert sec_id in index_tpl["sections"]


def test_store_synthesizer_product_generation():
    """Verify synthesis of high-AOV product detail page template."""
    prod_tpl = store_synthesizer.synthesize_product_template(
        store_name="BioLongevity Lab",
        niche="health_supplements"
    )

    assert "sections" in prod_tpl
    assert "main_product" in prod_tpl["sections"]

    main_pdp = prod_tpl["sections"]["main_product"]
    assert "blocks" in main_pdp
    blocks = main_pdp["blocks"]

    # Check for high-converting blocks
    assert "bundle_offer" in blocks
    assert "delivery_estimate" in blocks
    assert "variant_picker" in blocks
    assert "buy_buttons" in blocks


def test_store_synthesizer_full_store_package():
    """Verify full store package generation with tokens and summary."""
    tokens = {
        "accent": "#06b6d4",
        "bgDark": "#030712",
        "fontHeading": "'Outfit', sans-serif"
    }

    result = store_synthesizer.synthesize_store(
        store_name="Apex Cybernetics",
        niche="tech_apparel",
        theme_tokens=tokens
    )

    assert result["store_name"] == "Apex Cybernetics"
    assert result["niche"] == "tech_apparel"
    assert result["theme_tokens"] == tokens
    assert "index.json" in result["templates"]
    assert "product.json" in result["templates"]

    summary = result["summary"]
    assert summary["index_sections_count"] >= 5
    assert summary["product_sections_count"] >= 3
    assert summary["total_blocks_used"] >= 10


def test_template_state_engine_stateless_mutate():
    """Verify the new stateless TemplateStateEngine.mutate helper."""
    base_template = {
        "sections": {
            "header": {"type": "header"},
            "footer": {"type": "footer"}
        },
        "order": ["header", "footer"]
    }

    updated = TemplateStateEngine.mutate(
        base_template,
        action="add_section",
        section_type="promo-banner",
        after_ordinal=1,
        settings={"title": "Flash Sale"}
    )

    assert len(updated["order"]) == 3
    assert updated["order"][0] == "header"
    assert updated["order"][2] == "footer"


def test_theme_exporter_zip():
    """Verify ThemeExporter creates a valid, non-empty ZIP archive with all Shopify OS 2.0 folders."""
    import zipfile
    import io
    from services.dnk_shopify_builder.theme_exporter import theme_exporter

    zip_bytes, manifest = theme_exporter.export_store_zip(
        store_name="Lumina Lux",
        niche="luxury_jewelry",
        theme_tokens={"accent": "#f59e0b", "bgDark": "#0a0a0a"}
    )

    assert len(zip_bytes) > 50000
    assert manifest["store_name"] == "Lumina Lux"
    assert manifest["niche"] == "luxury_jewelry"
    assert manifest["archive_name"] == "lumina_lux_shopify_theme.zip"
    assert manifest["files_summary"]["total_files"] > 300
    assert manifest["files_summary"]["templates"] == 2

    # Verify zip content structure
    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
        namelist = zf.namelist()
        assert "templates/index.json" in namelist
        assert "templates/product.json" in namelist
        assert "config/settings_data.json" in namelist
        assert any(n.startswith("blocks/") for n in namelist)
        assert any(n.startswith("sections/") for n in namelist)
        assert any(n.startswith("snippets/") for n in namelist)

