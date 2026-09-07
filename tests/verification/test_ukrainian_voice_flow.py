# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_ukrainian_voice_flow.py"
# purpose: "Verification tests for Ukrainian Voice Command Processor, phonetic dialect normalizer & REST API."
# canonical_source: true
# alters_files: []
# triggers_tasks: ["TASK-VOICE-FLOW-001"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym & Gerych Prime"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app
from core.voice.ukrainian_acoustic import UkrainianVoiceProcessor, VoiceCommandIntent


@pytest.fixture
def voice_processor():
    return UkrainianVoiceProcessor()


@pytest.fixture
def client():
    return TestClient(app)


def test_ukrainian_transcript_cleaning_and_phonetics(voice_processor):
    raw = "Герич, будь ласка, подивись на цей лайкхаус і зроби мені рілс"
    cleaned = voice_processor.clean_ukrainian_transcript(raw)
    assert "подивись на цей лейкхаус і зроби мені reels" in cleaned
    assert "герич" not in cleaned.lower()
    assert "будь ласка" not in cleaned.lower()


def test_intent_classification_video(voice_processor):
    cmd = "Слухай, зроби 9:16 відео ролик для інстаграм"
    intent = voice_processor.parse_voice_command(cmd)
    assert intent.target_agent == "dnk_video_ai_creator"
    assert intent.intent_action == "render_remotion_video"
    assert intent.confidence >= 0.90
    assert "dnk_video_ai_creator" in intent.feedback_phrase_ua


def test_intent_classification_lakehouse_bi(voice_processor):
    cmd = "Герич, покажи виручку та продажі за останній тиждень у лейкхаусі"
    intent = voice_processor.parse_voice_command(cmd)
    assert intent.target_agent == "dnk_analytics"
    assert intent.intent_action == "query_lakehouse_analytics"
    assert "DuckDB Lakehouse" in intent.feedback_phrase_ua


def test_intent_classification_canvas_ui(voice_processor):
    cmd = "Ану створи новий екран з карточкою товару"
    intent = voice_processor.parse_voice_command(cmd)
    assert intent.target_agent == "gerych_builder"
    assert intent.intent_action == "generate_canvas_screen"


def test_intent_classification_security_audit(voice_processor):
    cmd = "Перевір безпеку і проведи повний аудит репозиторію"
    intent = voice_processor.parse_voice_command(cmd)
    assert intent.target_agent == "gerych_auditor"
    assert intent.intent_action == "run_adversarial_audit"


def test_voice_api_status_endpoint(client):
    resp = client.get("/api/v1/voice/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "online"
    assert "uk-UA" in data["supported_languages"]
    assert "gerych_prime" in data["target_agents"]


def test_voice_api_parse_command_endpoint(client):
    resp = client.post("/api/v1/voice/parse_command", json={
        "transcript": "Слухай Герич, згенеруй тікток відео для нового товару"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["target_agent"] == "dnk_video_ai_creator"
    assert data["intent_action"] == "render_remotion_video"
    assert data["confidence"] > 0.8


def test_voice_api_transcribe_endpoint(client):
    resp = client.post("/api/v1/voice/transcribe", json={
        "fallback_text": "Герич, перевір тести і запусти аудит безпеки"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["intent"]["target_agent"] == "gerych_auditor"
