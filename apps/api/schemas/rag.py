# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/schemas/rag.py"
# purpose: "Pydantic validation schemas for Multimodal RAG REST and WebSocket API"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK Swarm (dnk_dev_fullstack & Gerych Prime)"
# --- END DNK-MRH-HEADER ---

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class IngestDocumentRequest(BaseModel):
    file_path: str = Field(description="Relative path to document to ingest")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    workspace_id: Optional[str] = Field(default=None, description="Target workspace ID")


class IngestTextRequest(BaseModel):
    text: str = Field(description="Raw markdown, latex, or text snippet to ingest")
    title: str = Field(default="snippet", description="Identifier or title for the snippet")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    workspace_id: Optional[str] = Field(default=None, description="Target workspace ID")


class IngestResponse(BaseModel):
    doc_id: str
    status: str = "success"
    message: str


class RAGQueryRequest(BaseModel):
    query: str = Field(description="Search question or prompt")
    mode: str = Field(default="hybrid", description="Retrieval mode: text, hybrid, graph")


class MultimodalElementSchema(BaseModel):
    type: str = Field(description="Element type: text, image, table, equation")
    content: str = Field(description="Content, equation, table body, or image path")
    caption: Optional[str] = None
    bounding_box: Optional[Dict[str, float]] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class MultimodalQueryRequest(BaseModel):
    query: str = Field(description="Search question or prompt")
    elements: List[MultimodalElementSchema] = Field(default_factory=list)
    mode: str = Field(default="hybrid", description="Retrieval mode")


class RAGQueryResponse(BaseModel):
    query: str
    answer: str
    referenced_nodes: List[Dict[str, Any]]
    visual_evidence_urls: List[str]
    confidence_score: float
    execution_time_ms: float
    mode: str


class DocumentGraphResponse(BaseModel):
    doc_id: str
    file_path: str
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    total_nodes: int
    total_edges: int


class IngestCanvasRequest(BaseModel):
    nodes: List[Dict[str, Any]] = Field(description="List of Visual Shell Canvas nodes")
    edges: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Optional Canvas connections")
    title: Optional[str] = Field(default="canvas_context", description="Title or identifier for the canvas context")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadata tags")
    workspace_id: Optional[str] = Field(default=None, description="Target workspace ID")


class DualLevelQueryRequest(BaseModel):
    query: str = Field(description="Search inquiry or question")
    mode: str = Field(default="hybrid", description="Retrieval mode: hybrid, local, or global")
    top_k: int = Field(default=5, description="Number of results to retrieve")
    workspace_id: Optional[str] = Field(default=None, description="Target workspace ID")
    workspace_ids: Optional[List[str]] = Field(
        default=None,
        description="Optional list of workspace IDs for cross-workspace retrieval (e.g. ['global-marketing', 'ws-reburn-001'])",
    )


class DualLevelQueryResponse(BaseModel):
    query: str
    mode: str
    themes: List[Dict[str, Any]]
    primary_matches: List[Dict[str, Any]]
    expanded_context: List[Dict[str, Any]]
    combined_context: str
    execution_time_ms: float
    workspace_ids: Optional[List[str]] = None


class SCONESSyncRequest(BaseModel):
    workspace_id: Optional[str] = Field(default="ws-alpha-001", description="Target workspace identifier")


class SCONESSyncResponse(BaseModel):
    status: str = "success"
    synced_nodes: int
    workspace_id: str
    message: str


class CanvasGraphResponse(BaseModel):
    workspace_id: str
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    node_count: int
    edge_count: int
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class MarketingBannerRequest(BaseModel):
    product_name: str = Field(description="Product name or line, e.g. ReBurn Pro Smoker")
    marketing_goal: str = Field(description="Campaign goal, e.g. Facebook lead gen banner focusing on water seal and clean smoke")
    target_audience: Optional[str] = Field(
        default="Outdoor enthusiasts, craft cooks, hunters, and BBQ masters",
        description="Target customer persona",
    )
    framework: Optional[str] = Field(
        default="AIDA",
        description="Marketing framework: AIDA, PAS, BAB, FAB",
    )
    workspace_ids: List[str] = Field(
        default_factory=lambda: ["global-marketing", "ws-alpha-001"],
        description="Knowledge base workspaces to consult (e.g. global marketing patterns + specific product)",
    )
    format: Optional[str] = Field(
        default="square_1_1",
        description="Banner layout format: square_1_1, story_9_16, landscape_16_9",
    )


class MarketingBannerResponse(BaseModel):
    status: str = "success"
    product_name: str
    framework: str
    headline: str
    subheadline: str
    bullet_points: List[str]
    call_to_action: str
    psychological_angle: str
    product_facts_grounded: List[str]
    referenced_assets: List[Dict[str, Any]]
    svg_markup: str
    html_markup: str
    remotion_props: Dict[str, Any]
    canvas_node: Dict[str, Any]
    workspaces_consulted: List[str]
    execution_time_ms: float

