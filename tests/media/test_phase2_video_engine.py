# --- DNK-MRH-HEADER ---
# mrh_id: "tests/media/test_phase2_video_engine.py"
# purpose: "Unit and Integration tests for DNK-MEDIA-001 Phase 2: FPSController, HeadlessRenderer & FFmpegOrchestrator."
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import tempfile
from pathlib import Path
import pytest
pytest.importorskip("PIL")
from PIL import Image

from services.dnk_video_ai_creator.src import (
    AnimatedProperty,
    Clip,
    ClipType,
    EasingType,
    FFmpegOrchestrator,
    FPSController,
    HeadlessRenderer,
    Keyframe,
    Track,
    VideoCompositionSchema,
)


def test_fps_controller_timing_and_timecode():
    fps30 = FPSController(fps=30)
    assert fps30.frame_to_seconds(30) == 1.0
    assert fps30.frame_to_seconds(45) == 1.5
    assert fps30.seconds_to_frame(1.5) == 45

    # SMPTE Timecode
    tc = fps30.frame_to_timecode(75)  # 2 seconds + 15 frames
    assert tc == "00:00:02:15"
    assert fps30.timecode_to_frame("00:00:02:15") == 75

    # Chunk partitioning
    chunks = fps30.get_chunk_intervals(total_frames=65, chunk_size=30)
    assert chunks == [(0, 29), (30, 59), (60, 64)]

    with pytest.raises(ValueError):
        FPSController(fps=45)


def test_headless_renderer_frame_rendering():
    comp = VideoCompositionSchema(
        id="comp_render_test",
        title="Render Test",
        width=320,
        height=240,
        fps=30,
        duration_frames=10,
        background_color="#112233",
        tracks=[
            Track(
                id="track_bg",
                name="Background Shape",
                kind="video",
                clips=[
                    Clip(
                        id="shape_clip",
                        clip_type=ClipType.CANVAS,
                        start_frame=0,
                        duration_frames=10,
                        layer=1,
                        properties={"shape": "rectangle", "x": 10, "y": 10, "width": 100, "height": 50, "fill": "#ff5500"},
                    ),
                    Clip(
                        id="text_clip",
                        clip_type=ClipType.TEXT,
                        start_frame=0,
                        duration_frames=10,
                        layer=2,
                        content="Title",
                        properties={"x": 160, "y": 120, "font_size": 24, "color": "#ffffff", "opacity": 0.8},
                    ),
                ],
            )
        ],
    )

    renderer = HeadlessRenderer(composition=comp)
    img = renderer.render_frame(frame_idx=0)
    assert isinstance(img, Image.Image)
    assert img.size == (320, 240)
    assert img.mode == "RGBA"

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        paths = renderer.render_chunk(start_frame=0, end_frame=4, output_dir=tmp_path)
        assert len(paths) == 5
        for p in paths:
            assert p.exists()
            assert p.stat().st_size > 0


def test_ffmpeg_orchestrator_e2e_render():
    comp = VideoCompositionSchema(
        id="comp_e2e_video",
        title="Short Video Test",
        width=320,
        height=240,
        fps=30,
        duration_frames=15,  # 0.5s
        background_color="#000000",
        tracks=[
            Track(
                id="track_txt",
                name="Title Track",
                kind="video",
                clips=[
                    Clip(
                        id="txt_01",
                        clip_type=ClipType.TEXT,
                        start_frame=0,
                        duration_frames=15,
                        content="DNK OS Engine",
                        properties={"x": 160, "y": 120, "color": "#00ffcc", "font_size": 20},
                    )
                ],
            )
        ],
    )

    orchestrator = FFmpegOrchestrator()
    if not orchestrator.is_ffmpeg_available():
        pytest.skip("FFmpeg is not available in environment")

    with tempfile.TemporaryDirectory() as tmp_dir:
        out_mp4 = Path(tmp_dir) / "output_test.mp4"
        result = orchestrator.render_composition(composition=comp, output_file=out_mp4, chunk_size=10)

        assert result.success, f"Render failed: {result.error_message}"
        assert result.frame_count == 15
        assert result.duration_seconds == 0.5
        assert out_mp4.exists()
        assert out_mp4.stat().st_size > 0
