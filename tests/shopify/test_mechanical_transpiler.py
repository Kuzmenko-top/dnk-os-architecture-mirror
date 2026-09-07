# --- DNK-MRH-HEADER ---
# mrh_id: "tests/shopify/test_mechanical_transpiler.py"
# purpose: "Unit tests for MechanicalTranspiler: Canvas HTML to Liquid AST and Open Design Tokens"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-30"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import pytest
from typing import Dict, Any

from services.dnk_shopify_builder.mechanical_transpiler import (
    MechanicalTranspiler,
    mechanical_transpiler,
)
from services.dnk_shopify_builder.liquid_compiler import liquid_compiler


@pytest.fixture
def sample_canvas_html() -> str:
    return """
    <div class="hero-container bg-slate-900 text-white p-8 rounded-xl">
        <h1 class="text-4xl font-bold tracking-tight mb-2">Summer Collection 2026</h1>
        <p class="text-lg text-slate-300 mb-6">Discover our newest arrivals designed for ultimate performance.</p>
        <button class="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-3 rounded-lg font-medium">
            Shop Now
        </button>
        <div class="grid grid-cols-3 gap-4 mt-8">
            <div class="feature-card p-4 border border-slate-700 rounded-lg">
                <h3 class="font-semibold text-lg">Fast Delivery</h3>
                <p class="text-sm text-slate-400">Ships worldwide within 48h.</p>
            </div>
            <div class="feature-card p-4 border border-slate-700 rounded-lg">
                <h3 class="font-semibold text-lg">Premium Quality</h3>
                <p class="text-sm text-slate-400">Crafted from sustainable materials.</p>
            </div>
            <div class="feature-card p-4 border border-slate-700 rounded-lg">
                <h3 class="font-semibold text-lg">24/7 Support</h3>
                <p class="text-sm text-slate-400">Our customer team is always here.</p>
            </div>
        </div>
    </div>
    """


@pytest.fixture
def open_design_tokens() -> Dict[str, Any]:
    return {
        "color_accent": "#6366f1",
        "color_text": "#ffffff",
        "bg_card": "#1e293b",
        "border_color": "#334155",
        "font_family": "Inter, sans-serif",
    }


def test_transpile_canvas_html_basic(sample_canvas_html, open_design_tokens):
    transpiler = MechanicalTranspiler()
    result = transpiler.transpile(
        html_content=sample_canvas_html,
        section_name="Hero Showcase",
        theme_tokens=open_design_tokens,
    )

    assert result["success"] is True
    assert result["section_name"] == "Hero Showcase"
    assert len(result["liquid_code"]) > 0
    assert "name" in result["schema_json"]
    assert "settings" in result["schema_json"]
    assert len(result["settings"]) > 0
    assert len(result["blocks"]) > 0

    # Verify template contains schema and style tags
    full_template = result["full_liquid_template"]
    assert "{% schema %}" in full_template
    assert "{% endschema %}" in full_template
    assert "{% style %}" in full_template
    assert "{% endstyle %}" in full_template

    # Verify CSS variables from Open Design tokens are injected
    assert "--dnk-accent: #6366f1;" in full_template
    assert "--dnk-card-bg: #1e293b;" in full_template


def test_transpiled_section_passes_liquid_compiler_validation(sample_canvas_html, open_design_tokens):
    transpiler = MechanicalTranspiler()
    result = transpiler.transpile(
        html_content=sample_canvas_html,
        section_name="Validated Section",
        theme_tokens=open_design_tokens,
    )

    validation = liquid_compiler.validate_section_full(result["full_liquid_template"])
    assert validation["is_valid"] is True
    assert len(validation["errors"]) == 0
    assert validation["schema"] is not None
    assert validation["schema"]["name"] == "Validated Section"


def test_repeating_blocks_contain_shopify_attributes(sample_canvas_html):
    transpiler = MechanicalTranspiler()
    result = transpiler.transpile(
        html_content=sample_canvas_html,
        section_name="Feature List",
    )

    # Check for block loop
    assert "{% for block in section.blocks %}" in result["liquid_code"]
    assert "{% endfor %}" in result["liquid_code"]

    # Check block attributes injection
    assert "{{ block.shopify_attributes }}" in result["liquid_code"]


def test_convenience_instance():
    res = mechanical_transpiler.transpile(
        html_content="<section><h2>Simple Title</h2><p>Description text</p></section>",
        section_name="Simple Banner",
    )
    assert res["success"] is True
    assert "section.settings" in res["liquid_code"]
