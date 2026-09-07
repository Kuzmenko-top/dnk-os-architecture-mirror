# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_remotion_compiler.py"
# purpose: "Unit tests for RemotionCompiler template generation, subtitles sync, and TSX compiling."
# author: "DNK-e.com Maksym"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import pytest
from services.dnk_video_ai_creator.remotion_compiler import remotion_compiler


def test_compile_shorts_ugc():
    comp = remotion_compiler.compile_shorts_composition(
        template_type="ugc",
        title="DNK Cyber Hoodie",
        price=89.99,
        original_price=120.00,
        transcription={
            "segments": [
                {"start": 0.0, "end": 2.5, "text": "This hoodie is insane!"},
                {"start": 2.5, "end": 6.0, "text": "Super high quality material."},
            ]
        },
        username="@cyber_wear"
    )

    assert comp.id.startswith("shorts_comp_ugc_")
    assert comp.width == 1080
    assert comp.height == 1920
    assert len(comp.tracks) >= 2  # Background + Overlay tracks
    
    # Assert subtitles synced correctly
    overlay_track = next(t for t in comp.tracks if t.id == "track-overlays")
    subtitles = [c for c in overlay_track.clips if c.id.startswith("subtitle_")]
    assert len(subtitles) == 2
    assert subtitles[0].content == "This hoodie is insane!"
    assert subtitles[1].content == "Super high quality material."


def test_compile_shorts_asmr():
    comp = remotion_compiler.compile_shorts_composition(
        template_type="asmr",
        title="Satisfying Kinetic Sand",
        price=19.99,
    )
    assert comp.id.startswith("shorts_comp_asmr_")
    
    # Assert ASMR audio asset set
    audio_track = next(t for t in comp.tracks if t.id == "track-audio")
    assert any("calm_waves" in clip.src for clip in audio_track.clips if clip.src)


def test_compile_to_remotion_tsx():
    comp = remotion_compiler.compile_shorts_composition(
        template_type="product_demo",
        title="Smart Water Bottle",
        price=49.99,
    )
    tsx = remotion_compiler.compile_to_remotion_tsx(comp)
    assert "ShortsCompositionProps" in tsx
    assert comp.id in tsx
    assert "AbsoluteFill" in tsx
    assert "spring" in tsx
    assert "interpolate" in tsx


