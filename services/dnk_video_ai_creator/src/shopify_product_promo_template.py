# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_video_ai_creator/src/shopify_product_promo_template.py"
# purpose: "Composable Shopify Product Promo video template generator (9:16 vertical, 1080x1920, 30fps, 5-15s)."
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
Shopify Product Promo Video Template for dnk_video_ai_creator.
Produces deterministic, highly-composable video AST compositions featuring:
- Dynamic Title + Price Drop Badge
- Product Images with 3D spin/zoom animated keyframes
- Kinetic Call-To-Action (CTA)
- Fail-closed security validation on resource paths
"""

from typing import Any, Dict, Optional
from .timeline_validator import TimelineValidator
from .video_composition_schema import (
    AnimatedProperty,
    Clip,
    ClipType,
    EasingType,
    Keyframe,
    Track,
    VideoCompositionSchema,
)


def create_product_promo_composition(
    title: str = "DNK Minimalist Hoodie",
    original_price: str = "$120.00",
    promo_price: str = "$89.00",
    badge_text: str = "-25% OFF",
    cta_text: str = "SHOP NOW ON SHOPIFY",
    product_image_src: Optional[str] = "assets/products/hoodie.png",
    background_color: str = "#0f172a",
    width: int = 1080,
    height: int = 1920,
    fps: int = 30,
    duration_seconds: float = 10.0,
    brand_name: str = "DNK OS STORE",
) -> VideoCompositionSchema:
    """
    Build a deterministic VideoCompositionSchema AST for a Shopify Product Promo video.

    :param title: Product title text
    :param original_price: Original price string (e.g. '$120.00')
    :param promo_price: Promo price string (e.g. '$89.00')
    :param badge_text: Price drop badge text (e.g. '-25% OFF')
    :param cta_text: Kinetic Call-To-Action text
    :param product_image_src: Relative file path to product image asset
    :param background_color: Hex color string for video background
    :param width: Canvas width in pixels (default 1080)
    :param height: Canvas height in pixels (default 1920)
    :param fps: Target FPS (must be 24, 30, or 60)
    :param duration_seconds: Duration in seconds (5.0 to 15.0)
    :param brand_name: Brand label displayed at top
    :return: Validated VideoCompositionSchema instance
    :raises ValueError: If parameters or resource paths violate security boundary
    """
    # 1. Fail-closed Resource Security Validation
    if product_image_src:
        path_errs = TimelineValidator.validate_resource_path(product_image_src)
        if path_errs:
            raise ValueError(f"Invalid product_image_src resource path: {'; '.join(path_errs)}")

    total_frames = int(fps * duration_seconds)
    if total_frames <= 0:
        raise ValueError(f"Invalid duration_seconds {duration_seconds}. Must result in > 0 frames.")

    # 2. Track 1: Background & Brand Layer
    bg_clip = Clip(
        id="bg_canvas_01",
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

    brand_text_clip = Clip(
        id="brand_header_txt_01",
        clip_type=ClipType.TEXT,
        start_frame=0,
        duration_frames=total_frames,
        layer=1,
        content=brand_name.upper(),
        properties={
            "x": width // 2,
            "y": 120,
            "font_size": 32,
            "color": "#94a3b8",
            "anchor": "mm",
        },
    )

    track_bg = Track(
        id="track_bg",
        name="Background & Brand",
        kind="video",
        clips=[bg_clip, brand_text_clip],
    )

    # 3. Track 2: Product Image with 3D Spin & Zoom Keyframes
    # Product Image centered in upper-middle area (e.g. y=750)
    img_width = int(width * 0.75)  # 810px
    img_height = int(width * 0.75) # 810px
    center_x = (width - img_width) // 2
    center_y = 350

    product_img_clip = Clip(
        id="product_img_01",
        clip_type=ClipType.IMAGE,
        start_frame=0,
        duration_frames=total_frames,
        layer=2,
        src=product_image_src,
        properties={
            "x": center_x,
            "y": center_y,
            "width": img_width,
            "height": img_height,
            "opacity": 1.0,
        },
        animated_properties={
            "opacity": AnimatedProperty(
                name="opacity",
                keyframes=[
                    Keyframe(frame=0, value=0.0, easing=EasingType.EASE_OUT),
                    Keyframe(frame=15, value=1.0, easing=EasingType.EASE_OUT),
                ],
            ),
            "scale": AnimatedProperty(
                name="scale",
                keyframes=[
                    Keyframe(frame=0, value=0.8, easing=EasingType.SPRING, easing_params={"stiffness": 100, "damping": 10}),
                    Keyframe(frame=30, value=1.05, easing=EasingType.EASE_IN_OUT),
                    Keyframe(frame=total_frames - 15, value=1.0, easing=EasingType.EASE_IN_OUT),
                ],
            ),
            "y_offset": AnimatedProperty(
                name="y_offset",
                keyframes=[
                    Keyframe(frame=0, value=50.0, easing=EasingType.EASE_OUT),
                    Keyframe(frame=30, value=0.0, easing=EasingType.EASE_IN_OUT),
                    Keyframe(frame=int(total_frames * 0.5), value=-15.0, easing=EasingType.EASE_IN_OUT),
                    Keyframe(frame=total_frames - 1, value=0.0, easing=EasingType.EASE_IN_OUT),
                ],
            ),
        },
    )

    track_product = Track(
        id="track_product",
        name="Product Media",
        kind="video",
        clips=[product_img_clip],
    )

    # 4. Track 3: Dynamic Title & Price Drop Badge
    # Product Title Clip
    title_clip = Clip(
        id="product_title_txt_01",
        clip_type=ClipType.TEXT,
        start_frame=10,
        duration_frames=max(1, total_frames - 10),
        layer=3,
        content=title,
        properties={
            "x": width // 2,
            "y": 1220,
            "font_size": 48,
            "color": "#ffffff",
            "anchor": "mm",
        },
        animated_properties={
            "opacity": AnimatedProperty(
                name="opacity",
                keyframes=[
                    Keyframe(frame=0, value=0.0, easing=EasingType.LINEAR),
                    Keyframe(frame=15, value=1.0, easing=EasingType.EASE_OUT),
                ],
            )
        },
    )

    # Price Drop Badge Canvas
    badge_w = 360
    badge_h = 70
    badge_x = (width - badge_w) // 2
    badge_y = 1320

    price_badge_canvas = Clip(
        id="price_badge_bg_01",
        clip_type=ClipType.CANVAS,
        start_frame=20,
        duration_frames=max(1, total_frames - 20),
        layer=3,
        properties={
            "shape": "rectangle",
            "x": badge_x,
            "y": badge_y,
            "width": badge_w,
            "height": badge_h,
            "corner_radius": 16,
            "fill": "#ef4444",
        },
        animated_properties={
            "scale": AnimatedProperty(
                name="scale",
                keyframes=[
                    Keyframe(frame=0, value=0.5, easing=EasingType.SPRING),
                    Keyframe(frame=15, value=1.0, easing=EasingType.EASE_OUT),
                ],
            )
        },
    )

    price_badge_text = Clip(
        id="price_badge_txt_01",
        clip_type=ClipType.TEXT,
        start_frame=20,
        duration_frames=max(1, total_frames - 20),
        layer=4,
        content=f"{badge_text}  {promo_price}",
        properties={
            "x": width // 2,
            "y": badge_y + (badge_h // 2),
            "font_size": 36,
            "color": "#ffffff",
            "anchor": "mm",
        },
    )

    # Original Price Text (Strikethrough display)
    orig_price_text = Clip(
        id="orig_price_txt_01",
        clip_type=ClipType.TEXT,
        start_frame=20,
        duration_frames=max(1, total_frames - 20),
        layer=4,
        content=f"WAS {original_price}",
        properties={
            "x": width // 2,
            "y": badge_y + badge_h + 40,
            "font_size": 28,
            "color": "#64748b",
            "anchor": "mm",
        },
    )

    track_overlay = Track(
        id="track_overlay",
        name="Title & Price Badges",
        kind="video",
        clips=[title_clip, price_badge_canvas, price_badge_text, orig_price_text],
    )

    # 5. Track 4: Kinetic Call-To-Action (CTA)
    cta_w = 720
    cta_h = 100
    cta_x = (width - cta_w) // 2
    cta_y = 1620

    cta_btn_canvas = Clip(
        id="cta_btn_bg_01",
        clip_type=ClipType.CANVAS,
        start_frame=30,
        duration_frames=total_frames - 30,
        layer=5,
        properties={
            "shape": "rectangle",
            "x": cta_x,
            "y": cta_y,
            "width": cta_w,
            "height": cta_h,
            "corner_radius": 24,
            "fill": "#3b82f6",
        },
        animated_properties={
            "scale": AnimatedProperty(
                name="scale",
                keyframes=[
                    Keyframe(frame=0, value=0.8, easing=EasingType.EASE_OUT),
                    Keyframe(frame=15, value=1.0, easing=EasingType.SPRING),
                    Keyframe(frame=45, value=1.05, easing=EasingType.EASE_IN_OUT),
                    Keyframe(frame=75, value=1.0, easing=EasingType.EASE_IN_OUT),
                ],
            )
        },
    )

    cta_btn_text = Clip(
        id="cta_btn_txt_01",
        clip_type=ClipType.TEXT,
        start_frame=30,
        duration_frames=total_frames - 30,
        layer=6,
        content=cta_text,
        properties={
            "x": width // 2,
            "y": cta_y + (cta_h // 2),
            "font_size": 36,
            "color": "#ffffff",
            "anchor": "mm",
        },
    )

    track_cta = Track(
        id="track_cta",
        name="Kinetic CTA",
        kind="video",
        clips=[cta_btn_canvas, cta_btn_text],
    )

    comp = VideoCompositionSchema(
        id=f"comp_shopify_promo_{int(duration_seconds)}s",
        title=f"Shopify Promo - {title}",
        width=width,
        height=height,
        fps=fps,
        duration_frames=total_frames,
        background_color=background_color,
        tracks=[track_bg, track_product, track_overlay, track_cta],
        metadata={
            "template": "shopify_product_promo",
            "aspect_ratio": "9:16",
            "original_price": original_price,
            "promo_price": promo_price,
            "badge_text": badge_text,
        },
    )

    # Validate complete composition AST
    val_res = TimelineValidator.validate_composition(comp)
    if not val_res.is_valid:
        raise ValueError(f"Composition validation failed: {'; '.join(val_res.errors)}")

    return comp


class ShopifyProductPromoTemplate:
    """Builder class interface for Shopify Product Promo Video Template."""

    @staticmethod
    def build(params: Optional[Dict[str, Any]] = None) -> VideoCompositionSchema:
        """Instantiate Shopify Product Promo template using a parameters dictionary."""
        p = params or {}
        return create_product_promo_composition(
            title=p.get("title", "DNK Minimalist Hoodie"),
            original_price=p.get("original_price", "$120.00"),
            promo_price=p.get("promo_price", "$89.00"),
            badge_text=p.get("badge_text", "-25% OFF"),
            cta_text=p.get("cta_text", "SHOP NOW ON SHOPIFY"),
            product_image_src=p.get("product_image_src", "assets/products/hoodie.png"),
            background_color=p.get("background_color", "#0f172a"),
            width=p.get("width", 1080),
            height=p.get("height", 1920),
            fps=p.get("fps", 30),
            duration_seconds=p.get("duration_seconds", 10.0),
            brand_name=p.get("brand_name", "DNK OS STORE"),
        )
