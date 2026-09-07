# --- DNK-MRH-HEADER ---
# mrh_id: "tests/test_dnk_agentic_video_adapter.py"
# purpose: "Unit tests for DNKAgenticVideoAdapter (Gemini Agentic Video Understanding in DNK OS)."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "Gerych (Hermes Prime) & Maxim Kuzmenko"
# --- END DNK-MRH-HEADER ---

import pytest
from core.adapters.dnk_agentic_video_adapter import (
    DNKAgenticVideoAdapter,
    ProcessingMode,
    VideoAnalysisResult,
    VideoChapter,
    VideoSegmentRef,
)


@pytest.fixture
def adapter():
    # Enforce mock mode for deterministic CI test execution
    return DNKAgenticVideoAdapter(mock_mode=True)


@pytest.mark.asyncio
async def test_agentic_mode_analysis(adapter):
    result = await adapter.analyze_video(
        video_uri="gs://dnk-media/sample_keynote.mp4",
        prompt="Summarize the core architecture and show timeline steps",
        mode=ProcessingMode.AGENTIC,
    )
    assert isinstance(result, VideoAnalysisResult)
    assert result.processing_mode == ProcessingMode.AGENTIC
    assert result.tokens_consumed < 1000  # Highly token-efficient
    assert len(result.steps_trace) > 0
    assert any(step.step_type == "thought" for step in result.steps_trace)
    assert any(step.step_type == "processing_call" for step in result.steps_trace)


@pytest.mark.asyncio
async def test_static_mode_analysis(adapter):
    result = await adapter.analyze_video(
        video_uri="https://www.youtube.com/watch?v=mock_video",
        prompt="Transcribe every second of this 10-second clip",
        mode=ProcessingMode.STATIC,
    )
    assert isinstance(result, VideoAnalysisResult)
    assert result.processing_mode == ProcessingMode.STATIC
    assert result.tokens_consumed > 5000  # Static 1 FPS consumes significantly more tokens


@pytest.mark.asyncio
async def test_moment_retrieval(adapter):
    moments = await adapter.retrieve_moments(
        video_uri="gs://dnk-media/live_demo.mp4",
        target_description="architecture diagram",
    )
    assert len(moments) > 0
    assert isinstance(moments[0], VideoSegmentRef)
    assert ":" in moments[0].start_timestamp
    assert moments[0].confidence > 0.8


@pytest.mark.asyncio
async def test_smart_chapter_generation(adapter):
    chapters = await adapter.generate_smart_chapters(
        video_uri="https://youtu.be/dnk_tech_talk",
    )
    assert len(chapters) >= 3
    assert isinstance(chapters[0], VideoChapter)
    assert chapters[0].start_time == "00:00"
    assert len(chapters[0].title) > 0
