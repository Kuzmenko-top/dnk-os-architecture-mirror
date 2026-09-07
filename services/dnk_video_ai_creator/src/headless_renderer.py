# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_video_ai_creator/src/headless_renderer.py"
# purpose: "Deterministic Headless Layered Video Frame Renderer using Pillow RGBA rasterization."
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
Headless Layered Frame Renderer for dnk_video_ai_creator.
Renders Text, Shapes, Images, and Overlays onto deterministic RGBA buffers.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
try:
    from PIL import Image, ImageColor, ImageDraw, ImageFont  # type: ignore
except ImportError:
    Image = ImageColor = ImageDraw = ImageFont = None  # type: ignore

from .keyframe_interpolator import KeyframeInterpolator
from .video_composition_schema import Clip, ClipType, VideoCompositionSchema


def parse_color_tuple(color_val: Any, default_alpha: int = 255) -> tuple[int, int, int, int]:
    """Parse color string or tuple into (R, G, B, A) integer tuple."""
    if isinstance(color_val, (tuple, list)) and len(color_val) in (3, 4):
        r, g, b = int(color_val[0]), int(color_val[1]), int(color_val[2])
        a = int(color_val[3]) if len(color_val) == 4 else default_alpha
        return (r, g, b, a)
    if isinstance(color_val, str):
        val = color_val.strip()
        try:
            if val.startswith("#") and len(val) == 9:
                # #RRGGBBAA
                rgb = ImageColor.getrgb(val[:7])
                alpha = int(val[7:9], 16)
                return (rgb[0], rgb[1], rgb[2], alpha)
            rgb = ImageColor.getrgb(val)
            return (rgb[0], rgb[1], rgb[2], default_alpha)
        except Exception:
            return (255, 255, 255, default_alpha)
    return (255, 255, 255, default_alpha)


