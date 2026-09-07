# --- DNK-MRH-HEADER ---
# mrh_id: "tests/media/test_video_audit_core.py"
# purpose: "Unit and integration tests for @dnk/video-audit-core multimodal audit orchestrator."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import pytest
import asyncio
from packages.video_audit_core import (
    WhisperXAdapter,
    SceneExtractionWorker,
    OCRWorker,
    AudioFeatureWorker,
    HookRetentionAnalyzer,
    ClaimVerificationEngine,
    VideoAuditOrchestrator
)

@pytest.mark.asyncio
async def test_sub_workers_individually():
    transcriber = WhisperXAdapter()
    scenes = SceneExtractionWorker()
    ocr = OCRWorker()
    audio = AudioFeatureWorker()
    hook = HookRetentionAnalyzer()
    claims = ClaimVerificationEngine()

    # 1. ASR Transcriber
    t_res = await transcriber.transcribe_video("https://tiktok.com/@test/video/123", language="uk")
    assert t_res["success"] is True
    assert "segments" in t_res
    assert len(t_res["segments"]) > 0

    # 2. Scene Extraction
    s_res = await scenes.extract_scenes("https://tiktok.com/@test/video/123")
    assert s_res["success"] is True
    assert "scenes" in s_res
    assert len(s_res["scenes"]) > 0

    # 3. OCR Text Overlay
    o_res = await ocr.extract_screen_text("https://tiktok.com/@test/video/123")
    assert o_res["success"] is True
    assert "detections" in o_res
    assert len(o_res["detections"]) > 0

    # 4. Audio Features
    a_res = await audio.analyze_audio("https://tiktok.com/@test/video/123")
    assert a_res["success"] is True
    assert a_res["tempo_bpm"] == 128
    assert "volume_curve_datapoints" in a_res

    # 5. Hook Analyzer
    h_res = await hook.analyze_hook(t_res, s_res, o_res, a_res)
    assert h_res["success"] is True
    assert h_res["hook_score"] > 80.0
    assert "retention_curve" in h_res

    # 6. Claim Verification
    c_res = await claims.verify_claims(t_res, o_res)
    assert c_res["success"] is True
    assert len(c_res["claims"]) > 0
    assert c_res["claims"][0]["type"] == "observed"

@pytest.mark.asyncio
async def test_orchestrator_full_pipeline():
    orchestrator = VideoAuditOrchestrator()
    result = await orchestrator.execute_full_audit("https://tiktok.com/@test/video/123", language="uk")

    assert result is not None
    assert result["success"] is True
    assert result["video_source"] == "https://tiktok.com/@test/video/123"
    assert "transcription" in result
    assert "scenes" in result
    assert "ocr" in result
    assert "audio" in result
    assert "hook_analysis" in result
    assert "claim_verification" in result
