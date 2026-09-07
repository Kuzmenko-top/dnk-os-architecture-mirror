# --- DNK-MRH-HEADER ---
# mrh_id: "tests/shopify/test_liquid_compiler.py"
# purpose: "Unit tests verifying Shopify Liquid AST validation, tag pairing, and section compilation."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-27"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import pytest
import sys
from pathlib import Path

HUB_ROOT = Path(__file__).resolve().parent.parent.parent
MVP_PATH = HUB_ROOT
if str(MVP_PATH) not in sys.path:
    sys.path.insert(0, str(MVP_PATH))

from services.dnk_shopify_builder.liquid_compiler import (
    liquid_compiler,
    LiquidSectionModel,
    LiquidSyntaxError,
)


def test_liquid_compiler_validation_success():
    valid_liquid = """
    {% if product.available %}
      <div class="product-badge">In Stock</div>
      {% for variant in product.variants %}
        <span>{{ variant.title }}</span>
      {% endfor %}
    {% endif %}
    """
    is_valid, error = liquid_compiler.validate_syntax(valid_liquid)
    assert is_valid is True
    assert error is None


def test_liquid_compiler_validation_unclosed_tag():
    invalid_liquid = """
    {% if product.available %}
      <div class="product-badge">In Stock</div>
    """
    is_valid, error = liquid_compiler.validate_syntax(invalid_liquid)
    assert is_valid is False
    assert "Unclosed tag 'if'" in error


def test_liquid_compiler_validation_mismatched_tag():
    invalid_liquid = """
    {% if product.available %}
      <div class="product-badge">In Stock</div>
    {% endfor %}
    """
    is_valid, error = liquid_compiler.validate_syntax(invalid_liquid)
    assert is_valid is False
    assert "Mismatched closing tag 'endfor'" in error


def test_liquid_compiler_section_compilation():
    section = LiquidSectionModel(
        name="Hero Sticky ATC",
        liquid_body="""
        <div class="dnk-hero-atc">
          {% if section.settings.show_button %}
            <button>{{ section.settings.btn_label }}</button>
          {% endif %}
        </div>
        """,
        css_content=".dnk-hero-atc { background: #000; color: #fff; }",
        js_content="console.log('DNK ATC Mounted');",
        settings_schema={
            "name": "Hero Sticky ATC",
            "settings": [
                {"type": "checkbox", "id": "show_button", "label": "Show Button", "default": True},
                {"type": "text", "id": "btn_label", "label": "Button Label", "default": "Buy Now"},
            ],
        },
    )

    compiled = liquid_compiler.compile_section(section)
    assert "{% style %}" in compiled
    assert ".dnk-hero-atc { background: #000;" in compiled
    assert "{% javascript %}" in compiled
    assert "console.log('DNK ATC Mounted');" in compiled
    assert "{% schema %}" in compiled
    assert '"name": "Hero Sticky ATC"' in compiled
