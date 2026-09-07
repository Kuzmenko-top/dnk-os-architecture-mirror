# --- DNK-MRH-HEADER ---
# mrh_id: "tests_ecom_test_shopify_canvas_sync"
# purpose: "Integration & Contract tests for Shopify Theme Asset Tree and Canvas Graph generation (DNK-ECOM-004)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import os
import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from apps.api.routers.shopify import set_adapter
from apps.api.services.shopify_adapter import ShopifyAdapter
from apps.api.services.shopify_transport import MockShopifyTransport


@pytest.fixture
def mock_transport():
    transport = MockShopifyTransport()
    # Mock theme asset listing with multiple categories
    transport.register_route(
        "admin/api/2024-01/themes/160000001/assets.json",
        {
            "assets": [
                {"key": "layout/theme.liquid", "content_type": "text/x-liquid", "size": 12450},
                {"key": "templates/index.json", "content_type": "application/json", "size": 3200},
                {"key": "templates/product.json", "content_type": "application/json", "size": 4100},
                {"key": "sections/header.liquid", "content_type": "text/x-liquid", "size": 8900},
                {"key": "sections/hero-banner.liquid", "content_type": "text/x-liquid", "size": 5600},
                {"key": "snippets/price.liquid", "content_type": "text/x-liquid", "size": 1200},
                {"key": "snippets/card-product.liquid", "content_type": "text/x-liquid", "size": 2400},
                {"key": "assets/base.css", "content_type": "text/css", "size": 45000},
                {"key": "config/settings_schema.json", "content_type": "application/json", "size": 18000},
                {"key": "locales/en.default.json", "content_type": "application/json", "size": 9500}
            ]
        },
        200
    )
    return transport


@pytest.fixture
def adapter(mock_transport):
    return ShopifyAdapter(transport=mock_transport)


@pytest.fixture
def client(adapter):
    set_adapter(adapter)
    return TestClient(app)


def test_theme_asset_tree_categorization(adapter):
    """Verify get_theme_asset_tree categorizes assets into strict Shopify theme folders."""
    res = adapter.get_theme_asset_tree("dnk-e-com.myshopify.com", 160000001)
    assert res.error_code is None
    assert res.data_source == "live"
    
    tree = res.data
    assert isinstance(tree, dict)
    assert tree["store_domain"] == "dnk-e-com.myshopify.com"
    assert tree["total_files"] == 10
    
    # Assert categorized counts
    assert len(tree["layout"]) == 1
    assert len(tree["templates"]) == 2
    assert len(tree["sections"]) == 2
    assert len(tree["snippets"]) == 2
    assert len(tree["assets"]) == 1
    assert len(tree["config"]) == 1
    assert len(tree["locales"]) == 1
    
    assert tree["layout"][0]["key"] == "layout/theme.liquid"
    assert tree["sections"][0]["key"] == "sections/header.liquid"


def test_theme_canvas_graph_generation(adapter):
    """Verify get_theme_canvas_graph creates Canvas nodes and render relationship edges."""
    res = adapter.get_theme_canvas_graph("dnk-e-com.myshopify.com", 160000001)
    assert res.error_code is None
    assert res.data_source == "live"
    
    graph = res.data
    assert isinstance(graph, dict)
    assert "nodes" in graph
    assert "edges" in graph
    
    nodes = graph["nodes"]
    edges = graph["edges"]
    
    assert len(nodes) >= 7  # layout, templates, sections, snippets
    
    # Check node structure
    section_node = next((n for n in nodes if n["key"] == "sections/header.liquid"), None)
    assert section_node is not None
    assert section_node["category"] == "sections"
    assert section_node["node_type"] == "section"
    assert section_node["position_x"] == 700.0
    assert section_node["settings_count"] > 0
    assert "snippets/price.liquid" in section_node["snippet_dependencies"]
    
    # Check edge connection
    render_edge = next((e for e in edges if e["relationship_type"] == "renders"), None)
    assert render_edge is not None
    assert render_edge["label"] == "{% render %}"


def test_shopify_canvas_endpoints_integration(client):
    """Verify FastAPI GET /tree and /canvas-graph endpoints with authentication."""
    headers = {"Authorization": "Bearer test-token"}
    
    # Test /tree endpoint
    res_tree = client.get("/api/shopify/dnk-e-com.myshopify.com/themes/160000001/tree", headers=headers)
    assert res_tree.status_code == 200
    tree_payload = res_tree.json()
    assert tree_payload["data"]["total_files"] == 10
    
    # Test /canvas-graph endpoint
    res_graph = client.get("/api/shopify/dnk-e-com.myshopify.com/themes/160000001/canvas-graph", headers=headers)
    assert res_graph.status_code == 200
    graph_payload = res_graph.json()
    assert len(graph_payload["data"]["nodes"]) >= 7
    assert len(graph_payload["data"]["edges"]) >= 1


def test_canvas_graph_fixture_mode_deterministic(monkeypatch):
    """Verify zero-egress deterministic execution in FIXTURE_MODE."""
    monkeypatch.setenv("FIXTURE_MODE", "true")
    adapter = ShopifyAdapter()
    
    res = adapter.get_theme_canvas_graph("dnk-e-com.myshopify.com", 101010101)
    assert res.data_source == "fixture"
    assert res.error_code is None
    assert len(res.data["nodes"]) >= 4
