# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/sota_assimilation/remotion_framecn.md"
# purpose: "Clean-Room Programmatic Video Engine Architecture, AST DSL Spec & Test Plan (DNK-MEDIA-001)."
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

# 🎬 DNK-MEDIA-001: Programmatic Video Engine Spec & Architecture

## 1. Architecture Overview
The Programmatic Video Engine (`dnk_video_ai_creator`) provides a 100% deterministic, headless video rendering pipeline synthesized clean-room from Remotion & FrameCN primitives.

### Core Component Breakdown:
1. **AST DSL Schema (`video_composition_schema.py`)**: Pydantic v2 schemas defining `VideoCompositionSchema`, `Track`, `Clip`, `Keyframe`, `AnimatedProperty`, and `Transition`.
2. **Easing Functions Engine (`easing_functions.py`)**: Pure mathematical curves for `linear`, `quad`, `cubic`, `cubic_bezier` (Newton-Raphson solved), and `spring` physics (damped harmonic oscillator).
3. **Keyframe Interpolator (`keyframe_interpolator.py`)**: Evaluates animated values at any frame `f` for numbers, 2D/3D vectors, and RGBA hex colors (`#RRGGBB` / `#RRGGBBAA`).
4. **Timeline Security & Validity (`timeline_validator.py`)**: Validates FPS standards (24, 30, 60), clip bounds, keyframe order, and enforces strict security boundaries (zero path traversal, whitelist extensions).

---

## 2. DSL Schema Specification

```json
{
  "id": "comp_promo_001",
  "title": "Shopify Product Promo",
  "width": 1080,
  "height": 1920,
  "fps": 30,
  "duration_frames": 150,
  "background_color": "#0a0a0a",
  "tracks": [
    {
      "id": "track_text",
      "name": "Kinetic Typography",
      "kind": "overlay",
      "clips": [
        {
          "id": "clip_title",
          "clip_type": "text",
          "start_frame": 0,
          "duration_frames": 90,
          "layer": 10,
          "content": "DNK OS Summer Sale",
          "properties": {
            "color": "#ffffff",
            "font_size": 64,
            "x": 540,
            "y": 960
          },
          "animated_properties": {
            "scale": {
              "name": "scale",
              "keyframes": [
                {"frame": 0, "value": 0.5, "easing": "spring", "easing_params": {"stiffness": 180, "damping": 12}},
                {"frame": 30, "value": 1.0, "easing": "linear"}
              ]
            },
            "opacity": {
              "name": "opacity",
              "keyframes": [
                {"frame": 0, "value": 0.0, "easing": "ease_out"},
                {"frame": 15, "value": 1.0, "easing": "linear"}
              ]
            }
          }
        }
      ]
    }
  ],
  "transitions": []
}
```

---

## 3. Test & Verification Plan

| Test Suite | Scope | Target Invariant | Status |
| :--- | :--- | :--- | :--- |
| `test_video_composition_schema_serialization` | Pydantic V2 Model dump / parse | Valid AST JSON roundtrip | ✅ PASS |
| `test_easing_functions` | Bezier, Spring, Quad, Linear | Mathematical accuracy & bounds [0, 1] | ✅ PASS |
| `test_keyframe_interpolator_colors_and_vectors` | Color RGBA & Vector blend | Precise linear & eased interpolation | ✅ PASS |
| `test_keyframe_interpolator_clip_evaluation` | Clip relative frame evaluation | Active bounds & state calculation | ✅ PASS |
| `test_timeline_validator_valid_and_invalid` | Security & FPS boundary checks | Fail-closed path traversal & FPS check | ✅ PASS |
