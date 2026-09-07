# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_node_tasks_video_generator.py"
# purpose: "Verification tests for Node Tasks Remotion Marketing Video Script & Schema Generator"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import os
import pytest
from fastapi.testclient import TestClient
from apps.api.main import app
from apps.api.routers.node_tasks_router import _task_marketing_videos, _task_artifacts
from services.dnk_node_tasks.models import NodeItem, NodeStatus, ExecutionStage
from services.dnk_node_tasks.persistence import NodeTaskPersistenceManager
from services.dnk_video_ai_creator.task_video_synthesizer import (
    TaskVideoSynthesizer,
    MarketingVideoPayload,
)


@pytest.fixture
def client(tmp_path):
    """Isolated test client with a fresh temporary persistence store."""
    test_db = str(tmp_path / "test_tasks_graph.json")
    manager = NodeTaskPersistenceManager(data_file_path=test_db)
    NodeTaskPersistenceManager._instance = manager
    _task_marketing_videos.clear()
    _task_artifacts.clear()

    with TestClient(app) as tc:
        yield tc

    NodeTaskPersistenceManager._instance = None
    _task_marketing_videos.clear()
    _task_artifacts.clear()


def test_synthesizer_unit_structure_and_duration():
    """Verify that TaskVideoSynthesizer generates a valid 4-scene 9:16 vertical video schema with 480 frames."""
    synthesizer = TaskVideoSynthesizer()
    node = NodeItem(
        id="task_feat_001",
        title="Automated Remotion Storyboard Generation",
        description="Users were struggling to convert completed coding tasks into engaging social video updates.",
        priority="high",
        status=NodeStatus.COMPLETED,
        acceptance_criteria=[
            "Synthesize 4-scene vertical video schema",
            "Generate grounded voiceover text with file diff summary",
            "Expose POST and GET endpoints in node_tasks_router"
        ],
        target_files=[
            "services/dnk_video_ai_creator/task_video_synthesizer.py",
            "apps/api/routers/node_tasks_router.py"
        ],
    )

    artifacts = {
        "files": [
            {
                "file_path": "services/dnk_video_ai_creator/task_video_synthesizer.py",
                "status": "created",
                "additions": 180,
                "deletions": 0,
            },
            {
                "file_path": "apps/api/routers/node_tasks_router.py",
                "status": "modified",
                "additions": 45,
                "deletions": 2,
            }
        ],
        "total_files": 2,
        "total_additions": 225,
        "total_deletions": 2,
    }

    result = synthesizer.synthesize_task_marketing_script(
        node_id=node.id,
        node=node,
        artifacts=artifacts,
    )

    assert result["composition_id"] == "comp_task_task_feat_001"
    assert result["aspect_ratio"] == "9:16"
    assert result["duration_in_frames"] == 480
    assert result["fps"] == 30

    scenes = result["scenes"]
    assert len(scenes) == 4

    scene_ids = [s["id"] for s in scenes]
    assert scene_ids == ["scene_hook", "scene_problem", "scene_solution", "scene_cta"]

    durations = [s["duration_frames"] for s in scenes]
    assert durations == [90, 120, 180, 90]
    assert sum(durations) == 480

    for s in scenes:
        assert s["bg_gradient"].startswith("linear-gradient")
        assert s["accent_color"].startswith("#")
        assert len(s["title"]) > 0
        assert len(s["subtitle"]) > 0

    # Grounded diffs
    assert result["grounded_diffs_summary"] == [
        "services/dnk_video_ai_creator/task_video_synthesizer.py",
        "apps/api/routers/node_tasks_router.py",
    ]

    # Voiceover script contains key components
    vo = result["voiceover_script"]
    assert "Automated Remotion Storyboard Generation" in vo
    assert "DNK OS" in vo
    assert "Synthesize 4-scene vertical video schema" in vo or "problem" in vo.lower()


def test_synthesizer_fallback_without_artifacts():
    """Verify synthesizer handles missing or empty artifacts gracefully."""
    synthesizer = TaskVideoSynthesizer()
    node = NodeItem(
        id="task_fallback_002",
        title="Quick Fix For Logging",
        description="Logging dropped stack traces on unhandled exceptions.",
        status=NodeStatus.IN_PROGRESS,
    )

    result = synthesizer.synthesize_task_marketing_script(
        node_id=node.id,
        node=node,
        artifacts=None,
    )

    assert result["composition_id"] == "comp_task_task_fallback_002"
    assert result["duration_in_frames"] == 480
    assert len(result["scenes"]) == 4
    assert isinstance(result["grounded_diffs_summary"], list)
    assert len(result["voiceover_script"]) > 20


def test_api_generate_and_get_marketing_video(client):
    """Verify REST API endpoints POST /generate_marketing_video and GET /marketing_video."""
    # 1. Create a node task first
    create_resp = client.post(
        "/api/v3/node_tasks/node",
        json={
            "id": "node_video_test_100",
            "title": "Build Unified Video Engine",
            "description": "Implement autonomous marketing clip generator for completed tasks.",
            "status": "completed",
            "priority": "high",
            "acceptance_criteria": ["Clean 4-scene timeline", "TTS script ready"],
            "target_files": ["services/dnk_video_ai_creator/engine.py"],
        },
    )
    assert create_resp.status_code == 200

    # 2. POST /api/v3/node_tasks/{node_id}/generate_marketing_video
    gen_resp = client.post("/api/v3/node_tasks/node_video_test_100/generate_marketing_video")
    assert gen_resp.status_code == 200
    gen_data = gen_resp.json()
    assert gen_data["status"] == "success"
    video = gen_data["video"]
    assert video["composition_id"] == "comp_task_node_video_test_100"
    assert video["aspect_ratio"] == "9:16"
    assert video["duration_in_frames"] == 480
    assert video["fps"] == 30
    assert len(video["scenes"]) == 4
    assert "Build Unified Video Engine" in video["voiceover_script"]

    # 3. GET /api/v3/node_tasks/{node_id}/marketing_video (returns cached)
    get_resp = client.get("/api/v3/node_tasks/node_video_test_100/marketing_video")
    assert get_resp.status_code == 200
    get_data = get_resp.json()
    assert get_data["status"] == "success"
    assert get_data["video"]["composition_id"] == "comp_task_node_video_test_100"
    assert get_data["video"]["duration_in_frames"] == 480

    # 4. GET /api/v3/node_tasks/{node_id}/marketing_video on fresh node (lazy synthesis)
    client.post(
        "/api/v3/node_tasks/node",
        json={
            "id": "node_video_lazy_200",
            "title": "Lazy Synthesized Task",
            "description": "Test lazy on-demand generation.",
            "status": "completed",
        },
    )
    # Clear in-memory cache to test lazy synthesis path
    _task_marketing_videos.pop("node_video_lazy_200", None)

    lazy_get = client.get("/api/v3/node_tasks/node_video_lazy_200/marketing_video")
    assert lazy_get.status_code == 200
    assert lazy_get.json()["status"] == "success"
    assert lazy_get.json()["video"]["composition_id"] == "comp_task_node_video_lazy_200"

    # 5. Non-existent node returns 404
    not_found_post = client.post("/api/v3/node_tasks/non_existent_node_xyz/generate_marketing_video")
    assert not_found_post.status_code == 404

    not_found_get = client.get("/api/v3/node_tasks/non_existent_node_xyz/marketing_video")
    assert not_found_get.status_code == 404
