# --- DNK-MRH-HEADER ---
# mrh_id: "tests/media/test_phase3_video_engine.py"
# purpose: "Unit tests for DNK-MEDIA-001 Phase 3: E-commerce Templates & Template Registry."
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
    ShopifyProductPromoTemplate,
    TemplateMetadata,
    TemplateRegistry,
    UGCVerticalReelTemplate,
    VideoCompositionSchema,
    create_default_registry,
    create_product_promo_composition,
    create_ugc_vertical_reel_composition,
)


def test_shopify_product_promo_template_generation():
    """Test generating a valid Shopify Product Promo AST composition."""
    comp = create_product_promo_composition(
        title="DNK Tactical Backpack",
        original_price="$150.00",
        promo_price="$99.00",
        badge_text="-34% OFF",
        cta_text="GET YOURS TODAY",
        product_image_src="assets/products/backpack.jpg",
        duration_seconds=10.0,
        fps=30,
    )

    assert isinstance(comp, VideoCompositionSchema)
    assert comp.width == 1080
    assert comp.height == 1920
    assert comp.fps == 30
    assert comp.duration_frames == 300
    assert len(comp.tracks) == 4

    # Verify metadata
    assert comp.metadata["template"] == "shopify_product_promo"
    assert comp.metadata["promo_price"] == "$99.00"
    assert comp.metadata["badge_text"] == "-34% OFF"

    # Verify tracks content
    track_names = [t.name for t in comp.tracks]
    assert "Background & Brand" in track_names
    assert "Product Media" in track_names
    assert "Title & Price Badges" in track_names
    assert "Kinetic CTA" in track_names


def test_shopify_product_promo_security_rejection():
    """Test fail-closed path traversal and forbidden scheme rejection in Shopify Product Promo template."""
    # Path traversal attack attempt
    with pytest.raises(ValueError, match="Invalid product_image_src resource path"):
        create_product_promo_composition(product_image_src="../../etc/passwd.jpg")

    # Forbidden scheme attack attempt
    with pytest.raises(ValueError, match="Invalid product_image_src resource path"):
        create_product_promo_composition(product_image_src="javascript:alert(1)")


def test_ugc_vertical_reel_template_generation():
    """Test generating a valid UGC Vertical Reel AST composition."""
    subtitles = [
        {"start_frame": 0, "end_frame": 60, "text": "This item completely blew my mind!"},
        {"start_frame": 60, "end_frame": 120, "text": "Super fast shipping and 10/10 build quality."},
    ]

    comp = create_ugc_vertical_reel_composition(
        username="@tech_reviewer_2026",
        avatar_src="assets/ugc/tech_avatar.png",
        media_src="assets/ugc/review_clip.jpg",
        subtitles=subtitles,
        cta_text="Check link in bio!",
        duration_seconds=8.0,
        fps=30,
    )

    assert isinstance(comp, VideoCompositionSchema)
    assert comp.width == 1080
    assert comp.height == 1920
    assert comp.fps == 30
    assert comp.duration_frames == 240
    assert len(comp.tracks) == 4

    # Verify metadata & subtitles
    assert comp.metadata["template"] == "ugc_vertical_reel"
    assert comp.metadata["username"] == "@tech_reviewer_2026"
    assert comp.metadata["subtitles_count"] == 2


def test_ugc_vertical_reel_security_rejection():
    """Test fail-closed security boundary rejection in UGC Vertical Reel template."""
    with pytest.raises(ValueError, match="Invalid avatar_src resource path"):
        create_ugc_vertical_reel_composition(avatar_src="../secret_keys.png")

    with pytest.raises(ValueError, match="Invalid media_src resource path"):
        create_ugc_vertical_reel_composition(media_src="/absolute/system/path.mov")


