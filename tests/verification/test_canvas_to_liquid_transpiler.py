# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_canvas_to_liquid_transpiler.py"
# purpose: "Verify Canvas-to-Liquid Transpiler Engine with Remotion Video Embeds & API Endpoint."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "Gerych Prime & Maksym Kuzmenko"
# --- END DNK-MRH-HEADER ---

import pytest
from fastapi.testclient import TestClient
from core.shopify_liquid.canvas_to_liquid_transpiler import (
    CanvasToLiquidTranspiler,
    CanvasGraphPayload,
    CanvasNodeData,
)
from apps.api.main import app

client = TestClient(app)


def test_canvas_to_liquid_transpiler_direct():
    transpiler = CanvasToLiquidTranspiler()
    payload = CanvasGraphPayload(
        screen_id="screen_test_001",
        section_name="smokehouse_pro_showcase",
        category="Smokehouse Systems",
        nodes=[
            CanvasNodeData(
                id="node_hero",
                type="hero_banner",
                title="Крафтова Коптильня Lagrange Pro",
                subtitle="Нержавіюча сталь AISI 304, цифровий термоконтролер",
                price="24,990 ₴",
                cta_text="Замовити прямо зараз",
                cta_link="/products/lagrange-pro",
            ),
            CanvasNodeData(
                id="node_video",
                type="video_player",
                title="Демонстрація Роботи (Remotion 9:16)",
                video_url="https://cdn.dnk-smokehouse.com/videos/lagrange_demo_916.mp4",
            ),
            CanvasNodeData(
                id="node_features",
                type="feature_list",
                title="Ключові Переваги",
                features=[
                    "Точність температури ±0.5 °C",
                    "Димогенератор лабіринтного типу",
                    "Швидке очищення парою",
                ],
            ),
        ],
    )

    result = transpiler.transpile(payload)

    assert result.section_name == "smokehouse_pro_showcase"
    assert result.filename == "sections/smokehouse_pro_showcase.liquid"
    assert result.schema_valid is True
    assert result.nodes_count == 3
    assert result.ledger_artifact_id is not None

    code = result.liquid_code
    assert "{% schema %}" in code
    assert "{% endschema %}" in code
    assert "Крафтова Коптильня Lagrange Pro" in code
    assert "lagrange_demo_916.mp4" in code
    assert "Точність температури ±0.5 °C" in code


def test_canvas_to_liquid_transpile_api_endpoint():
    req_body = {
        "screen_id": "screen_api_999",
        "section_name": "wood_chips_banner",
        "category": "Consumables",
        "nodes": [
            {
                "id": "node_hero_chips",
                "type": "hero_banner",
                "title": "Набір Тріски Вільха та Бук",
                "price": "890 ₴",
                "cta_text": "Купити набір",
                "cta_link": "/products/chips-bundle",
            }
        ],
    }

    response = client.post("/api/v3/shopify/transpile-canvas-graph", json=req_body)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["section_name"] == "wood_chips_banner"
    assert data["schema_valid"] is True
    assert data["nodes_count"] == 1
    assert data["ledger_artifact_id"] is not None
