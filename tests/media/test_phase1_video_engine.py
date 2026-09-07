# --- DNK-MRH-HEADER ---
# mrh_id: "tests/media/test_phase1_video_engine.py"
# purpose: "Unit tests for DNK-MEDIA-001 Phase 1: AST DSL, Easings, Interpolator, and Validator."
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import pytest
pytest.importorskip("PIL")
from services.dnk_video_ai_creator.src import (
    VideoCompositionSchema,
    Track,
    Clip,
    ClipType,
    Keyframe,
    AnimatedProperty,
    EasingType,
    Transition,
    TransitionType,
    get_easing_function,
    evaluate_easing,
    KeyframeInterpolator,
    TimelineValidator,
)


def test_video_composition_schema_serialization():
    comp = VideoCompositionSchema(
        id="comp_test_001",
        title="Promo Video",
        width=1920,
        height=1080,
        fps=30,
        duration_frames=150,
        tracks=[
            Track(
                id="track_v1",
                name="Main Video",
                kind="video",
                clips=[
                    Clip(
                        id="clip_01",
                        clip_type=ClipType.TEXT,
                        start_frame=0,
                        duration_frames=90,
                        properties={"text": "DNK OS", "color": "#ff0000"},
                        animated_properties={
                            "opacity": AnimatedProperty(
                                name="opacity",
                                keyframes=[
                                    Keyframe(frame=0, value=0.0, easing=EasingType.LINEAR),
                                    Keyframe(frame=30, value=1.0, easing=EasingType.EASE_OUT),
                                ],
                            )
                        },
                    )
                ],
            )
        ],
    )

    data = comp.model_dump()
    assert data["id"] == "comp_test_001"
    assert data["fps"] == 30
    assert len(data["tracks"]) == 1
    assert data["tracks"][0]["clips"][0]["clip_type"] == "text"


def test_easing_functions():
    assert evaluate_easing(EasingType.LINEAR, 0.0) == 0.0
    assert evaluate_easing(EasingType.LINEAR, 0.5) == 0.5
    assert evaluate_easing(EasingType.LINEAR, 1.0) == 1.0

    # Quad ease in
    assert evaluate_easing(EasingType.QUAD_IN, 0.5) == 0.25

    # Bezier
    bez_val = evaluate_easing(EasingType.BEZIER, 0.5, {"x1": 0.25, "y1": 0.1, "x2": 0.25, "y2": 1.0})
    assert 0.0 < bez_val < 1.0

    # Spring
    spring_start = evaluate_easing(EasingType.SPRING, 0.0)
    spring_end = evaluate_easing(EasingType.SPRING, 1.0)
    assert spring_start == 0.0
    assert spring_end == 1.0


def test_keyframe_interpolator_colors_and_vectors():
    # RGBA color interpolation
    mid_color = KeyframeInterpolator.evaluate_animated_property(
        AnimatedProperty(
            name="color",
            keyframes=[
                Keyframe(frame=0, value="#000000", easing=EasingType.LINEAR),
                Keyframe(frame=100, value="#ffffff", easing=EasingType.LINEAR),
            ],
        ),
        relative_frame=50,
    )
    assert mid_color.lower() in ["#808080", "#7f7f7f"]

    # Vector interpolation
    mid_vec = KeyframeInterpolator.evaluate_animated_property(
        AnimatedProperty(
            name="position",
            keyframes=[
                Keyframe(frame=0, value=[0.0, 100.0], easing=EasingType.LINEAR),
                Keyframe(frame=10, value=[100.0, 200.0], easing=EasingType.LINEAR),
            ],
        ),
        relative_frame=5,
    )
    assert mid_vec == [50.0, 150.0]


def test_keyframe_interpolator_clip_evaluation():
    clip = Clip(
        id="clip_anim",
        clip_type=ClipType.CANVAS,
        start_frame=10,
        duration_frames=50,
        properties={"scale": 1.0, "color": "#ff0000"},
        animated_properties={
            "opacity": AnimatedProperty(
                name="opacity",
                keyframes=[
                    Keyframe(frame=0, value=0.0),
                    Keyframe(frame=50, value=1.0),
                ],
            )
        },
    )

    # Before start_frame
    res_before = KeyframeInterpolator.evaluate_clip(clip, absolute_frame=5)
    assert not res_before["active"]

    # At start_frame
    res_start = KeyframeInterpolator.evaluate_clip(clip, absolute_frame=10)
    assert res_start["active"]
    assert res_start["relative_frame"] == 0
    assert res_start["properties"]["opacity"] == 0.0

    # At end of clip
    res_mid = KeyframeInterpolator.evaluate_clip(clip, absolute_frame=35)
    assert res_mid["active"]
    assert res_mid["relative_frame"] == 25
    assert res_mid["properties"]["opacity"] == 0.5


def test_timeline_validator_valid_and_invalid():
    valid_comp = VideoCompositionSchema(
        id="comp_valid",
        fps=30,
        width=1920,
        height=1080,
        duration_frames=100,
        tracks=[
            Track(
                id="t1",
                name="V1",
                clips=[
                    Clip(
                        id="c1",
                        clip_type=ClipType.IMAGE,
                        start_frame=0,
                        duration_frames=50,
                        src="assets/banner.png",
                    )
                ],
            )
        ],
    )
    val_res = TimelineValidator.validate_composition(valid_comp)
    assert val_res.is_valid
    assert len(val_res.errors) == 0

    # Test Path Traversal Violation
    invalid_path_comp = VideoCompositionSchema(
        id="comp_invalid_path",
        fps=30,
        width=1920,
        height=1080,
        duration_frames=100,
        tracks=[
            Track(
                id="t1",
                name="V1",
                clips=[
                    Clip(
                        id="c1",
                        clip_type=ClipType.IMAGE,
                        start_frame=0,
                        duration_frames=50,
                        src="../secret_config.json",
                    )
                ],
            )
        ],
    )
    val_path_res = TimelineValidator.validate_composition(invalid_path_comp)
    assert not val_path_res.is_valid
    assert any("Path traversal" in err for err in val_path_res.errors)

    # Test Invalid FPS Violation
    invalid_fps_comp = VideoCompositionSchema(
        id="comp_invalid_fps",
        fps=25,
        width=1920,
        height=1080,
        duration_frames=100,
    )
    val_fps_res = TimelineValidator.validate_composition(invalid_fps_comp)
    assert not val_fps_res.is_valid
    assert any("Invalid FPS" in err for err in val_fps_res.errors)