def test_template_registry_registration_and_lookup():
    """Test TemplateRegistry custom template registration, retrieval, listing, and dynamic composition creation."""
    registry = TemplateRegistry()

    meta = TemplateMetadata(
        id="custom_promo",
        name="Custom Test Promo",
        description="Test template for registry functionality",
        aspect_ratio="1:1",
        default_fps=30,
        tags=["test", "custom"],
    )

    # Register custom builder
    registry.register(meta, ShopifyProductPromoTemplate.build)

    # Lookup
    retrieved_meta, builder_fn = registry.get("custom_promo")
    assert retrieved_meta.name == "Custom Test Promo"

    # List with tag filtering
    tagged_list = registry.list_templates(tag="custom")
    assert len(tagged_list) == 1
    assert tagged_list[0].id == "custom_promo"

    # Create composition via registry
    comp = registry.create_composition("custom_promo", {"title": "Registry Test Product"})
    assert isinstance(comp, VideoCompositionSchema)


def test_template_registry_default_templates():
    """Test that default_registry includes built-in Phase 3 templates."""
    registry = create_default_registry()

    templates = registry.list_templates()
    template_ids = [t.id for t in templates]

    assert "shopify_product_promo" in template_ids
    assert "ugc_vertical_reel" in template_ids

    # Test creating shopify promo composition via default registry
    comp_shopify = registry.create_composition("shopify_product_promo", {"title": "Hoodie Promo"})
    assert comp_shopify.metadata["template"] == "shopify_product_promo"

    # Test creating UGC reel composition via default registry
    comp_ugc = registry.create_composition("ugc_vertical_reel", {"username": "@test_user"})
    assert comp_ugc.metadata["template"] == "ugc_vertical_reel"


def test_deterministic_template_output():
    """Test that same template inputs produce identical AST output dictionaries (determinism invariant)."""
    comp1 = create_product_promo_composition(title="Deterministic Product", promo_price="$50.00")
    comp2 = create_product_promo_composition(title="Deterministic Product", promo_price="$50.00")

    assert comp1.model_dump() == comp2.model_dump()


def test_ugc_vertical_reel_custom_transitions():
    """Test UGC Vertical Reel template with explicit transition list (Glitch, Slide, Kinetic Zoom)."""
    custom_transitions = [
        {"id": "t1", "from_clip_id": "ugc_media_01", "to_clip_id": "ugc_subtitle_txt_01", "type": "glitch", "duration_frames": 12},
        {"id": "t2", "from_clip_id": "ugc_subtitle_txt_01", "to_clip_id": "ugc_subtitle_txt_02", "type": "kinetic_zoom", "duration_frames": 15},
    ]
    subtitles = [
        {"start_frame": 0, "end_frame": 60, "text": "Clip 1"},
        {"start_frame": 60, "end_frame": 120, "text": "Clip 2"},
    ]
    comp = create_ugc_vertical_reel_composition(
        subtitles=subtitles,
        transitions=custom_transitions,
    )
    assert len(comp.transitions) == 2
    assert comp.transitions[0].transition_type.value == "glitch"
    assert comp.transitions[1].transition_type.value == "kinetic_zoom"


def test_template_registry_error_handling():
    """Test error handling in TemplateRegistry for unregistered lookup or invalid metadata."""
    registry = TemplateRegistry()
    with pytest.raises(KeyError, match="not registered"):
        registry.get("non_existent_template")

    with pytest.raises(ValueError, match="id must be a non-empty string"):
        meta = TemplateMetadata(id="", name="Empty ID", description="Test")
        registry.register(meta, ShopifyProductPromoTemplate.build)


def test_phase3_headless_rendering_integration():
    """Test headless frame rendering of Phase 3 template compositions."""
    from services.dnk_video_ai_creator.src import HeadlessRenderer

    comp = create_product_promo_composition(title="Render Test")
    renderer = HeadlessRenderer(comp)

    # Render frame 0 (RGBA Image)
    frame = renderer.render_frame(0)
    assert frame.size == (1080, 1920)
    assert frame.mode == "RGBA"

    # Render mid-duration frame
    mid_frame = renderer.render_frame(150)
    assert mid_frame.size == (1080, 1920)
    assert mid_frame.mode == "RGBA"

