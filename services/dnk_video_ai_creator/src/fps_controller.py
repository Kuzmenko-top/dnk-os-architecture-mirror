# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_video_ai_creator/src/fps_controller.py"
# purpose: "Deterministic FPS Controller, zero-drift timecode conversion & chunk scheduling."
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
FPS Controller for dnk_video_ai_creator.
Ensures sample-accurate timing, zero drift, and deterministic frame chunk partitioning.
"""

from fractions import Fraction
from typing import List, Tuple

ALLOWED_FPS = (24, 30, 60)


class FPSController:
    """Deterministic FPS controller and timing synchronizer."""

    def __init__(self, fps: int = 30):
        if fps not in ALLOWED_FPS:
            raise ValueError(f"Unsupported FPS: {fps}. Must be one of {ALLOWED_FPS}")
        self.fps = fps
        self.timebase = Fraction(1, fps)

    def frame_to_seconds(self, frame: int) -> float:
        """Convert frame number to fractional seconds with zero drift."""
        if frame < 0:
            raise ValueError(f"Frame number must be >= 0, got {frame}")
        return float(Fraction(frame, self.fps))

    def seconds_to_frame(self, seconds: float) -> int:
        """Convert seconds timestamp to discrete frame index."""
        if seconds < 0:
            raise ValueError(f"Seconds must be >= 0, got {seconds}")
        return int(round(seconds * self.fps))

    def frame_to_timecode(self, frame: int) -> str:
        """Format frame number to SMPTE timecode string HH:MM:SS:FF."""
        if frame < 0:
            raise ValueError(f"Frame must be >= 0, got {frame}")
        ff = frame % self.fps
        total_seconds = frame // self.fps
        ss = total_seconds % 60
        total_minutes = total_seconds // 60
        mm = total_minutes % 60
        hh = total_minutes // 60
        return f"{hh:02d}:{mm:02d}:{ss:02d}:{ff:02d}"

    def timecode_to_frame(self, timecode: str) -> int:
        """Parse SMPTE timecode HH:MM:SS:FF to frame number."""
        parts = timecode.strip().split(":")
        if len(parts) != 4:
            raise ValueError(f"Invalid timecode format: '{timecode}'. Expected HH:MM:SS:FF")
        try:
            hh, mm, ss, ff = map(int, parts)
        except ValueError as exc:
            raise ValueError(f"Invalid integer in timecode '{timecode}'") from exc

        if not (0 <= ff < self.fps):
            raise ValueError(f"Frame field {ff} out of range [0, {self.fps - 1}]")
        if not (0 <= ss < 60) or not (0 <= mm < 60) or hh < 0:
            raise ValueError(f"Time field out of range in '{timecode}'")

        total_seconds = hh * 3600 + mm * 60 + ss
        return total_seconds * self.fps + ff

    def get_chunk_intervals(self, total_frames: int, chunk_size: int = 30) -> List[Tuple[int, int]]:
        """
        Split total_frames into deterministic chunks of [start_frame, end_frame] (inclusive).
        Example: total_frames=65, chunk_size=30 -> [(0, 29), (30, 59), (60, 64)]
        """
        if total_frames <= 0:
            return []
        if chunk_size <= 0:
            raise ValueError("chunk_size must be > 0")

        intervals: List[Tuple[int, int]] = []
        for start in range(0, total_frames, chunk_size):
            end = min(start + chunk_size - 1, total_frames - 1)
            intervals.append((start, end))
        return intervals

    def get_pts(self, frame: int, time_scale: int = 1000) -> int:
        """Calculate Presentation Time Stamp (PTS) with target time scale (e.g. milliseconds)."""
        return int(round((frame / self.fps) * time_scale))
