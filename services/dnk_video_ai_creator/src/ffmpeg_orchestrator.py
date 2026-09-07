# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_video_ai_creator/src/ffmpeg_orchestrator.py"
# purpose: "Chunk-based frame rendering orchestrator and secure FFmpeg video stitching."
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

"""
FFmpeg Orchestration Pipeline for dnk_video_ai_creator.
Orchestrates chunk-based rendering, multi-pass frame stitching, audio muxing, and enforces security.
"""

import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from .fps_controller import FPSController
from .headless_renderer import HeadlessRenderer
from .timeline_validator import TimelineValidator
from .video_composition_schema import ClipType, VideoCompositionSchema


@dataclass
class RenderResult:
    """Outcome metadata of a video rendering job."""
    success: bool
    output_path: Optional[str]
    frame_count: int
    duration_seconds: float
    error_message: Optional[str] = None


class FFmpegOrchestrator:
    """Security-hardened FFmpeg video composition orchestrator."""

    def __init__(self, ffmpeg_bin: Optional[str] = None):
        self.ffmpeg_bin = ffmpeg_bin or shutil.which("ffmpeg") or "ffmpeg"

    def is_ffmpeg_available(self) -> bool:
        """Check if FFmpeg executable is reachable in system PATH."""
        return shutil.which(self.ffmpeg_bin) is not None

    def render_composition(
        self,
        composition: VideoCompositionSchema,
        output_file: Path,
        chunk_size: int = 30,
        asset_base_dir: Optional[Path] = None,
    ) -> RenderResult:
        """
        Execute full end-to-end rendering pipeline:
        1. Validate timeline and security boundaries.
        2. Render frame chunks into secure temporary directories.
        3. Stitch frames with FFmpeg using secure argument vectors (zero shell injection).
        4. Mux audio tracks if present.
        """
        # Step 1: Security & Timeline Validation
        val_result = TimelineValidator.validate_composition(composition)
        if not val_result.is_valid:
            return RenderResult(
                success=False,
                output_path=None,
                frame_count=0,
                duration_seconds=0.0,
                error_message=f"Validation failed: {'; '.join(val_result.errors)}",
            )

        if not self.is_ffmpeg_available():
            return RenderResult(
                success=False,
                output_path=None,
                frame_count=0,
                duration_seconds=0.0,
                error_message="FFmpeg binary not found on host system.",
            )

        fps_ctrl = FPSController(fps=composition.fps)
        total_frames = composition.duration_frames
        duration_sec = fps_ctrl.frame_to_seconds(total_frames)

        # Create isolated temporary directory
        with tempfile.TemporaryDirectory(prefix="dnk_video_render_") as tmp_dir_str:
            temp_dir = Path(tmp_dir_str)
            frames_dir = temp_dir / "frames"
            frames_dir.mkdir(parents=True, exist_ok=True)

            renderer = HeadlessRenderer(composition=composition, asset_base_dir=asset_base_dir)

            # Step 2: Chunk-Based Frame Rendering
            chunks = fps_ctrl.get_chunk_intervals(total_frames=total_frames, chunk_size=chunk_size)
            for start_frame, end_frame in chunks:
                renderer.render_chunk(start_frame=start_frame, end_frame=end_frame, output_dir=frames_dir)

            # Step 3: Check for Audio Clips
            audio_clips = []
            for track in composition.tracks:
                for clip in track.clips:
                    if clip.clip_type == ClipType.AUDIO and clip.src:
                        audio_clips.append(clip)

            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Step 4: Build FFmpeg Argument Vector (strictly as a list, NEVER shell=True)
            frame_pattern = str(frames_dir / "frame_%06d.png")
            cmd: List[str] = [
                self.ffmpeg_bin,
                "-y",  # overwrite output
                "-framerate",
                str(composition.fps),
                "-i",
                frame_pattern,
            ]

            # Append audio inputs if present
            has_valid_audio = False
            if audio_clips and asset_base_dir:
                audio_src = asset_base_dir / audio_clips[0].src
                if audio_src.exists():
                    cmd.extend(["-i", str(audio_src)])
                    has_valid_audio = True

            # Video encoding parameters
            cmd.extend([
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-pix_fmt",
                "yuv420p",
                "-r",
                str(composition.fps),
            ])

            if has_valid_audio:
                cmd.extend(["-c:a", "aac", "-b:a", "192k", "-shortest"])
            else:
                cmd.append("-an")

            cmd.extend(["-movflags", "+faststart", str(output_file)])

            # Execute subprocess safely
            try:
                proc = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=300,
                    check=False,
                )
                if proc.returncode != 0:
                    return RenderResult(
                        success=False,
                        output_path=None,
                        frame_count=total_frames,
                        duration_seconds=duration_sec,
                        error_message=f"FFmpeg failed with exit code {proc.returncode}: {proc.stderr[:500]}",
                    )
            except subprocess.TimeoutExpired:
                return RenderResult(
                    success=False,
                    output_path=None,
                    frame_count=total_frames,
                    duration_seconds=duration_sec,
                    error_message="FFmpeg execution timed out (limit: 300s).",
                )
            except Exception as exc:
                return RenderResult(
                    success=False,
                    output_path=None,
                    frame_count=total_frames,
                    duration_seconds=duration_sec,
                    error_message=f"Subprocess execution error: {str(exc)}",
                )

        return RenderResult(
            success=True,
            output_path=str(output_file),
            frame_count=total_frames,
            duration_seconds=duration_sec,
            error_message=None,
        )
