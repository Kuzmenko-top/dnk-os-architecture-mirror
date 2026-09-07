# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/routers/video_router.py"
# purpose: "FastAPI REST API router for programmatic video generation and Remotion packaging."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

from core.video.kinetic_templates import (
    kinetic_templates,
    KineticTemplateSpec,
    TemplateStyle,
)
from core.video.remotion_renderer import (
    remotion_renderer,
    VideoRenderSpec,
    RenderResult,
)
from core.video.timeline_engine import (
    timeline_engine,
    TimelineComposition,
    TimelineTrack,
    TimelineClip,
    TrackType,
)

router = APIRouter(prefix="/api/v1/video", tags=["Video AI Creator"])


class VideoGenerationRequest(BaseModel):
    template_style: TemplateStyle = TemplateStyle.VIRAL_TIKTOK
    title: str
    hook: str = "Unbelievable Deal"
    price: float
    original_price: Optional[float] = None
    cta_text: str = "Get Yours Now"
    captions: List[str] = Field(default_factory=list)
    reviewer_name: Optional[str] = "Verified Buyer"
    review_text: Optional[str] = "Absolute game-changer!"


@router.get("/templates")
async def list_video_templates():
    """
    Lists available Remotion programmatic video templates with metadata and dimensions.
    """
    return {
        "success": True,
        "templates": [
            {
                "id": "VIRAL_TIKTOK",
                "name": "Viral TikTok Hook Reel",
                "aspect_ratio": "9:16",
                "resolution": "1080x1920",
                "fps": 30,
                "duration_seconds": 5,
                "composition_id": "ViralReelComposition",
                "recommended_for": ["Fashion", "Tech Gadgets", "Impulse Buys"],
            },
            {
                "id": "CLEAN_LUXURY",
                "name": "Clean Luxury UGC Testimonial",
                "aspect_ratio": "9:16",
                "resolution": "1080x1920",
                "fps": 30,
                "duration_seconds": 5,
                "composition_id": "UGCReelComposition",
                "recommended_for": ["High-Ticket Brands", "Jewelry", "Cosmetics"],
            },
            {
                "id": "ECOMMERCE_URGENCY",
                "name": "E-Commerce Flash Sale Countdown",
                "aspect_ratio": "9:16",
                "resolution": "1080x1920",
                "fps": 30,
                "duration_seconds": 5,
                "composition_id": "FlashSaleComposition",
                "recommended_for": ["Black Friday", "Flash Drops", "Clearance"],
            },
        ],
    }


@router.get("/preview/{style}")
async def get_template_preview_scene(style: TemplateStyle = TemplateStyle.VIRAL_TIKTOK, title: str = "DNK Ultra Clean Hoodie", price: float = 89.99):
    """
    Generates declarative Remotion scene graph with kinetic keyframes for live frontend visual rendering.
    """
    return {
        "success": True,
        "style": style.value,
        "title": title,
        "price": price,
        "aspect_ratio": "9:16",
        "duration_frames": 150,
        "fps": 30,
        "scenes": [
            {
                "id": "scene_hook",
                "start_frame": 0,
                "end_frame": 45,
                "type": "kinetic_hook",
                "text": f"Wait! Stop Scrolling! 🔥",
                "animation": "pop_in_spring",
            },
            {
                "id": "scene_product",
                "start_frame": 46,
                "end_frame": 105,
                "type": "product_showcase",
                "title": title,
                "price": f"${price:.2f}",
                "original_price": f"${price * 1.5:.2f}",
                "animation": "slide_up_fade",
            },
            {
                "id": "scene_cta",
                "start_frame": 106,
                "end_frame": 150,
                "type": "call_to_action",
                "cta_text": "Claim 50% OFF Today",
                "animation": "pulse_glow",
            },
        ],
    }


@router.post("/generate", response_model=RenderResult)
async def generate_video_ad(request: VideoGenerationRequest):
    try:
        spec = KineticTemplateSpec(
            template_name="ad_campaign_reel",
            style=request.template_style,
            title=request.title,
            hook=request.hook,
            price=request.price,
            original_price=request.original_price,
            cta_text=request.cta_text,
            captions=request.captions,
            reviewer_name=request.reviewer_name or "Verified Buyer",
            review_text=request.review_text or "Great product!",
        )

        if request.template_style == TemplateStyle.CLEAN_LUXURY and hasattr(kinetic_templates, "generate_social_proof_ugc_tsx"):
            tsx_code = kinetic_templates.generate_social_proof_ugc_tsx(spec)
            comp_id = "UGCReelComposition"
        elif request.template_style == TemplateStyle.ECOMMERCE_URGENCY and hasattr(kinetic_templates, "generate_flash_sale_countdown_tsx"):
            tsx_code = kinetic_templates.generate_flash_sale_countdown_tsx(spec)
            comp_id = "FlashSaleComposition"
        else:
            tsx_code = kinetic_templates.generate_viral_reel_tsx(spec)
            comp_id = "ViralReelComposition"

        render_spec = VideoRenderSpec(
            composition_id=comp_id,
            width=1080,
            height=1920,
            fps=30,
            duration_in_frames=150,
            tsx_component_code=tsx_code,
            output_filename=f"video_ad_{int(spec.price)}_{spec.style.value.lower()}.mp4",
            props={
                "title": spec.title,
                "hook": spec.hook,
                "price": spec.price,
                "original_price": spec.original_price,
                "cta_text": spec.cta_text,
                "captions": spec.captions,
                "reviewer_name": request.reviewer_name,
                "review_text": request.review_text,
            },
        )

        result = await remotion_renderer.render_video(render_spec)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


class TimelineSynthesisRequest(BaseModel):
    title: str = "DNK Ultra Clean Hoodie"
    price: float = 89.99
    original_price: Optional[float] = None
    hook: str = "Wait! Stop Scrolling! 🔥"
    cta_text: str = "Order Now with 50% OFF"
    template_style: str = "VIRAL_TIKTOK"


@router.get("/timeline")
async def get_default_timeline():
    """
    Returns default multi-track video timeline composition.
    """
    comp = timeline_engine.synthesize_ad_timeline()
    return {"success": True, "composition": comp}


@router.post("/timeline/synthesize")
async def synthesize_timeline_project(req: TimelineSynthesisRequest):
    """
    Synthesizes a full 4-track timeline AST (Video, Kinetic Subtitles, Audio, Badges) from prompt/product data.
    """
    comp = timeline_engine.synthesize_ad_timeline(
        title=req.title,
        price=req.price,
        original_price=req.original_price,
        hook=req.hook,
        cta_text=req.cta_text,
        template_style=req.template_style,
    )
    tsx_code = timeline_engine.compile_to_remotion_tsx(comp)
    return {"success": True, "composition": comp, "tsx_code": tsx_code}


@router.post("/timeline/compile-tsx")
async def compile_timeline_to_tsx(composition: TimelineComposition):
    """
    Compiles given multi-track timeline AST into Remotion TSX code.
    """
    tsx_code = timeline_engine.compile_to_remotion_tsx(composition)
    return {"success": True, "tsx_code": tsx_code}
