# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_video_ai_creator/src/__init__.py"
# purpose: "Core module exports for dnk_video_ai_creator (Phase 1, 2, 3 & 4)."
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.3.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

"""
dnk_video_ai_creator core module exports.
"""

from .cache_manager import (
    CacheEntry,
    CacheManager,
    get_default_cache_manager,
)
from .easing_functions import (
    cubic_bezier,
    cubic_in,
    cubic_in_out,
    cubic_out,
    evaluate_easing,
    get_easing_function,
    linear,
    quad_in,
    quad_in_out,
    quad_out,
    spring,
)
from .ffmpeg_orchestrator import FFmpegOrchestrator, RenderResult
from .fps_controller import FPSController
from .headless_renderer import HeadlessRenderer
from .job_queue import (
    JobStatus,
    JobType,
    MediaJob,
    MediaJobQueue,
    default_job_queue,
    get_default_job_queue,
)
from .keyframe_interpolator import KeyframeInterpolator
from .media_router import (
    JobResponse,
    PreviewRequest,
    RenderRequest,
    TemplateListResponse,
    router as media_router,
)
from .progress_streamer import (
    ProgressEvent,
    ProgressStreamer,
    RenderStage,
    default_progress_streamer,
    get_default_progress_streamer,
)
from .shopify_product_promo_template import (
    ShopifyProductPromoTemplate,
    create_product_promo_composition,
)
from .template_registry import (
    TemplateMetadata,
    TemplateRegistry,
    create_default_registry,
    default_registry,
)
from .timeline_validator import TimelineValidator, ValidationResult
from .ugc_vertical_reel_template import (
    UGCVerticalReelTemplate,
    create_ugc_vertical_reel_composition,
)
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

__all__ = [
    "AnimatedProperty",
    "CacheEntry",
    "CacheManager",
    "Clip",
    "ClipType",
    "EasingType",
    "FFmpegOrchestrator",
    "FPSController",
    "HeadlessRenderer",
    "JobResponse",
    "JobStatus",
    "JobType",
    "Keyframe",
    "KeyframeInterpolator",
    "MediaJob",
    "MediaJobQueue",
    "PreviewRequest",
    "ProgressEvent",
    "ProgressStreamer",
    "RenderRequest",
    "RenderResult",
    "RenderStage",
    "ShopifyProductPromoTemplate",
    "TemplateListResponse",
    "TemplateMetadata",
    "TemplateRegistry",
    "TimelineValidator",
    "Track",
    "Transition",
    "TransitionType",
    "UGCVerticalReelTemplate",
    "ValidationResult",
    "VideoCompositionSchema",
    "create_default_registry",
    "create_product_promo_composition",
    "create_ugc_vertical_reel_composition",
    "cubic_bezier",
    "cubic_in",
    "cubic_in_out",
    "cubic_out",
    "default_job_queue",
    "default_progress_streamer",
    "default_registry",
    "evaluate_easing",
    "get_default_cache_manager",
    "get_default_job_queue",
    "get_default_progress_streamer",
    "get_easing_function",
    "linear",
    "media_router",
    "quad_in",
    "quad_in_out",
    "quad_out",
    "spring",
]
