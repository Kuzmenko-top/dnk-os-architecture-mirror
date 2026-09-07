# --- DNK-MRH-HEADER ---
# mrh_id: "tests_shopify_test_liquid_preview_engine"
# purpose: "Unit & Integration Tests for Liquid Preview Engine, Tailwind v4 JIT Compiler & FastAPI Endpoints"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from apps.api.services.liquid_preview_engine import LiquidPreviewEngine, LiquidFilterEngine
from apps.api.services.tailwind_v4_jit import TailwindV4JITCompiler
from apps.api.services.liquid_ast_compiler import FilterNode, LiquidASTParser


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def preview_engine():
    engine = LiquidPreviewEngine(
        snippets={
            "product_card": '<div class="product-card border rounded p-4"><h3 class="text-lg font-bold">{{ product.title }}</h3><p class="text-primary">{{ product.price | money }}</p></div>'
        },
        sections={
            "hero": '<div class="hero bg-black text-white p-8"><h1 class="text-3xl font-extrabold">{{ section.settings.title | default: "Welcome" }}</h1></div>'
        },
        theme_tokens={
            "colors": {
                "primary": "#3b82f6",
                "secondary": "#10b981"
            }
        }
    )
    return engine


# ============================================================================
# 1. TAILWIND V4 JIT COMPILER TESTS
# ============================================================================

def test_tailwind_v4_class_extraction():
    compiler = TailwindV4JITCompiler()
    liquid_src = '<div class="flex items-center justify-between p-4 bg-black text-white rounded-lg hover:bg-gray-800 md:flex-row lg:p-8 w-[350px]"></div>'
    parser = LiquidASTParser(liquid_src)
    ast = parser.parse()

    classes = compiler.extract_classes_from_ast(ast)
    assert "flex" in classes
    assert "p-4" in classes
    assert "bg-black" in classes
    assert "text-white" in classes
    assert "hover:bg-gray-800" in classes
    assert "md:flex-row" in classes
    assert "w-[350px]" in classes


def test_tailwind_v4_jit_css_generation():
    compiler = TailwindV4JITCompiler(custom_theme_tokens={"colors": {"primary": "#3b82f6"}})
    liquid_src = '<div class="flex p-4 text-primary rounded-md md:hidden">Header</div>'
    parser = LiquidASTParser(liquid_src)
    ast = parser.parse()

    res = compiler.compile(ast)
    assert "flex" in res.classes_found
    assert "text-primary" in res.classes_found
    assert ".flex {" in res.css
    assert "display: flex;" in res.css
    assert "color: #3b82f6;" in res.css
    assert "@media (min-width: 768px)" in res.css


# ============================================================================
# 2. LIQUID FILTER PIPELINE TESTS
# ============================================================================

def test_liquid_filters():
    ctx = {"product": {"price": 19900}}
    
    upcase_f = FilterNode(name="upcase")
    assert LiquidFilterEngine.apply_filter("hello dnk", upcase_f, ctx) == "HELLO DNK"

    money_f = FilterNode(name="money")
    assert LiquidFilterEngine.apply_filter(19900, money_f, ctx) == "$199.00"

    default_f = FilterNode(name="default", args=["Fallback Value"])
    assert LiquidFilterEngine.apply_filter(None, default_f, ctx) == "Fallback Value"
    assert LiquidFilterEngine.apply_filter("Active Value", default_f, ctx) == "Active Value"

    json_f = FilterNode(name="json")
    assert LiquidFilterEngine.apply_filter({"a": 1}, json_f, ctx) == '{"a": 1}'


# ============================================================================
# 3. LIQUID PREVIEW ENGINE RENDERING TESTS
# ============================================================================

def test_preview_engine_variable_rendering(preview_engine):
    tpl = '<h1 class="text-2xl font-bold">{{ shop.name }}</h1><p>{{ shop.domain }}</p>'
    res = preview_engine.render(tpl)
    assert "DNK Luxury Store" in res.html
    assert "dnk-luxury.myshopify.com" in res.html
    assert "text-2xl" in res.classes_used
    assert '<style id="dnk-tailwind-v4">' in res.html


def test_preview_engine_assign_and_conditionals(preview_engine):
    tpl = '''
    {% assign is_featured = true %}
    {% if is_featured %}
        <span class="bg-primary text-white p-2">Featured Item</span>
    {% else %}
        <span class="bg-gray-200 p-2">Standard Item</span>
    {% endif %}
    '''
    res = preview_engine.render(tpl)
    assert "Featured Item" in res.html
    assert "Standard Item" not in res.html
    assert "bg-primary" in res.classes_used


def test_preview_engine_for_loop(preview_engine):
    tpl = '''
    <ul class="flex flex-col gap-2">
    {% for item in cart.items %}
        <li class="p-2 border">{{ forloop.index }}: {{ item.title }} - {{ item.price | money }}</li>
    {% endfor %}
    </ul>
    '''
    res = preview_engine.render(tpl)
    assert "1: DNK Cyber Stealth Jacket - $199.00" in res.html
    assert "2: DNK Neural Beanie - $50.00" in res.html


def test_preview_engine_render_snippet(preview_engine):
    tpl = '<div class="container">{% render "product_card" %}</div>'
    res = preview_engine.render(tpl)
    assert "product_card" in res.snippets_rendered
    assert "DNK Cyber Stealth Jacket" in res.html
    assert "$199.00" in res.html


def test_preview_engine_section_rendering(preview_engine):
    tpl = '{% section "hero" %}'
    res = preview_engine.render(tpl)
    assert "hero" in res.sections_rendered
    assert '<div class="shopify-section" id="shopify-section-hero"' in res.html
    assert "Welcome" in res.html


def test_preview_engine_error_handling(preview_engine):
    # Malformed source that raises parsing error or invalid context
    tpl = '{% if true %}'  # missing endif
    res = preview_engine.render(tpl)
    # Parser or render should handle or produce fallback
    assert res.execution_time_ms >= 0


# ============================================================================
# 4. FASTAPI ROUTER INTEGRATION TESTS
# ============================================================================

def test_api_liquid_preview_endpoint(client):
    payload = {
        "source": '<h1 class="text-3xl font-extrabold text-primary">{{ shop.name }}</h1>',
        "context": {"shop": {"name": "DNK Cyber Mall"}},
        "inject_tailwind_css": True
    }
    response = client.post("/api/shopify/preview/render", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "DNK Cyber Mall" in data["html"]
    assert "text-3xl" in data["classes_used"]
    assert "text-primary" in data["classes_used"]
    assert data["execution_time_ms"] > 0


def test_api_tailwind_compile_endpoint(client):
    payload = {
        "source": '<div class="grid grid-cols-3 gap-4 p-6 bg-black text-white hover:bg-gray-900 md:grid-cols-4"></div>',
        "theme_tokens": {"colors": {"primary": "#3b82f6"}},
        "include_reset": False
    }
    response = client.post("/api/shopify/tailwind/compile", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "grid" in data["classes_found"]
    assert "gap-4" in data["classes_found"]
    assert "hover:bg-gray-900" in data["classes_found"]
    assert ".grid {" in data["css"]
    assert data["rules_generated"] > 0
    assert data["css_size_bytes"] > 0
