# --- DNK-MRH-HEADER ---
# mrh_id: "tests/rag/test_rag_router_and_tools.py"
# purpose: "Comprehensive test suite for RAG-Anything FastAPI endpoints and Swarm Agent tools."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK Swarm (Gerych Prime)"
# --- END DNK-MRH-HEADER ---

import json
import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from apps.api.routers.rag import get_rag_adapter
from core.adapters.dnk_rag_anything_adapter import DNKRAGAnythingAdapter, RAGConfig
from core.orchestrator.tools.dnk_rag_tool import (
    dnk_rag_query,
    dnk_rag_ingest,
    dnk_rag_sync_scones
)


@pytest.fixture
def test_client():
    # Instantiate isolated adapter
    test_adapter = DNKRAGAnythingAdapter(
        config=RAGConfig(enable_spend_guard=False, workspace_id="ws-test-rag")
    )
    # Pre-populate with sample document and canvas data
    test_adapter.ingest_text(
        text="# Neural Architecture\nDeep Transformer models leverage multi-head self-attention.",
        title="neural_arch",
        metadata={"category": "ai"}
    )
    canvas_payload = {
        "nodes": [
            {
                "id": "node_vlm_1",
                "type": "DocNode",
                "data": {"title": "Vision Transformer", "text": "ViT segments images into patches."}
            },
            {
                "id": "node_vlm_2",
                "type": "ImageNode",
                "data": {"title": "Architecture Diagram", "description": "Diagram illustrating patch projection."}
            }
        ],
        "edges": [
            {"source": "node_vlm_1", "target": "node_vlm_2", "type": "illustrates"}
        ]
    }
    test_adapter.ingest_canvas(canvas_payload, canvas_id="canvas_test")

    # Dependency override
    app.dependency_overrides[get_rag_adapter] = lambda: test_adapter

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_api_ingest_canvas(test_client):
    payload = {
        "nodes": [
            {"id": "c1", "type": "DocNode", "data": {"text": "Diffusion denoising steps."}},
            {"id": "c2", "type": "TableNode", "data": {"title": "Hyperparameters", "rows": [["lr", "1e-4"]]}}
        ],
        "edges": [{"source": "c1", "target": "c2", "type": "contains_table"}],
        "title": "diffusion_specs"
    }
    res = test_client.post("/api/v1/rag/ingest-canvas", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "success"
    assert "doc_id" in data
    assert data["doc_id"].startswith("canvas_")


def test_api_query_dual_level_hybrid(test_client):
    query_payload = {
        "query": "Transformer self-attention",
        "mode": "hybrid",
        "top_k": 3
    }
    res = test_client.post("/api/v1/rag/query-dual-level", json=query_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["mode"] == "hybrid"
    assert data["query"] == "Transformer self-attention"
    assert "primary_matches" in data
    assert "themes" in data
    assert "combined_context" in data
    assert len(data["primary_matches"]) > 0


def test_api_query_dual_level_local_and_global(test_client):
    # Test local mode
    local_res = test_client.post(
        "/api/v1/rag/query-dual-level",
        json={"query": "Vision Transformer patches", "mode": "local", "top_k": 2}
    )
    assert local_res.status_code == 200
    local_data = local_res.json()
    assert local_data["mode"] == "local"
    assert len(local_data["primary_matches"]) > 0

    # Test global mode
    global_res = test_client.post(
        "/api/v1/rag/query-dual-level",
        json={"query": "Neural Architecture", "mode": "global", "top_k": 2}
    )
    assert global_res.status_code == 200
    global_data = global_res.json()
    assert global_data["mode"] == "global"


def test_api_scones_sync(test_client):
    res = test_client.post("/api/v1/rag/scones-sync", json={"workspace_id": "ws-test-rag"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "synced_nodes" in data
    assert data["workspace_id"] == "ws-test-rag"


def test_api_canvas_graph_export(test_client):
    res = test_client.get("/api/v1/rag/canvas-graph")
    assert res.status_code == 200
    data = res.json()
    assert "nodes" in data
    assert "edges" in data
    assert data["node_count"] == len(data["nodes"])
    assert data["edge_count"] == len(data["edges"])
    assert data["node_count"] > 0


def test_swarm_tool_dnk_rag_query():
    # Ingest content first via tool
    ingest_res_str = dnk_rag_ingest(
        content_or_path="# Multi-Agent Swarm\nSpecialized agents cooperate via message bus.",
        title="swarm_architecture"
    )
    ingest_res = json.loads(ingest_res_str)
    assert ingest_res["status"] == "success"
    assert "doc_id" in ingest_res

    # Query via dnk_rag_query tool
    query_res_str = dnk_rag_query(query="Multi-Agent Swarm cooperate", mode="hybrid")
    query_res = json.loads(query_res_str)
    assert query_res["status"] == "success"
    assert query_res["mode"] == "hybrid"
    assert len(query_res["primary_matches"]) > 0
    assert "combined_context" in query_res


def test_swarm_tool_dnk_rag_ingest_canvas():
    canvas_json = json.dumps({
        "nodes": [
            {"id": "tool_node_1", "type": "DocNode", "data": {"text": "Tool pipeline integration."}}
        ],
        "edges": []
    })
    res_str = dnk_rag_ingest(content_or_path=canvas_json, title="canvas_tool_test")
    res = json.loads(res_str)
    assert res["status"] == "success"
    assert res["type"] == "canvas"


def test_swarm_tool_dnk_rag_sync_scones():
    res_str = dnk_rag_sync_scones(workspace_id="ws-test-swarm")
    res = json.loads(res_str)
    assert res["status"] == "success"
    assert "synced_nodes" in res
