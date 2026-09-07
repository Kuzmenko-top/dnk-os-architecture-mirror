# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_video_ai_creator/src/keyframe_interpolator.py"
# purpose: "Deterministic property interpolation engine supporting numbers, vectors, and RGBA colors."
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
Deterministic Keyframe Interpolator for dnk_video_ai_creator.
Evaluates static and animated clip properties across timeline frames.
"""

import re
from typing import Any, Dict, List, Tuple, Union
from .video_composition_schema import AnimatedProperty, Clip, Keyframe
from .easing_functions import evaluate_easing

HEX_COLOR_REGEX = re.compile(r"^#([0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")


def parse_hex_color(hex_str: str) -> Tuple[int, int, int, int]:
    """Parse hex color string to RGBA tuple (0-255)."""
    hex_str = hex_str.lstrip("#")
    if len(hex_str) == 3:
        r, g, b = (int(c * 2, 16) for c in hex_str)
        return r, g, b, 255
    elif len(hex_str) == 4:
        r, g, b, a = (int(c * 2, 16) for c in hex_str)
        return r, g, b, a
    elif len(hex_str) == 6:
        r = int(hex_str[0:2], 16)
        g = int(hex_str[2:4], 16)
        b = int(hex_str[4:6], 16)
        return r, g, b, 255
    elif len(hex_str) == 8:
        r = int(hex_str[0:2], 16)
        g = int(hex_str[2:4], 16)
        b = int(hex_str[4:6], 16)
        a = int(hex_str[6:8], 16)
        return r, g, b, a
    raise ValueError(f"Invalid hex color format: '{hex_str}'")


def format_hex_color(r: int, g: int, b: int, a: int) -> str:
    """Format RGBA ints (0-255) to hex color string #RRGGBBAA or #RRGGBB."""
    r = max(0, min(255, int(r)))
    g = max(0, min(255, int(g)))
    b = max(0, min(255, int(b)))
    a = max(0, min(255, int(a)))
    if a == 255:
        return f"#{r:02x}{g:02x}{b:02x}"
    return f"#{r:02x}{g:02x}{b:02x}{a:02x}"


def interpolate_value(val_start: Any, val_end: Any, progress: float) -> Any:
    """
    Interpolate between val_start and val_end using float progress in [0, 1].
    Supports numbers, list/tuple of numbers, and hex colors.
    """
    progress = max(0.0, min(1.0, float(progress)))

    # Numeric interpolation
    if isinstance(val_start, (int, float)) and isinstance(val_end, (int, float)):
        res = float(val_start) + (float(val_end) - float(val_start)) * progress
        if isinstance(val_start, int) and isinstance(val_end, int):
            return int(round(res))
        return res

    # List / Vector interpolation
    if isinstance(val_start, (list, tuple)) and isinstance(val_end, (list, tuple)):
        if len(val_start) == len(val_end):
            return [interpolate_value(s, e, progress) for s, e in zip(val_start, val_end)]

    # Hex Color interpolation
    if isinstance(val_start, str) and isinstance(val_end, str):
        if HEX_COLOR_REGEX.match(val_start) and HEX_COLOR_REGEX.match(val_end):
            r1, g1, b1, a1 = parse_hex_color(val_start)
            r2, g2, b2, a2 = parse_hex_color(val_end)
            r = r1 + (r2 - r1) * progress
            g = g1 + (g2 - g1) * progress
            b = b1 + (b2 - b1) * progress
            a = a1 + (a2 - a1) * progress
            return format_hex_color(int(round(r)), int(round(g)), int(round(b)), int(round(a)))

    # Fallback step function for non-numeric/incompatible types
    return val_start if progress < 1.0 else val_end


class KeyframeInterpolator:
    """Evaluates properties of clips and compositions at specific frames."""

    @staticmethod
    def evaluate_animated_property(prop: AnimatedProperty, relative_frame: int) -> Any:
        """
        Evaluate single animated property at relative_frame.
        Keyframes are assumed to be sorted by frame number.
        """
        keyframes = sorted(prop.keyframes, key=lambda k: k.frame)
        if not keyframes:
            raise ValueError(f"AnimatedProperty '{prop.name}' has no keyframes.")

        first_kf = keyframes[0]
        if relative_frame <= first_kf.frame:
            return first_kf.value

        last_kf = keyframes[-1]
        if relative_frame >= last_kf.frame:
            return last_kf.value

        # Locate surrounding keyframe segment
        for i in range(len(keyframes) - 1):
            k_start = keyframes[i]
            k_end = keyframes[i + 1]
            if k_start.frame <= relative_frame <= k_end.frame:
                frame_delta = k_end.frame - k_start.frame
                if frame_delta == 0:
                    return k_end.value

                raw_progress = (relative_frame - k_start.frame) / float(frame_delta)
                eased_progress = evaluate_easing(k_end.easing, raw_progress, k_end.easing_params)
                return interpolate_value(k_start.value, k_end.value, eased_progress)

        return last_kf.value

    @classmethod
    def evaluate_clip(cls, clip: Clip, absolute_frame: int) -> Dict[str, Any]:
        """
        Evaluate full state of clip at absolute_frame.
        Returns state dictionary containing active state, relative frame, progress, and properties.
        """
        end_frame = clip.start_frame + clip.duration_frames
        is_active = clip.start_frame <= absolute_frame < end_frame

        if not is_active:
            return {
                "active": False,
                "relative_frame": 0,
                "progress": 0.0,
                "properties": dict(clip.properties),
            }

        relative_frame = absolute_frame - clip.start_frame
        progress = relative_frame / float(max(1, clip.duration_frames - 1)) if clip.duration_frames > 1 else 1.0

        evaluated_props = dict(clip.properties)
        for name, anim_prop in clip.animated_properties.items():
            evaluated_props[name] = cls.evaluate_animated_property(anim_prop, relative_frame)

        return {
            "active": True,
            "relative_frame": relative_frame,
            "progress": max(0.0, min(1.0, progress)),
            "properties": evaluated_props,
        }
