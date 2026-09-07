# Phase 3: E-commerce & UGC Dynamic Templates Architecture

## Overview
Phase 3 expands the video composition engine with composable dynamic templates (Shopify Product Promo, UGC Vertical Reel) and an extensible `TemplateRegistry`.

## 1. Shopify Product Promo Template (`shopify_product_promo_template.py`)
- **Dimensions & FPS**: 1080x1920 (9:16 vertical), 30 FPS, customizable duration (5–15s).
- **Core Elements**:
  - **Dynamic Title & Badge**: Renders original price with strikethrough, discounted price, and dynamic percentage savings badge ("-25% OFF").
  - **3D Product Zoom & Spin**: Animated keyframes modulating `scale` (1.0 -> 1.15) and Y-offset (`y_offset`) with spring/easing physics (`EASING_IN_OUT_CUBIC`, `SPRING`).
  - **Kinetic CTA**: Animated "SWIPE UP TO BUY" / "SHOP NOW" call-to-action button with opacity pulsing keyframes.
- **Path Security**: All font and product image inputs pass through `validate_resource_path()` to prevent arbitrary file reading and path traversal attacks (`..`).

## 2. UGC Vertical Reel Template (`ugc_vertical_reel_template.py`)
- **Dimensions & Format**: 1080x1920 (9:16 vertical for TikTok, Instagram Reels, Shorts).
- **Core Elements**:
  - **UGC Creator Header**: Avatar badge, creator handle (`@handle`), and verified checkmark.
  - **Kinetic Typography Subtitles**: Automated caption sequence mapping words/phrases to timed kinetic text clips with stroke outlines (`#000000`) and scaling keyframes (`0.9 -> 1.05`).
  - **Scene Transitions**: Built-in support for transition types:
    - `TransitionType.GLITCH`
    - `TransitionType.CROSSFADE`
    - `TransitionType.SLIDE_LEFT`
    - `TransitionType.KINETIC_ZOOM`

## 3. Template Registry (`template_registry.py`)
- **Registry Specification**:
  ```python
  @dataclass
  class TemplateMetadata:
      template_id: str
      name: str
      aspect_ratio: str
      duration_range: Tuple[float, float]
      default_fps: int
      tags: List[str]
      parameters_schema: Dict[str, Any]
  ```
- **Extensible Catalog**: Allows dynamic registration, tag-based filtering (`get_templates_by_tag("e-commerce")`), and factory instantiation (`create_composition(template_id, **kwargs)`).
- **Fail-Closed Guarantees**: Reject unknown template IDs with `KeyError` and invalid parameters with `ValueError`.
