# --- DNK-MRH-HEADER ---
# mrh_id: "tests/rag/test_cross_workspace_marketing.py"
# purpose: "Comprehensive test suite for cross-workspace retrieval and grounded marketing banner synthesis"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK Swarm (gerych_auditor & dnk_dev_fullstack)"
# --- END DNK-MRH-HEADER ---

import os
import json
import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from core.adapters.dnk_rag_anything_adapter import DNKRAGAnythingAdapter, RAGConfig
from core.rag.knowledge_graph import GraphNode
from core.rag.marketing_banner import GroundedMarketingBannerSynthesizer
from core.orchestrator.tools.dnk_rag_tool import (
    dnk_rag_query,
    dnk_rag_ingest,
    dnk_generate_marketing_banner,
)


@pytest.fixture
def rag_adapter(tmp_path):
    cache_dir = str(tmp_path / "rag_cache")
    config = RAGConfig(cache_dir=cache_dir, workspace_id="ws-alpha-001")
    return DNKRAGAnythingAdapter(config=config)


@pytest.fixture
def test_client():
    return TestClient(app)


def test_cross_workspace_ingestion_and_retrieval(rag_adapter):
    """
    Validates that:
    1. Marketing knowledge can be ingested into 'global-marketing'.
    2. ReBurn smoker manual and specs can be ingested into 'ws-reburn-001'.
    3. Cross-workspace query retrieves facts and themes from both workspaces simultaneously.
    """
    # 1. Ingest marketing patterns into global-marketing
    marketing_text = """
    # Психологія продажів та структура оферів
    Основні фреймворки конверсії:
    - AIDA: Увага (Hook), Інтерес (Факти), Бажання (Вигода), Дія (CTA).
    - PAS: Проблема (Problem), Загострення (Agitate), Вирішення (Solution).
    Ключові тригери для крафтових виробів: довговічність, екологічність, якість металу, смак без хімії.
    """
    rag_adapter.ingest_text(
        text=marketing_text,
        title="marketing_frameworks",
        workspace_id="global-marketing"
    )

    # 2. Ingest ReBurn smoker technical manual into ws-reburn-001
    reburn_manual = """
    # Інструкція користувача: Коптильня ReBurn Pro
    Технічні параметри:
    - Матеріал: харчова нержавіюча сталь AISI 304 товщиною 2.0 мм.
    - Водяний гідрозатвор: запобігає виходу диму та проникненню повітря в камеру.
    - Робочий температурний режим холодного копчення: від 20°C до 25°C.
    - Рекомендована тріска: вільха та бук для чистого диму без гіркоти.
    - Об'єм камери: 60 літрів, вміщує до 10 кг м'яса або риби.
    """
    reburn_doc_id = rag_adapter.ingest_text(
        text=reburn_manual,
        title="reburn_user_manual",
        workspace_id="ws-reburn-001"
    )
    assert reburn_doc_id is not None

    # Manually add an image artifact node representing an extracted photo of the smoker water seal
    reburn_kg = rag_adapter.get_knowledge_graph("ws-reburn-001")
    reburn_kg.add_node(
        GraphNode(
            id="reburn_img_seal",
            content=".extracted_assets/reburn/water_seal_weld.jpg",
            node_type="artifact",
            modality="image",
            label="Фото гідрозатвора та швів коптильні ReBurn Pro",
            attributes={"asset_path": ".extracted_assets/reburn/water_seal_weld.jpg"}
        )
    )

    # 3. Cross-workspace retrieval query
    res = rag_adapter.query_dual_level(
        prompt="коптильня гідрозатвор сталь товщина маркетинг",
        mode="hybrid",
        workspace_ids=["global-marketing", "ws-reburn-001"]
    )

    assert "workspace_ids" in res
    assert "global-marketing" in res["workspace_ids"]
    assert "ws-reburn-001" in res["workspace_ids"]
    assert len(res["entities"]) > 0 or len(res["themes"]) > 0

    combined_context = res["combined_context"]
    assert "Cross-Workspace Retrieval" in combined_context
    assert "ws-reburn-001" in combined_context


