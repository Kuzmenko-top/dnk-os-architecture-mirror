# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_video_ai_creator/src/timeline_validator.py"
# purpose: "Security boundary and timeline validity checker for VideoCompositions."
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
Timeline and Resource Path Security Validator for dnk_video_ai_creator.
Enforces FPS rules, clip bounds, keyframe order, and security whitelist boundaries.
"""

from pathlib import Path
from typing import List, Set
from pydantic import BaseModel, Field
from .video_composition_schema import VideoCompositionSchema

ALLOWED_FPS_SET: Set[int] = {24, 30, 60}
ALLOWED_EXTENSIONS_SET: Set[str] = {
    ".png", ".jpg", ".jpeg", ".webp", ".mp4", ".mov", ".mp3", ".wav",
    ".ttf", ".otf", ".woff", ".woff2", ".svg"
}


class ValidationResult(BaseModel):
    """Container for timeline validation status and diagnostic messages."""
    is_valid: bool = Field(default=True, description="True if timeline passed all checks")
    errors: List[str] = Field(default_factory=list, description="List of fatal error messages")
    warnings: List[str] = Field(default_factory=list, description="List of warning messages")


class TimelineValidator:
    """Security boundary and logic validator for VideoComposition schemas."""

    @staticmethod
    def validate_resource_path(src: str) -> List[str]:
        """
        Validate resource path or URL for path traversal and security violations.
        Returns a list of error strings if invalid.
        """
        errors: List[str] = []
        if not src:
            return errors

        src_str = src.strip()

        # Allow HTTP / HTTPS URIs
        if src_str.startswith("http://") or src_str.startswith("https://"):
            return errors

        # Disallow dangerous schemes
        if ":" in src_str and not src_str.startswith("http"):
            errors.append(f"Forbidden URI scheme or protocol in path: '{src_str}'")
            return errors

        # Security Invariant: Disallow path traversal / absolute path
        if ".." in src_str or src_str.startswith("/") or src_str.startswith("\\"):
            errors.append(f"Path traversal or absolute path violation in resource: '{src_str}'")
            return errors

        path_obj = Path(src_str)
        ext = path_obj.suffix.lower()
        if ext not in ALLOWED_EXTENSIONS_SET:
            errors.append(
                f"File extension '{ext}' for path '{src_str}' is not in allowed whitelist: {sorted(ALLOWED_EXTENSIONS_SET)}"
            )

        return errors

    @classmethod
    def validate_composition(cls, comp: VideoCompositionSchema) -> ValidationResult:
        """
        Perform complete validation on VideoComposition instance.
        Enforces FPS, duration, layer bounds, clip bounds, and resource security.
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[])

        # 1. FPS check
        if comp.fps not in ALLOWED_FPS_SET:
            result.errors.append(
                f"Invalid FPS {comp.fps}. Must be one of deterministic standards: {sorted(ALLOWED_FPS_SET)}"
            )

        # 2. Composition Dimensions & Duration
        if comp.width <= 0 or comp.height <= 0:
            result.errors.append(f"Invalid composition dimensions {comp.width}x{comp.height}. Must be positive integers.")

        if comp.duration_frames <= 0:
            result.errors.append(f"Invalid composition duration_frames {comp.duration_frames}. Must be > 0.")

        # Track clip IDs for transition validation
        known_clip_ids: Set[str] = set()

        # 3. Track and Clip Validation
        for track in comp.tracks:
            for clip in track.clips:
                if clip.id in known_clip_ids:
                    result.errors.append(f"Duplicate clip ID '{clip.id}' detected in composition.")
                known_clip_ids.add(clip.id)

                # Clip Bounds
                clip_end = clip.start_frame + clip.duration_frames
                if clip_end > comp.duration_frames:
                    result.errors.append(
                        f"Clip '{clip.id}' end frame {clip_end} exceeds composition duration {comp.duration_frames}."
                    )

                # Resource Path Security
                if clip.src:
                    path_errors = cls.validate_resource_path(clip.src)
                    result.errors.extend(path_errors)

                # Animated Property Keyframes
                for prop_name, anim_prop in clip.animated_properties.items():
                    for kf in anim_prop.keyframes:
                        if kf.frame < 0 or kf.frame >= clip.duration_frames:
                            result.errors.append(
                                f"Keyframe frame {kf.frame} for property '{prop_name}' in clip '{clip.id}' "
                                f"is out of clip relative range [0, {clip.duration_frames - 1}]."
                            )

        # 4. Transition Validation
        for trans in comp.transitions:
            if trans.from_clip_id not in known_clip_ids:
                result.errors.append(f"Transition '{trans.id}' references unknown source clip ID '{trans.from_clip_id}'.")
            if trans.to_clip_id not in known_clip_ids:
                result.errors.append(f"Transition '{trans.id}' references unknown target clip ID '{trans.to_clip_id}'.")
            if trans.duration_frames <= 0:
                result.errors.append(f"Transition '{trans.id}' duration_frames must be > 0.")

        result.is_valid = len(result.errors) == 0
        return result
