# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_video_ai_creator/src/template_registry.py"
# purpose: "Centralized Template Registry & Factory for dnk_video_ai_creator templates."
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
Extensible Template Registry and Catalog for dnk_video_ai_creator.
Provides template discovery, parameter validation, dynamic instantiation, and tag-based querying.
"""

from typing import Any, Callable, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field
from .shopify_product_promo_template import ShopifyProductPromoTemplate
from .ugc_vertical_reel_template import UGCVerticalReelTemplate
from .video_composition_schema import VideoCompositionSchema


class TemplateMetadata(BaseModel):
    """Metadata schema describing a video template, its limits, tags, and parameters."""
    id: str = Field(..., description="Unique template identifier (e.g. 'shopify_product_promo')")
    name: str = Field(..., description="Human-readable template name")
    description: str = Field(..., description="Description of visual style and purpose")
    aspect_ratio: str = Field(default="9:16", description="Canvas aspect ratio string ('9:16', '16:9', '1:1')")
    duration_range: Dict[str, float] = Field(
        default_factory=lambda: {"min_seconds": 5.0, "max_seconds": 15.0},
        description="Supported video duration limits in seconds",
    )
    default_fps: int = Field(default=30, description="Default FPS for composition generation")
    tags: List[str] = Field(default_factory=list, description="Categorization tags (e.g. ['e-commerce', 'shopify'])")
    parameters_schema: Dict[str, Any] = Field(
        default_factory=dict, description="Dictionary describing available template input parameters"
    )


BuilderCallable = Callable[[Optional[Dict[str, Any]]], VideoCompositionSchema]


class TemplateRegistry:
    """Thread-safe registry managing template registration, lookup, listing, and dynamic creation."""

    def __init__(self) -> None:
        self._registry: Dict[str, Tuple[TemplateMetadata, BuilderCallable]] = {}

    def register(self, metadata: TemplateMetadata, builder_fn: BuilderCallable) -> None:
        """
        Register a new template factory into the registry.

        :param metadata: TemplateMetadata instance describing template capabilities
        :param builder_fn: Callable accepting a dict of parameters and returning a VideoCompositionSchema
        """
        if not metadata.id:
            raise ValueError("TemplateMetadata.id must be a non-empty string.")
        self._registry[metadata.id] = (metadata, builder_fn)

    def get(self, template_id: str) -> Tuple[TemplateMetadata, BuilderCallable]:
        """
        Retrieve metadata and builder function for a given template ID.

        :param template_id: Template identifier string
        :return: Tuple of (TemplateMetadata, BuilderCallable)
        :raises KeyError: If template_id is not registered
        """
        if template_id not in self._registry:
            raise KeyError(f"Template '{template_id}' is not registered in TemplateRegistry.")
        return self._registry[template_id]

    def list_templates(self, tag: Optional[str] = None) -> List[TemplateMetadata]:
        """
        List all registered template metadatas, optionally filtered by tag.

        :param tag: Optional string tag filter
        :return: List of TemplateMetadata matching criteria
        """
        results: List[TemplateMetadata] = []
        for metadata, _ in self._registry.values():
            if tag is None or tag.lower() in [t.lower() for t in metadata.tags]:
                results.append(metadata)
        return results

    def create_composition(self, template_id: str, params: Optional[Dict[str, Any]] = None) -> VideoCompositionSchema:
        """
        Instantiate a VideoCompositionSchema AST from a registered template.

        :param template_id: Registered template identifier
        :param params: Optional parameter override dictionary
        :return: VideoCompositionSchema AST instance
        """
        _, builder_fn = self.get(template_id)
        return builder_fn(params)


def create_default_registry() -> TemplateRegistry:
    """Create and populate a TemplateRegistry instance with all built-in Phase 3 templates."""
    registry = TemplateRegistry()

    # 1. Register Shopify Product Promo Template
    shopify_meta = TemplateMetadata(
        id="shopify_product_promo",
        name="Shopify Product Promo",
        description="High-converting 9:16 promo video with price drop badge, 3D spin/zoom image, and kinetic CTA.",
        aspect_ratio="9:16",
        duration_range={"min_seconds": 5.0, "max_seconds": 15.0},
        default_fps=30,
        tags=["e-commerce", "shopify", "product-promo", "vertical"],
        parameters_schema={
            "title": {"type": "str", "default": "DNK Minimalist Hoodie"},
            "original_price": {"type": "str", "default": "$120.00"},
            "promo_price": {"type": "str", "default": "$89.00"},
            "badge_text": {"type": "str", "default": "-25% OFF"},
            "cta_text": {"type": "str", "default": "SHOP NOW ON SHOPIFY"},
            "product_image_src": {"type": "str", "default": "assets/products/hoodie.png"},
            "background_color": {"type": "str", "default": "#0f172a"},
            "duration_seconds": {"type": "float", "default": 10.0},
        },
    )
    registry.register(shopify_meta, ShopifyProductPromoTemplate.build)

    # 2. Register UGC Vertical Reel Template
    ugc_meta = TemplateMetadata(
        id="ugc_vertical_reel",
        name="UGC Vertical Reel",
        description="TikTok / Reels style UGC review video with profile header, kinetic subtitles, and transitions.",
        aspect_ratio="9:16",
        duration_range={"min_seconds": 5.0, "max_seconds": 15.0},
        default_fps=30,
        tags=["ugc", "vertical", "tiktok", "reels", "kinetic-typography"],
        parameters_schema={
            "username": {"type": "str", "default": "@alex_review"},
            "avatar_src": {"type": "str", "default": "assets/ugc/avatar.png"},
            "media_src": {"type": "str", "default": "assets/ugc/product_review.jpg"},
            "subtitles": {"type": "list[dict]", "default": "timed subtitle list"},
            "cta_text": {"type": "str", "default": "Link in bio to order!"},
            "duration_seconds": {"type": "float", "default": 10.0},
        },
    )
    registry.register(ugc_meta, UGCVerticalReelTemplate.build)

    return registry


# Singleton default registry instance
default_registry: TemplateRegistry = create_default_registry()
