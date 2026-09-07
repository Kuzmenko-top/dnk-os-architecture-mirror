# --- DNK-MRH-HEADER ---
# mrh_id: "tests/bricks/test_brick_registry.py"
# purpose: "Unit tests for DNK Brick Registry discovery, validation, and dependency resolution DAG."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym & Antigravity Orchestrator"
# --- END DNK-MRH-HEADER ---

import pytest
from pathlib import Path
from core.bricks.registry import DNKBrickRegistry, BrickManifest


def test_load_all_six_bricks():
    registry = DNKBrickRegistry()
    bricks = registry.list_bricks()
    assert len(bricks) == 6, f"Expected 6 bricks, found {len(bricks)}: {[b.id for b in bricks]}"
    
    expected_ids = {
        "brick_01_agentic_brain",
        "brick_02_scones_memory",
        "brick_03_spatial_canvas",
        "brick_04_shopify_engine",
        "brick_05_video_ai",
        "brick_06_web_api_shell",
    }
    assert {b.id for b in bricks} == expected_ids


def test_brick_manifest_fields():
    registry = DNKBrickRegistry()
    brick = registry.get_brick("brick_04_shopify_engine")
    assert brick is not None
    assert brick.name == "Shopify 3.0 Engine & Liquid AST"
    assert brick.category == "ecommerce_engine"
    assert "brick_02_scones_memory" in brick.dependencies.internal
    assert "services/dnk_shopify_builder" in brick.paths
    assert brick.quality_gate is not None
    assert brick.quality_gate.min_coverage == 90


def test_dependency_dag_resolution():
    registry = DNKBrickRegistry()
    
    # Resolving canvas should include scones_memory first
    resolved = registry.resolve_dependencies(["brick_03_spatial_canvas"])
    assert resolved == ["brick_02_scones_memory", "brick_03_spatial_canvas"]

    # Resolving web_api_shell
    resolved_shell = registry.resolve_dependencies(["brick_06_web_api_shell"])
    assert "brick_01_agentic_brain" in resolved_shell
    assert "brick_02_scones_memory" in resolved_shell
    assert resolved_shell[-1] == "brick_06_web_api_shell"


def test_collect_export_paths():
    registry = DNKBrickRegistry()
    paths = registry.collect_export_paths(["brick_04_shopify_engine"])
    assert "services/dnk_shopify_builder" in paths
    assert "core/scones_memory.py" in paths  # from brick_02 dependency


def test_unknown_brick_raises_key_error():
    registry = DNKBrickRegistry()
    with pytest.raises(KeyError):
        registry.resolve_dependencies(["non_existent_brick"])


def test_import_and_validate_all_brick_contracts():
    from core.bricks.brick_01_agentic_brain.contracts.schemas import AgentTaskRequest, AgentTaskResponse
    from core.bricks.brick_02_scones_memory.contracts.schemas import MemoryRecord, ErrorDistillationQuery
    from core.bricks.brick_03_spatial_canvas.contracts.schemas import CanvasNode, CanvasGraphState
    from core.bricks.brick_04_shopify_engine.contracts.schemas import ShopifySection, ShopifyTemplateState
    from core.bricks.brick_05_video_ai.contracts.schemas import VideoScene, VideoRenderJob
    from core.bricks.brick_06_web_api_shell.contracts.schemas import GatewayHealthResponse, APISessionToken

    # Validate instantiation
    t = AgentTaskRequest(task_id="t1", goal="build")
    assert t.task_id == "t1"

    m = MemoryRecord(topic="architecture", content="composite bricks")
    assert m.confidence == 1.0

    c = CanvasGraphState(canvas_id="c1", nodes=[CanvasNode(id="n1", type="card", position={"x": 0, "y": 0})])
    assert len(c.nodes) == 1

    s = ShopifyTemplateState(name="index", sections={"hero": ShopifySection(id="hero", type="hero_banner")})
    assert "hero" in s.sections

    v = VideoRenderJob(job_id="v1", title="Promo", scenes=[VideoScene(scene_id="s1", duration_frames=60)])
    assert len(v.scenes) == 1

    g = GatewayHealthResponse(active_services=["shopify", "canvas"])
    assert g.status == "ok"

