# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_shopify_models"
# purpose: "Pydantic response models and normalized schemas for Shopify read-only adapter"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

from typing import Optional, List, Literal, Union, Any
from pydantic import BaseModel, Field


ShopifyDataSource = Literal["live", "cache", "fixture"]
ShopifyErrorCode = Literal[
    "timeout",
    "rate_limit",
    "upstream_5xx",
    "unauthorized",
    "not_found",
    "forbidden_store",
    "invalid_asset",
    "mutation_forbidden",
    "connection_error",
    "unknown"
]


class ShopifyRateLimitInfo(BaseModel):
    """Rate limit Leaky Bucket metadata parsed from response headers."""
    call_limit: Optional[str] = Field(None, description="Shopify call limit header, e.g. '1/40'")
    retry_after: Optional[float] = Field(None, description="Seconds to wait before retrying on 429")


class NormalizedShopMeta(BaseModel):
    """Normalized high-level shop information."""
    id: Optional[Union[int, str]] = None
    name: str
    email: Optional[str] = None
    myshopify_domain: str
    domain: Optional[str] = None
    currency: str = "USD"
    plan_name: Optional[str] = None


class NormalizedTheme(BaseModel):
    """Normalized theme descriptor."""
    id: Union[int, str]
    name: str
    role: str = "unpublished"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    previewable: bool = True
    processing: bool = False


class NormalizedThemeAsset(BaseModel):
    """Normalized file metadata inside a Shopify theme."""
    key: str
    content_type: str = "application/octet-stream"
    size: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    public_url: Optional[str] = None


class NormalizedAssetContent(BaseModel):
    """Full text or base64 attachment content of a specific theme asset."""
    key: str
    theme_id: Union[int, str]
    content_type: str = "text/x-liquid"
    value: Optional[str] = None
    attachment: Optional[str] = None
    public_url: Optional[str] = None
    size: Optional[int] = None


class ShopifyAdapterResult(BaseModel):
    """Universal envelope for Shopify Adapter responses guaranteeing metadata invariants."""
    data: Optional[Any] = Field(None, description="Normalized response data or None on error")
    data_source: ShopifyDataSource = Field(..., description="Source of returned data: live | cache | fixture")
    stale: bool = Field(False, description="True if data was served from stale cache due to upstream failure")
    fetched_at: str = Field(..., description="ISO 8601 UTC timestamp when data was fetched or cached")
    expires_at: str = Field(..., description="ISO 8601 UTC timestamp when cached item expires")
    error_code: Optional[ShopifyErrorCode] = Field(None, description="Error classification if call failed")
    rate_limit_info: Optional[ShopifyRateLimitInfo] = Field(None, description="Current Leaky Bucket rate limit metrics")


class NormalizedThemeTree(BaseModel):
    """Categorized file hierarchy of a Shopify theme."""
    store_domain: str
    theme_id: Union[int, str]
    total_files: int
    layout: List[NormalizedThemeAsset] = Field(default_factory=list)
    templates: List[NormalizedThemeAsset] = Field(default_factory=list)
    sections: List[NormalizedThemeAsset] = Field(default_factory=list)
    snippets: List[NormalizedThemeAsset] = Field(default_factory=list)
    assets: List[NormalizedThemeAsset] = Field(default_factory=list)
    config: List[NormalizedThemeAsset] = Field(default_factory=list)
    locales: List[NormalizedThemeAsset] = Field(default_factory=list)


class ShopifyCanvasNode(BaseModel):
    """Visual Canvas Node representation of a Shopify section or template."""
    id: str
    key: str
    node_type: str = "section"
    label: str
    category: str
    content_type: str = "text/x-liquid"
    position_x: float = 0.0
    position_y: float = 0.0
    snippet_dependencies: List[str] = Field(default_factory=list)
    schema_title: Optional[str] = None
    settings_count: int = 0
    size_bytes: int = 0


class ShopifyCanvasEdge(BaseModel):
    """Directed relationship between Canvas nodes (e.g. section -> snippet render)."""
    id: str
    source: str
    target: str
    relationship_type: str = "renders"
    label: Optional[str] = None


class ShopifyCanvasGraph(BaseModel):
    """Full Canvas Whiteboard graph for interactive Shopify Theme visual modeling."""
    store_domain: str
    theme_id: Union[int, str]
    nodes: List[ShopifyCanvasNode] = Field(default_factory=list)
    edges: List[ShopifyCanvasEdge] = Field(default_factory=list)
    generated_at: str = Field(..., description="ISO 8601 UTC timestamp")
