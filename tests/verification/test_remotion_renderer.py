# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_remotion_renderer.py"
# purpose: "Unit tests verifying Remotion Headless Video Renderer composition generation and output creation."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import asyncio
import pytest
import sys
from pathlib import Path

HUB_ROOT = Path(__file__).resolve().parent.parent.parent
MVP_PATH = HUB_ROOT
if str(MVP_PATH) not in sys.path:
    sys.path.insert(0, str(MVP_PATH))

from core.video.remotion_renderer import (
    remotion_renderer,
    VideoRenderSpec,
    RenderResult,
)


@pytest.mark.asyncio
async def test_remotion_renderer_composition_harness_and_rendering():
    spec = VideoRenderSpec(
        composition_id="ProductLaunchReel",
        width=1080,
        height=1920,
        fps=30,
        duration_in_frames=150,
        tsx_component_code="export const ProductLaunchReel = () => null;",
        output_filename="test_launch_9_16.mp4",
        props={"title": "DNK Smart Desk", "price": 499},
    )

    # 1. Test harness generation
    harness = remotion_renderer.generate_composition_harness(spec)
    assert 'id="ProductLaunchReel"' in harness
    assert "durationInFrames={150}" in harness
    assert "width={1080}" in harness
    assert "height={1920}" in harness
    assert '"title": "DNK Smart Desk"' in harness

    # 2. Test rendering pipeline
    result = await remotion_renderer.render_video(spec)
    assert isinstance(result, RenderResult)
    assert result.success is True
    assert result.dimensions == "1080x1920"
    assert result.duration_seconds == 5.0
    assert result.file_size_bytes > 0
    assert Path(result.output_path).exists()
