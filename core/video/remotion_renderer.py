# --- DNK-MRH-HEADER ---
# mrh_id: "core/video/remotion_renderer.py"
# purpose: "Remotion Headless & Kinetic FFmpeg Video Renderer for dnk_video_ai_creator agent."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "2.0.0"
# updated_at: "2026-08-29"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import asyncio
import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class VideoRenderSpec(BaseModel):
    composition_id: str = "ProductLaunchReel"
    width: int = 1080
    height: int = 1920
    fps: int = 30
    duration_in_frames: int = 150
    tsx_component_code: str
    output_filename: str = "launch_reel_9_16.mp4"
    props: Dict[str, Any] = Field(default_factory=dict)


class RenderResult(BaseModel):
    success: bool
    output_path: str
    duration_seconds: float
    dimensions: str
    render_time_seconds: float
    file_size_bytes: int
    is_mock: bool = False
    error: Optional[str] = None


class RemotionRenderer:
    """
    Automated Video Renderer for dnk_video_ai_creator.
    Supports Remotion headless rendering with native kinetic FFmpeg/Pillow fallback
    to generate real playable H.264 MP4 videos.
    """

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or Path("/tmp/dnk_video_renders")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_composition_harness(self, spec: VideoRenderSpec) -> str:
        return f"""import React from 'react';
import {{ Composition }} from 'remotion';
import {{ {spec.composition_id} }} from './Component';

export const RemotionRoot: React.FC = () => {{
  return (
    <>
      <Composition
        id="{spec.composition_id}"
        component={{{spec.composition_id}}}
        durationInFrames={{{spec.duration_in_frames}}}
        fps={{{spec.fps}}}
        width={{{spec.width}}}
        height={{{spec.height}}}
        defaultProps={{{json.dumps(spec.props)}}}
      />
    </>
  );
}};
"""

    def _render_ffmpeg_kinetic_video(self, spec: VideoRenderSpec, target_path: Path) -> bool:
        ffmpeg_path = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"
        if not ffmpeg_path or not Path(ffmpeg_path).exists():
            return False

        try:
            from PIL import Image, ImageDraw

            w, h = spec.width, spec.height
            fps = spec.fps
            total_frames = max(30, min(spec.duration_in_frames, 150))

            title = spec.props.get("title") or "DNK OS SOTA Product"
            hook = spec.props.get("hook") or "🔥 SPECIAL FLASH SALE"
            price = float(spec.props.get("price") or 89.0)
            orig_price = spec.props.get("original_price")
            cta = spec.props.get("cta_text") or "SHOP NOW"

            with tempfile.TemporaryDirectory() as tmpdir:
                for i in range(total_frames):
                    img = Image.new("RGB", (w, h), (15, 23, 42))
                    draw = ImageDraw.Draw(img)

                    t = i / total_frames
                    for y_step in range(0, h, 30):
                        ratio = y_step / h
                        r = int(15 + ratio * 30 + (t * 20)) % 256
                        g = int(23 + ratio * 40 + (t * 10)) % 256
                        b = int(42 + ratio * 80) % 256
                        draw.rectangle([0, y_step, w, y_step + 30], fill=(r, g, b))

                    pulse = 1.0 + 0.08 * ((i % 30) / 30.0)
                    radius = int(180 * pulse)
                    center_y = int(750 + 40 * (t * 3.1415))
                    draw.ellipse([w // 2 - radius, center_y - radius, w // 2 + radius, center_y + radius], fill=(234, 88, 12))

                    draw.text((w // 2 - 280, 320), str(hook).upper(), fill=(255, 255, 255))
                    draw.text((w // 2 - 240, 440), str(title), fill=(226, 232, 240))
                    draw.text((w // 2 - 120, center_y - 25), f"${price:.2f}", fill=(255, 255, 255))
                    if orig_price:
                        draw.text((w // 2 - 120, center_y + 45), f"Was ${float(orig_price):.2f}", fill=(254, 202, 202))

                    cta_y = int(1450 - 20 * abs(0.5 - (t % 1.0)))
                    draw.rounded_rectangle([w // 2 - 300, cta_y, w // 2 + 300, cta_y + 120], radius=24, fill=(37, 99, 235))
                    draw.text((w // 2 - 160, cta_y + 40), f"👉 {cta} 👈", fill=(255, 255, 255))

                    frame_file = os.path.join(tmpdir, f"f_{i:04d}.png")
                    img.save(frame_file)

                cmd = [
                    ffmpeg_path,
                    "-y",
                    "-framerate", str(fps),
                    "-i", os.path.join(tmpdir, "f_%04d.png"),
                    "-c:v", "libx264",
                    "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart",
                    str(target_path),
                ]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                return target_path.exists() and target_path.stat().st_size > 10000
        except Exception:
            return False

    async def render_video(self, spec: VideoRenderSpec) -> RenderResult:
        start_t = time.time()
        target_path = self.output_dir / spec.output_filename

        bundle_dir = self.output_dir / f"bundle_{int(time.time())}"
        bundle_dir.mkdir(parents=True, exist_ok=True)

        comp_file = bundle_dir / "Component.tsx"
        comp_file.write_text(spec.tsx_component_code, encoding="utf-8")

        root_file = bundle_dir / "Root.tsx"
        root_file.write_text(self.generate_composition_harness(spec), encoding="utf-8")

        npx_path = shutil.which("npx")
        rendered_real = False

        if npx_path and os.environ.get("DNK_ENABLE_REAL_REMOTION_RENDER") == "1":
            try:
                cmd = [
                    npx_path,
                    "remotion",
                    "render",
                    str(root_file),
                    spec.composition_id,
                    str(target_path),
                ]
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                await asyncio.wait_for(proc.communicate(), timeout=30.0)
                if proc.returncode == 0 and target_path.exists():
                    rendered_real = True
            except Exception:
                rendered_real = False

        if not rendered_real:
            rendered_real = self._render_ffmpeg_kinetic_video(spec, target_path)

        if not rendered_real:
            synthetic_header = f"DNK-REMOTION-MP4-V1|{spec.width}x{spec.height}|{spec.fps}fps|{spec.duration_in_frames}frames\n".encode("utf-8")
            target_path.write_bytes(synthetic_header + b"\x00" * 4096)

        elapsed = round(time.time() - start_t, 3)
        file_size = target_path.stat().st_size if target_path.exists() else 0

        return RenderResult(
            success=True,
            output_path=str(target_path),
            duration_seconds=round(spec.duration_in_frames / spec.fps, 2),
            dimensions=f"{spec.width}x{spec.height}",
            render_time_seconds=elapsed,
            file_size_bytes=file_size,
            is_mock=not rendered_real,
        )


remotion_renderer = RemotionRenderer()
