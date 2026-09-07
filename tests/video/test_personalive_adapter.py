# --- DNK-MRH-HEADER ---
# mrh_id: "tests/video/test_personalive_adapter.py"
# purpose: "Unit and integration tests for DNKPersonaLiveAdapter and PersonaLive API router"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK Swarm & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import pytest
from starlette.testclient import TestClient
from apps.api.main import app
from core.adapters.dnk_personalive_adapter import (
    DNKPersonaLiveAdapter,
    PersonaLiveConfig,
    PersonaLiveRequest,
)


@pytest.fixture
def adapter():
    cfg = PersonaLiveConfig(spendguard_budget_usd=1.0, max_frames_default=50)
    return DNKPersonaLiveAdapter(cfg)


@pytest.fixture
def client():
    return TestClient(app)


def test_adapter_animate_success(adapter):
    req = PersonaLiveRequest(
        reference_image="assets/avatars/portrait_01.png",
        audio_source="assets/audio/speech_01.wav",
        max_frames=60,
        fps=30,
        use_xformers=True,
        stream_gen=True,
    )
    res = adapter.animate_portrait(req)
    assert res.session_id.startswith("pl_")
    assert res.status == "ready"
    assert res.total_frames == 60
    assert res.fps == 30
    assert res.duration_sec == 2.0
    assert "wss://" in res.output_stream_url
    assert res.cost_usd > 0
    assert res.metrics["xformers_enabled"] is True


def test_adapter_path_traversal_guard(adapter):
    req = PersonaLiveRequest(
        reference_image="../../../etc/shadow",
        audio_source="assets/audio/speech.wav",
    )
    with pytest.raises(ValueError, match="Path traversal or absolute path detected"):
        adapter.animate_portrait(req)

    req2 = PersonaLiveRequest(
        reference_image="assets/avatar.png",
        audio_source="/etc/passwd",
    )
    with pytest.raises(ValueError, match="Path traversal or absolute path detected"):
        adapter.animate_portrait(req2)


def test_adapter_spendguard_limit():
    strict_cfg = PersonaLiveConfig(spendguard_budget_usd=0.015)
    strict_adapter = DNKPersonaLiveAdapter(strict_cfg)

    req1 = PersonaLiveRequest(
        reference_image="assets/img1.png",
        audio_source="assets/aud1.wav",
        max_frames=100,
    )
    strict_adapter.animate_portrait(req1)

    req2 = PersonaLiveRequest(
        reference_image="assets/img2.png",
        audio_source="assets/aud2.wav",
        max_frames=100,
    )
    with pytest.raises(RuntimeError, match="SpendGuard ceiling exceeded"):
        strict_adapter.animate_portrait(req2)


@pytest.mark.asyncio
async def test_adapter_async_frame_stream(adapter):
    req = PersonaLiveRequest(
        reference_image="assets/avatar.png",
        audio_source="assets/speech.wav",
        max_frames=5,
        fps=25,
    )
    res = adapter.animate_portrait(req)
    packets = []
    async for packet in adapter.generate_frame_stream(res.session_id):
        packets.append(packet)

    assert len(packets) == 5
    assert packets[0].frame_index == 0
    assert packets[0].is_keyframe is True
    assert packets[4].frame_index == 4


def test_api_animate_and_status(client):
    payload = {
        "reference_image": "uploads/portraits/ceo.jpg",
        "audio_source": "uploads/audio/announcement.mp3",
        "max_frames": 50,
        "fps": 25,
        "use_xformers": True,
        "stream_gen": True,
    }
    response = client.post("/personalive/animate", json=payload)
    if response.status_code == 404:
        response = client.post("/api/v1/personalive/animate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["total_frames"] == 50
    assert data["fps"] == 25
    assert data["duration_sec"] == 2.0

    session_id = data["session_id"]
    status_resp = client.get(f"/personalive/status/{session_id}")
    if status_resp.status_code == 404:
        status_resp = client.get(f"/api/v1/personalive/status/{session_id}")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["session_id"] == session_id
    assert status_data["status"] == "ready"


def test_api_security_path_traversal(client):
    payload = {
        "reference_image": "../../../var/log/secret.png",
        "audio_source": "audio.wav",
    }
    response = client.post("/personalive/animate", json=payload)
    if response.status_code == 404:
        response = client.post("/api/v1/personalive/animate", json=payload)
    assert response.status_code == 400
    assert "Path traversal" in response.json()["detail"]


def test_api_websocket_stream(client):
    payload = {
        "reference_image": "uploads/face.png",
        "audio_source": "uploads/voice.wav",
        "max_frames": 10,
        "fps": 25,
    }
    resp = client.post("/personalive/animate", json=payload)
    if resp.status_code == 404:
        resp = client.post("/api/v1/personalive/animate", json=payload)
    assert resp.status_code == 200
    session_id = resp.json()["session_id"]

    with client.websocket_connect(f"/personalive/stream/{session_id}") as websocket:
        messages = []
        for _ in range(11):
            msg = websocket.receive_json()
            messages.append(msg)

        assert len(messages) == 11
        assert messages[0]["frame_index"] == 0
        assert messages[-1]["event"] == "stream_complete"