class HeadlessRenderer:
    """Deterministic headless multi-track layered frame renderer."""

    def __init__(self, composition: VideoCompositionSchema, asset_base_dir: Optional[Path] = None):
        self.composition = composition
        self.asset_base_dir = asset_base_dir or Path(".")

    def _render_text_layer(self, clip: Clip, evaluated_props: Dict[str, Any]) -> Image.Image:
        """Render text clip onto transparent RGBA surface."""
        w, h = self.composition.width, self.composition.height
        layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)

        text = evaluated_props.get("text") or clip.content or ""
        font_size = int(evaluated_props.get("font_size", 48))
        color_str = evaluated_props.get("color", "#ffffff")
        opacity = float(evaluated_props.get("opacity", 1.0))
        opacity = max(0.0, min(1.0, opacity))

        rgba_color = parse_color_tuple(color_str, default_alpha=int(opacity * 255))
        # Modify alpha channel by clip opacity
        final_color = (rgba_color[0], rgba_color[1], rgba_color[2], int(rgba_color[3] * opacity))

        x = int(evaluated_props.get("x", w // 2))
        y = int(evaluated_props.get("y", h // 2))

        # Default Pillow font
        try:
            font = ImageFont.load_default(size=font_size)
        except Exception:
            font = ImageFont.load_default()

        # Anchor center if specified
        anchor = evaluated_props.get("anchor", "mm")
        draw.text((x, y), text, font=font, fill=final_color, anchor=anchor)
        return layer

    def _render_canvas_layer(self, clip: Clip, evaluated_props: Dict[str, Any]) -> Image.Image:
        """Render vector shapes (rectangles, circles, badges) onto transparent RGBA surface."""
        w, h = self.composition.width, self.composition.height
        layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)

        shape_type = evaluated_props.get("shape", "rectangle")
        opacity = float(evaluated_props.get("opacity", 1.0))
        opacity = max(0.0, min(1.0, opacity))
        fill_color = parse_color_tuple(evaluated_props.get("fill", "#3b82f6"), default_alpha=int(opacity * 255))

        x = int(evaluated_props.get("x", 100))
        y = int(evaluated_props.get("y", 100))
        shape_w = int(evaluated_props.get("width", 200))
        shape_h = int(evaluated_props.get("height", 100))

        if shape_type == "circle":
            draw.ellipse([x, y, x + shape_w, y + shape_h], fill=fill_color)
        else:
            radius = int(evaluated_props.get("corner_radius", 0))
            if radius > 0:
                draw.rounded_rectangle([x, y, x + shape_w, y + shape_h], radius=radius, fill=fill_color)
            else:
                draw.rectangle([x, y, x + shape_w, y + shape_h], fill=fill_color)

        return layer

    def _render_image_layer(self, clip: Clip, evaluated_props: Dict[str, Any]) -> Image.Image:
        """Render image asset or fallback placeholder onto transparent RGBA surface."""
        w, h = self.composition.width, self.composition.height
        layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))

        src = clip.src
        img: Optional[Image.Image] = None
        if src:
            full_path = self.asset_base_dir / src
            if full_path.exists():
                try:
                    img = Image.open(full_path).convert("RGBA")
                except Exception:
                    img = None

        target_w = int(evaluated_props.get("width", 400))
        target_h = int(evaluated_props.get("height", 400))
        x = int(evaluated_props.get("x", (w - target_w) // 2))
        y = int(evaluated_props.get("y", (h - target_h) // 2))
        opacity = float(evaluated_props.get("opacity", 1.0))
        opacity = max(0.0, min(1.0, opacity))

        if img is None:
            # Deterministic synthetic placeholder
            img = Image.new("RGBA", (target_w, target_h), (50, 50, 60, int(255 * opacity)))
            draw = ImageDraw.Draw(img)
            draw.rectangle([0, 0, target_w - 1, target_h - 1], outline=(100, 100, 120, 255), width=2)
            draw.text((target_w // 2, target_h // 2), f"Asset: {clip.id}", fill=(200, 200, 200, 255), anchor="mm")
        else:
            img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
            if opacity < 1.0:
                # Adjust alpha channel
                r, g, b, a = img.split()
                a = a.point(lambda p: int(p * opacity))
                img = Image.merge("RGBA", (r, g, b, a))

        layer.paste(img, (x, y), img)
        return layer

    def render_frame(self, frame_idx: int) -> Image.Image:
        """
        Render complete composition at frame_idx into a PIL RGBA Image.
        Composites layers in ascending layer (z-index) order.
        """
        w, h = self.composition.width, self.composition.height
        bg_color = parse_color_tuple(self.composition.background_color)
        base_frame = Image.new("RGBA", (w, h), bg_color)

        # Collect active visual clips
        active_clips: List[Clip] = []
        for track in self.composition.tracks:
            for clip in track.clips:
                if clip.clip_type == ClipType.AUDIO:
                    continue  # Audio handled in FFmpeg orchestrator
                if clip.start_frame <= frame_idx < (clip.start_frame + clip.duration_frames):
                    active_clips.append(clip)

        # Sort clips by layer (z-index)
        active_clips.sort(key=lambda c: c.layer)

        for clip in active_clips:
            eval_state = KeyframeInterpolator.evaluate_clip(clip, frame_idx)
            props = eval_state.get("properties", {})

            layer_img: Optional[Image.Image] = None
            if clip.clip_type == ClipType.TEXT:
                layer_img = self._render_text_layer(clip, props)
            elif clip.clip_type in (ClipType.CANVAS, ClipType.SVG):
                layer_img = self._render_canvas_layer(clip, props)
            elif clip.clip_type in (ClipType.IMAGE, ClipType.VIDEO):
                layer_img = self._render_image_layer(clip, props)

            if layer_img:
                base_frame.alpha_composite(layer_img)

        return base_frame

    def render_chunk(self, start_frame: int, end_frame: int, output_dir: Path) -> List[Path]:
        """
        Render a chunk of frames [start_frame, end_frame] and save them as PNGs.
        Returns list of generated frame file paths.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        rendered_paths: List[Path] = []

        for f_idx in range(start_frame, end_frame + 1):
            frame_img = self.render_frame(f_idx)
            frame_filename = f"frame_{f_idx:06d}.png"
            frame_path = output_dir / frame_filename
            frame_img.save(frame_path, format="PNG")
            rendered_paths.append(frame_path)

        return rendered_paths
