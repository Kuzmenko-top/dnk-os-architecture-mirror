# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_video_ai_creator/src/ugc_vertical_reel_template.py"
# purpose: "UGC Vertical Reel video template generator (9:16 vertical, 1080x1920, 30fps, TikTok/Reels/Shorts format)."
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
UGC Vertical Reel Video Template for dnk_video_ai_creator.
Produces deterministic 9:16 vertical video AST compositions targeting TikTok, Instagram Reels, and YouTube Shorts:
- User-Generated Content (UGC) header overlay (avatar + handle + verified icon)
- Subtitles with Kinetic Typography (animated opacity & scale keyframes)
- Multi-scene transitions (Glitch, Cross-fade, Slide, Zoom)
- Fail-closed security validation on resource paths
"""

from typing import Any, Dict, List, Optional
from .timeline_validator import TimelineValidator
from .video_composition_schema import (
    AnimatedProperty,
    Clip,
    ClipType,
    EasingType,
    Keyframe,
    Track,
    Transition,
    TransitionType,
    VideoCompositionSchema,
)


def create_ugc_vertical_reel_composition(
    username: str = "@alex_review",
    avatar_src: Optional[str] = "assets/ugc/avatar.png",
    media_src: Optional[str] = "assets/ugc/product_review.jpg",
    subtitles: Optional[List[Dict[str, Any]]] = None,
    cta_text: str = "Link in bio to order!",
    background_color: str = "#000000",
    width: int = 1080,
    height: int = 1920,
    fps: int = 30,
    duration_seconds: float = 10.0,
    transitions: Optional[List[Dict[str, Any]]] = None,
) -> VideoCompositionSchema:
    """
    Build a deterministic VideoCompositionSchema AST for a UGC-style Vertical Reel.

    :param username: Creator handle string (e.g. '@alex_review')
    :param avatar_src: Creator avatar image relative path
    :param media_src: Main UGC background image or video relative path
    :param subtitles: List of dicts specifying timed subtitles [{'start_frame': 0, 'end_frame': 90, 'text': '...'}]
    :param cta_text: Call-to-action string displayed at bottom
    :param background_color: Hex color string for canvas fallback
    :param width: Canvas width (default 1080)
    :param height: Canvas height (default 1920)
    :param fps: Target FPS (must be 24, 30, or 60)
    :param duration_seconds: Total duration in seconds (5.0 to 15.0)
    :param transitions: List of custom transition dicts
    :return: Validated VideoCompositionSchema instance
    :raises ValueError: If parameters or resource paths fail security validation
    """
    # 1. Resource Security Validation
    if avatar_src:
        errs = TimelineValidator.validate_resource_path(avatar_src)
        if errs:
            raise ValueError(f"Invalid avatar_src resource path: {'; '.join(errs)}")

    if media_src:
        errs = TimelineValidator.validate_resource_path(media_src)
        if errs:
            raise ValueError(f"Invalid media_src resource path: {'; '.join(errs)}")

    total_frames = int(fps * duration_seconds)
    if total_frames <= 0:
        raise ValueError(f"Invalid duration_seconds {duration_seconds}. Must result in > 0 frames.")

    # Default Subtitles if not provided
    if subtitles is None:
        subtitles = [
            {"start_frame": 0, "end_frame": int(total_frames * 0.4), "text": "Guys, you won't believe how amazing this is!"},
            {"start_frame": int(total_frames * 0.4), "end_frame": int(total_frames * 0.8), "text": "The quality is 10/10 for this price."},
            {"start_frame": int(total_frames * 0.8), "end_frame": total_frames, "text": "Grab yours before it sells out!"},
        ]

    # 2. Track 1: Background & Media Layer
    bg_canvas = Clip(
        id="ugc_bg_canvas_01",
        clip_type=ClipType.CANVAS,
        start_frame=0,
        duration_frames=total_frames,
        layer=0,
        properties={
            "shape": "rectangle",
            "x": 0,
            "y": 0,
            "width": width,
            "height": height,
            "fill": background_color,
        },
    )

    media_clip = Clip(
        id="ugc_media_01",
        clip_type=ClipType.IMAGE,
        start_frame=0,
        duration_frames=total_frames,
        layer=1,
        src=media_src,
        properties={
            "x": 0,
            "y": 0,
            "width": width,
            "height": height,
            "opacity": 1.0,
        },
        animated_properties={
            "scale": AnimatedProperty(
                name="scale",
                keyframes=[
                    Keyframe(frame=0, value=1.0, easing=EasingType.LINEAR),
                    Keyframe(frame=total_frames - 1, value=1.08, easing=EasingType.EASE_IN_OUT),
                ],
            )
        },
    )

    track_media = Track(
        id="track_ugc_media",
        name="UGC Media",
        kind="video",
        clips=[bg_canvas, media_clip],
    )

    # 3. Track 2: UGC Profile Header Overlay (Avatar + Username + Verified Badge)
    header_bar_y = 120
    avatar_size = 80
    avatar_x = 60

    avatar_clip = Clip(
        id="ugc_avatar_01",
        clip_type=ClipType.IMAGE,
        start_frame=0,
        duration_frames=total_frames,
        layer=2,
        src=avatar_src,
        properties={
            "x": avatar_x,
            "y": header_bar_y,
            "width": avatar_size,
            "height": avatar_size,
            "corner_radius": 40,
        },
    )

    username_clip = Clip(
        id="ugc_username_txt_01",
        clip_type=ClipType.TEXT,
        start_frame=0,
        duration_frames=total_frames,
        layer=3,
        content=username,
        properties={
            "x": avatar_x + avatar_size + 20,
            "y": header_bar_y + 20,
            "font_size": 32,
            "color": "#ffffff",
            "anchor": "lt",
        },
    )

    verified_badge = Clip(
        id="ugc_verified_badge_01",
        clip_type=ClipType.CANVAS,
        start_frame=0,
        duration_frames=total_frames,
        layer=3,
        properties={
            "shape": "circle",
            "x": avatar_x + avatar_size + 200,
            "y": header_bar_y + 24,
            "radius": 12,
            "fill": "#3b82f6",
        },
    )

    track_header = Track(
        id="track_ugc_header",
        name="UGC Creator Header",
        kind="video",
        clips=[avatar_clip, username_clip, verified_badge],
    )

    # 4. Track 3: Subtitles & Kinetic Typography
    subtitle_clips: List[Clip] = []
    for idx, sub in enumerate(subtitles):
        s_start = int(sub.get("start_frame", 0))
        s_end = int(sub.get("end_frame", total_frames))
        s_dur = s_end - s_start
        if s_dur <= 0:
            continue

        sub_txt_clip = Clip(
            id=f"ugc_subtitle_txt_{idx+1:02d}",
            clip_type=ClipType.TEXT,
            start_frame=s_start,
            duration_frames=s_dur,
            layer=4,
            content=sub.get("text", ""),
            properties={
                "x": width // 2,
                "y": 1400,
                "font_size": 42,
                "color": "#facc15",  # Yellow kinetic caption style
                "anchor": "mm",
                "stroke_color": "#000000",
                "stroke_width": 4,
            },
            animated_properties={
                "opacity": AnimatedProperty(
                    name="opacity",
                    keyframes=[
                        Keyframe(frame=0, value=0.0, easing=EasingType.EASE_OUT),
                        Keyframe(frame=10, value=1.0, easing=EasingType.EASE_OUT),
                        Keyframe(frame=max(0, s_dur - 10), value=1.0, easing=EasingType.EASE_IN),
                        Keyframe(frame=s_dur - 1, value=0.0, easing=EasingType.EASE_IN),
                    ],
                ),
                "scale": AnimatedProperty(
                    name="scale",
                    keyframes=[
                        Keyframe(frame=0, value=0.85, easing=EasingType.SPRING),
                        Keyframe(frame=10, value=1.0, easing=EasingType.EASE_OUT),
                    ],
                ),
            },
        )
        subtitle_clips.append(sub_txt_clip)

    track_subtitles = Track(
        id="track_ugc_subtitles",
        name="Kinetic Typography Subtitles",
        kind="video",
        clips=subtitle_clips,
    )

    # 5. Track 4: Kinetic Call-To-Action (CTA) Overlay
    cta_bg_clip = Clip(
        id="ugc_cta_bg_01",
        clip_type=ClipType.CANVAS,
        start_frame=int(total_frames * 0.5),
        duration_frames=int(total_frames * 0.5),
        layer=5,
        properties={
            "shape": "rectangle",
            "x": 140,
            "y": 1680,
            "width": 800,
            "height": 90,
            "corner_radius": 20,
            "fill": "#22c55e",
        },
        animated_properties={
            "scale": AnimatedProperty(
                name="scale",
                keyframes=[
                    Keyframe(frame=0, value=0.7, easing=EasingType.SPRING),
                    Keyframe(frame=15, value=1.0, easing=EasingType.EASE_OUT),
                ],
            )
        },
    )

    cta_txt_clip = Clip(
        id="ugc_cta_txt_01",
        clip_type=ClipType.TEXT,
        start_frame=int(total_frames * 0.5),
        duration_frames=int(total_frames * 0.5),
        layer=6,
        content=cta_text.upper(),
        properties={
            "x": width // 2,
            "y": 1725,
            "font_size": 34,
            "color": "#ffffff",
            "anchor": "mm",
        },
    )

    track_cta = Track(
        id="track_ugc_cta",
        name="UGC CTA",
        kind="video",
        clips=[cta_bg_clip, cta_txt_clip],
    )

    # 6. Transitions List
    comp_transitions: List[Transition] = []
    if transitions:
        for t_idx, tr in enumerate(transitions):
            comp_transitions.append(
                Transition(
                    id=tr.get("id", f"trans_ugc_{t_idx+1:02d}"),
                    from_clip_id=tr["from_clip_id"],
                    to_clip_id=tr["to_clip_id"],
                    transition_type=TransitionType(tr.get("type", TransitionType.CROSSFADE)),
                    duration_frames=tr.get("duration_frames", 15),
                )
            )
    else:
        # Default transitions between subtitle clips if multiple present
        if len(subtitle_clips) >= 2:
            comp_transitions.append(
                Transition(
                    id="trans_subtitle_01_02",
                    from_clip_id=subtitle_clips[0].id,
                    to_clip_id=subtitle_clips[1].id,
                    transition_type=TransitionType.CROSSFADE,
                    duration_frames=10,
                )
            )

    comp = VideoCompositionSchema(
        id=f"comp_ugc_reel_{int(duration_seconds)}s",
        title=f"UGC Reel - {username}",
        width=width,
        height=height,
        fps=fps,
        duration_frames=total_frames,
        background_color=background_color,
        tracks=[track_media, track_header, track_subtitles, track_cta],
        transitions=comp_transitions,
        metadata={
            "template": "ugc_vertical_reel",
            "aspect_ratio": "9:16",
            "username": username,
            "subtitles_count": len(subtitle_clips),
        },
    )

    # Validate AST
    val_res = TimelineValidator.validate_composition(comp)
    if not val_res.is_valid:
        raise ValueError(f"Composition validation failed: {'; '.join(val_res.errors)}")

    return comp


class UGCVerticalReelTemplate:
    """Builder class interface for UGC Vertical Reel Video Template."""

    @staticmethod
    def build(params: Optional[Dict[str, Any]] = None) -> VideoCompositionSchema:
        """Instantiate UGC Vertical Reel template using a parameters dictionary."""
        p = params or {}
        return create_ugc_vertical_reel_composition(
            username=p.get("username", "@alex_review"),
            avatar_src=p.get("avatar_src", "assets/ugc/avatar.png"),
            media_src=p.get("media_src", "assets/ugc/product_review.jpg"),
            subtitles=p.get("subtitles", None),
            cta_text=p.get("cta_text", "Link in bio to order!"),
            background_color=p.get("background_color", "#000000"),
            width=p.get("width", 1080),
            height=p.get("height", 1920),
            fps=p.get("fps", 30),
            duration_seconds=p.get("duration_seconds", 10.0),
            transitions=p.get("transitions", None),
        )
