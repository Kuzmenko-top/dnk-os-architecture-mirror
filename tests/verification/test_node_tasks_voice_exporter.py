# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_node_tasks_voice_exporter.py"
# purpose: "Verification tests for Voice AI Audio Synthesis & Remotion 9:16 MP4 Exporter (Slice 1)"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from apps.api.main import app
from apps.api.routers.node_tasks_router import _task_marketing_videos, _task_artifacts
from services.dnk_node_tasks.models import NodeItem, NodeStatus
from services.dnk_node_tasks.persistence import NodeTaskPersistenceManager
from services.dnk_video_ai_creator.voice_synthesizer import VoiceSynthesizer
from services.dnk_video_ai_creator.remotion_exporter import RemotionExporter, _GLOBAL_EXPORT_JOBS


@pytest.fixture
def client(tmp_path):
    """Isolated test client with a fresh temporary persistence store."""
    test_db = str(tmp_path / "test_voice_tasks_graph.json")
    manager = NodeTaskPersistenceManager(data_file_path=test_db)
    NodeTaskPersistenceManager._instance = manager
    _task_marketing_videos.clear()
    _task_artifacts.clear()
    _GLOBAL_EXPORT_JOBS.clear()

    with TestClient(app) as tc:
        yield tc

    NodeTaskPersistenceManager._instance = None
    _task_marketing_videos.clear()
    _task_artifacts.clear()
    _GLOBAL_EXPORT_JOBS.clear()


def test_synthesize_voiceover_creates_valid_audio(tmp_path):
    """Verify that VoiceSynthesizer produces a valid audio artifact and metadata."""
    custom_dir = str(tmp_path / "videos")
    synthesizer = VoiceSynthesizer(output_dir=custom_dir)

    node_id = "node_voice_test_001"
    sample_text = (
        "Welcome to DNK OS automated voice synthesis. "
        "In this update, we deliver seamless 9:16 vertical video exports for all completed coding tasks."
    )
    result = synthesizer.synthesize_voiceover(text=sample_text, node_id=node_id, voice_id="aura-1")

    assert result["status"] == "success"
    assert result["node_id"] == node_id
    assert result["voice_id"] == "aura-1"
    assert result["duration_seconds"] > 0
    assert result["file_size_bytes"] > 0

    audio_path = Path(result["audio_path"])
    assert audio_path.exists()
    assert audio_path.is_file()
    assert audio_path.stat().st_size == result["file_size_bytes"]

    # Test retrieval helper
    resolved_path = synthesizer.get_voiceover_audio_path(node_id)
    assert resolved_path is not None
    assert resolved_path == audio_path

    # Nonexistent node returns None
    assert synthesizer.get_voiceover_audio_path("nonexistent_node_xyz") is None


def test_api_voiceover_audio_streaming(client):
    """Verify API lifecycle: synthesize_voiceover endpoint and voiceover_audio streaming."""
    manager = NodeTaskPersistenceManager.get_instance()
    graph = manager.load_graph()

    node = NodeItem(
        id="task_voice_stream_001",
        title="Live Voice AI Narration",
        description="Integrate automated audio voiceover narration for social video reels.",
        priority="high",
        status=NodeStatus.COMPLETED,
        acceptance_criteria=["Generate MP3 audio file", "Stream audio/mpeg via GET endpoint"],
        target_files=["services/dnk_video_ai_creator/voice_synthesizer.py"],
    )
    graph.nodes[node.id] = node
    manager.save_graph(graph)

    # 1. Synthesize voiceover via API
    resp_synth = client.post(
        f"/api/v3/node_tasks/{node.id}/synthesize_voiceover",
        json={"voice_id": "aura-2", "text_override": "Short promo script for testing streaming audio."},
    )
    assert resp_synth.status_code == 200, resp_synth.text
    data = resp_synth.json()
    assert data["status"] == "success"
    assert data["node_id"] == node.id
    assert data["voice_id"] == "aura-2"
    assert data["duration_seconds"] > 0

    # 2. Stream audio via GET endpoint
    resp_audio = client.get(f"/api/v3/node_tasks/{node.id}/voiceover_audio")
    assert resp_audio.status_code == 200
    assert "audio/mpeg" in resp_audio.headers.get("content-type", "")
    assert len(resp_audio.content) > 0

    # 3. Check 404 for unknown node audio
    resp_404 = client.get("/api/v3/node_tasks/unknown_node_9999/voiceover_audio")
    assert resp_404.status_code == 404


def test_api_export_video_mp4_lifecycle(client):
    """Verify API lifecycle: export_video_mp4 generation and status tracking."""
    manager = NodeTaskPersistenceManager.get_instance()
    graph = manager.load_graph()

    node = NodeItem(
        id="task_video_export_001",
        title="Remotion 9:16 Video Exporter",
        description="Render completed tasks into 9:16 MP4 video format ready for social media publishing.",
        priority="high",
        status=NodeStatus.COMPLETED,
        acceptance_criteria=["Export 1080x1920 30fps MP4", "Provide export status query API"],
        target_files=["services/dnk_video_ai_creator/remotion_exporter.py"],
    )
    graph.nodes[node.id] = node
    manager.save_graph(graph)

    # 1. Trigger export
    resp_export = client.post(
        f"/api/v3/node_tasks/{node.id}/export_video_mp4",
        json={"composition_id": "CustomTestComposition"},
    )
    assert resp_export.status_code == 200, resp_export.text
    export_data = resp_export.json()
    assert export_data["status"] == "completed"
    assert export_data["node_id"] == node.id
    assert export_data["aspect_ratio"] == "9:16"
    assert export_data["width"] == 1080
    assert export_data["height"] == 1920
    assert export_data["fps"] == 30
    assert export_data["duration_frames"] == 480
    assert export_data["duration_seconds"] == 16.0
    assert export_data["file_size_bytes"] > 0

    # 2. Check export status
    resp_status = client.get(f"/api/v3/node_tasks/{node.id}/video_export_status")
    assert resp_status.status_code == 200
    status_data = resp_status.json()
    assert status_data["status"] == "completed"
    assert status_data["node_id"] == node.id
    assert Path(status_data["video_path"]).exists()

    # 3. Nonexistent node handling
    resp_export_404 = client.post("/api/v3/node_tasks/unknown_node_404/export_video_mp4")
    assert resp_export_404.status_code == 404

    resp_status_404 = client.get("/api/v3/node_tasks/unknown_node_404/video_export_status")
    assert resp_status_404.status_code == 404
