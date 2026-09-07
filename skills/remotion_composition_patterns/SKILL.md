---
name: "remotion_composition_patterns"
description: "Clean-room composition, timing, and physics patterns from Remotion v5 for dnk_video_ai_creator"
version: "1.0.0"
category: "media"
assimilated_at: "2026-09-04"
---

# 🎬 Remotion Composition Patterns (Clean-Room Assimilated)

Assimilated architectural patterns, timeline composition formulas, and motion physics distilled from `remotion-dev/remotion` v5 under **Track 2: Clean-Room Reverse Engineering**.

## ⚖️ 1. Legal & Two-Track Policy
- **Source**: `remotion-dev/remotion` (v5.0.x)
- **License**: Proprietary / Remotion Commercial License
- **Protocol Track**: **Track 2 (Restrictive / Reverse Engineering Synthesis)**
- **Invariant**: No copy-pasting of proprietary code. All patterns are implemented via independent clean-room Python (`core/video/`) and TypeScript (`apps/web/`) modules under permissive MIT.

---

## 📐 2. Core Composition Primitives

### 1. Frame-as-a-Function-of-Time
Every animation and layout property is a pure function of frame $f$:
```typescript
const frame = useCurrentFrame();
const { fps, durationInFrames, width, height } = useVideoConfig();

const opacity = interpolate(frame, [0, 15], [0, 1], {
  extrapolateLeft: "clamp",
  extrapolateRight: "clamp",
});
```

### 2. Relative Timeline Slicing (`<Sequence />`)
Instead of calculating absolute frames for every element, wrap child components in sequences:
```tsx
<Sequence from={30} durationInFrames={60}>
  {/* Inside this sequence, useCurrentFrame() starts at 0 at global frame 30 */}
  <ProductTitle text="Sovereign AI Video" />
</Sequence>
```

### 3. Spring Physics Engine
Natural spring motion without keyframe bloat:
```typescript
const scale = spring({
  frame,
  fps,
  config: {
    damping: 12,    // Controls oscillation decay
    mass: 0.8,      // Weight of layer
    stiffness: 180, // Spring tension
    overshootClamping: false,
  },
});
```

---

## 🛠️ 3. Quick Recipes for `dnk_video_ai_creator`

### Recipe A: Generating a 9:16 Kinetic Story AST
To render a high-converting TikTok/Reels product promo via `core/video/video_composition_schema.py`:
```json
{
  "id": "comp_product_reel_001",
  "title": "Clean-Room Product Reel",
  "width": 1080,
  "height": 1920,
  "fps": 30,
  "duration_frames": 180,
  "background_color": "#09090b",
  "tracks": [
    {
      "id": "track_main_title",
      "name": "Main Kinetic Title",
      "kind": "overlay",
      "clips": [
        {
          "id": "clip_heading",
          "clip_type": "text",
          "start_frame": 15,
          "duration_frames": 90,
          "layer": 10,
          "content": "DNK OS Studio",
          "properties": {
            "color": "#ffffff",
            "font_size": 72,
            "x": 540,
            "y": 960
          },
          "animated_properties": {
            "scale": {
              "name": "scale",
              "keyframes": [
                {"frame": 0, "value": 0.4, "easing": "spring", "easing_params": {"stiffness": 200, "damping": 14}},
                {"frame": 25, "value": 1.0, "easing": "linear"}
              ]
            }
          }
        }
      ]
    }
  ]
}
```

### Recipe B: Invoking RemotionRenderer in Python
```python
from core.video.remotion_renderer import RemotionRenderer, VideoRenderSpec

renderer = RemotionRenderer()
spec = VideoRenderSpec(
    composition_id="CleanRoomReel",
    width=1080,
    height=1920,
    fps=30,
    duration_in_frames=120,
    tsx_component_code="""
    export const CleanRoomReel = () => {
        return <AbsoluteFill style={{backgroundColor: '#000', color: '#fff'}}>Ready</AbsoluteFill>;
    };
    """
)
result = renderer.render_sync(spec)
print(f"Rendered video: {result.output_path} ({result.file_size_bytes} bytes)")
```

---

## 🧪 4. Verification & Quality Gates
- Test suite: `pytest tests/test_video_pipeline.py` or `pytest core/tests/test_timeline_engine.py`
- Verification script: `bash scripts/verify_all.sh`
- Reference spec: `docs/tech/sota_assimilation/remotion_v5_patterns.md`
