# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_video_ai_creator/remotion_compiler.py"
# purpose: "SOTA Remotion video compiler translating marketing scripts and Canvas storyboards into deterministic Remotion v5 React AST specifications with CanvasRuntimeBridge progress streaming."
# author: "DNK-e.com Maksym"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "2.0.0"
# updated_at: "2026-09-04"
# --- END DNK-MRH-HEADER ---

import json
import re
from typing import Any, Dict, List, Optional, Tuple
from core.canvas_runtime_bridge import CanvasRuntimeBridge
from services.dnk_video_ai_creator.src.video_composition_schema import (
    VideoCompositionSchema,
    Track,
    Clip,
    ClipType,
    AnimatedProperty,
    Keyframe,
    EasingType,
)
from services.dnk_video_ai_creator.src.timeline_validator import TimelineValidator


class RemotionCompiler:
    """
    Compiler engine that converts storyboard + transcription + audio and Canvas storyboards
    into unified Remotion VideoCompositions and high-fidelity React TSX components with
    CanvasRuntimeBridge progress streaming.
    """

    def __init__(self, bridge: Optional[CanvasRuntimeBridge] = None) -> None:
        self.bridge = bridge or CanvasRuntimeBridge()

    def compile_shorts_composition(
        self,
        template_type: str,  # 'ugc', 'asmr', 'product_demo'
        title: str,
        price: float,
        original_price: Optional[float] = None,
        transcription: Optional[Dict[str, Any]] = None,
        voiceover_url: Optional[str] = None,
        background_media: Optional[str] = None,
        username: str = "@dnk_store",
        duration_seconds: float = 10.0,
        fps: int = 30,
    ) -> VideoCompositionSchema:
        """
        Synthesizes a 9:16 vertical VideoCompositionSchema AST.
        Auto-syncs subtitles using WhisperX segment timestamps.
        Integrates optional TTS voiceover.
        """
        total_frames = int(fps * duration_seconds)
        orig_p = original_price or round(price * 1.5, 2)
        discount_pct = int(round((1 - price / orig_p) * 100)) if orig_p > price else 33

        tracks: List[Track] = []

        # 1. Background Video/Image Track
        bg_media = background_media or "assets/ugc/default_bg.jpg"
        # Validate path
        errs = TimelineValidator.validate_resource_path(bg_media)
        if errs:
            bg_media = "assets/ugc/product_review.jpg"  # fallback safe asset

        bg_clip = Clip(
            id="bg_media_clip",
            clip_type=ClipType.IMAGE if bg_media.endswith((".jpg", ".jpeg", ".png", ".webp")) else ClipType.VIDEO,
            start_frame=0,
            duration_frames=total_frames,
            layer=1,
            src=bg_media,
            properties={
                "x": 0,
                "y": 0,
                "width": 1080,
                "height": 1920,
                "opacity": 1.0,
                "object_fit": "cover",
            }
        )
        tracks.append(Track(id="track-bg", name="Background Track", kind="video", clips=[bg_clip]))

        # 2. Template Specific Overlay Layers
        overlay_clips: List[Clip] = []

        if template_type.lower() == "ugc":
            # UGC Avatar & Handle Badge
            overlay_clips.append(
                Clip(
                    id="ugc_header_badge",
                    clip_type=ClipType.TEXT,
                    start_frame=0,
                    duration_frames=total_frames,
                    layer=5,
                    content=f"{username} • Verified Creator ✅",
                    properties={
                        "x": 80,
                        "y": 120,
                        "font_size": 36,
                        "color": "#ffffff",
                        "font_weight": "bold",
                        "text_shadow": "0 2px 8px rgba(0,0,0,0.5)",
                    }
                )
            )
        elif template_type.lower() == "asmr":
            # ASMR Calming Soundwaves and Minimalism
            overlay_clips.append(
                Clip(
                    id="asmr_calm_badge",
                    clip_type=ClipType.TEXT,
                    start_frame=0,
                    duration_frames=total_frames,
                    layer=5,
                    content="🎧 Turn Volume UP — Oddly Satisfying ASMR",
                    properties={
                        "x": 80,
                        "y": 120,
                        "font_size": 32,
                        "color": "#a5f3fc",
                        "font_weight": "semibold",
                        "text_shadow": "0 2px 10px rgba(0,0,0,0.6)",
                    }
                )
            )
        elif template_type.lower() == "product_demo":
            # Urgency & Showcase Badge
            overlay_clips.append(
                Clip(
                    id="demo_sale_badge",
                    clip_type=ClipType.TEXT,
                    start_frame=0,
                    duration_frames=total_frames,
                    layer=5,
                    content=f"⚡ SPECIAL INTRODUCTORY OFFER • {discount_pct}% OFF",
                    properties={
                        "x": 80,
                        "y": 120,
                        "font_size": 36,
                        "color": "#facc15",
                        "font_weight": "black",
                        "text_shadow": "0 4px 12px rgba(251,191,36,0.3)",
                    }
                )
            )

        # Dynamic Subtitles Auto-Sync
        subtitle_clips: List[Clip] = []
        if transcription and ("segments" in transcription or "words" in transcription):
            segments = transcription.get("segments", [])
            for i, seg in enumerate(segments):
                start_sec = seg.get("start", seg.get("start_time", 0.0))
                end_sec = seg.get("end", seg.get("end_time", duration_seconds))
                text = seg.get("text", "")

                start_f = min(int(start_sec * fps), total_frames - 5)
                end_f = min(int(end_sec * fps), total_frames)
                dur_f = max(end_f - start_f, 15)

                # Add subtitle clip with kinetic zoom-in effect
                scale_keyframes = [
                    Keyframe(frame=0, value=0.8, easing=EasingType.SPRING),
                    Keyframe(frame=5, value=1.0, easing=EasingType.LINEAR),
                    Keyframe(frame=dur_f - 5, value=1.0, easing=EasingType.LINEAR),
                    Keyframe(frame=dur_f, value=0.9, easing=EasingType.EASE_OUT),
                ]

                subtitle_clips.append(
                    Clip(
                        id=f"subtitle_{i}",
                        clip_type=ClipType.TEXT,
                        start_frame=start_f,
                        duration_frames=dur_f,
                        layer=10,
                        content=text,
                        properties={
                            "x": 100,
                            "y": 1400,
                            "width": 880,
                            "font_size": 52,
                            "color": "#ffffff",
                            "font_weight": "extrabold",
                            "text_align": "center",
                            "background_fill": "rgba(0,0,0,0.6)",
                            "border_radius": 16,
                            "padding": "16px 24px",
                        },
                        animated_properties={
                            "scale": AnimatedProperty(name="scale", keyframes=scale_keyframes)
                        }
                    )
                )
        else:
            # Fallback subtitles if no transcription is provided
            default_texts = [
                "Wait! Don't scroll past this! 🔥",
                f"Meet the incredible {title}!",
                f"Only ${price} today (was ${orig_p})!",
                "Link in bio to shop now ➔"
            ]
            segment_dur = total_frames // len(default_texts)
            for i, txt in enumerate(default_texts):
                subtitle_clips.append(
                    Clip(
                        id=f"fallback_sub_{i}",
                        clip_type=ClipType.TEXT,
                        start_frame=i * segment_dur,
                        duration_frames=segment_dur,
                        layer=10,
                        content=txt,
                        properties={
                            "x": 100,
                            "y": 1400,
                            "width": 880,
                            "font_size": 52,
                            "color": "#ffffff",
                            "font_weight": "extrabold",
                            "text_align": "center",
                            "background_fill": "rgba(0,0,0,0.65)",
                            "border_radius": 16,
                            "padding": "16px 24px",
                        }
                    )
                )

        overlay_clips.extend(subtitle_clips)

        # Call-To-Action Button (pulsing in the last few seconds)
        cta_start_frame = max(0, total_frames - int(fps * 3.0))
        cta_dur = total_frames - cta_start_frame
        if cta_dur > 0:
            overlay_clips.append(
                Clip(
                    id="cta_overlay_button",
                    clip_type=ClipType.TEXT,
                    start_frame=cta_start_frame,
                    duration_frames=cta_dur,
                    layer=12,
                    content="🛒 ORDER TODAY AND SAVE!",
                    properties={
                        "x": 140,
                        "y": 1650,
                        "width": 800,
                        "font_size": 48,
                        "color": "#000000",
                        "font_weight": "black",
                        "background_fill": "#22c55e",
                        "border_radius": 24,
                        "padding": "24px 32px",
                        "text_align": "center",
                        "box_shadow": "0 10px 30px rgba(34,197,94,0.4)",
                    }
                )
            )

        tracks.append(Track(id="track-overlays", name="Graphics Overlay Track", kind="overlay", clips=overlay_clips))

        # 3. Audio & Voiceover Track
        audio_clips: List[Clip] = []
        if voiceover_url:
            # Validate path
            errs = TimelineValidator.validate_resource_path(voiceover_url)
            if not errs:
                audio_clips.append(
                    Clip(
                        id="voiceover_audio_clip",
                        clip_type=ClipType.AUDIO,
                        start_frame=0,
                        duration_frames=total_frames,
                        src=voiceover_url,
                        volume=1.0,
                    )
                )

        # Background music track (satisfying soundscape for ASMR, high energy for others)
        music_file = "assets/audio/calm_waves.mp3" if template_type.lower() == "asmr" else "assets/audio/viral_phonk.mp3"
        errs = TimelineValidator.validate_resource_path(music_file)
        if not errs:
            audio_clips.append(
                Clip(
                    id="background_music_clip",
                    clip_type=ClipType.AUDIO,
                    start_frame=0,
                    duration_frames=total_frames,
                    src=music_file,
                    volume=0.25 if voiceover_url else 0.6,
                )
            )

        if audio_clips:
            tracks.append(Track(id="track-audio", name="Audio Track", kind="audio", clips=audio_clips))

        # Compile composition schema
        composition = VideoCompositionSchema(
            id=f"shorts_comp_{template_type}_{int(price)}",
            title=f"{template_type.upper()} Shorts: {title}",
            width=1080,
            height=1920,
            fps=fps,
            duration_frames=total_frames,
            background_color="#090d16",
            tracks=tracks,
        )

        return composition

    def compile_canvas_storyboard(
        self,
        node: Dict[str, Any],
        canvas_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        bridge: Optional[CanvasRuntimeBridge] = None,
        emit_events: bool = True,
    ) -> VideoCompositionSchema:
        """
        Compiles a Canvas visual storyboard node into a clean-room Remotion v5 VideoCompositionSchema AST.
        Hydrates timeline sequences using clean-room math (Frame-as-a-Function-of-Time, <Sequence />, and Spring physics)
        per skills/remotion_composition_patterns/SKILL.md, and emits real-time progress events via CanvasRuntimeBridge.
        """
        active_bridge = bridge or self.bridge
        node_id = str(node.get("id") or "node_storyboard")
        data = node.get("data") if isinstance(node.get("data"), dict) else node

        title = str(data.get("title") or node.get("title") or "Canvas Storyboard Video")
        aspect_ratio = str(data.get("aspectRatio") or node.get("aspectRatio") or "9:16")
        duration_seconds = float(data.get("duration") or node.get("duration") or 15.0)
        fps = int(data.get("fps") or node.get("fps") or 30)
        total_frames = max(1, int(round(fps * duration_seconds)))

        if aspect_ratio == "16:9":
            width, height = 1920, 1080
        elif aspect_ratio == "1:1":
            width, height = 1080, 1080
        else:  # 9:16 default
            width, height = 1080, 1920

        raw_scenes = data.get("scenes") or node.get("scenes") or []
        if not raw_scenes:
            raw_scenes = [
                {
                    "id": "scene_0",
                    "timeRange": f"0:00 - 0:{int(duration_seconds):02d}",
                    "visualPrompt": title,
                    "voiceover": title,
                }
            ]

        # 1. Emit compile start event via CanvasRuntimeBridge
        if emit_events and active_bridge:
            active_bridge.publish_node_executed(
                node_id=node_id,
                status="started",
                canvas_id=canvas_id,
                execution_id=execution_id,
                event_type="node.started",
                payload={
                    "step": "compile_start",
                    "title": title,
                    "aspect_ratio": aspect_ratio,
                    "duration_seconds": duration_seconds,
                    "total_frames": total_frames,
                    "fps": fps,
                    "scenes_count": len(raw_scenes),
                },
            )

        def _parse_time_range(tr_val: Any) -> Optional[Tuple[float, float]]:
            if not isinstance(tr_val, str):
                return None
            try:
                parts = tr_val.split("-")
                if len(parts) == 2:
                    def _to_sec(s: str) -> float:
                        s = s.strip()
                        if ":" in s:
                            m_str, s_str = s.split(":")
                            return float(m_str) * 60.0 + float(s_str)
                        return float(s)
                    return _to_sec(parts[0]), _to_sec(parts[1])
            except Exception:
                pass
            return None

        # 2. Hydrate timeline sequences using clean-room math (Sequence, Spring physics, Frame-as-a-Function-of-Time)
        video_clips: List[Clip] = []
        text_clips: List[Clip] = []
        num_scenes = len(raw_scenes)

        for idx, scene in enumerate(raw_scenes):
            parsed_tr = _parse_time_range(scene.get("timeRange"))
            if parsed_tr is not None:
                start_sec, end_sec = parsed_tr
            else:
                start_sec = idx * (duration_seconds / num_scenes)
                end_sec = (idx + 1) * (duration_seconds / num_scenes)

            start_frame = int(round(start_sec * fps))
            end_frame = min(total_frames, int(round(end_sec * fps)))
            duration_frames = max(1, end_frame - start_frame)
            scene_id = str(scene.get("id") or f"scene_{idx}")

            # Spring physics config per SOTA v5 patterns
            spring_config = {
                "stiffness": 180,
                "damping": 12,
                "mass": 0.8,
                "overshootClamping": False,
            }

            media_url = scene.get("mediaUrl") or scene.get("src") or f"assets/storyboard/{scene_id}.jpg"
            is_video = media_url.endswith(".mp4") or media_url.endswith(".webm")

            # Background Visual Clip with Spring Physics scale and Frame-as-a-Function-of-Time opacity
            bg_clip = Clip(
                id=f"clip_bg_{scene_id}",
                clip_type=ClipType.VIDEO if is_video else ClipType.IMAGE,
                start_frame=start_frame,
                duration_frames=duration_frames,
                layer=1,
                content=media_url,
                properties={
                    "x": 0,
                    "y": 0,
                    "width": width,
                    "height": height,
                    "opacity": 1.0,
                    "object_fit": "cover",
                },
                animated_properties={
                    "scale": AnimatedProperty(
                        name="scale",
                        keyframes=[
                            Keyframe(
                                frame=0,
                                value=0.95,
                                easing=EasingType.SPRING,
                                easing_params=spring_config,
                            ),
                            Keyframe(
                                frame=duration_frames,
                                value=1.05,
                                easing=EasingType.LINEAR,
                            ),
                        ],
                    ),
                    "opacity": AnimatedProperty(
                        name="opacity",
                        keyframes=[
                            Keyframe(frame=0, value=0.0, easing=EasingType.LINEAR),
                            Keyframe(frame=min(15, duration_frames), value=1.0, easing=EasingType.LINEAR),
                        ],
                    ),
                },
            )
            video_clips.append(bg_clip)

            # Foreground Voiceover / Title Text Clip
            text_content = scene.get("voiceover") or scene.get("visualPrompt") or ""
            if text_content:
                text_clip = Clip(
                    id=f"clip_txt_{scene_id}",
                    clip_type=ClipType.TEXT,
                    start_frame=start_frame,
                    duration_frames=duration_frames,
                    layer=10,
                    content=text_content,
                    properties={
                        "x": 80,
                        "y": height - 380 if aspect_ratio == "9:16" else height - 220,
                        "width": width - 160,
                        "font_size": 42 if aspect_ratio == "9:16" else 36,
                        "color": "#ffffff",
                        "font_weight": "bold",
                        "background_fill": "rgba(9, 9, 11, 0.8)",
                        "border_radius": 16,
                        "padding": "16px 24px",
                        "text_shadow": "0 2px 10px rgba(0,0,0,0.8)",
                    },
                    animated_properties={
                        "scale": AnimatedProperty(
                            name="scale",
                            keyframes=[
                                Keyframe(
                                    frame=0,
                                    value=0.8,
                                    easing=EasingType.SPRING,
                                    easing_params=spring_config,
                                ),
                                Keyframe(
                                    frame=min(20, duration_frames),
                                    value=1.0,
                                    easing=EasingType.LINEAR,
                                ),
                            ],
                        ),
                        "opacity": AnimatedProperty(
                            name="opacity",
                            keyframes=[
                                Keyframe(frame=0, value=0.0, easing=EasingType.LINEAR),
                                Keyframe(frame=min(12, duration_frames), value=1.0, easing=EasingType.LINEAR),
                            ],
                        ),
                    },
                )
                text_clips.append(text_clip)

            # 3. Emit frame render event per sequence
            if emit_events and active_bridge:
                current_rendered_frame = min(total_frames, start_frame + duration_frames)
                progress_pct = int(round((current_rendered_frame / total_frames) * 100))
                active_bridge.publish_node_executed(
                    node_id=node_id,
                    status="rendering",
                    canvas_id=canvas_id,
                    execution_id=execution_id,
                    event_type="node.progress",
                    payload={
                        "step": "frame_render",
                        "scene_index": idx,
                        "scene_id": scene_id,
                        "current_frame": current_rendered_frame,
                        "total_frames": total_frames,
                        "progress": progress_pct,
                    },
                )

        tracks = [
            Track(id="track_visuals", name="Storyboard Visuals", kind="video", clips=video_clips),
            Track(id="track_typography", name="Kinetic Typography", kind="overlay", clips=text_clips),
        ]

        clean_id = re.sub(r"[^a-zA-Z0-9_]", "_", node_id).lower()
        composition = VideoCompositionSchema(
            id=f"comp_{clean_id}",
            title=title,
            width=width,
            height=height,
            fps=fps,
            duration_frames=total_frames,
            background_color="#09090b",
            tracks=tracks,
        )

        # 4. Emit completion event
        if emit_events and active_bridge:
            active_bridge.publish_node_executed(
                node_id=node_id,
                status="completed",
                canvas_id=canvas_id,
                execution_id=execution_id,
                event_type="node.completed",
                execution_result=f"Compiled Remotion storyboard composition '{composition.id}' with {len(raw_scenes)} sequences.",
                payload={
                    "step": "completed",
                    "composition_id": composition.id,
                    "total_frames": total_frames,
                    "duration_seconds": duration_seconds,
                    "fps": fps,
                    "scenes_count": len(raw_scenes),
                    "progress": 100,
                },
            )

        return composition

    def compile_to_remotion_tsx(self, composition: VideoCompositionSchema) -> str:
        """
        Compiles the programmatic VideoCompositionSchema AST down into clean Remotion React TSX code.
        """
        clips_rendered = []
        audio_rendered = []

        for track in composition.tracks:
            for clip in track.clips:
                if clip.clip_type == ClipType.AUDIO:
                    audio_rendered.append(
                        f'      <Sequence from={{{clip.start_frame}}} durationInFrames={{{clip.duration_frames}}}>\n'
                        f'        <Audio src="{clip.src or ""}" volume={{{clip.volume}}} />\n'
                        f'      </Sequence>'
                    )
                elif clip.clip_type == ClipType.IMAGE:
                    img_styles = []
                    if "scale" in clip.animated_properties:
                        anim = clip.animated_properties["scale"]
                        stiffness = 180
                        damping = 12
                        mass = 0.8
                        if anim.keyframes and anim.keyframes[0].easing_params:
                            params = anim.keyframes[0].easing_params
                            def _clean_num(n: Any) -> Any:
                                try:
                                    fn = float(n)
                                    return int(fn) if fn.is_integer() else fn
                                except Exception:
                                    return n

                            stiffness = _clean_num(stiffness)
                            damping = _clean_num(damping)
                            mass = _clean_num(mass)
                        img_styles.append(f"transform: `scale(${{spring({{ frame, fps, config: {{ damping: {damping}, stiffness: {stiffness}, mass: {mass}, overshootClamping: false }} }})}})`")
                    if "opacity" in clip.animated_properties:
                        img_styles.append("opacity: interpolate(frame, [0, 15], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })")
                    img_style_str = f' style={{{{{", ".join(img_styles)}}}}}' if img_styles else ""

                    clips_rendered.append(
                        f'      <Sequence from={{{clip.start_frame}}} durationInFrames={{{clip.duration_frames}}}>\n'
                        f'        <div className="absolute inset-0 flex items-center justify-center overflow-hidden"{img_style_str}>\n'
                        f'          <img src="{clip.src or ""}" className="w-full h-full object-cover" alt="bg" />\n'
                        f'        </div>\n'
                        f'      </Sequence>'
                    )
                elif clip.clip_type == ClipType.VIDEO:
                    vid_styles = []
                    if "scale" in clip.animated_properties:
                        anim = clip.animated_properties["scale"]
                        stiffness = 180
                        damping = 12
                        mass = 0.8
                        if anim.keyframes and anim.keyframes[0].easing_params:
                            params = anim.keyframes[0].easing_params
                            def _clean_num(n: Any) -> Any:
                                try:
                                    fn = float(n)
                                    return int(fn) if fn.is_integer() else fn
                                except Exception:
                                    return n

                            stiffness = _clean_num(stiffness)
                            damping = _clean_num(damping)
                            mass = _clean_num(mass)
                        vid_styles.append(f"transform: `scale(${{spring({{ frame, fps, config: {{ damping: {damping}, stiffness: {stiffness}, mass: {mass}, overshootClamping: false }} }})}})`")
                    if "opacity" in clip.animated_properties:
                        vid_styles.append("opacity: interpolate(frame, [0, 15], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })")
                    vid_style_str = f' style={{{{{", ".join(vid_styles)}}}}}' if vid_styles else ""

                    clips_rendered.append(
                        f'      <Sequence from={{{clip.start_frame}}} durationInFrames={{{clip.duration_frames}}}>\n'
                        f'        <video src="{clip.src or ""}" className="absolute inset-0 w-full h-full object-cover"{vid_style_str} muted loop autoPlay />\n'
                        f'      </Sequence>'
                    )
                elif clip.clip_type == ClipType.TEXT:
                    props = clip.properties or {}
                    # Build styles string safely
                    styles = {
                        "position": "absolute",
                        "left": f"{props.get('x', 0)}px",
                        "top": f"{props.get('y', 0)}px",
                        "width": f"{props.get('width', 880)}px" if "width" in props else "auto",
                        "color": props.get("color", "#ffffff"),
                        "fontSize": f"{props.get('font_size', 48)}px",
                        "fontWeight": props.get("font_weight", "normal"),
                        "textAlign": props.get("text_align", "left"),
                        "background": props.get("background_fill", "transparent"),
                        "borderRadius": f"{props.get('border_radius', 0)}px",
                        "padding": props.get("padding", "0px"),
                        "boxShadow": props.get("box_shadow", "none"),
                        "textShadow": props.get("text_shadow", "none"),
                    }
                    styles_str = ", ".join([f"{k}: '{v}'" for k, v in styles.items() if v])

                    anim_styles = []
                    if "scale" in clip.animated_properties:
                        anim = clip.animated_properties["scale"]
                        stiffness = 180
                        damping = 12
                        mass = 0.8
                        if anim.keyframes and anim.keyframes[0].easing_params:
                            params = anim.keyframes[0].easing_params
                            def _clean_num(n: Any) -> Any:
                                try:
                                    fn = float(n)
                                    return int(fn) if fn.is_integer() else fn
                                except Exception:
                                    return n

                            stiffness = _clean_num(stiffness)
                            damping = _clean_num(damping)
                            mass = _clean_num(mass)
                        anim_styles.append(f"transform: `scale(${{spring({{ frame, fps, config: {{ damping: {damping}, stiffness: {stiffness}, mass: {mass}, overshootClamping: false }} }})}})`")
                    else:
                        anim_styles.append("transform: `scale(1.0)`")

                    if "opacity" in clip.animated_properties:
                        anim_styles.append("opacity: interpolate(frame, [0, 15], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })")

                    all_styles = f"{styles_str}, {', '.join(anim_styles)}" if styles_str else ", ".join(anim_styles)

                    clips_rendered.append(
                        f'      <Sequence from={{{clip.start_frame}}} durationInFrames={{{clip.duration_frames}}}>\n'
                        f'        <div \n'
                        f'          style={{{{{all_styles}}}}}\n'
                        f'          className="font-sans"\n'
                        f'        >\n'
                        f'          {clip.content or ""}\n'
                        f'        </div>\n'
                        f'      </Sequence>'
                    )

        clips_combined = "\n".join(clips_rendered)
        audio_combined = "\n".join(audio_rendered)

        tsx_code = f"""// --- DNK-MRH-HEADER ---
// mrh_id: "remotion/compositions/{composition.id}.tsx"
// purpose: "Auto-compiled React Remotion Shorts composition (9:16 format)."
// status: "Active"
// version: "1.0.0"
// --- END DNK-MRH-HEADER ---

import React from 'react';
import {{ AbsoluteFill, Sequence, Audio, spring, interpolate, useCurrentFrame, useVideoConfig }} from 'remotion';

export interface ShortsCompositionProps {{
  title?: string;
  price?: number;
}}

export const {composition.id}Composition: React.FC<ShortsCompositionProps> = ({{
  title = "{composition.title}",
  price = {composition.tracks[0].clips[0].properties.get("price", 99.99) if composition.tracks else 99.99}
}}) => {{
  const frame = useCurrentFrame();
  const {{ fps }} = useVideoConfig();

  return (
    <AbsoluteFill className="bg-slate-950 overflow-hidden select-none select-none">
      {{/* Media and Text layers */}}
{clips_combined}

      {{/* Audio layers */}}
{audio_combined}
    </AbsoluteFill>
  );
}};
"""
        return tsx_code


remotion_compiler = RemotionCompiler()