def test_grounded_marketing_banner_synthesizer(rag_adapter):
    """
    Tests GroundedMarketingBannerSynthesizer generating a 100% grounded banner:
    Combines marketing framework (AIDA) + verified ReBurn technical specs + extracted photo asset.
    """
    # Setup bases
    rag_adapter.ingest_text(
        text="AIDA маркетинг для преміум інструментів та коптилень: акцент на чесний метал та смак.",
        title="marketing_aida",
        workspace_id="global-marketing"
    )
    rag_adapter.ingest_text(
        text="Коптильня ReBurn Pro. Харчова нержавіюча сталь 2 мм. Водяний гідрозатвор без запаху в приміщенні. Робоча температура 20-25°C. Без гіркоти.",
        title="reburn_specs",
        workspace_id="ws-reburn-001"
    )
    reburn_kg = rag_adapter.get_knowledge_graph("ws-reburn-001")
    reburn_kg.add_node(
        GraphNode(
            id="reburn_pro_main_img",
            content=".extracted_assets/reburn/reburn_pro_main.png",
            node_type="artifact",
            modality="image",
            label="Головне фото коптильні ReBurn Pro з гідрозатвором",
            attributes={"asset_path": ".extracted_assets/reburn/reburn_pro_main.png"}
        )
    )

    synthesizer = GroundedMarketingBannerSynthesizer(rag_adapter=rag_adapter)
    banner_spec = synthesizer.synthesize(
        product_name="Коптильня ReBurn Pro",
        marketing_goal="Залучити клієнтів у Facebook: акцент на товщину сталі 2 мм та гідрозатвор",
        target_audience="Любителі справжнього копчення та барбекю",
        framework="AIDA",
        format_type="square_1_1",
        workspace_ids=["global-marketing", "ws-reburn-001"]
    )

    # Assertions on grounded facts
    assert banner_spec.product_name == "Коптильня ReBurn Pro"
    assert banner_spec.framework == "AIDA"
    assert len(banner_spec.bullet_points) >= 3
    assert banner_spec.headline != ""
    assert banner_spec.subheadline != ""
    assert banner_spec.call_to_action != ""

    # Verify SVG markup
    assert "<svg" in banner_spec.svg_markup
    assert "</svg>" in banner_spec.svg_markup
    assert "ReBurn" in banner_spec.svg_markup

    # Verify HTML5 markup
    assert "<div" in banner_spec.html_markup
    assert "button" in banner_spec.html_markup

    # Verify Remotion props
    assert "title" in banner_spec.remotion_props
    assert "bullets" in banner_spec.remotion_props
    assert "cta_text" in banner_spec.remotion_props

    # Verify Canvas node
    assert banner_spec.canvas_node["type"] == "marketing_banner_card"
    assert banner_spec.canvas_node["data"]["product_name"] == "Коптильня ReBurn Pro"

    # Verify extracted asset is referenced
    assert len(banner_spec.referenced_assets) > 0
    assert any(".extracted_assets/reburn" in (a.get("path_or_url") or a.get("path") or "") for a in banner_spec.referenced_assets)


def test_swarm_tool_dnk_generate_marketing_banner():
    """
    Tests the Hermes Swarm tool dnk_generate_marketing_banner.
    """
    raw_res = dnk_generate_marketing_banner(
        product_name="ReBurn Pro Smoker",
        marketing_goal="Facebook campaign for cold smoking craft meats",
        framework="AIDA",
        workspace_ids=["global-marketing", "ws-alpha-001"]
    )
    data = json.loads(raw_res)
    assert data["status"] == "success"
    assert data["product_name"] == "ReBurn Pro Smoker"
    assert data["framework"] == "AIDA"
    assert "<svg" in data["svg_markup"]
    assert "canvas_node" in data


def test_api_endpoint_marketing_banner(test_client):
    """
    Tests the POST /api/v1/rag/marketing-banner FastAPI endpoint.
    """
    payload = {
        "product_name": "Коптильня ReBurn Pro",
        "marketing_goal": "Створити банер для соцмереж про ідеальне холодне копчення",
        "target_audience": "Крафтові кулінари та грилери",
        "framework": "AIDA",
        "workspace_ids": ["global-marketing", "ws-alpha-001"],
        "format": "square_1_1"
    }
    response = test_client.post("/api/v1/rag/marketing-banner", json=payload)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "success"
    assert res_data["product_name"] == "Коптильня ReBurn Pro"
    assert len(res_data["bullet_points"]) >= 3
    assert "<svg" in res_data["svg_markup"]
    assert "remotion_props" in res_data
    assert "canvas_node" in res_data