def test_compile_canvas_storyboard_with_runtime_bridge():
    from core.canvas_runtime_bridge import CanvasRuntimeBridge
    from services.dnk_video_ai_creator.src.video_composition_schema import EasingType

    bridge = CanvasRuntimeBridge()
    captured_events = []
    original_publish = bridge.publish_node_executed

    def spy_publish(*args, **kwargs):
        ev = original_publish(*args, **kwargs)
        captured_events.append(ev)
        return ev

    bridge.publish_node_executed = spy_publish

    canvas_node = {
        "id": "node_storyboard_reburn_001",
        "type": "VideoStoryboardNoteNode",
        "data": {
            "title": "ReBurn Titanium Cocktail Smoker",
            "aspectRatio": "9:16",
            "motionStyle": "Cyberpunk Neon Motion",
            "duration": 9.0,
            "fps": 30,
            "scenes": [
                {
                    "id": "scene_hook",
                    "timeRange": "0:00 - 0:03",
                    "visualPrompt": "Macro shot of CNC-machined titanium smoking chamber emitting dense aromatic smoke.",
                    "voiceover": "Tired of boring cocktails? Upgrade your craft.",
                    "mediaUrl": "https://cdn.dnk.ai/assets/reburn_macro.mp4",
                },
                {
                    "id": "scene_feature",
                    "timeRange": "0:03 - 0:06",
                    "visualPrompt": "Aero-grade mesh filter catching cherrywood embers in 120fps slow-motion.",
                    "voiceover": "Zero soot. Pure flavor. Built for true connoisseurs.",
                    "mediaUrl": "https://cdn.dnk.ai/assets/reburn_smoke.jpg",
                },
                {
                    "id": "scene_cta",
                    "timeRange": "0:06 - 0:09",
                    "visualPrompt": "Luxury matte black gift box opening with smoked old fashioned glass.",
                    "voiceover": "Claim your limited First-Edition batch today.",
                    "mediaUrl": "https://cdn.dnk.ai/assets/reburn_unboxing.jpg",
                },
            ],
        },
    }

    comp = remotion_compiler.compile_canvas_storyboard(
        node=canvas_node,
        canvas_id="canvas_test_123",
        execution_id="exec_test_456",
        bridge=bridge,
        emit_events=True,
    )

    # 1. Composition Dimensions and Meta
    assert comp.id == "comp_node_storyboard_reburn_001"
    assert comp.width == 1080
    assert comp.height == 1920
    assert comp.fps == 30
    assert comp.duration_frames == 270  # 9 seconds * 30 fps

    # 2. Timeline Sequences Hydration
    assert len(comp.tracks) == 2
    visual_track = next(t for t in comp.tracks if t.id == "track_visuals")
    text_track = next(t for t in comp.tracks if t.id == "track_typography")
    assert len(visual_track.clips) == 3
    assert len(text_track.clips) == 3

    # Check Sequence from/duration clean-room math
    first_visual = visual_track.clips[0]
    assert first_visual.start_frame == 0
    assert first_visual.duration_frames == 90
    assert "scale" in first_visual.animated_properties
    scale_anim = first_visual.animated_properties["scale"]
    assert scale_anim.keyframes[0].easing == EasingType.SPRING
    assert scale_anim.keyframes[0].easing_params is not None
    assert scale_anim.keyframes[0].easing_params["stiffness"] == 180
    assert scale_anim.keyframes[0].easing_params["damping"] == 12
    assert scale_anim.keyframes[0].easing_params["mass"] == 0.8

    first_text = text_track.clips[0]
    assert first_text.start_frame == 0
    assert first_text.duration_frames == 90
    assert first_text.content is not None
    assert "Tired of boring cocktails" in first_text.content
    assert "opacity" in first_text.animated_properties

    # 3. CanvasRuntimeBridge WebSocket Stream Event Emission
    assert len(captured_events) >= 5  # 1 start + 3 frame_render + 1 completed
    start_ev = next(e for e in captured_events if e.payload.get("step") == "compile_start")
    assert start_ev.node_id == "node_storyboard_reburn_001"
    assert start_ev.payload["status"] == "started"
    assert start_ev.event_type == "node.started"
    assert start_ev.payload["total_frames"] == 270

    render_events = [e for e in captured_events if e.payload.get("step") == "frame_render"]
    assert len(render_events) == 3
    assert render_events[-1].payload["progress"] == 100
    assert render_events[0].payload["status"] == "rendering"

    completed_ev = next(e for e in captured_events if e.payload.get("step") == "completed")
    assert completed_ev.payload["status"] == "completed"
    assert completed_ev.event_type == "node.completed"
    assert completed_ev.payload["composition_id"] == "comp_node_storyboard_reburn_001"
    assert completed_ev.payload["progress"] == 100

    # 4. TSX Code Generation with Remotion v5 Clean-Room Math
    tsx = remotion_compiler.compile_to_remotion_tsx(comp)
    assert "import { AbsoluteFill, Sequence, Audio, spring, interpolate" in tsx
    assert "<Sequence from={0} durationInFrames={90}>" in tsx
    assert "<Sequence from={90} durationInFrames={90}>" in tsx
    assert "<Sequence from={180} durationInFrames={90}>" in tsx
    assert "spring({ frame, fps, config: { damping: 12, stiffness: 180, mass: 0.8" in tsx
    assert "interpolate(frame, [0, 15], [0, 1]" in tsx


def test_compile_canvas_storyboard_aspect_ratios():
    # 16:9 Landscape
    node_16_9 = {
        "id": "node_16_9",
        "data": {"title": "Landscape Video", "aspectRatio": "16:9", "duration": 5.0, "fps": 24},
    }
    comp_16_9 = remotion_compiler.compile_canvas_storyboard(node_16_9, emit_events=False)
    assert comp_16_9.width == 1920
    assert comp_16_9.height == 1080
    assert comp_16_9.duration_frames == 120

    # 1:1 Square
    node_1_1 = {
        "id": "node_1_1",
        "data": {"title": "Square Video", "aspectRatio": "1:1", "duration": 4.0, "fps": 30},
    }
    comp_1_1 = remotion_compiler.compile_canvas_storyboard(node_1_1, emit_events=False)
    assert comp_1_1.width == 1080
    assert comp_1_1.height == 1080
    assert comp_1_1.duration_frames == 120

