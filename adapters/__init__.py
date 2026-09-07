# --- DNK-MRH-HEADER ---
# mrh_id: "adapters/__init__.py"
# purpose: "DNK OS MVP Framework Adapters Package"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

"""DNK OS Framework Adapters for HuggingFace Transformers, LlamaIndex, CrewAI, AutoGen, and LangGraph."""

from .autogen_adapter import AutoGenAdapter
from .crewai_adapter import CrewAIAdapter
from .dnk_open_design_adapter import (
    OpenDesignAdapter,
    CanvasNode,
    CanvasNodeType,
    CanvasMutation,
    MutationType,
    CanvasBounds,
    CanvasStyle,
    DesignSession,
)
from .langgraph_adapter import LangGraphAdapter
from .llamaindex_adapter import LlamaIndexAdapter
from .transformers_adapter import TransformersAdapter

__all__ = [
    "AutoGenAdapter",
    "CrewAIAdapter",
    "OpenDesignAdapter",
    "CanvasNode",
    "CanvasNodeType",
    "CanvasMutation",
    "MutationType",
    "CanvasBounds",
    "CanvasStyle",
    "DesignSession",
    "LangGraphAdapter",
    "LlamaIndexAdapter",
    "TransformersAdapter",
]
