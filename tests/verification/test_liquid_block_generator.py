# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_liquid_block_generator.py"
# purpose: "Verification test suite for Liquid Block Generator & Theme App Extensions."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import pytest
from apps.api.services.liquid_block_generator import LiquidBlockGenerator, LiquidBlockSpec


class TestLiquidBlockGenerator:
    def test_generate_upsell_banner(self):
        generator = LiquidBlockGenerator()
        spec = LiquidBlockSpec(
            name="dnk-upsell-banner",
            block_type="upsell_banner",
            schema_fields=[
                {
                    "type": "product",
                    "id": "recommended_product",
                    "label": "Рекомендований товар",
                },
                {
                    "type": "text",
                    "id": "banner_text",
                    "label": "Текст банера",
                    "default": "Додайте ще для безкоштовної доставки!",
                },
            ],
            target="section",
        )
        result = generator.generate(spec)

        assert result["liquid_file"] == "dnk-upsell-banner.liquid"
        assert result["schema_file"] == "dnk-upsell-banner.json"
        assert "dnk-upsell-banner" in result["template"]
        assert "recommended_product" in result["template"]
        assert result["schema"]["name"] == "dnk-upsell-banner"
        assert result["schema"]["target"] == "section"
        assert len(result["schema"]["schema"]) == 2

    def test_generate_loyalty_widget(self):
        generator = LiquidBlockGenerator()
        spec = LiquidBlockSpec(
            name="dnk-loyalty-widget",
            block_type="loyalty_widget",
            schema_fields=[
                {
                    "type": "text",
                    "id": "widget_title",
                    "label": "Заголовок",
                    "default": "DNK Rewards Club",
                },
                {
                    "type": "text",
                    "id": "redeem_text",
                    "label": "Текст кнопки",
                    "default": "Обміняти бали",
                },
            ],
        )
        result = generator.generate(spec)

        assert result["liquid_file"] == "dnk-loyalty-widget.liquid"
        assert result["schema_file"] == "dnk-loyalty-widget.json"
        assert "dnk-loyalty-widget" in result["template"]
        assert "dnk-loyalty-progress-fill" in result["template"]
        assert len(result["schema"]["schema"]) == 2

    def test_generate_product_recommendations(self):
        generator = LiquidBlockGenerator()
        spec = LiquidBlockSpec(
            name="dnk-product-recommendations",
            block_type="product_recommendations",
            schema_fields=[
                {
                    "type": "text",
                    "id": "section_title",
                    "label": "Заголовок",
                    "default": "Вам також може сподобатися",
                }
            ],
        )
        result = generator.generate(spec)

        assert result["liquid_file"] == "dnk-product-recommendations.liquid"
        assert "recommendations.products" in result["template"]

    def test_generate_generic_block(self):
        generator = LiquidBlockGenerator()
        custom_template = "<div class='custom'><h3>Custom</h3></div>"
        spec = LiquidBlockSpec(
            name="dnk-custom-block",
            block_type="custom_block",
            template=custom_template,
            schema_fields=[],
        )
        result = generator.generate(spec)

        assert result["liquid_file"] == "dnk-custom-block.liquid"
        assert result["template"] == custom_template
        assert result["schema"]["name"] == "dnk-custom-block"
